# import os
# import pickle
# import base64
# from dotenv import load_dotenv
# from google.auth.transport.requests import Request
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from email.mime.text import MIMEText
# from langchain_ollama import OllamaLLM
# from langchain.schema import HumanMessage

# # -------------------------------
# # Load environment variables
# # -------------------------------
# load_dotenv()

# # -------------------------------
# # Gmail API scopes (read + send)
# # -------------------------------
# SCOPES = [
#     "https://www.googleapis.com/auth/gmail.readonly",
#     "https://www.googleapis.com/auth/gmail.send"
# ]

# # -------------------------------
# # Step 1: Authenticate Gmail
# # -------------------------------
# def authenticate_gmail():
#     creds = None
#     if os.path.exists("token.pickle"):
#         with open("token.pickle", "rb") as token:
#             creds = pickle.load(token)

#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
#             creds = flow.run_local_server(port=0)

#         with open("token.pickle", "wb") as token:
#             pickle.dump(creds, token)

#     return creds

# # -------------------------------
# # Step 2: Decode email body safely
# # -------------------------------
# def decode_email_body(data: str) -> str:
#     text = base64.urlsafe_b64decode(data)
#     try:
#         return text.decode("utf-8")
#     except UnicodeDecodeError:
#         try:
#             return text.decode("latin-1")
#         except Exception:
#             return text.decode(errors="ignore")

# # -------------------------------
# # Step 3: Fetch unread emails
# # -------------------------------
# def fetch_unread_emails(service, max_results=10):
#     emails_list = []

#     results = service.users().messages().list(userId="me", q="is:unread", maxResults=max_results).execute()
#     if "messages" not in results:
#         print("✅ No unread emails found.")
#         return emails_list

#     for msg in results["messages"]:
#         msg_data = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
#         payload = msg_data["payload"]

#         headers = payload.get("headers", [])
#         subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
#         sender = next((h["value"] for h in headers if h["name"] == "From"), "(Unknown Sender)")

#         body = ""
#         if "parts" in payload:
#             for part in payload["parts"]:
#                 if part["mimeType"] == "text/plain":
#                     data = part["body"].get("data")
#                     if data:
#                         body = decode_email_body(data)
#                         break
#         else:
#             data = payload["body"].get("data")
#             if data:
#                 body = decode_email_body(data)

#         emails_list.append({
#             "sender": sender,
#             "subject": subject,
#             "body": body[:1000]  # limit to 1000 chars
#         })

#     return emails_list

# # -------------------------------
# # Step 4: Summarize & Categorize Emails using OllamaLLM
# # -------------------------------
# # def summarize_and_categorize(emails_list):
# #     if not emails_list:
# #         return "✅ No emails to summarize."

# #     llm = OllamaLLM(model="llama2:13b-chat")  # Using Llama2 Chat

# #     formatted_emails = ""
# #     for e in emails_list:
# #         formatted_emails += f"Sender: {e['sender']}\nSubject: {e['subject']}\nBody: {e['body']}\n\n"

# #     prompt = f"""
# # You are an AI assistant. 
# # Categorize each email into one of three categories:

# # 1. Items Requiring Attention (needs action/response)
# # 2. Items to Review Later (informational, useful later)
# # 3. Items of No Immediate Relevance (spam/promotions)

# # Return the digest in professional HTML format, with clear headings, colors, and sections. Include concise summaries.
# # Emails:
# # {formatted_emails}
# # """

# #     # Call LLM
# #     response = llm.invoke([HumanMessage(content=prompt)])

# #     # Extract text safely
# #     if hasattr(response, "content"):
# #         return response.content
# #     elif isinstance(response, str):
# #         return response
# #     else:
# #         return str(response)

# # -------------------------------
# # Step 4: Summarize & Categorize Emails using OllamaLLM
# # -------------------------------
# # def summarize_and_categorize(emails_list):
# #     if not emails_list:
# #         return "✅ No emails to summarize."

# #     llm = OllamaLLM(model="llama2:13b-chat")  # Using Llama2 Chat

