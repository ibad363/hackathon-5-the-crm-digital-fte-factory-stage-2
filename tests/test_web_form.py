import asyncio
import httpx

async def test_form_submission():
    async with httpx.AsyncClient() as client:
        print("Submitting test form via Next.js API route...")
        try:
            response = await client.post(
                "http://127.0.0.1:3000/api/support/submit",
                json={
                    "name": "Hafiz Ibad ur Rehman",
                    "email": "hafizibadurrehman363@gmail.com",
                    # "subject": "How do I integrate Slack with my TaskVault projects?",
                    "subject": "Slack Integration Support Request",
                    "category": "technical",
                    "priority": "medium",
                    "message": "Hello, my team lives in Slack and we want to start getting notifications whenever a task status changes to 'Done' in TaskVault. I looked around the dashboard but couldn't figure out how to set up the webhook. Can you give me the step-by-step instructions on how to connect a TaskVault board to a Slack channel?"
                    # "message": "Hi, my dashboard keeps crashing when I click the save button."
                    # "message": "How to Set Up a Slack Integration"
                },
                timeout=10.0
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_form_submission())
