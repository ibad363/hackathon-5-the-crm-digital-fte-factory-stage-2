# channels/gmail_handler.py
"""
Gmail Handler for TaskVault CRM

Handles Gmail integration via Push notifications (Pub/Sub)
- Receives email notifications via webhook
- Fetches and parses email content
- Sends reply emails via Gmail API
- Persists history state to avoid backlog floods
"""

import os
import sys
import re
import base64
import json
import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from channels.gmail_auth import get_gmail_credentials
from database.queries import get_db_pool

logger = logging.getLogger(__name__)

_STATE_NAME = "gmail_watch"

async def _load_last_history_id() -> Optional[int]:
    """Read last_history_id from `integration_state`. Returns None if not set."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT last_hid FROM integration_state WHERE name = $1",
                _STATE_NAME,
            )
            return int(row["last_hid"]) if row and row["last_hid"] else None
    except Exception as e:
        logger.error(f"Error loading history id: {e}")
        return None

async def _save_last_history_id(hid: int) -> None:
    """Up-sert the new historyId."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO integration_state (name, last_hid, updated_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (name) DO UPDATE
                SET last_hid = EXCLUDED.last_hid,
                    updated_at = NOW()
                """,
                _STATE_NAME,
                hid,
            )
    except Exception as e:
        logger.error(f"Error saving history id: {e}")


class GmailHandler:
    """
    Gmail integration handler for TaskVault CRM.

    Now production-ready with state persistence and backlog filtering.
    """

    def __init__(self):
        """Initialize Gmail handler with OAuth credentials."""
        self.credentials = get_gmail_credentials()
        self.service = build('gmail', 'v1', credentials=self.credentials)
        self._last_history_id: Optional[int] = None
        self._processed_msg_ids: set[str] = set()

        # Load persisted state in the background
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self._init_history_id())

        logger.info("📧 GmailHandler initialized successfully")

    async def _init_history_id(self):
        self._last_history_id = await _load_last_history_id()
        if self._last_history_id:
            logger.info(f"🔎 Loaded persisted last_history_id = {self._last_history_id}")

    async def setup_push_notifications(self, project_id: str, topic_name: str = "gmail-notifications") -> dict:
        """
        Set up Gmail push notifications via Google Pub/Sub.
        """
        full_topic_name = f"projects/{project_id}/topics/{topic_name}"

        request = {
            'labelIds': ['INBOX'],
            'topicName': full_topic_name,
            'labelFilterAction': 'include'
        }

        try:
            response = self.service.users().watch(userId='me', body=request).execute()
            new_hid = int(response.get('historyId'))
            self._last_history_id = new_hid
            await _save_last_history_id(new_hid)

            logger.info(f"✅ Gmail watch setup successful! Stored HID: {new_hid}")
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
        """
        history_id = int(pubsub_message.get('historyId'))
        email_address = pubsub_message.get('emailAddress')

        logger.info(f"📬 Processing Gmail notification for {email_address} (HID: {history_id})")

        # Load HID if not yet loaded
        if self._last_history_id is None:
            self._last_history_id = await _load_last_history_id()

        # If still no HID, jump to present
        if self._last_history_id is None:
            self._last_history_id = history_id
            await _save_last_history_id(history_id)
            logger.info(f"⚡ First run - jumping to present HID: {history_id}")
            return []

        # If history_id is behind our last seen, skip
        if history_id <= self._last_history_id:
            logger.info(f"🔁 History ID {history_id} <= last seen {self._last_history_id} - skipping")
            return []

        # If jump is too large (over 500 history events), skip the gap to avoid backlog flooding
        if history_id - self._last_history_id > 500:
            logger.info(f"⏩ Backlog too large ({history_id - self._last_history_id} events) - jumping to present")
            self._last_history_id = history_id
            await _save_last_history_id(history_id)
            return []

        try:
            # Get new messages since last history ID
            history = self.service.users().history().list(
                userId='me',
                startHistoryId=str(self._last_history_id),
                historyTypes=['messageAdded']
            ).execute()

            # Update last history ID immediately
            self._last_history_id = history_id
            await _save_last_history_id(history_id)

            messages = []
            now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
            # Filter: only emails received in the last 15 minutes
            recent_cutoff_ms = now_ms - (15 * 60 * 1000)

            for record in history.get('history', []):
                for msg_added in record.get('messagesAdded', []):
                    msg_meta = msg_added['message']
                    msg_id = msg_meta['id']

                    # 0. Deduplication: skip if message already processed in this session
                    if msg_id in self._processed_msg_ids:
                        continue

                    self._processed_msg_ids.add(msg_id)
                    # Memory management: reset after 1000 IDs to avoid unbounded growth
                    if len(self._processed_msg_ids) > 1000:
                        self._processed_msg_ids.clear()
                        self._processed_msg_ids.add(msg_id)

                    # 1. Skip messages we sent
                    if 'SENT' in msg_meta.get('labelIds', []):
                        continue

                    # 2. Skip messages older than 15 minutes
                    # msg_meta in history list doesn't have internalDate, we check it in get_message

                    # 3. Fetch full message
                    message = await self.get_message(msg_id)
                    if not message:
                        continue

                    # Internal date check
                    msg_date_ms = int(message.get('internalDate', now_ms))
                    if msg_date_ms < recent_cutoff_ms:
                        logger.debug(f"⏭️ Skipping old message {msg_id}")
                        continue

                    # Automated/Bounce check
                    sender = message['customer_email'].lower()
                    if any(x in sender for x in ["noreply", "no-reply", "mailer-daemon"]):
                        logger.info(f"⏭️ Skipping automated/bounce email from: {sender}")
                        continue

                    messages.append(message)
                    logger.info(f"📩 New email from: {sender}")

            logger.info(f"   Total new emails to process: {len(messages)}")
            return messages

        except Exception as e:
            logger.error(f"❌ Error processing history: {e}")
            if "History ID not found" in str(e):
                # HID expired (older than ~7 days). Jump to current.
                self._last_history_id = history_id
                await _save_last_history_id(history_id)
            return []

    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and parse a Gmail message.
        """
        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            headers = {h['name'].lower(): h['value'] for h in msg['payload']['headers']}
            body = self._extract_body(msg['payload'])
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
                'internalDate': msg.get('internalDate'),
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
            if "404" in str(e) or "not found" in str(e).lower():
                pass
            else:
                logger.error(f"❌ Error fetching message {message_id}: {e}")
            return None

    def _extract_body(self, payload: dict) -> str:
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'multipart/alternative':
                    return self._extract_body(part)
                if part['mimeType'] == 'text/plain' and part['body'].get('data'):
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            for part in payload['parts']:
                if part['mimeType'] == 'text/html' and part['body'].get('data'):
                    html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    return re.sub('<[^<]+?>', '', html)
        return ''

    def _extract_email(self, from_header: str) -> str:
        match = re.search(r'<([^>]+)>', from_header)
        return match.group(1).lower() if match else from_header.strip().lower()

    def _extract_name(self, from_header: str) -> str:
        match = re.match(r'^"?([^"<]+)"?\s*<', from_header)
        return match.group(1).strip() if match else ""

    async def send_reply(self, to_email: str, subject: str, body: str, thread_id: str = None, in_reply_to: str = None) -> Dict[str, Any]:
        try:
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            message['subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject
            if in_reply_to:
                message['In-Reply-To'] = in_reply_to
                message['References'] = in_reply_to
            message.attach(MIMEText(body, 'plain'))
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            send_request = {'raw': raw}
            if thread_id: send_request['threadId'] = thread_id
            result = self.service.users().messages().send(userId='me', body=send_request).execute()
            logger.info(f"✅ Email sent successfully to {to_email}")
            return {'channel_message_id': result['id'], 'thread_id': result.get('threadId'), 'delivery_status': 'sent', 'sent_at': datetime.utcnow().isoformat()}
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return {'channel_message_id': None, 'delivery_status': 'failed', 'error': str(e)}

    async def mark_as_read(self, message_id: str):
        try:
            self.service.users().messages().modify(userId='me', id=message_id, body={'removeLabelIds': ['UNREAD']}).execute()
        except Exception as e: logger.error(f"❌ Failed to mark read: {e}")

    async def add_label(self, message_id: str, label_name: str):
        try:
            labels = self.service.users().labels().list(userId='me').execute()
            label_id = next((l['id'] for l in labels.get('labels', []) if l['name'].lower() == label_name.lower()), None)
            if not label_id:
                new_label = self.service.users().labels().create(userId='me', body={'name': label_name}).execute()
                label_id = new_label['id']
            self.service.users().messages().modify(userId='me', id=message_id, body={'addLabelIds': [label_id]}).execute()
        except Exception as e: logger.error(f"❌ Failed to add label: {e}")

_gmail_handler: Optional[GmailHandler] = None

def get_gmail_handler() -> GmailHandler:
    global _gmail_handler
    if _gmail_handler is None:
        _gmail_handler = GmailHandler()
    return _gmail_handler

if __name__ == "__main__":
    import asyncio
    async def test():
        handler = get_gmail_handler()
        print("Gmail Handler production-ready test complete!")
    asyncio.run(test())
