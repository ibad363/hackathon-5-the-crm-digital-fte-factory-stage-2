# channels/gmail_handler.py
"""
Gmail Handler for TaskVault CRM

Handles Gmail integration via Push notifications (Pub/Sub)
- Receives email notifications via webhook
- Fetches and parses email content
- Sends reply emails via Gmail API
"""

import os
import sys
import re
import base64
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from channels.gmail_auth import get_gmail_credentials

logger = logging.getLogger(__name__)


class GmailHandler:
    """
    Gmail integration handler for TaskVault CRM.

    Provides methods to:
    - Set up push notifications via Pub/Sub
    - Process incoming email notifications
    - Fetch and parse email messages
    - Send reply emails
    """

    def __init__(self):
        """Initialize Gmail handler with OAuth credentials."""
        self.credentials = get_gmail_credentials()
        self.service = build('gmail', 'v1', credentials=self.credentials)
        self._last_history_id = None
        logger.info("📧 GmailHandler initialized successfully")

    async def setup_push_notifications(self, project_id: str, topic_name: str = "gmail-notifications") -> dict:
        """
        Set up Gmail push notifications via Google Pub/Sub.

        Args:
            project_id: Google Cloud project ID
            topic_name: Pub/Sub topic name (default: gmail-notifications)

        Returns:
            dict: Watch response with historyId and expiration
        """
        full_topic_name = f"projects/{project_id}/topics/{topic_name}"

        request = {
            'labelIds': ['INBOX'],
            'topicName': full_topic_name,
            'labelFilterAction': 'include'
        }

        try:
            response = self.service.users().watch(userId='me', body=request).execute()
            self._last_history_id = response.get('historyId')

            logger.info(f"✅ Gmail watch setup successful!")
            logger.info(f"   History ID: {self._last_history_id}")
            logger.info(f"   Expiration: {response.get('expiration')}")

            return response
        except Exception as e:
            logger.error(f"❌ Failed to setup Gmail watch: {e}")
            raise

    async def stop_push_notifications(self):
        """Stop watching for Gmail push notifications."""
        try:
            self.service.users().stop(userId='me').execute()
            logger.info("🛑 Gmail watch stopped")
        except Exception as e:
            logger.error(f"❌ Failed to stop Gmail watch: {e}")

    async def process_pubsub_notification(self, pubsub_message: dict) -> List[Dict[str, Any]]:
        """
        Process incoming Pub/Sub notification from Gmail.

        Args:
            pubsub_message: Decoded Pub/Sub message data

        Returns:
            List of parsed email messages
        """
        history_id = pubsub_message.get('historyId')
        email_address = pubsub_message.get('emailAddress')

        logger.info(f"📬 Processing Gmail notification for {email_address}")
        logger.info(f"   History ID: {history_id}")

        if not self._last_history_id:
            # First notification - just store the history ID
            self._last_history_id = history_id
            logger.info("   First notification - storing history ID")
            return []

        try:
            # Get new messages since last history ID
            history = self.service.users().history().list(
                userId='me',
                startHistoryId=self._last_history_id,
                historyTypes=['messageAdded']
            ).execute()

            # Update last history ID
            self._last_history_id = history_id

            messages = []
            for record in history.get('history', []):
                for msg_added in record.get('messagesAdded', []):
                    msg_id = msg_added['message']['id']

                    # Skip messages we sent (SENT label)
                    labels = msg_added['message'].get('labelIds', [])
                    if 'SENT' in labels:
                        continue

                    message = await self.get_message(msg_id)
                    if message:
                        messages.append(message)
                        logger.info(f"   📩 New email from: {message['customer_email']}")

            logger.info(f"   Total new emails: {len(messages)}")
            return messages

        except Exception as e:
            logger.error(f"❌ Error processing history: {e}")
            # Reset history ID on error
            self._last_history_id = history_id
            return []

    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and parse a Gmail message.

        Args:
            message_id: Gmail message ID

        Returns:
            Parsed message dict with channel, content, customer info
        """
        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            headers = {h['name'].lower(): h['value'] for h in msg['payload']['headers']}

            # Extract body
            body = self._extract_body(msg['payload'])

            # Extract customer email
            from_header = headers.get('from', '')
            customer_email = self._extract_email(from_header)
            customer_name = self._extract_name(from_header)

            return {
                'channel': 'email',
                'channel_message_id': message_id,
                'customer_email': customer_email,
                'customer_name': customer_name,
                'subject': headers.get('subject', '(No Subject)'),
                'content': body,
                'received_at': datetime.utcnow().isoformat(),
                'thread_id': msg.get('threadId'),
                'metadata': {
                    'gmail_id': message_id,
                    'labels': msg.get('labelIds', []),
                    'snippet': msg.get('snippet', ''),
                    'headers': {
                        'from': headers.get('from'),
                        'to': headers.get('to'),
                        'date': headers.get('date'),
                        'message-id': headers.get('message-id'),
                        'in-reply-to': headers.get('in-reply-to'),
                    }
                }
            }

        except Exception as e:
            logger.error(f"❌ Error fetching message {message_id}: {e}")
            return None

    def _extract_body(self, payload: dict) -> str:
        """
        Extract text body from email payload.

        Handles both simple and multipart emails.
        """
        # Simple message with body data
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        # Multipart message - look for text/plain
        if 'parts' in payload:
            for part in payload['parts']:
                # Recursively handle nested parts
                if part.get('mimeType') == 'multipart/alternative':
                    return self._extract_body(part)

                if part['mimeType'] == 'text/plain' and part['body'].get('data'):
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')

            # Fallback to HTML if no plain text
            for part in payload['parts']:
                if part['mimeType'] == 'text/html' and part['body'].get('data'):
                    html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    # Basic HTML stripping (for better parsing, use beautifulsoup)
                    return re.sub('<[^<]+?>', '', html)

        return ''

    def _extract_email(self, from_header: str) -> str:
        """Extract email address from From header."""
        match = re.search(r'<([^>]+)>', from_header)
        if match:
            return match.group(1).lower()
        # No angle brackets - assume entire string is email
        return from_header.strip().lower()

    def _extract_name(self, from_header: str) -> str:
        """Extract name from From header."""
        # Format: "John Doe <john@example.com>"
        match = re.match(r'^"?([^"<]+)"?\s*<', from_header)
        if match:
            return match.group(1).strip()
        # No name found
        return ""

    async def send_reply(
        self,
        to_email: str,
        subject: str,
        body: str,
        thread_id: str = None,
        in_reply_to: str = None
    ) -> Dict[str, Any]:
        """
        Send an email reply.

        Args:
            to_email: Recipient email address
            subject: Email subject (will add "Re:" if not present)
            body: Plain text email body
            thread_id: Gmail thread ID to reply in
            in_reply_to: Message-ID header for proper threading

        Returns:
            dict with channel_message_id and delivery_status
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            message['subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject

            # Add threading headers
            if in_reply_to:
                message['In-Reply-To'] = in_reply_to
                message['References'] = in_reply_to

            # Add plain text body
            text_part = MIMEText(body, 'plain')
            message.attach(text_part)

            # Encode
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Prepare send request
            send_request = {'raw': raw}
            if thread_id:
                send_request['threadId'] = thread_id

            # Send
            result = self.service.users().messages().send(
                userId='me',
                body=send_request
            ).execute()

            logger.info(f"✅ Email sent successfully to {to_email}")
            logger.info(f"   Message ID: {result['id']}")

            return {
                'channel_message_id': result['id'],
                'thread_id': result.get('threadId'),
                'delivery_status': 'sent',
                'sent_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return {
                'channel_message_id': None,
                'delivery_status': 'failed',
                'error': str(e)
            }

    async def mark_as_read(self, message_id: str):
        """Mark a message as read by removing UNREAD label."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            logger.info(f"📖 Marked message {message_id} as read")
        except Exception as e:
            logger.error(f"❌ Failed to mark message as read: {e}")

    async def add_label(self, message_id: str, label_name: str):
        """Add a label to a message (creates label if needed)."""
        try:
            # Get or create label
            labels = self.service.users().labels().list(userId='me').execute()
            label_id = None

            for label in labels.get('labels', []):
                if label['name'].lower() == label_name.lower():
                    label_id = label['id']
                    break

            if not label_id:
                # Create label
                new_label = self.service.users().labels().create(
                    userId='me',
                    body={'name': label_name}
                ).execute()
                label_id = new_label['id']

            # Add label
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()

            logger.info(f"🏷️ Added label '{label_name}' to message {message_id}")

        except Exception as e:
            logger.error(f"❌ Failed to add label: {e}")


# --- Singleton Instance ---
_gmail_handler: Optional[GmailHandler] = None


def get_gmail_handler() -> GmailHandler:
    """Get or create singleton GmailHandler instance."""
    global _gmail_handler
    if _gmail_handler is None:
        _gmail_handler = GmailHandler()
    return _gmail_handler


# --- Test Script ---
if __name__ == "__main__":
    import asyncio

    async def test():
        print("=" * 60)
        print("📧 Testing Gmail Handler")
        print("=" * 60)

        handler = get_gmail_handler()

        # Test fetching recent messages
        print("\n📬 Fetching recent messages...")
        messages = handler.service.users().messages().list(
            userId='me',
            maxResults=5,
            labelIds=['INBOX']
        ).execute()

        for msg in messages.get('messages', [])[:3]:
            parsed = await handler.get_message(msg['id'])
            if parsed:
                print(f"\n   From: {parsed['customer_email']}")
                print(f"   Subject: {parsed['subject']}")
                print(f"   Preview: {parsed['content'][:100]}...")

        print("\n✅ Gmail Handler test complete!")

    asyncio.run(test())
