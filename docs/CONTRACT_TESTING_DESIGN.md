# 微服务契约测试架构设计 (Pact)

## 1. 概述

本文档描述百姓助手项目微服务契约测试解决方案，采用 **Pact** 实现消费者驱动的契约测试（Consumer-Driven Contract Testing）。

## 2. 为什么选择 Pact

| 特性 | Pact | Spring Cloud Contract | 说明 |
|------|------|----------------------|------|
| 多语言支持 | ✅ (12种语言) | 主要 Java | Pact 更通用 |
| 消费者驱动 | ✅ 原生支持 | 需额外配置 | Pact 更适合 |
| Broker 平台 | ✅ PactFlow | PactFlow 也支持 | 两者都可 |
| CI/CD 集成 | ✅ 简单 | 中等 | Pact 更简单 |
| 可视化 | ✅ 优秀 | 中等 | Pact 更好 |

## 3. 目标架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         契约测试架构                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Consumer Services                                                   Provider │
│  ┌──────────────┐                                                  ┌──────────────┐
│  │ User Service│◄────── Pact Broker ──────────────────────────────│Legal Service │
│  │              │        │                                         │              │
│  │ 1. 定义消费者│        │  2. 发布契约                            │3. 验证契约   │
│  │    expectations│     │                                         │              │
│  └──────────────┘        │                                         └──────────────┘
│         │                 │                                                   │
│         │                 ▼                                                   │
│         │         ┌─────────────────────────────────────┐                     │
│         │         │         Pact Broker                  │                     │
│         │         │  ┌─────────────────────────────────┐│                     │
│         │         │  │  contract: user-legal.json     ││                     │
│         │         │  │  pact: user + legal            ││                     │
│         │         │  │  can-i-deploy: ✓              ││                     │
│         │         │  └─────────────────────────────────┘│                     │
│         │         └─────────────────────────────────────┘                     │
│         │                                                                  │
│         ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                           CI/CD Pipeline                               │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐               │  │
│  │  │ Consumer│──►│  Publish│──►│ Verify  │──►│ Deploy  │               │  │
│  │  │   Test  │  │  Pact   │  │ Contracts│  │  (if OK) │               │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4. Pact Broker 部署

### 4.1 Docker Compose 配置

```yaml
# docker-compose.pact.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: pact-postgres
    environment:
      POSTGRES_DB: pact
      POSTGRES_USER: pact
      POSTGRES_PASSWORD: pact_password
    volumes:
      - pact-data:/var/lib/postgresql/data
    networks:
      - baixing-network

  pact-broker:
    image: pactfoundation/pact-broker:2.105.0.0
    container_name: pact-broker
    ports:
      - "9292:9292"
    environment:
      PACT_BROKER_DATABASE_URL: postgresql://pact:pact_password@postgres:5432/pact
      PACT_BROKER_PORT: 9292
      PACT_BROKER_LOG_LEVEL: INFO
      PACT_BROKER_BASE_URL: http://localhost:9292
      PACT_BROKER_S3: false
      PACT_BROKER_ALLOW_PUBLIC_READ: true
    depends_on:
      - postgres
    networks:
      - baixing-network

  pact-verifier:
    image: pactfoundation/pact-verifier:1
    container_name: pact-verifier
    volumes:
      - ./pact-contracts:/pact-contracts:ro
    command: --help
    networks:
      - baixing-network

volumes:
  pact-data:
    driver: local

networks:
  baixing-network:
    external: true
```

## 5. 消费者端实现

### 5.1 目录结构

```
services/
├── user-service/
│   ├── app/
│   │   ├── consumers/
│   │   │   ├── __init__.py
│   │   │   ├── legal_consumer.py      # 对 Legal Service 的消费者测试
│   │   │   └── payment_consumer.py   # 对 Payment Service 的消费者测试
│   │   └── providers/
│   │       └── legal_provider.py     # 模拟 Legal Service 响应
│   └── tests/
│       ├── contracts/
│       │   ├── test_user_legal_contract.py
│       │   └── test_user_payment_contract.py
│       └── conftest.py
│   └── requirements.txt
│
├── payment-service/
│   ├── app/
│   │   └── consumers/
│   │       └── user_consumer.py
│   └── tests/
│       └── contracts/
│           └── test_payment_user_contract.py
```

