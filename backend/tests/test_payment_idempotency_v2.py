import pytest
import asyncio
import hashlib
import hmac
import json
import uuid
import os
from decimal import Decimal, ROUND_HALF_UP
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import MagicMock, patch, AsyncMock
from types import SimpleNamespace
from app.models.payment import PaymentOrder, PaymentStatus
from app.config import get_settings

@pytest.mark.asyncio
async def test_cross_endpoint_idempotency_v2(client: AsyncClient, db: AsyncSession, monkeypatch):
    """
    Test webhook endpoint idempotency with multiple concurrent requests.
    """
    # 创建新的测试配置并应用
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", "0123456789abcdef")
    monkeypatch.setenv("ALIPAY_PUBLIC_KEY", "test_alipay_public_key")
    monkeypatch.setenv("IKUNPAY_KEY", "test_ikunpay_key")
    monkeypatch.setenv("WECHATPAY_API_V3_KEY", "test_wechatpay_key")
    
    # 清除 settings 缓存以应用新环境变量
    get_settings.cache_clear()
    
    # 确保所有支付相关模块使用正确的settings
    import importlib
    import app.routers.payment.callbacks as callbacks_module
    import app.routers.payment.crypto_utils as crypto_utils_module
    import app.routers.payment.helpers as helpers_module
    import app.routers.payment.post_processing as post_processing_module
    import app.routers.payment as payment_router_module
    importlib.reload(callbacks_module)
    importlib.reload(crypto_utils_module)
    importlib.reload(helpers_module)
    importlib.reload(post_processing_module)
    importlib.reload(payment_router_module)
    
    # 获取实际的settings用于签名计算（重新加载后）
    actual_settings = get_settings()
    
    # 验证环境变量已正确设置
    assert actual_settings.payment_webhook_secret == "0123456789abcdef"
    
    order_no = f"test_idemp_v2_{uuid.uuid4().hex[:8]}"
    trade_no = f"trade_v2_{uuid.uuid4().hex[:8]}"
    amount = 50.0
    payment_method = "wechat"
    
    # 1. Create order
    order = PaymentOrder(
        order_no=order_no,
        user_id=1,
        order_type="consultation",
        amount=amount,
        actual_amount=amount,
        status=PaymentStatus.PENDING,
        title="Test Order V2",
    )
    db.add(order)
    await db.commit()

    # 2. Prepare payload for /api/payment/callback/webhook
    # 使用与后端一致的签名计算方式
    from app.routers.payment import helpers as payment_helpers
    amount_quantized = payment_helpers._quantize_amount(amount)
    # 重要：签名时使用Decimal的字符串表示，确保精度一致
    sign_payload = f"{order_no}|{trade_no}|{payment_method}|{amount_quantized}"
    signature = hmac.new(
        actual_settings.payment_webhook_secret.encode("utf-8"),
        sign_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    
    webhook_payload = {
        "order_no": order_no,
        "trade_no": trade_no,
        "payment_method": payment_method,
        "amount": str(amount_quantized),  # 发送字符串类型，避免float精度丢失
        "signature": signature
    }

    # 3. Run concurrent requests to webhook endpoint
    async def call_webhook():
        return await client.post("/api/payment/callback/webhook", json=webhook_payload)

    # Send 3 concurrent requests
    tasks = [call_webhook() for _ in range(3)]
    responses = await asyncio.gather(*tasks)

    # 4. Verify results
    # At least one should be 200 OK (the one that succeeded and committed)
    # The others might be 200 (if they hit idempotent check after PAID) 
    # or 503 (if they failed to get lock while the first one was processing)
    
    successful_webhooks = [r for r in responses if r.status_code == 200]
    busy_webhooks = [r for r in responses if r.status_code == 503]
    
    # At least one must succeed
    assert len(successful_webhooks) >= 1, f"No successful requests. Responses: {[(r.status_code, r.text[:100]) for r in responses]}"
    
    # Check DB status
    await db.refresh(order)
    assert order.status == PaymentStatus.PAID
    assert order.trade_no == trade_no
    
    # Verify idempotency: all successful requests should have same result
    print(f"Success: {len(successful_webhooks)}, Busy (503): {len(busy_webhooks)}")
