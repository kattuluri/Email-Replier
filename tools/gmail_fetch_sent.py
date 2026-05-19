"""Fetch sent email threads to build email-reply pairs for RAG seeding."""
import base64
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from gmail_auth import get_gmail_service


def fetch_sent_email_pairs(max_results=100):
    """Return list of {original_email, reply} dicts from the sent folder."""
    service = get_gmail_service()

    result = service.users().messages().list(
        userId='me', labelIds=['SENT'], maxResults=max_results
    ).execute()

    pairs = []
    for msg_ref in result.get('messages', []):
        msg = service.users().messages().get(
            userId='me', id=msg_ref['id'], format='full'
        ).execute()
        sent_email = parse_email(msg)

        thread = service.users().threads().get(
            userId='me', id=msg['threadId']
        ).execute()
        thread_msgs = thread.get('messages', [])

        sent_idx = next(
            (i for i, m in enumerate(thread_msgs) if m['id'] == msg['id']), None
        )
        if sent_idx is not None and sent_idx > 0:
            prev = service.users().messages().get(
                userId='me', id=thread_msgs[sent_idx - 1]['id'], format='full'
            ).execute()
            original = parse_email(prev)
            if original['body'].strip() and sent_email['body'].strip():
                pairs.append({'original_email': original, 'reply': sent_email})

    return pairs


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
    return ''


if __name__ == '__main__':
    pairs = fetch_sent_email_pairs(max_results=50)
    print(f'Found {len(pairs)} email-reply pairs')
    for p in pairs[:3]:
        print(f"  Original: {p['original_email']['subject']}")
        print(f"  Reply snippet: {p['reply']['body'][:80].strip()}")
        print()
