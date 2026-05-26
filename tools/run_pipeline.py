"""Entry point: fetch unread inbox emails, generate replies, create Gmail drafts."""
import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from gmail_fetch_inbox import fetch_unread_emails
from gmail_create_draft import create_draft_reply
from generate_reply import generate_reply
from user_store import pending_drafts_path


def load_pending(user_email):
    path = pending_drafts_path(user_email)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def save_pending(user_email, drafts):
    with open(pending_drafts_path(user_email), 'w') as f:
        json.dump(drafts, f, indent=2)


def run(user_email):
    print(f'[{user_email}] Fetching unread emails...')
    emails, service, processed_label_id = fetch_unread_emails(user_email=user_email)

    if not emails:
        print(f'[{user_email}] No new emails.')
        return

    print(f'[{user_email}] Found {len(emails)} email(s). Generating replies...\n')
    pending = load_pending(user_email)

    for email in emails:
        print(f"  [{email['from']}] {email['subject']}")
        try:
            reply_text = generate_reply(email, user_email=user_email)
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

    save_pending(user_email, pending)
    print(f'[{user_email}] Done. {len(emails)} email(s) processed. Check Gmail Drafts.')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python run_pipeline.py <user_email>')
        sys.exit(1)
    run(sys.argv[1])
