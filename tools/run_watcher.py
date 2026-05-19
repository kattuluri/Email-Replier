"""
Email watcher — polls Gmail every 60 seconds and runs the pipeline
automatically when new Primary inbox emails arrive.

Usage:
    python tools/run_watcher.py
    python tools/run_watcher.py --interval 30   # check every 30 seconds

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
    """Return True if there are unread Primary inbox emails not yet processed."""
    get_or_create_label(service, PROCESSED_LABEL)
    query = f'is:unread -label:{PROCESSED_LABEL}'
    result = service.users().messages().list(userId='me', q=query, maxResults=5).execute()

    for msg_ref in result.get('messages', []):
        msg = service.users().messages().get(
            userId='me', id=msg_ref['id'], format='metadata'
        ).execute()
        label_ids = set(msg.get('labelIds', []))
        if not (label_ids & SKIP_CATEGORIES):
            return True
    return False


def timestamp():
    return datetime.now().strftime('%H:%M:%S')


def watch(interval=60):
    print(f'Watching inbox every {interval}s. Press Ctrl+C to stop.\n')

    service = get_gmail_service()

    while True:
        try:
            if has_new_emails(service):
                print(f'[{timestamp()}] New email detected — running pipeline...', flush=True)
                run_pipeline()
                print(f'[{timestamp()}] Done. Resuming watch.\n', flush=True)
            else:
                print(f'[{timestamp()}] No new emails.', end='\r', flush=True)

            time.sleep(interval)

        except KeyboardInterrupt:
            print(f'\n[{timestamp()}] Watcher stopped.')
            break
        except Exception as e:
            print(f'[{timestamp()}] Error: {e} — retrying in {interval}s')
            time.sleep(interval)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=60, help='Poll interval in seconds')
    args = parser.parse_args()
    watch(interval=args.interval)