### 5.2 Python 消费者测试 (services/user-service/tests/contracts/test_user_legal_contract.py)

```python
import pytest
from pact import Consumer, Provider, EachLike, Like, Term
from pact.matchers import like
import json
from datetime import datetime


@pytest.fixture
def pact_user_legal():
    consumer = Consumer("UserService")
    provider = Provider("LegalService")

    pact = consumer.has_pact_with(provider, pact_dir="./pact-contracts")
    pact.start_service()
    yield pact
    pact.stop_service()


class TestUserLegalContract:
    """User Service 作为消费者，Legal Service 作为提供者"""

    def test_get_lawyer_profile(self, pact_user_legal):
        """测试获取律师信息"""

        expected_response = {
            "lawyer_id": "like(lawyer-123)",
            "name": "Test Lawyer",
            "firm_id": "like(firm-456)",
            "title": "Senior Partner",
            "expertise": ["like(criminal)", "like(civil)"],
            "rating": 4.5,
            "consultation_count": 100,
            "price_per_hour": 50000
        }

        (
            pact_user_legal
            .given("Lawyer with ID lawyer-123 exists")
            .upon_receiving("a request for lawyer profile")
            .with_request(
                method="GET",
                path="/api/v1/legal/lawyers/lawyer-123",
                headers={
                    "Accept": "application/json",
                    "Authorization": Term(r"Bearer \w+", "Bearer test-token")
                }
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body=Like({
                    "lawyer_id": "lawyer-123",
                    "name": "Test Lawyer",
                    "firm_id": "firm-456",
                    "title": "Senior Partner",
                    "expertise": ["criminal", "civil"],
                    "rating": like(4.5),
                    "consultation_count": like(100),
                    "price_per_hour": like(50000)
                })
            )
        )

        with pact_user_legal:
            from services.user_service.app.clients.legal_client import LegalServiceClient
            client = LegalServiceClient(base_url=pact_user_legal.uri)
            response = client.get_lawyer("lawyer-123", "test-token")

            assert response["lawyer_id"] == "lawyer-123"
            assert response["name"] == "Test Lawyer"

    def test_get_lawyer_schedule(self, pact_user_legal):
        """测试获取律师日程"""

        (
            pact_user_legal
            .given("Lawyer lawyer-123 has available slots")
            .upon_receiving("a request for lawyer schedule")
            .with_request(
                method="GET",
                path="/api/v1/legal/lawyers/lawyer-123/schedule",
                query={
                    "date": "2024-03-25"
                },
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer test-token"
                }
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body=Like({
                    "lawyer_id": "lawyer-123",
                    "available_slots": EachLike({
                        "slot_id": "slot-1",
                        "start_time": "2024-03-25T09:00:00Z",
                        "end_time": "2024-03-25T10:00:00Z",
                        "is_available": True
                    }, minimum=1)
                })
            )
        )

        with pact_user_legal:
            from services.user_service.app.clients.legal_client import LegalServiceClient
            client = LegalServiceClient(base_url=pact_user_legal.uri)
            response = client.get_schedule("lawyer-123", "2024-03-25", "test-token")

            assert response["lawyer_id"] == "lawyer-123"
            assert len(response["available_slots"]) >= 1

    def test_create_consultation(self, pact_user_legal):
        """测试创建咨询"""

        (
            pact_user_legal
            .given("User user-123 wants to create consultation")
            .upon_receiving("a request to create consultation")
            .with_request(
                method="POST",
                path="/api/v1/legal/consultations",
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer test-token"
                },
                body=Like({
                    "user_id": "user-123",
                    "lawyer_id": "lawyer-123",
                    "type": "video",
                    "scheduled_at": "2024-03-25T10:00:00Z",
                    "description": "法律咨询"
                })
            )
            .will_respond_with(
                status=201,
                headers={"Content-Type": "application/json"},
                body=Like({
                    "consultation_id": "like(consultation-789)",
                    "user_id": "user-123",
                    "lawyer_id": "lawyer-123",
                    "type": "video",
                    "status": "pending",
                    "scheduled_at": "2024-03-25T10:00:00Z"
                })
            )
        )

        with pact_user_legal:
            from services.user_service.app.clients.legal_client import LegalServiceClient
            client = LegalServiceClient(base_url=pact_user_legal.uri)
            response = client.create_consultation(
                user_id="user-123",
                lawyer_id="lawyer-123",
                consultation_type="video",
                scheduled_at="2024-03-25T10:00:00Z",
                description="法律咨询",
                token="test-token"
            )

            assert response["consultation_id"] is not None
            assert response["status"] == "pending"


@pytest.fixture(scope="module")
def publish_pact_files():
    """发布 Pact 文件到 Broker"""
    import os
    import subprocess

    pact_dir = "./pact-contracts"
    broker_url = os.getenv("PACT_BROKER_URL", "http://localhost:9292")
    broker_token = os.getenv("PACT_BROKER_TOKEN", "")

    for filename in os.listdir(pact_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(pact_dir, filename)
            cmd = [
                "pact-broker", "publish",
                filepath,
                "--broker-base-url", broker_url,
                "--consumer-app-version", os.getenv("GIT_SHA", "dev"),
            ]
            if broker_token:
                cmd.extend(["--broker-token", broker_token])

            subprocess.run(cmd, check=True)

    # 验证能否部署
    subprocess.run([
        "pact-broker", "can-i-deploy",
        "--pacticipant", "UserService",
        "--broker-base-url", broker_url,
        "--broker-token", broker_token,
        "--to-environment", "production"
    ])
```