# #     formatted_emails = ""
# #     for e in emails_list:
# #         formatted_emails += f"Sender: {e['sender']}\nSubject: {e['subject']}\nBody: {e['body']}\n\n"

# #     prompt = f"""
# # You are an AI assistant. 
# # Categorize each email into one of three categories:

# # 1. Items Requiring Attention (needs action/response)
# # 2. Items to Review Later (informational, useful later)
# # 3. Items of No Immediate Relevance (spam/promotions)

# # Return the digest in plain text format with the following structure:
# # - Use '========== DAILY EMAIL DIGEST ==========' as the header.
# # - List categories as '* Items Requiring Attention:'
# #   '* Items to Review Later:'
# #   '* Items of No Immediate Relevance:'
# # - Number each item under the categories (e.g., 1., 2., 3.).
# # - Keep summaries concise and professional.
# # - End with 'Please note that the categorization is based on the content of the email provided and may not be accurate or comprehensive.'
# # Emails:
# # {formatted_emails}
# # """

# #     # Call LLM
# #     response = llm.invoke([HumanMessage(content=prompt)])

# #     # Extract text safely
# #     if hasattr(response, "content"):
# #         return response.content
# #     elif isinstance(response, str):
# #         return response
# #     else:
# #         return str(response)

# # -------------------------------
# # Step 4: Summarize & Categorize Emails using OllamaLLM
# # -------------------------------
# def summarize_and_categorize(emails_list):
#     if not emails_list:
#         return "<p>✅ No emails to summarize.</p>"

#     llm = OllamaLLM(model="llama2:13b-chat")  # Using Llama2 Chat

#     formatted_emails = ""
#     for e in emails_list:
#         formatted_emails += f"""
#         <p><b>Sender:</b> {e['sender']}<br>
#         <b>Subject:</b> {e['subject']}<br>
#         <b>Body:</b> {e['body']}</p>
#         """

#     prompt = f"""
# You are an AI assistant. 
# Categorize each email into one of three categories:

# 1. Items Requiring Attention (needs action/response)
# 2. Items to Review Later (informational, useful later)
# 3. Items of No Immediate Relevance (spam/promotions)

# Return the digest in PROFESSIONAL HTML format with the following rules:
# - Add a big header: <h2 style="color:#2E86C1;">📬 Daily Email Digest</h2>
# - Use <h3> for category titles
# - Use <ul><li> for listing emails inside each category
# - Keep summaries concise and professional
# - End with a footer line: <p style="color:gray; font-size:small;">⚠️ Categorization is AI-generated and may not be fully accurate.</p>

# Emails:
# {formatted_emails}
# """

#     # Call LLM
#     response = llm.invoke([HumanMessage(content=prompt)])

#     # Extract text safely
#     if hasattr(response, "content"):
#         return response.content
#     elif isinstance(response, str):
#         return response
#     else:
#         return str(response)








# # -------------------------------
# # Step 5: Send Digest Email
# # -------------------------------
# def send_email(service, to, subject, html_body):
#     message = MIMEText(html_body, "html")  # send as HTML
#     message['to'] = to
#     message['subject'] = subject
#     raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
#     msg = {'raw': raw}
#     service.users().messages().send(userId="me", body=msg).execute()
#     print(f"✅ Digest sent to {to}")

# # -------------------------------
# # Step 6: Main Execution
# # -------------------------------
# if __name__ == "__main__":
#     creds = authenticate_gmail()
#     service = build(serviceName="gmail", version="v1", credentials=creds)

#     emails_list = fetch_unread_emails(service, max_results=3)

#     digest_html = summarize_and_categorize(emails_list)

#     print("\n========== DAILY EMAIL DIGEST ==========\n")
#     print(digest_html)

#     # Send digest email as professional HTML
#     send_email(
#         service,
#         to="namya.vishal.shah.campus@gmail.com",
#         subject="📬 Daily Email Digest",
#         html_body=digest_html
#     )

# -----------------------------------------------------------------------------------------

