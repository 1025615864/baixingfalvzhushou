import os
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response, JSONResponse

LEGAL_SERVICE_URL = os.getenv("LEGAL_SERVICE_URL", "http://legal-service:8008")
TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=60.0, pool=5.0)


async def _proxy(request: Request, legal_path: str) -> Response:
    target_url = f"{LEGAL_SERVICE_URL}/api/v1/legal/{legal_path.lstrip('/')}"
    params = dict(request.query_params) if request.query_params else None

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers={
                    k: v for k, v in request.headers.items()
                    if k.lower() in ("authorization", "content-type", "x-request-id", "x-user-id", "x-user-role", "accept")
                },
                params=params,
                content=await request.body(),
                follow_redirects=False,
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type"),
            )
        except httpx.ConnectError:
            return JSONResponse(status_code=503, content={"detail": "支付服务暂时不可用"})
        except httpx.TimeoutException:
            return JSONResponse(status_code=504, content={"detail": "支付服务响应超时"})
        except Exception as e:
            return JSONResponse(status_code=502, content={"detail": str(e)})


# ==========================================
# 支付路由 — prefix=/payments
# ==========================================
payment_router = APIRouter(prefix="/payments", tags=["Payment"])


@payment_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def payment_proxy(request: Request, path: str = ""):
    return await _proxy(request, f"payments/{path}")


@payment_router.api_route("", methods=["GET", "POST"])
async def payment_root_proxy(request: Request):
    return await _proxy(request, "payments/")


# ==========================================
# 钱包路由 — prefix=/wallet
# ==========================================
wallet_router = APIRouter(prefix="/wallet", tags=["Wallet"])


@wallet_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def wallet_proxy(request: Request, path: str = ""):
    return await _proxy(request, f"wallets/{path}")


@wallet_router.api_route("", methods=["GET", "POST"])
async def wallet_root_proxy(request: Request):
    return await _proxy(request, "wallets/")