### 5.3 TypeScript 消费者测试 (services/user-service/tests/contracts/user-legal.pact.test.ts)

```typescript
import { PactV3, MatchersV3, PactV3Options } from '@pact-foundation/pact';
import path from 'path';

const { like, eachLike, term, string } = MatchersV3;

describe('User Service -> Legal Service Contract', () => {
  const provider = new PactV3({
    consumer: 'UserService',
    provider: 'LegalService',
    logLevel: 'warn',
    dir: path.resolve(__dirname, '../pacts'),
    spec: 3,
  });

  describe('GET /api/v1/legal/lawyers/:lawyerId', () => {
    it('returns lawyer profile', async () => {
      await provider.addInteraction({
        states: [{ description: 'Lawyer lawyer-123 exists' }],
        uponReceiving: 'a request for lawyer profile',
        withRequest: {
          method: 'GET',
          path: '/api/v1/legal/lawyers/lawyer-123',
          headers: {
            Accept: 'application/json',
            Authorization: string('Bearer test-token'),
          },
        },
        willRespondWith: {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: {
            lawyer_id: string('lawyer-123'),
            name: string('Test Lawyer'),
            firm_id: string('firm-456'),
            title: string('Senior Partner'),
            expertise: eachLike(string('criminal')),
            rating: like(4.5),
            consultation_count: like(100),
            price_per_hour: like(50000),
          },
        },
      });

      const response = await fetch(
        `${provider.mockService.baseUrl}/api/v1/legal/lawyers/lawyer-123`,
        {
          headers: {
            Accept: 'application/json',
            Authorization: 'Bearer test-token',
          },
        }
      );

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.lawyer_id).toBe('lawyer-123');
    });
  });
});
```

## 6. 提供者端实现

### 6.1 Python 提供者验证 (services/legal-service/tests/contracts/test_provider_contracts.py)

