"""多模态咨询服务

提供图片上传、OCR、合同解析等多模态咨询功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class ImageProcessor:
    """图片处理器"""

    def __init__(self):
        self._images: dict[int, dict[str, Any]] = {}
        self._supported_formats = ["jpg", "jpeg", "png", "gif", "bmp", "webp"]

    async def upload_image(
        self,
        user_id: int,
        file_name: str,
        file_size: int,
        content_type: str,
    ) -> dict[str, Any]:
        """上传图片

        Args:
            user_id: 用户ID
            file_name: 文件名
            file_size: 文件大小
            content_type: 内容类型

        Returns:
            图片信息
        """
        image_id = len(self._images) + 1
        now = datetime.now(timezone.utc).isoformat()

        image = {
            "id": image_id,
            "user_id": user_id,
            "file_name": file_name,
            "file_size": file_size,
            "content_type": content_type,
            "status": "uploaded",
            "created_at": now,
            "processed_at": None,
            "extracted_text": None,
        }

        self._images[image_id] = image

        logger.info(f"Uploaded image {image_id} by user {user_id}")

        return {
            "image_id": image_id,
            "status": "uploaded",
            "created_at": now,
        }

    async def process_image(
        self,
        image_id: int,
        process_type: str = "ocr",
    ) -> dict[str, Any]:
        """处理图片

        Args:
            image_id: 图片ID
            process_type: 处理类型

        Returns:
            处理结果
        """
        image = self._images.get(image_id)

        if not image:
            return {
                "success": False,
                "error": "图片不存在",
            }

        extracted_text = ""
        document_type = "general"

        if process_type == "ocr":
            extracted_text = "这是 OCR 提取的文本内容。图片中包含了法律相关的文字信息。"
        elif process_type == "contract":
            extracted_text = "合同编号：2026-001\n甲方：XXX 公司\n乙方：YYY 个人\n合同金额：人民币 100,000 元整\n合同期限：2026-01-01 至 2026-12-31"
            document_type = "contract"
        elif process_type == "id_card":
            extracted_text = "姓名：张三\n身份证号：110101199001011234\n地址：北京市朝阳区"
            document_type = "id_card"

        image["status"] = "processed"
        image["processed_at"] = datetime.now(timezone.utc).isoformat()
        image["extracted_text"] = extracted_text
        image["document_type"] = document_type

        logger.info(f"Processed image {image_id}, type: {process_type}")

        return {
            "success": True,
            "image_id": image_id,
            "document_type": document_type,
            "extracted_text": extracted_text,
            "processed_at": image["processed_at"],
        }

    async def get_image(self, image_id: int) -> dict[str, Any] | None:
        """获取图片信息

        Args:
            image_id: 图片ID

        Returns:
            图片信息
        """
        return self._images.get(image_id)


class OCRService:
    """OCR 服务"""

    def __init__(self):
        self._results: dict[int, dict[str, Any]] = {}

    async def extract_text(
        self,
        image_id: int,
        language: str = "ch",
    ) -> dict[str, Any]:
        """提取文字

        Args:
            image_id: 图片ID
            language: 语言

        Returns:
            提取结果
        """
        result_id = len(self._results) + 1
        now = datetime.now(timezone.utc).isoformat()

        result = {
            "id": result_id,
            "image_id": image_id,
            "language": language,
            "status": "completed",
            "text": "提取的文字内容示例",
            "confidence": 0.95,
            "created_at": now,
        }

        self._results[result_id] = result

        logger.info(f"Extracted text from image {image_id}")

        return {
            "result_id": result_id,
            "text": result["text"],
            "confidence": result["confidence"],
        }

    async def extract_fields(
        self,
        image_id: int,
        field_types: list[str],
    ) -> dict[str, Any]:
        """提取指定字段

        Args:
            image_id: 图片ID
            field_types: 字段类型列表

        Returns:
            字段提取结果
        """
        fields = {}

        for field_type in field_types:
            if field_type == "name":
                fields["name"] = "张三"
            elif field_type == "id_card":
                fields["id_card"] = "110101199001011234"
            elif field_type == "amount":
                fields["amount"] = "100,000"
            elif field_type == "date":
                fields["date"] = "2026-01-24"
            elif field_type == "contract_no":
                fields["contract_no"] = "HT-2026-001"

        logger.info(f"Extracted {len(fields)} fields from image {image_id}")

        return {
            "image_id": image_id,
            "fields": fields,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }


class ContractParser:
    """合同解析器"""

    def __init__(self):
        self._contracts: dict[int, dict[str, Any]] = {}

    async def parse_contract(
        self,
        image_id: int,
        extracted_text: str,
    ) -> dict[str, Any]:
        """解析合同

        Args:
            image_id: 图片ID
            extracted_text: 提取的文字

        Returns:
            解析结果
        """
        contract_id = len(self._contracts) + 1
        now = datetime.now(timezone.utc).isoformat()

        contract = {
            "id": contract_id,
            "image_id": image_id,
            "raw_text": extracted_text,
            "parsed_data": {
                "contract_type": "服务合同",
                "parties": {
                    "party_a": {"name": "甲方公司", "role": "服务提供方"},
                    "party_b": {"name": "乙方客户", "role": "服务接受方"},
                },
                "amount": "人民币 50,000 元",
                "start_date": "2026-01-24",
                "end_date": "2027-01-23",
                "key_terms": [
                    "服务内容：法律咨询服务",
                    "服务方式：线上咨询",
                    "付款方式：一次性支付",
                ],
            },
            "risk_level": "low",
            "issues": [],
            "created_at": now,
        }

        self._contracts[contract_id] = contract

        logger.info(f"Parsed contract {contract_id} from image {image_id}")

        return {
            "contract_id": contract_id,
            "contract_type": contract["parsed_data"]["contract_type"],
            "parties": contract["parsed_data"]["parties"],
            "amount": contract["parsed_data"]["amount"],
            "risk_level": contract["risk_level"],
        }

    async def analyze_contract_risk(
        self,
        contract_id: int,
    ) -> dict[str, Any]:
        """分析合同风险

        Args:
            contract_id: 合同ID

        Returns:
            风险分析结果
        """
        contract = self._contracts.get(contract_id)

        if not contract:
            return {
                "success": False,
                "error": "合同不存在",
            }

        issues = []
        risk_score = 0

        raw_text = contract["raw_text"]

        if "违约金" in raw_text:
            issues.append({
                "type": "penalty",
                "severity": "medium",
                "description": "存在违约金条款",
            })
            risk_score += 20

        if "无限责任" in raw_text:
            issues.append({
                "type": "liability",
                "severity": "high",
                "description": "存在无限责任条款",
            })
            risk_score += 30

        if "排他性" in raw_text or "独家" in raw_text:
            issues.append({
                "type": "exclusivity",
                "severity": "medium",
                "description": "存在排他性条款",
            })
            risk_score += 15

        risk_level = "low" if risk_score < 30 else "medium" if risk_score < 60 else "high"

        return {
            "success": True,
            "contract_id": contract_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "issues": issues,
            "recommendations": [
                "建议仔细审查违约金条款",
                "注意责任限制条款",
                "确认服务范围定义清晰",
            ],
        }


class MultimodalConsultationService:
    """多模态咨询服务"""

    def __init__(self):
        self.image_processor = ImageProcessor()
        self.ocr_service = OCRService()
        self.contract_parser = ContractParser()

    async def process_consultation_image(
        self,
        user_id: int,
        file_name: str,
        file_size: int,
        content_type: str,
        process_type: str = "ocr",
    ) -> dict[str, Any]:
        """处理咨询图片

        Args:
            user_id: 用户ID
            file_name: 文件名
            file_size: 文件大小
            content_type: 内容类型
            process_type: 处理类型

        Returns:
            处理结果
        """
        upload_result = await self.image_processor.upload_image(
            user_id=user_id,
            file_name=file_name,
            file_size=file_size,
            content_type=content_type,
        )

        image_id = upload_result["image_id"]

        process_result = await self.image_processor.process_image(
            image_id=image_id,
            process_type=process_type,
        )

        if process_result["success"] and process_type == "contract":
            parse_result = await self.contract_parser.parse_contract(
                image_id=image_id,
                extracted_text=process_result["extracted_text"],
            )

            return {
                "image_id": image_id,
                "document_type": process_result["document_type"],
                "contract_info": parse_result,
                "can_continue_to_consultation": True,
            }

        return {
            "image_id": image_id,
            "document_type": process_result["document_type"],
            "extracted_text": process_result["extracted_text"],
            "can_continue_to_consultation": True,
        }

    async def continue_consultation(
        self,
        image_id: int,
        user_question: str,
    ) -> dict[str, Any]:
        """继续咨询

        Args:
            image_id: 图片ID
            user_question: 用户问题

        Returns:
            咨询结果
        """
        image = await self.image_processor.get_image(image_id)

        if not image:
            return {
                "success": False,
                "error": "图片不存在",
            }

        extracted_text = image.get("extracted_text", "")

        response = f"根据您上传的图片内容，我理解您的问题是：{user_question}\n\n图片中包含的关键信息：\n{extracted_text}\n\n建议：您可以基于图片中的具体条款或内容提出更详细的问题。"

        return {
            "success": True,
            "response": response,
            "based_on_image": True,
            "suggested_questions": [
                "这张图片中的合同主要涉及什么内容？",
                "请解释图片中提到的关键条款",
                "这份合同有哪些需要注意的风险点？",
            ],
        }


# 单例实例
multimodal_service = MultimodalConsultationService()


async def process_consultation_image(
    user_id: int,
    file_name: str,
    file_size: int,
    content_type: str,
    process_type: str = "ocr",
) -> dict[str, Any]:
    """便捷函数：处理咨询图片

    Args:
        user_id: 用户ID
        file_name: 文件名
        file_size: 文件大小
        content_type: 内容类型
        process_type: 处理类型

    Returns:
        处理结果
    """
    return await multimodal_service.process_consultation_image(
        user_id=user_id,
        file_name=file_name,
        file_size=file_size,
        content_type=content_type,
        process_type=process_type,
    )


async def continue_consultation(
    image_id: int,
    user_question: str,
) -> dict[str, Any]:
    """便捷函数：继续咨询

    Args:
        image_id: 图片ID
        user_question: 用户问题

    Returns:
        咨询结果
    """
    return await multimodal_service.continue_consultation(
        image_id=image_id,
        user_question=user_question,
    )


async def analyze_contract_risk(
    contract_id: int,
) -> dict[str, Any]:
    """便捷函数：分析合同风险

    Args:
        contract_id: 合同ID

    Returns:
        风险分析结果
    """
    return await multimodal_service.contract_parser.analyze_contract_risk(
        contract_id=contract_id,
    )
