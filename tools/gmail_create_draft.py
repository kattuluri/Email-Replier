"""Create a draft reply in a Gmail thread."""
import base64
import sys
import os
from email.mime.text import MIMEText

sys.path.insert(0, os.path.dirname(__file__))
from gmail_auth import get_gmail_service


def create_draft_reply(thread_id, original_message_id, reply_to, reply_subject, reply_body):
    service = get_gmail_service()

    subject = reply_subject if reply_subject.startswith('Re:') else f'Re: {reply_subject}'
    message = MIMEText(reply_body)
    message['To'] = reply_to
    message['Subject'] = subject
    message['In-Reply-To'] = original_message_id
    message['References'] = original_message_id

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

    draft = service.users().drafts().create(
        userId='me',
        body={'message': {'raw': raw, 'threadId': thread_id}},
    ).execute()

    return {
        'draft_id': draft['id'],
        'message_id': draft['message']['id'],
        'thread_id': thread_id,
    }