```python
import pytest
from pact import Verifier
import os
import subprocess


@pytest.fixture(scope="module")
def verifier():
    verifier = Verifier(
        provider="LegalService",
        provider_base_url=os.getenv("LEGAL_SERVICE_URL", "http://localhost:8004"),
        pact_dir="./pact-contracts",
    )
    return verifier


@pytest.fixture(scope="module", autouse=True)
def setup_provider():
    """启动 Legal Service 用于测试"""
    import subprocess
    import time

    # 启动服务 (实际项目中应该使用测试环境)
    # process = subprocess.Popen(["uvicorn", "app.main:app", "--port", "8004"])

    # 等待服务启动
    # time.sleep(5)

    yield

    # 关闭服务
    # process.terminate()


class TestLegalServiceContracts:
    """Legal Service 作为提供者验证契约"""

    def test_verify_user_service_contracts(self, verifier):
        """验证来自 User Service 的所有契约"""

        broker_url = os.getenv("PACT_BROKER_URL", "http://localhost:9292")
        broker_token = os.getenv("PACT_BROKER_TOKEN", "")

        output = verifier.verify_pacts(
            provider_states_setup_url=f"{os.getenv('LEGAL_SERVICE_URL')}/test/provider-states",
        )

        # 发布验证结果
        verifier.publish_results(
            broker_base_url=broker_url,
            broker_token=broker_token,
            version=os.getenv("GIT_SHA", "dev"),
        )

        assert "0 failures" in output


class TestProviderStates:
    """提供者状态端点"""

    @pytest.fixture
    def client(self):
        from services.legal_service.app.main import app
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_setup_lawyer_exists(self, client):
        """设置律师存在的状态"""
        response = client.post(
            "/test/provider-states",
            json={
                "description": "Lawyer lawyer-123 exists",
                "params": {"lawyer_id": "lawyer-123"}
            }
        )
        assert response.status_code == 200

    def test_teardown_lawyer_exists(self, client):
        """清理律师状态"""
        response = client.delete(
            "/test/provider-states",
            json={"description": "Lawyer lawyer-123 exists"}
        )
        assert response.status_code == 200
```

### 6.2 提供者状态端点 (services/legal-service/app/main.py)

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="LegalService")


class ProviderStateRequest(BaseModel):
    description: str
    params: dict = {}


class ProviderStateResponse(BaseModel):
    success: bool
    message: str


@app.post("/test/provider-states")
async def setup_provider_state(state: ProviderStateRequest):
    """设置测试状态"""
    if state.description == "Lawyer lawyer-123 exists":
        # 设置测试数据
        await TestData.setup_lawyer(state.params.get("lawyer_id"))
        return ProviderStateResponse(success=True, message="State setup")

    return ProviderStateResponse(success=True, message="No state to setup")


@app.delete("/test/provider-states")
async def teardown_provider_state(state: ProviderStateRequest):
    """清理测试状态"""
    if state.description == "Lawyer lawyer-123 exists":
        await TestData.teardown_lawyer(state.params.get("lawyer_id"))
        return ProviderStateResponse(success=True, message="State teardown")

    return ProviderStateResponse(success=True, message="No state to teardown")
```

## 7. CI/CD 集成

### 7.1 GitHub Actions 工作流 (.github/workflows/pact.yml)

```yaml
name: Contract Testing

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  consumer-tests:
    name: Consumer Contract Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r services/user-service/requirements.txt
          pip install pact-python pytest

      - name: Run consumer tests
        env:
          PACT_BROKER_URL: ${{ secrets.PACT_BROKER_URL }}
          PACT_BROKER_TOKEN: ${{ secrets.PACT_BROKER_TOKEN }}
          GIT_SHA: ${{ github.sha }}
        run: |
          cd services/user-service
          pytest tests/contracts/ -v

      - name: Publish pacts
        if: github.ref == 'refs/heads/main'
        env:
          PACT_BROKER_URL: ${{ secrets.PACT_BROKER_URL }}
          PACT_BROKER_TOKEN: ${{ secrets.PACT_BROKER_TOKEN }}
          GIT_SHA: ${{ github.sha }}
        run: |
          pact-broker publish pact-contracts/ \
            --broker-base-url $PACT_BROKER_URL \
            --broker-token $PACT_BROKER_TOKEN \
            --consumer-app-version $GIT_SHA

      - name: Check can-i-deploy
        if: github.ref == 'refs/heads/main'
        env:
          PACT_BROKER_URL: ${{ secrets.PACT_BROKER_URL }}
          PACT_BROKER_TOKEN: ${{ secrets.PACT_BROKER_TOKEN }}
        run: |
          pact-broker can-i-deploy \
            --pacticipant UserService \
            --broker-base-url $PACT_BROKER_URL \
            --broker-token $PACT_BROKER_TOKEN \
            --to-environment production

  provider-tests:
    name: Provider Contract Verification
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r services/legal-service/requirements.txt
          pip install pact-python pytest

      - name: Pull pacts from broker
        if: github.ref == 'refs/heads/main'
        env:
          PACT_BROKER_URL: ${{ secrets.PACT_BROKER_URL }}
          PACT_BROKER_TOKEN: ${{ secrets.PACT_BROKER_TOKEN }}
        run: |
          pact-broker broker-base-url $PACT_BROKER_URL \
            --broker-token $PACT_BROKER_TOKEN \
            pacticipant LegalService \
            --latest

      - name: Run provider verification
        env:
          PACT_BROKER_URL: ${{ secrets.PACT_BROKER_URL }}
          PACT_BROKER_TOKEN: ${{ secrets.PACT_BROKER_TOKEN }}
          LEGAL_SERVICE_URL: http://localhost:8004
          GIT_SHA: ${{ github.sha }}
        run: |
          # 启动服务 (使用后台运行)
          cd services/legal-service
          uvicorn app.main:app --port 8004 &
          sleep 5

          pytest tests/contracts/test_provider_contracts.py -v

      - name: Publish verification results
        if: github.ref == 'refs/heads/main'
        env:
          PACT_BROKER_URL: ${{ secrets.PACT_BROKER_URL }}
          PACT_BROKER_TOKEN: ${{ secrets.PACT_BROKER_TOKEN }}
          GIT_SHA: ${{ github.sha }}
        run: |
          # 验证结果会自动发布到 Broker
