import pytest
import asyncio
from pathlib import Path

from pact import Consumer, Provider, PactConfig, Broker
from pact.matchers import like, something_like, each_like


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def pact_dir():
    return Path(__file__).parent / "pacts"


@pytest.fixture(scope="session")
def pact_broker_url():
    import os
    return os.getenv("PACT_BROKER_URL", "http://localhost:9292")


@pytest.fixture(scope="session")
def pact_broker_token():
    import os
    return os.getenv("PACT_BROKER_TOKEN", "")


class PactContractMixin:
    consumer_name: str = "UnknownConsumer"
    provider_name: str = "UnknownProvider"
    pact_dir: Path = None
    log_dir: Path = None

    @property
    def pact_config(self):
        return PactConfig(
            consumer=self.consumer_name,
            provider=self.provider_name,
            pact_dir=str(self.pact_dir) if self.pact_dir else "./pacts",
            log_dir=str(self.log_dir) if self.log_dir else "./logs",
            publish_to_broker=False,
        )

    @property
    def consumer(self):
        return Consumer(self.consumer_name, version="1.0.0")

    @property
    def provider(self):
        return Provider(self.provider_name)


class UserServicePact(PactContractMixin):
    consumer_name = "UserService"
    provider_name = "LegalService"


class PaymentServicePact(PactContractMixin):
    consumer_name = "PaymentService"
    provider_name = "UserService"


class AIServicePact(PactContractMixin):
    consumer_name = "AIService"
    provider_name = "LegalService"


@pytest.fixture
def user_legal_pact(pact_dir, log_dir):
    consumer = Consumer("UserService", version="1.0.0")
    provider = Provider("LegalService")

    pact = consumer.has_pact_with(
        provider,
        pact_dir=str(pact_dir),
        log_dir=str(log_dir),
        publish_to_broker=False,
    )
    pact.start_service()

    yield pact

    pact.stop_service()


@pytest.fixture
def payment_user_pact(pact_dir, log_dir):
    consumer = Consumer("PaymentService", version="1.0.0")
    provider = Provider("UserService")

    pact = consumer.has_pact_with(
        provider,
        pact_dir=str(pact_dir),
        log_dir=str(log_dir),
        publish_to_broker=False,
    )
    pact.start_service()

    yield pact

    pact.stop_service()
