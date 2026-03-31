import streamlit as st
import imaplib
import email
from email.header import decode_header
from transformers import pipeline
from datetime import timedelta

# Title
st.title("📧 Email Summarizer")

# Inputs
user_email = st.text_input("Enter your Gmail")
app_password = st.text_input("Enter App Password", type="password")

# ✅ Date input (NEW)
selected_date = st.date_input("Select Date")

# Load summarizer model
@st.cache_resource
def load_model():
    return pipeline("summarization")

summarizer = load_model()

# Fetch Emails Function
def fetch_emails(email_user, email_pass, selected_date):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(email_user, email_pass)
    mail.select("inbox")

    # ✅ Convert date to IMAP format
    since_date = selected_date.strftime("%d-%b-%Y")
    before_date = (selected_date + timedelta(days=1)).strftime("%d-%b-%Y")

    # ✅ Apply date filter
    status, messages = mail.search(None, f'(SINCE "{since_date}" BEFORE "{before_date}")')
    email_ids = messages[0].split()

    emails = []

    for i in email_ids[-5:]:  # last 5 emails of that date
        _, msg = mail.fetch(i, "(RFC822)")
        for response in msg:
            if isinstance(response, tuple):
                msg = email.message_from_bytes(response[1])

                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")

                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                emails.append((subject, body[:1000]))

    return emails

# Button
if st.button("Fetch & Summarize Emails"):
    if user_email and app_password:
        try:
            # ✅ pass selected_date
            emails = fetch_emails(user_email, app_password, selected_date)

            if not emails:
                st.warning("No emails found for this date")

            for subject, body in emails:
                st.subheader(f"📌 {subject}")

                if len(body.strip()) > 50:
                    summary = summarizer(body, max_length=100, min_length=30, do_sample=False)
                    st.write(summary[0]['summary_text'])
                else:
                    st.write("⚠️ Not enough content to summarize")

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter email and app password")