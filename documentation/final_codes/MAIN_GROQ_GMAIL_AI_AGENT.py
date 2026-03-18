import os
import pickle
import base64
import re
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from langchain_community.tools.gmail.utils import build_resource_service
from langchain_groq import ChatGroq

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
# Step 2B: Mask sensitive information for privacy
# -------------------------------
def mask_sensitive_info(text: str) -> str:
    # Mask phone numbers (various formats)
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}'
    text = re.sub(phone_pattern, 'xxxxxxxxxx', text)

    # Mask email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    text = re.sub(email_pattern, 'xxxxxxxxxx', text)

    # Mask monetary amounts (e.g., $123.45, 100 USD)
    amount_pattern = r'[\$\£\€]?\d+(?:[.,]\d{2})?\s?(?:USD|EUR|GBP|INR)?\b'
    text = re.sub(amount_pattern, 'xxxxxxxxxx', text, flags=re.IGNORECASE)

    # Mask transaction IDs (e.g., after "transaction ID:", alphanumeric sequences of 6+ chars)
    trans_pattern = r'(transaction\s*(id|number|ref|reference)?\s*[:=]?\s*)[\w-]{6,}'
    text = re.sub(trans_pattern, r'\1xxxxxxxxxx', text, flags=re.IGNORECASE)

    # Mask credit card numbers (13-16 digits, with optional spaces/dashes)
    cc_pattern = r'\b(?:\d{4}[ -]?){3}\d{4}\b'
    text = re.sub(cc_pattern, 'xxxxxxxxxx', text)

    # Mask bank account numbers (assuming 8-12 digits, optional IBAN-like prefixes)
    account_pattern = r'\b(IBAN\s*)?[\w]{0,4}\s*\d{8,12}\b'
    text = re.sub(account_pattern, 'xxxxxxxxxx', text, flags=re.IGNORECASE)

    return text

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
                data = part["body"].get("data")
                if data:
                    decoded = decode_email_body(data)
                    if part["mimeType"] == "text/plain":
                        body = decoded
                        break
                    elif part["mimeType"] == "text/html" and not body:
                        body = BeautifulSoup(decoded, "html.parser").get_text()
        else:
            data = payload["body"].get("data")
            if data:
                body = decode_email_body(data)

        # Mask sensitive info in body immediately after fetching
        masked_body = mask_sensitive_info(body.strip()[:1000])  # limit to 1000 chars after masking

        emails_list.append({
            "sender": sender,
            "subject": subject,
            "body": masked_body
        })

    return emails_list

