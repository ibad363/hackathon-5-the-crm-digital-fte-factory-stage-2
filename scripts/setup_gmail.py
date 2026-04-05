# scripts/setup_gmail.py
"""
Gmail Integration Setup Script

This script helps you:
1. Authenticate with Gmail (OAuth)
2. Set up Pub/Sub watch for push notifications
3. Test the Gmail handler

Run this after placing your gmail_credentials.json in the credentials folder.
"""

import os
import sys
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def print_header(text: str):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(step: int, text: str):
    print(f"\n📍 Step {step}: {text}")
    print("-" * 40)


async def main():
    print_header("📧 Gmail Integration Setup for TaskVault")

    # Step 1: Check for credentials file
    print_step(1, "Checking for OAuth credentials")

    from pathlib import Path
    creds_file = Path("credentials/gmail_credentials.json")

    if not creds_file.exists():
        print("❌ gmail_credentials.json not found!")
        print("\n   To get this file:")
        print("   1. Go to: https://console.cloud.google.com")
        print("   2. Create a project (or select existing)")
        print("   3. Enable the Gmail API")
        print("   4. Go to APIs & Services → Credentials")
        print("   5. Create OAuth 2.0 Client ID (Desktop App)")
        print("   6. Download JSON and save as: credentials/gmail_credentials.json")
        return

    print("✅ gmail_credentials.json found!")

    # Step 2: Authenticate
    print_step(2, "Authenticating with Gmail")

    try:
        from channels.gmail_auth import get_gmail_credentials
        creds = get_gmail_credentials()
        print("✅ Gmail authentication successful!")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return

    # Step 3: Initialize handler
    print_step(3, "Initializing Gmail Handler")

    try:
        from channels.gmail_handler import GmailHandler
        handler = GmailHandler()
        print("✅ Gmail handler initialized!")
    except Exception as e:
        print(f"❌ Handler initialization failed: {e}")
        return

    # Step 4: Test fetching messages
    print_step(4, "Testing message fetch")

    try:
        messages = handler.service.users().messages().list(
            userId='me',
            maxResults=3,
            labelIds=['INBOX']
        ).execute()

        msg_list = messages.get('messages', [])
        print(f"✅ Found {len(msg_list)} recent messages in inbox")

        if msg_list:
            print("\n   Recent emails:")
            for msg in msg_list[:3]:
                parsed = await handler.get_message(msg['id'])
                if parsed:
                    print(f"   • From: {parsed['customer_email'][:30]}...")
                    print(f"     Subject: {parsed['subject'][:40]}...")
    except Exception as e:
        print(f"❌ Message fetch failed: {e}")

    # Step 5: Setup Pub/Sub watch (optional)
    print_step(5, "Pub/Sub Watch Setup (Optional)")

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        print("⚠️ GOOGLE_CLOUD_PROJECT not set in .env")
        print("   To enable push notifications, add to your .env:")
        print("   GOOGLE_CLOUD_PROJECT=your-project-id")
        print("\n   Skipping Pub/Sub setup...")
    else:
        print(f"   Project ID: {project_id}")
        setup = input("\n   Set up Gmail push notifications? (y/n): ").strip().lower()

        if setup == 'y':
            try:
                result = await handler.setup_push_notifications(project_id)
                print(f"✅ Gmail watch active!")
                print(f"   History ID: {result.get('historyId')}")
                print(f"   Expires: {result.get('expiration')}")
            except Exception as e:
                print(f"❌ Pub/Sub setup failed: {e}")
                print("\n   Make sure you have:")
                print("   1. Created a Pub/Sub topic: gmail-notifications")
                print("   2. Added gmail-api-push@system.gserviceaccount.com as Publisher")
                print("   3. Created a push subscription pointing to your webhook URL")
        else:
            print("   Skipping Pub/Sub setup.")

    # Summary
    print_header("Setup Complete!")
    print("""
Next steps:
1. Start the API server:
   python -m api.main

2. For local testing with push notifications:
   - Install ngrok: https://ngrok.com
   - Run: ngrok http 8000
   - Update your Pub/Sub subscription with the ngrok URL

3. Test the webhook:
   - Send an email to your Gmail account
   - Check the API logs for processing

4. Environment variables needed (.env):
   DATABASE_URL=postgresql://user:pass@localhost:5432/crm_db
   GOOGLE_CLOUD_PROJECT=your-project-id
   OPENROUTER_API_KEY=your-key
""")


if __name__ == "__main__":
    asyncio.run(main())
