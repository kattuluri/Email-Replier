"""
Email watcher — polls Gmail every 60 seconds for all registered users
and runs the pipeline automatically when new Primary inbox emails arrive.

Usage:
    python tools/run_watcher.py
    python tools/run_watcher.py --interval 30

Stop with Ctrl+C.
"""
import sys
import os
import time
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from gmail_auth import get_gmail_service
from run_pipeline import run as run_pipeline
from user_store import get_users

PROCESSED_LABEL = 'email-replier-processed'
SKIP_CATEGORIES = {'CATEGORY_PROMOTIONS', 'CATEGORY_UPDATES', 'CATEGORY_SOCIAL', 'CATEGORY_FORUMS'}


def get_or_create_label(service, label_name):
    labels = service.users().labels().list(userId='me').execute()
    for label in labels.get('labels', []):
        if label['name'] == label_name:
            return label['id']
    result = service.users().labels().create(userId='me', body={'name': label_name}).execute()
    return result['id']


def has_new_emails(service):
    get_or_create_label(service, PROCESSED_LABEL)
    result = service.users().messages().list(
        userId='me', q=f'is:unread -label:{PROCESSED_LABEL}', maxResults=5
    ).execute()
    for msg_ref in result.get('messages', []):
        msg = service.users().messages().get(
            userId='me', id=msg_ref['id'], format='metadata'
        ).execute()
        if not (set(msg.get('labelIds', [])) & SKIP_CATEGORIES):
            return True
    return False


def timestamp():
    return datetime.now().strftime('%H:%M:%S')


def watch(interval=60):
    users = get_users()
    if not users:
        print('No users registered. Run: python tools/add_user.py <email>')
        return

    print(f'Watching {len(users)} user(s) every {interval}s. Press Ctrl+C to stop.')
    print(f'Users: {", ".join(users)}\n')

    # Pre-authenticate all users so first poll is fast
    services = {}
    for email in users:
        try:
            services[email] = get_gmail_service(user_email=email)
            print(f'  Authenticated: {email}', flush=True)
        except Exception as e:
            print(f'  Auth failed for {email}: {e}', flush=True)
    print()

    while True:
        try:
            for email in users:
                service = services.get(email)
                if not service:
                    continue
                try:
                    if has_new_emails(service):
                        print(f'[{timestamp()}] [{email}] New email — running pipeline...', flush=True)
                        run_pipeline(email)
                        print(f'[{timestamp()}] [{email}] Done.\n', flush=True)
                except Exception as e:
                    print(f'[{timestamp()}] [{email}] Error: {e}', flush=True)

            print(f'[{timestamp()}] Checked {len(users)} user(s).', end='\r', flush=True)
            time.sleep(interval)

        except KeyboardInterrupt:
            print(f'\n[{timestamp()}] Watcher stopped.')
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=60, help='Poll interval in seconds')
    args = parser.parse_args()
    watch(interval=args.interval)
