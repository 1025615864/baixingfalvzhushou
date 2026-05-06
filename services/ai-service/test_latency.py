import requests
import time

print("测试优化后的延迟...")

start = time.time()
r = requests.post("http://localhost:8009/api/v1/ai/chat", json={"user_id": 1, "message": "老板不发工资我该怎么办"})
elapsed = time.time() - start
d = r.json()

print(f"总延迟: {elapsed:.1f}s")
print(f"intent: {d.get('intent')}")
print(f"sources: {len(d.get('sources', []))}")
print(f"响应预览: {d.get('message', '')[:80]}...")