# import os
# import pickle
# import base64
# from dotenv import load_dotenv
# from google.auth.transport.requests import Request
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from email.mime.text import MIMEText
# from langchain_ollama import OllamaLLM
# from langchain.schema import HumanMessage

# # -------------------------------
# # Load environment variables
# # -------------------------------
# load_dotenv()

# # -------------------------------
# # Gmail API scopes (read + send)
# # -------------------------------
# SCOPES = [
#     "https://www.googleapis.com/auth/gmail.readonly",
#     "https://www.googleapis.com/auth/gmail.send"
# ]

# # -------------------------------
# # Step 1: Authenticate Gmail
# # -------------------------------
# def authenticate_gmail():
#     creds = None
#     if os.path.exists("token.pickle"):
#         with open("token.pickle", "rb") as token:
#             creds = pickle.load(token)

#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
#             creds = flow.run_local_server(port=0)

#         with open("token.pickle", "wb") as token:
#             pickle.dump(creds, token)

#     return creds

# # -------------------------------
# # Step 2: Decode email body safely
# # -------------------------------
# def decode_email_body(data: str) -> str:
#     text = base64.urlsafe_b64decode(data)
#     try:
#         return text.decode("utf-8")
#     except UnicodeDecodeError:
#         try:
#             return text.decode("latin-1")
#         except Exception:
#             return text.decode(errors="ignore")

# # -------------------------------
# # Step 3: Fetch unread emails
# # -------------------------------
# def fetch_unread_emails(service, max_results=10):
#     emails_list = []

#     results = service.users().messages().list(userId="me", q="is:unread", maxResults=max_results).execute()
#     if "messages" not in results:
#         print("✅ No unread emails found.")
#         return emails_list

#     for msg in results["messages"]:
#         msg_data = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
#         payload = msg_data["payload"]

#         headers = payload.get("headers", [])
#         subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
#         sender = next((h["value"] for h in headers if h["name"] == "From"), "(Unknown Sender)")

#         body = ""
#         if "parts" in payload:
#             for part in payload["parts"]:
#                 if part["mimeType"] == "text/plain":
#                     data = part["body"].get("data")
#                     if data:
#                         body = decode_email_body(data)
#                         break
#         else:
#             data = payload["body"].get("data")
#             if data:
#                 body = decode_email_body(data)

#         emails_list.append({
#             "sender": sender,
#             "subject": subject,
#             "body": body[:1000]  # limit to 1000 chars
#         })

#     return emails_list

# # -------------------------------
# # Step 4: Summarize & Categorize Emails using OllamaLLM
# # -------------------------------
# def summarize_and_categorize(emails_list):
#     if not emails_list:
#         return "<p>✅ No emails to summarize.</p>"

#     llm = OllamaLLM(model="llama2:13b-chat")  # Using Llama2 Chat

#     formatted_emails = ""
#     for e in emails_list:
#         formatted_emails += f"Sender: {e['sender']}\nSubject: {e['subject']}\nBody: {e['body']}\n\n"

#     prompt = f"""
# You are an AI assistant. 
# Categorize each email into one of three categories:

# 1. Items Requiring Attention (needs action/response)
# 2. Items to Review Later (informational, useful later)
# 3. Items of No Immediate Relevance (spam/promotions)

# Return the digest in PROFESSIONAL HTML format with the following rules:
# - Use '<h1>========== DAILY EMAIL DIGEST ==========</h1>' as the header
# - Use '<h3>' tags for category titles (e.g., Items Requiring Attention, Items to Review Later, Items of No Immediate Relevance)
# - List each email under its category using '<ul><li>' with the format: 'Sender: [sender] Subject: [subject] Summary: [concise summary]'
# - Keep summaries concise and professional
# - End with a disclaimer: '<p style=\"color:gray; font-size:small;\">**Disclaimer:** This email digest is for informational purposes only and does not constitute professional advice. Please review the emails carefully and take appropriate action as needed.</p>'

# Emails:
# {formatted_emails}
# """

#     # Call LLM
#     response = llm.invoke([HumanMessage(content=prompt)])

