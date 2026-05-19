"""Entry point: fetch unread inbox emails, generate replies, create Gmail drafts."""
import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from gmail_fetch_inbox import fetch_unread_emails
from gmail_create_draft import create_draft_reply
from generate_reply import generate_reply

PENDING_DRAFTS_FILE = os.path.join(os.path.dirname(__file__), '..', '.tmp', 'pending_drafts.json')


def load_pending():
    if os.path.exists(PENDING_DRAFTS_FILE):
        with open(PENDING_DRAFTS_FILE) as f:
            return json.load(f)
    return []


def save_pending(drafts):
    os.makedirs(os.path.dirname(PENDING_DRAFTS_FILE), exist_ok=True)
    with open(PENDING_DRAFTS_FILE, 'w') as f:
        json.dump(drafts, f, indent=2)


def run():
    print('Fetching unread emails...')
    emails, service, processed_label_id = fetch_unread_emails()

    if not emails:
        print('No unread emails to process.')
        return

    print(f'Found {len(emails)} email(s). Generating replies...\n')
    pending = load_pending()

    for email in emails:
        print(f"  [{email['from']}] {email['subject']}")
        try:
            reply_text = generate_reply(email)
            print(f'  -> Reply generated ({len(reply_text)} chars)')

            draft = create_draft_reply(
                thread_id=email['thread_id'],
                original_message_id=email['id'],
                reply_to=email['from'],
                reply_subject=email['subject'],
                reply_body=reply_text,
            )
            print(f"  -> Draft saved: {draft['draft_id']}\n")

            pending.append({
                'draft_id': draft['draft_id'],
                'thread_id': email['thread_id'],
                'original_email': {
                    'id': email['id'],
                    'subject': email['subject'],
                    'from': email['from'],
                    'body': email['body'][:2000],
                },
                'generated_reply': reply_text,
            })

            service.users().messages().modify(
                userId='me',
                id=email['id'],
                body={'addLabelIds': [processed_label_id]},
            ).execute()

            time.sleep(0.3)

        except Exception as e:
            print(f'  ERROR: {e}\n')
            continue

    save_pending(pending)
    print(f'Done. {len(emails)} email(s) processed. Check Gmail Drafts to review.')


if __name__ == '__main__':
    run()
