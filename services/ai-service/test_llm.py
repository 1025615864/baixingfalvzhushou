import sys
sys.path.insert(0, '.')

import asyncio
from app.services.llm_client import ResilientLLMClient

async def test_llm():
    client = ResilientLLMClient()

    print("Testing LLM API...")
    messages = [{"role": "user", "content": "用一句话回答：老板不发工资怎么办？"}]

    try:
        response = await client.call(messages)
        print(f"Response content: {response.content}")
        print(f"Model: {response.model}")
        print(f"Provider: {response.provider}")
        print(f"Latency: {response.latency_ms}ms")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_llm())