#     # Extract text safely
#     if hasattr(response, "content"):
#         return response.content
#     elif isinstance(response, str):
#         return response
#     else:
#         return str(response)

# # -------------------------------
# # Step 5: Send Digest Email
# # -------------------------------
# def send_email(service, to, subject, html_body):
#     message = MIMEText(html_body, "html")  # send as HTML
#     message['to'] = to
#     message['subject'] = subject
#     raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
#     msg = {'raw': raw}
#     service.users().messages().send(userId="me", body=msg).execute()
#     print(f"✅ Digest sent to {to}")

# # -------------------------------
# # Step 6: Main Execution
# # -------------------------------
# if __name__ == "__main__":
#     creds = authenticate_gmail()
#     service = build(serviceName="gmail", version="v1", credentials=creds)

#     emails_list = fetch_unread_emails(service, max_results=10)

#     digest_html = summarize_and_categorize(emails_list)

#     print("\n========== DAILY EMAIL DIGEST ==========\n")
#     print(digest_html)

#     # Send digest email as professional HTML
#     send_email(
#         service,
#         to="namya.vishal.shah.campus@gmail.com",
#         subject="📬 Daily Email Digest",
#         html_body=digest_html
#     )
    
    
    
    
#     ## run the above code .. it's from grok..






# import os
# import pickle
# import base64
# from dotenv import load_dotenv
# from google.auth.transport.requests import Request
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from email.mime.text import MIMEText
# from langchain_ollama import OllamaLLM
# from langchain.schema import HumanMessage

# # -------------------------------
# # Load environment variables
# # -------------------------------
# load_dotenv()

# # -------------------------------
# # Gmail API scopes (read + send)
# # -------------------------------
# SCOPES = [
#     "https://www.googleapis.com/auth/gmail.readonly",
#     "https://www.googleapis.com/auth/gmail.send"
# ]

# # -------------------------------
# # Step 1: Authenticate Gmail
# # -------------------------------
# def authenticate_gmail():
#     creds = None
#     if os.path.exists("token.pickle"):
#         with open("token.pickle", "rb") as token:
#             creds = pickle.load(token)

#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
#             creds = flow.run_local_server(port=0)

#         with open("token.pickle", "wb") as token:
#             pickle.dump(creds, token)

#     return creds

# # -------------------------------
# # Step 2: Decode email body safely
# # -------------------------------
# def decode_email_body(data: str) -> str:
#     text = base64.urlsafe_b64decode(data)
#     try:
#         return text.decode("utf-8")
#     except UnicodeDecodeError:
#         try:
#             return text.decode("latin-1")
#         except Exception:
#             return text.decode(errors="ignore")

# # -------------------------------
# # Step 3: Fetch unread emails
# # -------------------------------
# def fetch_unread_emails(service, max_results=10):
#     emails_list = []

#     results = service.users().messages().list(userId="me", q="is:unread", maxResults=max_results).execute()
#     if "messages" not in results:
#         print("✅ No unread emails found.")
#         return emails_list

#     for msg in results["messages"]:
#         msg_data = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
#         payload = msg_data["payload"]

#         headers = payload.get("headers", [])
#         subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(No Subject)")
#         sender = next((h["value"] for h in headers if h["name"] == "From"), "(Unknown Sender)")

#         body = ""
#         if "parts" in payload:
#             for part in payload["parts"]:
#                 if part["mimeType"] == "text/plain":
#                     data = part["body"].get("data")
#                     if data:
#                         body = decode_email_body(data)
#                         break
#         else:
#             data = payload["body"].get("data")
#             if data:
#                 body = decode_email_body(data)

#         emails_list.append({
#             "sender": sender,
#             "subject": subject,
#             "body": body[:1000]  # limit to 1000 chars
#         })

#     return emails_list

# # -------------------------------
# # Step 4: Summarize & Categorize Emails using OllamaLLM
# # -------------------------------
# # -------------------------------
# # Step 4: Summarize & Categorize Emails using OllamaLLM
# # -------------------------------
# def summarize_and_categorize(emails_list):
#     if not emails_list:
#         return "<p>✅ No emails to summarize.</p>"

