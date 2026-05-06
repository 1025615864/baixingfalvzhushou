import sys
sys.path.insert(0, '.')

import asyncio
from app.services.legal_agent import stream_legal_agent

async def test_agent():
    print("Testing stream_legal_agent...")
    query = "老板不发工资怎么办？"

    event_count = 0
    async for event in stream_legal_agent(user_query=query, chat_history=[], session_id=None):
        event_count += 1
        print(f"Event {event_count}: {list(event.keys())}")

        if "stage" in event:
            print(f"  Stage: {event.get('stage')}, Status: {event.get('status')}")
        if "response" in event:
            print(f"  Response: {event.get('response')[:100] if event.get('response') else 'None'}...")
        if "token" in event:
            print(f"  Token: {event.get('token')}")

    print(f"\nTotal events: {event_count}")

asyncio.run(test_agent())