# -------------------------------
# Step 4: Summarize & Categorize Emails using Groq
# -------------------------------
def summarize_and_categorize(emails_list):
    if not emails_list:
        return "<p>✅ No emails to summarize.</p>"

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("❌ GROQ_API_KEY not found in environment variables!")

    llm = ChatGroq(model="openai/gpt-oss-120b", api_key=groq_api_key)

    formatted_emails = ""
    for e in emails_list:
        # Mask sender and subject as well for extra privacy
        masked_sender = mask_sensitive_info(e['sender'])
        masked_subject = mask_sensitive_info(e['subject'])
        formatted_emails += f"Sender: {masked_sender}\nSubject: {masked_subject}\nBody: {e['body']}\n\n"

    prompt = f"""
You are an AI assistant. Categorize each email into one of three categories with ABSOLUTE adherence to these rules:
1. Items Requiring Attention: Emails requiring immediate action, such as:
   - Financial deadlines (e.g., 'payment,' 'due,' 'invoice,' 'transaction,' 'bill') with a specific date or urgency.
   - IPO alerts (e.g., 'IPO ALERT,' 'investment opportunity') with application details.
   - Job applications (e.g., 'job,' 'hiring,' 'apply now,' 'vacancy') with clear action steps.
   - Time-sensitive opportunities with explicit deadlines (e.g., 'deadline,' 'due by,' 'apply before').
2. Items to Review Later: Informational emails with no immediate action, such as:
   - Course updates or newsletters.
   - General bank notifications without deadlines.
3. Items of No Immediate Relevance: Spam, general promotions, contests, or marketing emails without urgent action keywords.

Note: The email content may contain 'xxxxxxxxxx' placeholders for sensitive information like phone numbers, emails, amounts, transaction IDs, credit card numbers, or bank account numbers. Treat these as generic sensitive information in your summarization.

Return the digest in **HTML format** with:
- <h1>========== DAILY EMAIL DIGEST ==========</h1> as the header
- Each category as an <h2> heading
- Each email as a <li> with the format: 'Sender: [sender] Subject: [subject] Summary: [concise summary]'
- End with a disclaimer.
Emails:
{formatted_emails}
"""

    response = llm.invoke(prompt)
    digest_html = response.content if hasattr(response, "content") else str(response)

    digest_html = digest_html.replace("'''html", "").replace("'''", "").strip()

    # -------------------------------
    # Step 4B: Post-process categorization
    # -------------------------------
    keywords_attention = [
        "ipo", "alert", "payment", "transaction", "due", "deadline",
        "invoice", "bill", "job", "hiring", "vacancy", "apply now", "due by", "apply before"
    ]
    exclude_promotions = ["promotion", "offer", "discount", "voucher", "contest"]
    exclude_informational = ["update", "notification", "learn more"]

    for kw in keywords_attention:
        matches = re.findall(r"<li>.*?" + re.escape(kw) + r".*?</li>", digest_html, flags=re.IGNORECASE | re.DOTALL)
        for m in matches:
            is_promotion = any(exclude_kw in m.lower() for exclude_kw in exclude_promotions)
            is_informational = any(exclude_kw in m.lower() for exclude_kw in exclude_informational)
            if not (is_promotion or is_informational):
                digest_html = digest_html.replace(m, "")
                if "<h2>Items Requiring Attention</h2>" in digest_html:
                    digest_html = digest_html.replace(
                        "<h2>Items Requiring Attention</h2>",
                        "<h2>Items Requiring Attention</h2>\n<ul>" + m + "</ul>"
                    )
                else:
                    digest_html = digest_html.replace(
                        "<h1>========== DAILY EMAIL DIGEST ==========</h1>",
                        "<h1>========== DAILY EMAIL DIGEST ==========</h1>\n<h2>Items Requiring Attention</h2>\n<ul>" + m + "</ul>"
                    )

    digest_html = re.sub(r"<h2>.*?</h2>\s*<ul></ul>", "", digest_html, flags=re.DOTALL)

    # -------------------------------
    # Step 4C: Add Priority Scoring System
    # -------------------------------
    leadership_keywords = ["ceo", "cto", "founder", "director", "manager", "leadership"]

    def sort_and_tag_priority(html_block):
        """Reorders list items so HIGH PRIORITY appear first."""
        items = re.findall(r"<li>.*?</li>", html_block, flags=re.DOTALL | re.IGNORECASE)
        priority_items, normal_items = [], []

        for item in items:
            if any(kw in item.lower() for kw in leadership_keywords):
                tagged = item.replace(
                    "<li>",
                    "<li><span style='color:red; font-weight:bold;'>[HIGH PRIORITY]</span> "
                )
                priority_items.append(tagged)
            else:
                normal_items.append(item)

        return "".join(priority_items + normal_items)

    digest_html = re.sub(
        r"(<ul>)(.*?)(</ul>)",
        lambda m: f"{m.group(1)}{sort_and_tag_priority(m.group(2))}{m.group(3)}",
        digest_html,
        flags=re.DOTALL | re.IGNORECASE
    )

    return digest_html

# -------------------------------
# Step 5: Send Digest Email
# -------------------------------
def send_email(service, to, subject, html_body):
    message = MIMEText(html_body, "html", "utf-8")
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
    service = build_resource_service(creds)
    max_results = int(os.getenv("MAX_RESULTS_GROQ", 10))
    emails_list = fetch_unread_emails(service, max_results=max_results)

    digest_html = summarize_and_categorize(emails_list)

    print("\n========== DAILY EMAIL DIGEST ==========\n")
    print(digest_html)

    send_email(
        service,
        to=os.getenv("RECIPIENT_EMAIL"),
        subject=os.getenv("EMAIL_SUBJECT"),
        html_body=digest_html
    )

