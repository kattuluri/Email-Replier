"""
Register a new user: runs Gmail OAuth, seeds their RAG from sent history,
and adds them to the user registry.

Usage:
    python tools/add_user.py <email>
    python tools/add_user.py <email> --seed 200
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(__file__))
from gmail_auth import get_gmail_service
from rag_seed import seed_rag_from_sent
from user_store import register_user, get_users


def add_user(email, seed_count=100):
    print(f'Registering user: {email}')

    if email in get_users():
        print(f'  Already registered. Re-seeding RAG...')
    else:
        print(f'  Opening browser for Gmail OAuth...')

    # OAuth — opens browser for this specific account
    service = get_gmail_service(user_email=email)
    profile = service.users().getProfile(userId='me').execute()
    authenticated_as = profile['emailAddress']

    if authenticated_as.lower() != email.lower():
        print(f'  WARNING: Authenticated as {authenticated_as}, expected {email}')
        print(f'  Proceeding with {authenticated_as}')
        email = authenticated_as

    register_user(email)
    print(f'  Registered: {email}')

    print(f'  Seeding RAG from sent history (last {seed_count} emails)...')
    added = seed_rag_from_sent(user_email=email, max_results=seed_count)
    print(f'  RAG seeded with {added} email-reply pairs.')
    print(f'\nDone. {email} is ready. The watcher will now monitor their inbox.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('email', help='Gmail address to register')
    parser.add_argument('--seed', type=int, default=100, help='Number of sent emails to seed from')
    args = parser.parse_args()
    add_user(args.email, seed_count=args.seed)
