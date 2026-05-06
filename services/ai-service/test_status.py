import requests

print("=== AI服务完整测试 ===\n")

# 测试1: 法律问题
print("[测试1] 法律问题:")
r = requests.post("http://localhost:8009/api/v1/ai/chat", json={"user_id": 1, "message": "老板不发工资我该怎么办"})
d = r.json()
print(f"  intent: {d.get('intent')}")
print(f"  sources数量: {len(d.get('sources', []))}")
print(f"  响应预览: {d.get('message', '')[:80]}...")

# 测试2: 闲聊
print("\n[测试2] 闲聊:")
r = requests.post("http://localhost:8009/api/v1/ai/chat", json={"user_id": 1, "message": "你好"})
d = r.json()
print(f"  intent: {d.get('intent')}")
print(f"  响应: {d.get('message', '')[:60]}...")

# 测试3: RAG检索
print("\n[测试3] RAG检索:")
r = requests.get("http://localhost:8009/api/v1/ai/debug/rag", params={"query": "拖欠工资"})
d = r.json()
print(f"  retrieval_level: {d.get('retrieval_level')}")
print(f"  total_count: {d.get('total_count')}")
print(f"  sufficient: {d.get('sufficient')}")

# 测试4: 未知法律问题 - 应该是legal但无sources
print("\n[测试4] 未知法律问题(无相关法条):")
r = requests.post("http://localhost:8009/api/v1/ai/chat", json={"user_id": 1, "message": "什么是量子计算的法律问题"})
d = r.json()
print(f"  intent: {d.get('intent')}")
print(f"  sources数量: {len(d.get('sources', []))}")
print(f"  响应预览: {d.get('message', '')[:100]}...")

# 测试5: 测试冷启动延迟(第二次调用)
print("\n[测试5] 第二次法律调用(热启动):")
r = requests.post("http://localhost:8009/api/v1/ai/chat", json={"user_id": 1, "message": "公司不签劳动合同怎么办"})
d = r.json()
print(f"  intent: {d.get('intent')}")
print(f"  sources数量: {len(d.get('sources', []))}")
print(f"  延迟: {d.get('latency_ms')}ms")