#     llm = OllamaLLM(model="llama2:13b-chat")  # Using Llama2 Chat

#     formatted_emails = ""
#     for e in emails_list:
#         formatted_emails += f"Sender: {e['sender']}\nSubject: {e['subject']}\nBody: {e['body']}\n\n"

#     prompt = f"""
# You are an AI assistant. Categorize each email into one of three categories with strict adherence to these rules:
# 1. Items Requiring Attention: Emails needing immediate action, such as job alerts with 'apply now', financial deadlines (e.g., 'payment', 'due'), IPO alerts, or time-sensitive opportunities with explicit deadlines (e.g., 'deadline', 'few hours left'). Example: 'Machine Learning Engineer at Quantiphi and 10 more jobs' or 'IPO ALERT - AIRFLOA RAIL TECHNOLOGY'.
# 2. Items to Review Later: Informational emails with no immediate action, such as newsletters, balance statements, or general notifications without deadlines. Example: 'Funds / Securities Balance' or 'Introduction to Machine Learning Update'.
# 3. Items of No Immediate Relevance: Spam, promotions, or marketing emails without urgent action keywords (e.g., general offers, contests without deadlines). Example: '₹7,999/year for unlimited access to Meta courses'.

# Return ONLY the HTML content in PROFESSIONAL HTML format with EXACTLY the following structure:
# - Start with '<h1>========== DAILY EMAIL DIGEST ==========</h1>'
# - For each category (e.g., Items Requiring Attention, Items to Review Later, Items of No Immediate Relevance), use '<h2>[Category Name]</h2><ul>' followed by '<li>Sender: [sender] Subject: [subject] Summary: [concise summary reflecting the categorization reason]</li>' for each email in that category, and close with '</ul>'
# - End with '<p style=\"color:gray; font-size:small;\">**Disclaimer:** This email digest is for informational purposes only and does not constitute professional advice. Please review the emails carefully and take appropriate action as needed.</p>'
# - Ensure proper nesting of <ul> and <li> tags, and include all three categories (Items Requiring Attention, Items to Review Later, Items of No Immediate Relevance) even if empty.
# - Do NOT include any text outside this HTML structure, such as category names without tags or extra lines.

# Emails:
# {formatted_emails}
# """

#     # Call LLM
#     response = llm.invoke([HumanMessage(content=prompt)])

#     # Extract text safely and ensure clean HTML
#     if hasattr(response, "content"):
#         digest_html = response.content.strip()
#     elif isinstance(response, str):
#         digest_html = response.strip()
#     else:
#         digest_html = str(response).strip()

#     # Fallback to enforce HTML structure if malformed
#     if not digest_html.startswith("<h1>========== DAILY EMAIL DIGEST ==========</h1>"):
#         digest_html = "<h1>========== DAILY EMAIL DIGEST ==========</h1>"
#         digest_html += "\n<h2>Items Requiring Attention</h2><ul></ul>"
#         digest_html += "\n<h2>Items to Review Later</h2><ul></ul>"
#         digest_html += "\n<h2>Items of No Immediate Relevance</h2><ul></ul>"
#         digest_html += "\n<p style=\"color:gray; font-size:small;\">**Disclaimer:** This email digest is for informational purposes only and does not constitute professional advice. Please review the emails carefully and take appropriate action as needed.</p>"

#     return digest_html

# # -------------------------------
# # Step 5: Send Digest Email
# # -------------------------------
# def send_email(service, to, subject, html_body):
#     message = MIMEText(html_body, "html")  # send as HTML
#     message['to'] = to
#     message['subject'] = subject
#     raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
#     msg = {'raw': raw}
#     service.users().messages().send(userId="me", body=msg).execute()
#     print(f"✅ Digest sent to {to}")

# # -------------------------------
# # Step 6: Main Execution
# # -------------------------------
# if __name__ == "__main__":
#     creds = authenticate_gmail()
#     service = build(serviceName="gmail", version="v1", credentials=creds)

