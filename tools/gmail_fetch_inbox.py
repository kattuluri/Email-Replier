"""Fetch unread emails from inbox that haven't been processed yet."""
import base64
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from gmail_auth import get_gmail_service

PROCESSED_LABEL = 'email-replier-processed'

NO_REPLY_PATTERNS = (
    'noreply', 'no-reply', 'no_reply', 'donotreply', 'do-not-reply',
    'do_not_reply', 'notifications@', 'notification@', 'notify@',
    'alerts@', 'alert@', 'mailer-daemon', 'postmaster', 'lifecycle.',
    'updates@', 'newsletter', 'news@', 'info@',
)


def get_or_create_label(service, label_name):
    labels = service.users().labels().list(userId='me').execute()
    for label in labels.get('labels', []):
        if label['name'] == label_name:
            return label['id']
    result = service.users().labels().create(userId='me', body={'name': label_name}).execute()
    return result['id']


def is_no_reply(from_address):
    addr = from_address.lower()
    return any(pattern in addr for pattern in NO_REPLY_PATTERNS)


def fetch_unread_emails(user_email, max_results=20):
    service = get_gmail_service(user_email=user_email)
    label_id = get_or_create_label(service, PROCESSED_LABEL)

    SKIP_CATEGORIES = {'CATEGORY_PROMOTIONS', 'CATEGORY_UPDATES', 'CATEGORY_SOCIAL', 'CATEGORY_FORUMS'}

    query = f'is:unread -label:{PROCESSED_LABEL}'
    result = service.users().messages().list(
        userId='me', q=query, maxResults=max_results
    ).execute()

    emails = []
    for msg_ref in result.get('messages', []):
        msg = service.users().messages().get(
            userId='me', id=msg_ref['id'], format='full'
        ).execute()
        label_ids = set(msg.get('labelIds', []))
        if label_ids & SKIP_CATEGORIES:
            continue
        email = parse_email(msg)
        if is_no_reply(email['from']):
            continue
        emails.append(email)

    return emails, service, label_id


def parse_email(msg):
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    return {
        'id': msg['id'],
        'thread_id': msg['threadId'],
        'subject': headers.get('Subject', '(no subject)'),
        'from': headers.get('From', ''),
        'to': headers.get('To', ''),
        'date': headers.get('Date', ''),
        'body': extract_body(msg['payload']),
    }


def extract_body(payload):
    if payload.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    for part in payload.get('parts', []):
        if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
            return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
    for part in payload.get('parts', []):
        if part.get('mimeType') == 'text/html' and part.get('body', {}).get('data'):
            return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
    return ''


if __name__ == '__main__':
    import sys as _sys
    user = _sys.argv[1] if len(_sys.argv) > 1 else None
    emails, _, _ = fetch_unread_emails(user_email=user)
    print(f'Found {len(emails)} unread emails')
    for e in emails:
        print(f"  [{e['from']}] {e['subject']}")
