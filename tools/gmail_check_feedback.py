"""Check pending drafts for user feedback: sent, edited, or [FEEDBACK] replies."""
import base64
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from gmail_auth import get_gmail_service

PENDING_DRAFTS_FILE = os.path.join(os.path.dirname(__file__), '..', '.tmp', 'pending_drafts.json')
FEEDBACK_PREFIX = '[FEEDBACK]'


def load_pending():
    if not os.path.exists(PENDING_DRAFTS_FILE):
        return []
    with open(PENDING_DRAFTS_FILE) as f:
        return json.load(f)


def save_pending(drafts):
    os.makedirs(os.path.dirname(PENDING_DRAFTS_FILE), exist_ok=True)
    with open(PENDING_DRAFTS_FILE, 'w') as f:
        json.dump(drafts, f, indent=2)


def check_feedback():
    service = get_gmail_service()
    pending = load_pending()

    results = []
    still_pending = []

    for entry in pending:
        draft_id = entry['draft_id']
        thread_id = entry['thread_id']

        thread = service.users().threads().get(userId='me', id=thread_id).execute()
        thread_msgs = thread.get('messages', [])

        # Look for a SENT message in the thread — reliable regardless of draft API lag
        sent_body = None
        for msg in thread_msgs:
            if 'SENT' in msg.get('labelIds', []):
                full = service.users().messages().get(
                    userId='me', id=msg['id'], format='full'
                ).execute()
                sent_body = extract_body(full)
                break

        if sent_body:
            results.append({
                'status': 'sent',
                'original_email': entry['original_email'],
                'generated_reply': entry['generated_reply'],
                'actual_reply': sent_body,
                'thread_id': thread_id,
            })
            # Clean up the draft if it still exists
            try:
                service.users().drafts().delete(userId='me', id=draft_id).execute()
            except Exception:
                pass
        else:
            # Draft not sent yet — check for [FEEDBACK] reply
            feedback_text = None
            for msg in thread_msgs:
                full = service.users().messages().get(
                    userId='me', id=msg['id'], format='full'
                ).execute()
                body = extract_body(full)
                if body and body.strip().startswith(FEEDBACK_PREFIX):
                    feedback_text = body.strip()[len(FEEDBACK_PREFIX):].strip()
                    break

            if feedback_text:
                results.append({
                    'status': 'feedback',
                    'original_email': entry['original_email'],
                    'generated_reply': entry['generated_reply'],
                    'feedback': feedback_text,
                    'thread_id': thread_id,
                })
            else:
                # Check if draft was deleted without sending
                draft_exists = True
                try:
                    service.users().drafts().get(userId='me', id=draft_id).execute()
                except Exception:
                    draft_exists = False

                if not draft_exists:
                    results.append({
                        'status': 'deleted',
                        'original_email': entry['original_email'],
                        'generated_reply': entry['generated_reply'],
                        'actual_reply': None,
                        'thread_id': thread_id,
                    })
                else:
                    still_pending.append(entry)

    save_pending(still_pending)
    return results


def extract_body(msg):
    payload = msg.get('payload', {})
    if payload.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    for part in payload.get('parts', []):
        if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
            return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
    return ''


if __name__ == '__main__':
    results = check_feedback()
    print(f'Resolved {len(results)} drafts')
    for r in results:
        print(f"  [{r['status'].upper()}] {r['original_email']['subject'][:60]}")
