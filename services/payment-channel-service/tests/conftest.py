import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.main import create_app
from services.common.testing.fixtures import MockRedis, MockKafkaProducer


@pytest.fixture
def mock_redis():
    return MockRedis()


@pytest.fixture
def mock_kafka_producer():
    return MockKafkaProducer()


@pytest.fixture
async def app():
    application = create_app()
    yield application


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_order_data():
    return {
        "user_id": 1,
        "order_type": "membership",
        "amount": 99.0,
        "title": "会员订阅",
        "description": "月度会员",
        "payment_method": "alipay",
    }
