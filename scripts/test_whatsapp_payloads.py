# scripts/test_whatsapp_payloads.py
import asyncio
import httpx
import json
import os
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEBHOOK_URL = "http://localhost:8000/api/webhooks/whatsapp"

async def send_payload(name: str, phone: str, content: str, message_sid: str = None):
    if not message_sid:
        message_sid = f"SM{uuid.uuid4().hex}"

    payload = {
        "MessageSid": message_sid,
        "From": f"whatsapp:{phone}",
        "To": "whatsapp:+14155238886",
        "Body": content,
        "ProfileName": name,
        "WaId": phone,
        "SmsStatus": "received",
        "NumMedia": "0"
    }

    logger.info(f"\n--- Testing: {name} ({phone}) ---")
    logger.info(f"Content: {content}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                WEBHOOK_URL,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            logger.info(f"Response Code: {response.status_code}")
            logger.info(f"Response Body: {response.text}")
        except Exception as e:
            logger.error(f"Failed to send payload: {e}")

async def main():
    # 1. Normal: "how do i reset my password" — Ahmed
    await send_payload("Ahmed", "+20123456789", "how do i reset my password")

    # 2. Human keyword: "human" — instant escalate
    await send_payload("Human Test", "+1555000111", "I want to talk to a human please")

    # 3. Vague: "its not working" — Marcus
    await send_payload("Marcus", "+447700900123", "its not working")

    # 4. Angry: "THIS IS RIDICULOUS your app deleted all my data!!!" — Sara
    await send_payload("Sara", "+12125550199", "THIS IS RIDICULOUS your app deleted all my data!!!")

    # 5. Complex: "how do i integrate flowsync with github slack and google drive" — Bilal
    await send_payload("Bilal", "+923001234567", "how do i integrate flowsync with github slack and google drive")

if __name__ == "__main__":
    asyncio.run(main())