```

## 8. 契约定义示例

### 8.1 Pact 文件结构 (pacts/UserService-LegalService.json)

```json
{
  "consumer": {
    "name": "UserService"
  },
  "provider": {
    "name": "LegalService"
  },
  "interactions": [
    {
      "description": "a request for lawyer profile",
      "providerState": "Lawyer lawyer-123 exists",
      "request": {
        "method": "GET",
        "path": "/api/v1/legal/lawyers/lawyer-123",
        "headers": {
          "Accept": "application/json",
          "Authorization": "Bearer test-token"
        }
      },
      "response": {
        "status": 200,
        "headers": {
          "Content-Type": "application/json"
        },
        "body": {
          "lawyer_id": "lawyer-123",
          "name": "Test Lawyer",
          "firm_id": "firm-456",
          "title": "Senior Partner",
          "expertise": ["criminal", "civil"],
          "rating": 4.5,
          "consultation_count": 100,
          "price_per_hour": 50000
        },
        "matchingRules": {
          "$.body.lawyer_id": {"match": "type"},
          "$.body.expertise": {"min": 1}
        }
      }
    },
    {
      "description": "a request to create consultation",
      "providerState": "User user-123 wants to create consultation",
      "request": {
        "method": "POST",
        "path": "/api/v1/legal/consultations",
        "headers": {
          "Accept": "application/json",
          "Content-Type": "application/json",
          "Authorization": "Bearer test-token"
        },
        "body": {
          "user_id": "user-123",
          "lawyer_id": "lawyer-123",
          "type": "video",
          "scheduled_at": "2024-03-25T10:00:00Z",
          "description": "法律咨询"
        }
      },
      "response": {
        "status": 201,
        "headers": {
          "Content-Type": "application/json"
        },
        "body": {
          "consultation_id": "consultation-789",
          "user_id": "user-123",
          "lawyer_id": "lawyer-123",
          "type": "video",
          "status": "pending"
        }
      }
    }
  ],
  "metadata": {
    "pactSpecification": {
      "version": "3.0.0"
    }
  }
}
```

## 9. 迁移计划

### Phase 1: 基础设施 (Week 1)
1. 部署 Pact Broker (Docker Compose)
2. 配置 Python Pact 环境
3. 创建共享测试工具

### Phase 2: 核心契约测试 (Week 2)
1. User Service ↔ Legal Service 契约
2. User Service ↔ Payment Service 契约
3. 集成到 CI/CD

### Phase 3: 扩展契约测试 (Week 3)
1. AI Service 契约测试
2. Notification Service 契约测试
3. 覆盖率报告
