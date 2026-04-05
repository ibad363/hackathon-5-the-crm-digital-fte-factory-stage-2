# channels/gmail_auth.py
"""
Gmail OAuth 2.0 Authentication Handler

This module handles the OAuth flow for Gmail API access.
Run this script once to generate the token.json file.
"""

import os
import pickle
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Gmail API scopes required for full access
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',   # Read emails
    'https://www.googleapis.com/auth/gmail.send',       # Send emails
    'https://www.googleapis.com/auth/gmail.modify',     # Mark as read, labels
]

# Paths
CREDENTIALS_DIR = Path(__file__).parent.parent / "credentials"
CREDENTIALS_FILE = CREDENTIALS_DIR / "gmail_credentials.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"


def get_gmail_credentials() -> Credentials:
    """
    Get valid Gmail API credentials.

    If no valid credentials exist, initiates OAuth flow.
    Stores credentials in token.json for reuse.

    Returns:
        google.oauth2.credentials.Credentials: Valid credentials for Gmail API
    """
    creds = None

    # Check for existing token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # If no valid credentials, refresh or start OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"❌ Gmail credentials not found!\n"
                    f"   Please download OAuth credentials from Google Cloud Console\n"
                    f"   and save to: {CREDENTIALS_FILE}"
                )

            print("🔐 Starting OAuth flow...")
            print("   A browser window will open for authentication.")

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
            print("✅ Authentication successful!")

        # Save credentials for next run
        CREDENTIALS_DIR.mkdir(exist_ok=True)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print(f"💾 Token saved to: {TOKEN_FILE}")

    return creds


def revoke_credentials():
    """Revoke and delete stored credentials."""
    if TOKEN_FILE.exists():
        os.remove(TOKEN_FILE)
        print("🗑️ Token file deleted.")
    else:
        print("ℹ️ No token file found.")


if __name__ == "__main__":
    """Run this script directly to authenticate Gmail."""
    print("=" * 50)
    print("📧 Gmail OAuth Authentication Setup")
    print("=" * 50)

    try:
        creds = get_gmail_credentials()
        print("\n✅ Gmail credentials are valid!")
        print(f"   Token file: {TOKEN_FILE}")
    except FileNotFoundError as e:
        print(f"\n{e}")
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
