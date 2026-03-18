
import os
import pickle
import base64
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from langchain_ollama import OllamaLLM
from langchain.schema import HumanMessage

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()

# -------------------------------
# Gmail API scopes (read + send)
# -------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]

# -------------------------------
# Step 1: Authenticate Gmail
# -------------------------------
def authenticate_gmail():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return creds

# -------------------------------
# Step 2: Decode email body safely
# -------------------------------
def decode_email_body(data: str) -> str:
    text = base64.urlsafe_b64decode(data)
    try:
        return text.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return text.decode("latin-1")
        except Exception:
            return text.decode(errors="ignore")

# -------------------------------
# Step 3: Fetch unread emails
# -------------------------------
def fetch_unread_emails(service, max_results=10):
    emails_list = []

    results = service.users().messages().list(userId="me", q="is:unread", maxResults=max_results).execute()
    if "messages" not in results:
        print("✅ No unread emails found.")
        return emails_list

    for msg in results["messages"]:
        msg_data = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        payload = msg_data["payload"]

        headers = payload.get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "(Unknown Sender)")

        body = ""
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    data = part["body"].get("data")
                    if data:
                        body = decode_email_body(data)
                        break
        else:
            data = payload["body"].get("data")
            if data:
                body = decode_email_body(data)

        emails_list.append({
            "sender": sender,
            "subject": subject,
            "body": body[:1000]  # limit to 1000 chars
        })

    return emails_list

# -------------------------------
# Step 4: Summarize & Categorize Emails using OllamaLLM
# -------------------------------
# -------------------------------
# Step 4: Summarize & Categorize Emails using OllamaLLM
# -------------------------------
def summarize_and_categorize(emails_list):
    if not emails_list:
        return "<p>✅ No emails to summarize.</p>"

    llm = OllamaLLM(model="llama2:13b-chat")  # Using Llama2 Chat

    formatted_emails = ""
    for e in emails_list:
        formatted_emails += f"Sender: {e['sender']}\nSubject: {e['subject']}\nBody: {e['body']}\n\n"

    prompt = f"""
You are an AI assistant. Categorize each email into one of three categories with strict adherence to these rules:
1. Items Requiring Attention: Emails needing immediate action, such as job alerts with 'apply now', financial deadlines (e.g., 'payment', 'due'), IPO alerts, or time-sensitive opportunities with explicit deadlines (e.g., 'deadline', 'few hours left'). Example: 'Machine Learning Engineer at Quantiphi and 10 more jobs' or 'IPO ALERT - AIRFLOA RAIL TECHNOLOGY'.
2. Items to Review Later: Informational emails with no immediate action, such as newsletters, balance statements, or general notifications without deadlines. Example: 'Funds / Securities Balance' or 'Introduction to Machine Learning Update'.
3. Items of No Immediate Relevance: Spam, promotions, or marketing emails without urgent action keywords (e.g., general offers, contests without deadlines). Example: '₹7,999/year for unlimited access to Meta courses'.

Return ONLY the HTML content in PROFESSIONAL HTML format with EXACTLY the following structure:
- Start with '<h1>========== DAILY EMAIL DIGEST ==========</h1>'
- For each category (e.g., Items Requiring Attention, Items to Review Later, Items of No Immediate Relevance), use '<h2>[Category Name]</h2><ul>' followed by '<li>Sender: [sender] Subject: [subject] Summary: [concise summary reflecting the categorization reason]</li>' for each email in that category, and close with '</ul>'
- End with '<p style=\"color:gray; font-size:small;\">**Disclaimer:** This email digest is for informational purposes only and does not constitute professional advice. Please review the emails carefully and take appropriate action as needed.</p>'
- Ensure proper nesting of <ul> and <li> tags, and include all three categories (Items Requiring Attention, Items to Review Later, Items of No Immediate Relevance) even if empty.
- Do NOT include any text outside this HTML structure, such as category names without tags or extra lines.

Emails:
{formatted_emails}
"""

    # Call LLM
    response = llm.invoke([HumanMessage(content=prompt)])

    # Extract text safely and ensure clean HTML
    if hasattr(response, "content"):
        digest_html = response.content.strip()
    elif isinstance(response, str):
        digest_html = response.strip()
    else:
        digest_html = str(response).strip()

    # Fallback to enforce HTML structure if malformed
    if not digest_html.startswith("<h1>========== DAILY EMAIL DIGEST ==========</h1>"):
        digest_html = "<h1>========== DAILY EMAIL DIGEST ==========</h1>"
        digest_html += "\n<h2>Items Requiring Attention</h2><ul></ul>"
        digest_html += "\n<h2>Items to Review Later</h2><ul></ul>"
        digest_html += "\n<h2>Items of No Immediate Relevance</h2><ul></ul>"
        digest_html += "\n<p style=\"color:gray; font-size:small;\">**Disclaimer:** This email digest is for informational purposes only and does not constitute professional advice. Please review the emails carefully and take appropriate action as needed.</p>"

    return digest_html

# -------------------------------
# Step 5: Send Digest Email
# -------------------------------
def send_email(service, to, subject, html_body):
    message = MIMEText(html_body, "html")  # send as HTML
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    msg = {'raw': raw}
    service.users().messages().send(userId="me", body=msg).execute()
    print(f"✅ Digest sent to {to}")

# -------------------------------
# Step 6: Main Execution
# -------------------------------
if __name__ == "__main__":
    creds = authenticate_gmail()
    service = build(serviceName="gmail", version="v1", credentials=creds)

    max_results = int(os.getenv("MAX_RESULTS_OLLAMA", 10))
    emails_list = fetch_unread_emails(service, max_results=max_results)

    digest_html = summarize_and_categorize(emails_list)

    print("\n========== DAILY EMAIL DIGEST ==========\n")
    print(digest_html)

    # Send digest email as professional HTML
    send_email(
        service,
        to=os.getenv("RECIPIENT_EMAIL"),
        subject=os.getenv("EMAIL_SUBJECT"),
        html_body=digest_html
    )