"""批量导入导出API"""
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.archive_service import ArchiveService
from app.routers.archive import CaseCreateRequest, CaseResponse
try:
    from services.common.middleware import check_batch_rate_limit
except ImportError:
    def check_batch_rate_limit(*args, **kwargs):
        return True, 999

try:
    from services.common.events import (
        EventType,
        EventTopic,
        VectorSyncEvent,
        create_archive_event,
    )
except ImportError:
    import json as _json

    class EventType:
        PUBLISHED = "published"
        DELETED = "deleted"
        UPDATED = "updated"

    class EventTopic:
        ARCHIVE = "archive"

    class VectorSyncEvent:
        def __init__(self, topic, event_type, entity_id, data):
            self.topic = topic
            self.event_type = event_type
            self.entity_id = entity_id
            self.data = data

        def to_json(self):
            return _json.dumps({
                "topic": self.topic,
                "event_type": self.event_type,
                "entity_id": self.entity_id,
                "data": self.data,
            })

    def create_archive_event(event_type, case_id, data):
        return VectorSyncEvent(
            topic=EventTopic.ARCHIVE,
            event_type=event_type,
            entity_id=case_id,
            data=data,
        )

router = APIRouter(prefix="/api/v1/archive", tags=["批量操作"])


class BatchCaseImportRequest(BaseModel):
    items: List[CaseCreateRequest]
    skip_duplicates: bool = True
    parse_court_doc: bool = False


class BatchImportResponse(BaseModel):
    total: int
    successful: int
    failed: int
    errors: List[Dict]


class ExportQueryParams(BaseModel):
    court_level: Optional[str] = None
    case_type: Optional[str] = None
    cause_of_action: Optional[str] = None
    is_guiding_case: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=500)


class ExportResponse(BaseModel):
    items: List[CaseResponse]
    total: int
    page: int
    page_size: int


def get_archive_service(db: Session = Depends(get_db)) -> ArchiveService:
    return ArchiveService(db)


@router.post("/batch-import", response_model=BatchImportResponse, status_code=status.HTTP_201_CREATED)
async def batch_import_cases(
    request: BatchCaseImportRequest,
    http_request: Request,
    service: ArchiveService = Depends(get_archive_service)
):
    """批量导入案例"""
    client_id = http_request.client.host if http_request.client else "unknown"
    is_allowed, remaining = check_batch_rate_limit(client_id)
    if not is_allowed:
        raise HTTPException(status_code=429, detail="批量操作限流，请稍后再试")

    if not request.items:
        raise HTTPException(status_code=400, detail="导入数据不能为空")

    if len(request.items) > 200:
        raise HTTPException(status_code=400, detail="单次批量导入最多200条数据")

    try:
        successful, failed, errors = service.batch_create_cases(
            items=request.items,
            skip_duplicates=request.skip_duplicates,
            parse_court_doc=request.parse_court_doc
        )

        return BatchImportResponse(
            total=len(request.items),
            successful=successful,
            failed=failed,
            errors=errors
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量导入失败: {str(e)}")


@router.get("/export", response_model=ExportResponse)
async def export_cases(
    court_level: Optional[str] = Query(None, description="法院级别"),
    case_type: Optional[str] = Query(None, description="案件类型"),
    cause_of_action: Optional[str] = Query(None, description="案由"),
    is_guiding_case: Optional[bool] = Query(None, description="是否为指导性案例"),
    date_from: Optional[datetime] = Query(None, description="开始日期"),
    date_to: Optional[datetime] = Query(None, description="结束日期"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=100, ge=1, le=500, description="每页数量"),
    service: ArchiveService = Depends(get_archive_service)
):
    """导出案例（支持筛选和分页）"""
    try:
        cases, total = service.export_cases(
            court_level=court_level,
            case_type=case_type,
            cause_of_action=cause_of_action,
            is_guiding_case=is_guiding_case,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size
        )

        return ExportResponse(
            items=cases,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
