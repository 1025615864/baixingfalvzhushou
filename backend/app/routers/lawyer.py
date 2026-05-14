"""律师与律所管理 API 路由 — BFF 代理层

所有律师相关请求通过此层代理到 legal-service 微服务。
"""

from __future__ import annotations

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
            return JSONResponse(status_code=503, content={"detail": "律师服务暂时不可用"})
        except httpx.TimeoutException:
            return JSONResponse(status_code=504, content={"detail": "律师服务响应超时"})
        except Exception as e:
            return JSONResponse(status_code=502, content={"detail": str(e)})


# ==========================================
# 律师主路由 — prefix=/lawyers
# ==========================================
router = APIRouter(prefix="/lawyers", tags=["Lawyer"])


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def lawyer_proxy(request: Request, path: str = ""):
    return await _proxy(request, f"lawyers/{path}")


@router.api_route("", methods=["GET", "POST"])
async def lawyer_root_proxy(request: Request):
    return await _proxy(request, "lawyers/")


# ==========================================
# 评价路由 — prefix=/reviews
# ==========================================
review_router = APIRouter(prefix="/reviews", tags=["Reviews"])


@review_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def review_proxy(request: Request, path: str = ""):
    return await _proxy(request, f"reviews/{path}")


@review_router.api_route("", methods=["GET", "POST"])
async def review_root_proxy(request: Request):
    return await _proxy(request, "reviews/")


# ==========================================
# 日程路由 — prefix=/lawyer/schedules
# ==========================================
schedule_router = APIRouter(prefix="/lawyer/schedules", tags=["Schedules"])


@schedule_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def schedule_proxy(request: Request, path: str = ""):
    return await _proxy(request, f"schedules/{path}")


@schedule_router.api_route("", methods=["GET", "POST"])
async def schedule_root_proxy(request: Request):
    return await _proxy(request, "schedules/")


# ==========================================
# 咨询路由 — prefix=/consultations
# ==========================================
consultation_router = APIRouter(prefix="/consultations", tags=["Consultations"])


@consultation_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def consultation_proxy(request: Request, path: str = ""):
    return await _proxy(request, f"consultations/{path}")


@consultation_router.api_route("", methods=["GET", "POST"])
async def consultation_root_proxy(request: Request):
    return await _proxy(request, "consultations/")


# ==========================================
# 律所路由 — prefix=/lawfirm
# ==========================================
lawfirm_router = APIRouter(prefix="/lawfirm", tags=["LawFirm"])


@lawfirm_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def lawfirm_proxy(request: Request, path: str = ""):
    return await _proxy(request, f"firms/{path}")


@lawfirm_router.api_route("", methods=["GET", "POST"])
async def lawfirm_root_proxy(request: Request):
    return await _proxy(request, "firms/")


# ==========================================
# 律师认证路由 — prefix=/verification
# ==========================================
verification_router = APIRouter(prefix="/verification", tags=["Verification"])


@verification_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def verification_proxy(request: Request, path: str = ""):
    return await _proxy(request, f"lawyers/verification/{path}")


@verification_router.api_route("", methods=["GET", "POST"])
async def verification_root_proxy(request: Request):
    return await _proxy(request, "lawyers/verification/")


# ==========================================
# 智能匹配路由 — prefix=/matching
# ==========================================
matching_router = APIRouter(prefix="/matching", tags=["Matching"])


@matching_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def matching_proxy(request: Request, path: str = ""):
    return await _proxy(request, f"matching/{path}")


@matching_router.api_route("", methods=["GET", "POST"])
async def matching_root_proxy(request: Request):
    return await _proxy(request, "matching/")


# ==========================================
# 派单路由 — prefix=/dispatch
# ==========================================
dispatch_router = APIRouter(prefix="/dispatch", tags=["Dispatch"])


@dispatch_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def dispatch_proxy(request: Request, path: str = ""):
    return await _proxy(request, f"dispatch/{path}")


@dispatch_router.api_route("", methods=["GET", "POST"])
async def dispatch_root_proxy(request: Request):
    return await _proxy(request, "dispatch/")


# ==========================================
# 案件管理路由 — prefix=/cases
# ==========================================
case_router = APIRouter(prefix="/cases", tags=["Cases"])


@case_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def case_proxy(request: Request, path: str = ""):
    return await _proxy(request, f"cases/{path}")


@case_router.api_route("", methods=["GET", "POST"])
async def case_root_proxy(request: Request):
    return await _proxy(request, "cases/")


# ==========================================
# 数据分析路由 — prefix=/analytics
# ==========================================
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


@analytics_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def analytics_proxy(request: Request, path: str = ""):
    return await _proxy(request, f"analytics/{path}")


@analytics_router.api_route("", methods=["GET", "POST"])
async def analytics_root_proxy(request: Request):
    return await _proxy(request, "analytics/")


# ==========================================
# 视频咨询路由 — prefix=/video
# ==========================================
video_router = APIRouter(prefix="/video", tags=["Video"])


@video_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def video_proxy(request: Request, path: str = ""):
    return await _proxy(request, f"video/{path}")


@video_router.api_route("", methods=["GET", "POST"])
async def video_root_proxy(request: Request):
    return await _proxy(request, "video/")


# ==========================================
# 文书模板路由 — prefix=/documents
# ==========================================
document_router = APIRouter(prefix="/documents", tags=["Documents"])


@document_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def document_proxy(request: Request, path: str = ""):
    return await _proxy(request, f"documents/{path}")


@document_router.api_route("", methods=["GET", "POST"])
async def document_root_proxy(request: Request):
    return await _proxy(request, "documents/")