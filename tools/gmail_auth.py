"""Authenticate with Gmail API and return a service object."""
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify',
]

ROOT = os.path.join(os.path.dirname(__file__), '..')


def get_gmail_service(user_email=None, credentials_path=None, token_path=None):
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from user_store import token_path as user_token_path

    credentials_path = credentials_path or os.path.join(ROOT, 'credentials.json')
    if token_path is None:
        token_path = user_token_path(user_email) if user_email else os.path.join(ROOT, 'token.json')

    creds = None
    if os.path.exists(token_path):
        with open(token_path, 'rb') as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as f:
            pickle.dump(creds, f)

    return build('gmail', 'v1', credentials=creds)


if __name__ == '__main__':
    import sys as _sys
    email_arg = _sys.argv[1] if len(_sys.argv) > 1 else None
    service = get_gmail_service(user_email=email_arg)
    profile = service.users().getProfile(userId='me').execute()
    print(f"Authenticated as: {profile['emailAddress']}")
