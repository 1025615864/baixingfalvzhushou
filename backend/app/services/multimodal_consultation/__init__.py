"""Multimodal consultation service."""
from __future__ import annotations
import enum
import time
from typing import Optional
from dataclasses import dataclass, field


class ConsultationMode(enum.Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    VIDEO = "video"


class ConsultationStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ConsultationSession:
    id: str
    user_id: int
    mode: ConsultationMode
    status: ConsultationStatus = ConsultationStatus.PENDING
    input_data: Optional[str] = None
    result: Optional[dict] = None
    created_at: float = field(default_factory=time.time)


class ImageProcessor:
    def __init__(self):
        self._images: dict[int, dict] = {}
        self._next_id = 1

    async def upload_image(self, user_id: int, file_name: str, file_size: int, content_type: str) -> dict:
        image_id = self._next_id
        self._next_id += 1
        self._images[image_id] = {
            "image_id": image_id,
            "user_id": user_id,
            "file_name": file_name,
            "file_size": file_size,
            "content_type": content_type,
            "status": "uploaded",
            "document_type": None,
        }
        return {"status": "uploaded", "image_id": image_id}

    async def get_image(self, image_id: int) -> Optional[dict]:
        return self._images.get(image_id)

    async def process_image(self, image_id: int, process_type: str = "ocr") -> dict:
        image = self._images.get(image_id)
        if not image:
            return {"success": False, "error": "图片不存在"}
        if process_type == "ocr":
            image["status"] = "processed"
            image["document_type"] = "general"
            return {
                "success": True,
                "document_type": "general",
                "extracted_text": "OCR 提取的文本内容示例",
            }
        elif process_type == "contract":
            image["status"] = "processed"
            image["document_type"] = "contract"
            return {
                "success": True,
                "document_type": "contract",
                "extracted_text": "合同编号：HT-2026-001\n甲方：甲方公司\n乙方：乙方公司",
            }
        elif process_type == "id_card":
            image["status"] = "processed"
            image["document_type"] = "id_card"
            return {
                "success": True,
                "document_type": "id_card",
                "extracted_text": "姓名：张三\n身份证号：110101199001011234",
            }
        image["status"] = "processed"
        image["document_type"] = "general"
        return {"success": True, "document_type": "general", "extracted_text": "提取的文本内容"}


class OCRService:
    def __init__(self):
        self._results: dict[int, dict] = {}
        self._next_result_id = 1

    async def extract_text(self, image_id: int) -> dict:
        result_id = self._next_result_id
        self._next_result_id += 1
        result = {
            "result_id": result_id,
            "text": "提取的文字内容示例",
            "confidence": 0.95,
        }
        self._results[result_id] = result
        return result

    async def extract_fields(self, image_id: int, fields: list[str]) -> dict:
        field_map = {
            "name": "张三",
            "id_card": "110101199001011234",
            "amount": "100,000",
            "date": "2026-01-24",
            "contract_no": "HT-2026-001",
        }
        extracted = {f: field_map[f] for f in fields if f in field_map}
        return {"fields": extracted}


class ContractParser:
    RISK_KEYWORDS: dict[str, int] = {
        "违约金": 20,
        "无限责任": 30,
        "排他性": 15,
    }

    RISK_TYPE_MAP: dict[str, str] = {
        "违约金": "penalty",
        "无限责任": "liability",
        "排他性": "exclusivity",
    }

    def __init__(self):
        self._contracts: dict[int, dict] = {}
        self._next_id = 1

    async def parse_contract(self, image_id: int, text: str) -> dict:
        contract_id = self._next_id
        self._next_id += 1
        self._contracts[contract_id] = {
            "contract_id": contract_id,
            "image_id": image_id,
            "text": text,
            "contract_type": "服务合同",
            "parties": {
                "party_a": {"name": "甲方公司"},
                "party_b": {"name": "乙方公司"},
            },
            "amount": "人民币 50,000 元",
        }
        return self._contracts[contract_id]

    async def analyze_contract_risk(self, contract_id: int) -> dict:
        contract = self._contracts.get(contract_id)
        if not contract:
            return {"success": False, "error": "合同不存在"}
        text = contract.get("text", "")
        risk_score = 0
        issues = []
        for keyword, score in self.RISK_KEYWORDS.items():
            if keyword in text:
                risk_score += score
                issues.append({
                    "type": self.RISK_TYPE_MAP.get(keyword, "other"),
                    "keyword": keyword,
                    "score": score,
                })
        if risk_score >= 60:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "medium"
        else:
            risk_level = "low"
        return {
            "success": True,
            "contract_id": contract_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "issues": issues,
        }


class MultimodalConsultationService:
    def __init__(self):
        self._sessions: dict[str, ConsultationSession] = {}
        self._next_id = 1
        self.image_processor = ImageProcessor()
        self.ocr_service = OCRService()
        self.contract_parser = ContractParser()

    async def create_session(self, user_id: int, mode: ConsultationMode = ConsultationMode.TEXT, input_data: Optional[str] = None) -> ConsultationSession:
        session_id = f"consult_{self._next_id}"
        self._next_id += 1
        session = ConsultationSession(id=session_id, user_id=user_id, mode=mode, input_data=input_data)
        self._sessions[session_id] = session
        return session

    async def process_session(self, session_id: str) -> dict:
        session = self._sessions.get(session_id)
        if not session:
            return {"success": False, "error": "会话不存在"}
        session.status = ConsultationStatus.PROCESSING
        session.status = ConsultationStatus.COMPLETED
        session.result = {"analysis": "stub result", "confidence": 0.0}
        return {"success": True, "session_id": session_id, "status": session.status.value}

    async def get_session(self, session_id: str) -> Optional[ConsultationSession]:
        return self._sessions.get(session_id)

    async def get_user_sessions(self, user_id: int) -> list[ConsultationSession]:
        return [s for s in self._sessions.values() if s.user_id == user_id]

    async def process_consultation_image(self, user_id: int, file_name: str, file_size: int, content_type: str, process_type: str = "ocr") -> dict:
        upload = await self.image_processor.upload_image(user_id, file_name, file_size, content_type)
        image_id = upload["image_id"]
        proc_result = await self.image_processor.process_image(image_id, process_type)
        result = {
            "can_continue_to_consultation": True,
            "image_id": image_id,
            "document_type": proc_result.get("document_type", "general"),
            "extracted_text": proc_result.get("extracted_text", ""),
        }
        if process_type == "contract":
            contract = await self.contract_parser.parse_contract(image_id, proc_result.get("extracted_text", ""))
            result["contract_info"] = contract
        return result

    async def continue_consultation(self, image_id: int, question: str) -> dict:
        image = await self.image_processor.get_image(image_id)
        if not image:
            return {"success": False, "error": "图片不存在"}
        return {
            "success": True,
            "based_on_image": True,
            "response": f"我理解您的问题是：{question}",
            "suggested_questions": ["这个合同有什么风险？", "需要注意哪些条款？"],
        }


multimodal_consultation_service = MultimodalConsultationService()


async def process_consultation_image(user_id: int, file_name: str, file_size: int, content_type: str, process_type: str = "ocr") -> dict:
    return await multimodal_consultation_service.process_consultation_image(user_id, file_name, file_size, content_type, process_type)


async def continue_consultation(image_id: int, question: str) -> dict:
    return await multimodal_consultation_service.continue_consultation(image_id, question)


async def analyze_contract_risk(contract_id: int) -> dict:
    return await multimodal_consultation_service.contract_parser.analyze_contract_risk(contract_id)