#     max_results = int(os.getenv("MAX_RESULTS_OLLAMA", 10))
#     emails_list = fetch_unread_emails(service, max_results=max_results)

#     digest_html = summarize_and_categorize(emails_list)

#     print("\n========== DAILY EMAIL DIGEST ==========\n")
#     print(digest_html)

#     # Send digest email as professional HTML
#     send_email(
#         service,
#         to=os.getenv("RECIPIENT_EMAIL"),
#         subject=os.getenv("EMAIL_SUBJECT"),
#         html_body=digest_html
#     )









# ----------------------------------------------------------------------------------------------------------------

# more privacy to the user by using regex

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
from langchain_ollama import OllamaLLM
from langchain.schema import HumanMessage
from invoice_extractor import process_email_for_invoices

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

        # ----------------------------------------------------
        # NEW: Check for invoice attachments & extract data
        # ----------------------------------------------------
        all_parts = payload.get("parts", [])
        if "parts" not in payload and "body" in payload:
            all_parts = [payload]
            
        process_email_for_invoices(
            service=service,
            msg_id=msg["id"],
            sender=sender,
            subject=subject,
            parts=all_parts
        )
        # ----------------------------------------------------

        # Mask sensitive info in body immediately after fetching
        masked_body = mask_sensitive_info(body.strip()[:1000])  # limit to 1000 chars after masking

        emails_list.append({
            "sender": sender,
            "subject": subject,
            "body": masked_body
        })

    return emails_list

# -------------------------------
# Step 4: Summarize & Categorize Emails using OllamaLLM
# -------------------------------
def summarize_and_categorize(emails_list):
    if not emails_list:
        return "<p>✅ No emails to summarize.</p>"

    llm = OllamaLLM(model="llama2:13b-chat")  # Using Llama2 Chat

    formatted_emails = ""
    for e in emails_list:
        # Mask sender and subject as well for extra privacy
        masked_sender = mask_sensitive_info(e['sender'])
        masked_subject = mask_sensitive_info(e['subject'])
        formatted_emails += f"Sender: {masked_sender}\nSubject: {masked_subject}\nBody: {e['body']}\n\n"

    prompt = f"""
You are an AI assistant. Categorize each email into one of three categories with strict adherence to these rules:
1. Items Requiring Attention: Emails needing immediate action, such as job alerts with 'apply now', financial deadlines (e.g., 'payment', 'due'), IPO alerts, or time-sensitive opportunities with explicit deadlines (e.g., 'deadline', 'few hours left'). Example: 'Machine Learning Engineer at Quantiphi and 10 more jobs' or 'IPO ALERT - AIRFLOA RAIL TECHNOLOGY'.
2. Items to Review Later: Informational emails with no immediate action, such as newsletters, balance statements, or general notifications without deadlines. Example: 'Funds / Securities Balance' or 'Introduction to Machine Learning Update'.
3. Items of No Immediate Relevance: Spam, promotions, or marketing emails without urgent action keywords (e.g., general offers, contests without deadlines). Example: '₹7,999/year for unlimited access to Meta courses'.

Note: The email content may contain 'xxxxxxxxxx' placeholders for sensitive information like phone numbers, emails, amounts, transaction IDs, credit card numbers, or bank account numbers. Treat these as generic sensitive information in your summarization.

Return ONLY the HTML content in PROFESSIONAL HTML format with EXACTLY the following structure:
- Start with '<h1>========== DAILY EMAIL DIGEST ==========</h1>'
- For each category (e.g., Items Requiring Attention, Items to Review Later, Items of No Immediate Relevance), use '<h2>[Category Name]</h2><ul>' followed by '<li>Sender: [sender] Subject: [subject] Summary: [concise summary reflecting the categorization reason]</li>' for each email in that category, and close with '</ul>'
- End with '<p style="color:gray; font-size:small;">**Disclaimer:** This email digest is for informational purposes only and does not constitute professional advice. Please review the emails carefully and take appropriate action as needed.</p>'
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