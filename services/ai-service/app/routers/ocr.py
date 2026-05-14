"""OCR 识别路由 - 执业证智能识别"""
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class OCRRequest(BaseModel):
    image_url: str
    cert_type: str = "lawyer_license"


class OCRResult(BaseModel):
    request_id: str
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


@router.post("/extract-lawyer-license", response_model=OCRResult)
async def extract_lawyer_license(body: OCRRequest):
    """执业证 OCR 识别

    识别字段：姓名、执业证号、律所、发证日期、年检记录
    """
    request_id = str(uuid.uuid4())

    try:
        # 模拟 OCR 识别结果
        # 生产环境接入百度 OCR / 腾讯 OCR API
        extracted = {
            "name": "张三",
            "license_no": "12345678901234567890",
            "law_firm": "北京市某某律师事务所",
            "issue_date": "2020-03-15",
            "annual_check_date": "2026-06-30",
            "cert_type": "律师执业证",
            "confidence": 0.95,
        }

        return OCRResult(
            request_id=request_id,
            success=True,
            data=extracted,
        )
    except Exception as e:
        return OCRResult(
            request_id=request_id,
            success=False,
            data=None,
            error=str(e),
        )


@router.get("/health")
async def ocr_health():
    return {"status": "healthy", "service": "ocr"}