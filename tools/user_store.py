"""User registry — tracks registered users and provides per-user storage paths."""
import json
import os

USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json')
TOKENS_DIR = os.path.join(os.path.dirname(__file__), '..', 'tokens')
TMP_DIR = os.path.join(os.path.dirname(__file__), '..', '.tmp')


def user_id(email):
    """Sanitized identifier used for file and DB names."""
    return email.replace('@', '_at_').replace('.', '_').replace('-', '_').lower()


def token_path(email):
    os.makedirs(TOKENS_DIR, exist_ok=True)
    return os.path.join(TOKENS_DIR, f'{user_id(email)}.pickle')


def pending_drafts_path(email):
    os.makedirs(TMP_DIR, exist_ok=True)
    return os.path.join(TMP_DIR, f'pending_{user_id(email)}.json')


def get_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE) as f:
        return json.load(f)


def register_user(email):
    users = get_users()
    if email not in users:
        users.append(email)
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    return False
