from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class PaymentChannelAdapter(ABC):

    @abstractmethod
    async def create_payment(
        self,
        order_no: str,
        amount: int,
        title: str,
        description: str = "",
        notify_url: str = "",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def verify_callback(self, payload: Dict[str, Any]) -> bool:
        ...

    @abstractmethod
    async def query_payment(self, order_no: str) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def refund(
        self,
        order_no: str,
        refund_no: str,
        amount: int,
        total_amount: int,
        reason: str = "",
    ) -> Dict[str, Any]:
        ...
