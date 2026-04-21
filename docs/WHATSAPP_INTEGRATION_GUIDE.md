# WhatsApp Integration Guide — TaskVault CRM

## 📌 Introduction
The WhatsApp integration allows TaskVault to communicate with customers in real-time using the Twilio API. It uses a push-based model where Twilio notifies our server the moment a customer sends a message.

---

## 1. How It Works (Architecture)

The flow of a WhatsApp message is straightforward:
1. A customer sends a WhatsApp message to your Twilio number.
2. Twilio receives the message and immediately sends a notification to your server.
3. Your server validates that the message actually came from Twilio for security.
4. The system identifies the customer in the database or creates a new profile.
5. The message is logged, and the TaskVault Agent is triggered to generate a response.
6. The Agent's response is formatted for WhatsApp (concise and helpful).
7. The response is sent back to the customer via the Twilio API.

---

## 2. Prerequisites

Before starting the setup, ensure you have:
- A Twilio Account (the free trial/sandbox works for development).
- Python 3.11 or higher installed on your machine.
- A running PostgreSQL database for storing customer history.
- ngrok installed to allow Twilio to reach your local computer.
- A smartphone with WhatsApp installed for testing.

---

## 3. Step-by-Step Setup Guide

### Step 3.1: Twilio Account Setup
1. Sign up at Twilio.com and log in to your Console.
2. Locate your Account SID and Auth Token on the dashboard. You will need these for your configuration.
3. In the left menu, navigate to Messaging -> Try it out -> Send a WhatsApp message.
4. Follow the instructions to activate the Twilio Sandbox for WhatsApp. This usually involves sending a specific code (like "join-something") from your phone to a Twilio number.

### Step 3.2: Configure the Webhook
1. Start ngrok on your computer to create a public tunnel (usually on port 8000).
2. Copy the HTTPS URL provided by ngrok.
3. Go back to the Twilio Console under Messaging -> Settings -> WhatsApp Sandbox Settings.
4. In the field labeled "WHEN A MESSAGE COMES IN", paste your ngrok URL followed by /api/webhooks/whatsapp.
5. Ensure the method is set to POST.
6. Save your settings.

### Step 3.3: Environment Configuration
You need to add your Twilio credentials to your system's configuration. This includes your Account SID, Auth Token, and the Twilio WhatsApp number provided in the sandbox (it usually starts with whatsapp:+1...).

---

## 4. Common Mistakes & How to Avoid Them

### Validating the Source
Twilio sends a special signature with every request. If your server is not correctly validating this signature, it might ignore legitimate messages or be vulnerable to fake ones. Ensure your Auth Token is correctly set, as it is used for this validation.

### The ngrok URL Change
Every time you restart a free ngrok session, you get a new URL. You must remember to update the Webhook URL in the Twilio Sandbox settings every time you restart your development environment, or messages will not reach your server.

### Format and Length
WhatsApp messages have a character limit of 1600. While TaskVault automatically splits long messages, it is best to keep responses concise. The Agent is instructed to keep WhatsApp replies under 300 characters whenever possible for a better mobile experience.

---

## 5. Known Limitations

### Twilio Sandbox vs Production
The Sandbox is great for testing but has limitations. You can only send messages to users who have "joined" your sandbox. For a real-world application, you would need to apply for a WhatsApp Business Account and get a dedicated number approved by Meta.

### Session Windows
WhatsApp has a 24-hour "session window." You can send free-form messages to a customer within 24 hours of their last message. If more than 24 hours pass, you can only send pre-approved "Templates," which usually require a paid account and prior approval from WhatsApp.

### Media Support
The current integration focuses on text. While the system can detect if a customer sent an image or document, the Agent is currently optimized for text-based support.

---

*Guide written for the TaskVault CRM Digital FTE Factory.*
*Last Updated: April 2026*
