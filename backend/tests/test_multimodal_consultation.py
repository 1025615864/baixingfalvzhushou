import pytest
from app.services.multimodal_consultation import (
    ImageProcessor,
    OCRService,
    ContractParser,
    MultimodalConsultationService,
    process_consultation_image,
    continue_consultation,
    analyze_contract_risk
)

@pytest.mark.asyncio
class TestImageProcessor:
    async def test_upload_image(self):
        processor = ImageProcessor()
        result = await processor.upload_image(
            user_id=1,
            file_name="test.jpg",
            file_size=1024,
            content_type="image/jpeg"
        )
        assert result["status"] == "uploaded"
        assert result["image_id"] == 1
        
        image = await processor.get_image(1)
        assert image is not None
        assert image["user_id"] == 1
        assert image["file_name"] == "test.jpg"

    async def test_process_image_not_found(self):
        processor = ImageProcessor()
        result = await processor.process_image(999, "ocr")
        assert result["success"] is False
        assert result["error"] == "图片不存在"

    async def test_process_image_ocr(self):
        processor = ImageProcessor()
        upload = await processor.upload_image(1, "ocr.jpg", 100, "image/jpeg")
        image_id = upload["image_id"]
        
        result = await processor.process_image(image_id, "ocr")
        assert result["success"] is True
        assert result["document_type"] == "general"
        assert "OCR 提取的文本内容" in result["extracted_text"]
        
        image = await processor.get_image(image_id)
        assert image["status"] == "processed"
        assert image["document_type"] == "general"

    async def test_process_image_contract(self):
        processor = ImageProcessor()
        upload = await processor.upload_image(1, "contract.jpg", 100, "image/jpeg")
        image_id = upload["image_id"]
        
        result = await processor.process_image(image_id, "contract")
        assert result["success"] is True
        assert result["document_type"] == "contract"
        assert "合同编号" in result["extracted_text"]
        
        image = await processor.get_image(image_id)
        assert image["document_type"] == "contract"

    async def test_process_image_id_card(self):
        processor = ImageProcessor()
        upload = await processor.upload_image(1, "id.jpg", 100, "image/jpeg")
        image_id = upload["image_id"]
        
        result = await processor.process_image(image_id, "id_card")
        assert result["success"] is True
        assert result["document_type"] == "id_card"
        assert "身份证号" in result["extracted_text"]


@pytest.mark.asyncio
class TestOCRService:
    async def test_extract_text(self):
        service = OCRService()
        result = await service.extract_text(image_id=1)
        assert result["text"] == "提取的文字内容示例"
        assert result["confidence"] == 0.95
        assert result["result_id"] == 1
        
        # Multiple calls check ID increment
        result2 = await service.extract_text(image_id=2)
        assert result2["result_id"] == 2

    async def test_extract_fields(self):
        service = OCRService()
        fields = ["name", "id_card", "amount", "date", "contract_no", "unknown"]
        result = await service.extract_fields(1, fields)
        
        data = result["fields"]
        assert data["name"] == "张三"
        assert data["id_card"] == "110101199001011234"
        assert data["amount"] == "100,000"
        assert data["date"] == "2026-01-24"
        assert data["contract_no"] == "HT-2026-001"
        assert "unknown" not in data


@pytest.mark.asyncio
class TestContractParser:
    async def test_parse_contract(self):
        parser = ContractParser()
        result = await parser.parse_contract(1, "some text")
        
        assert result["contract_type"] == "服务合同"
        assert result["parties"]["party_a"]["name"] == "甲方公司"
        assert result["amount"] == "人民币 50,000 元"
        assert result["risk_level"] == "low"

    async def test_analyze_contract_risk_not_found(self):
        parser = ContractParser()
        result = await parser.analyze_contract_risk(999)
        assert result["success"] is False
        assert result["error"] == "合同不存在"

    async def test_analyze_contract_risk_levels(self):
        parser = ContractParser()
        
        # 1. Low risk
        res1 = await parser.parse_contract(1, "普通合同文本")
        cid1 = res1["contract_id"]
        risk1 = await parser.analyze_contract_risk(cid1)
        assert risk1["risk_level"] == "low"
        
        # 2. Medium risk (one keyword: 违约金(20) + 无限责任(30) > 30 and < 60? No.
        # "违约金" is +20 (remains low < 30).
        # "无限责任" is +30 (becomes medium >= 30).
        
        # Test "无限责任" -> Score 30 -> Medium
        res2 = await parser.parse_contract(2, "包含无限责任条款")
        cid2 = res2["contract_id"]
        risk2 = await parser.analyze_contract_risk(cid2)
        assert risk2["risk_score"] == 30
        assert risk2["risk_level"] == "medium"
        assert any(i["type"] == "liability" for i in risk2["issues"])

        # 3. High risk (>= 60)
        # 违约金(20) + 无限责任(30) + 排他性(15) = 65
        res3 = await parser.parse_contract(3, "违约金，无限责任，排他性条款")
        cid3 = res3["contract_id"]
        risk3 = await parser.analyze_contract_risk(cid3)
        assert risk3["risk_score"] == 65
        assert risk3["risk_level"] == "high"
        assert len(risk3["issues"]) == 3


@pytest.mark.asyncio
class TestMultimodalConsultationService:
    async def test_process_consultation_image_ocr(self):
        service = MultimodalConsultationService()
        result = await service.process_consultation_image(
            user_id=1,
            file_name="test.jpg",
            file_size=100,
            content_type="image/jpeg",
            process_type="ocr"
        )
        
        assert result["can_continue_to_consultation"] is True
        assert result["document_type"] == "general"
        assert "OCR 提取的文本内容" in result["extracted_text"]

    async def test_process_consultation_image_contract(self):
        service = MultimodalConsultationService()
        result = await service.process_consultation_image(
            user_id=1,
            file_name="contract.jpg",
            file_size=100,
            content_type="image/jpeg",
            process_type="contract"
        )
        
        assert result["can_continue_to_consultation"] is True
        assert result["document_type"] == "contract"
        assert "contract_info" in result
        assert result["contract_info"]["contract_type"] == "服务合同"

    async def test_continue_consultation_success(self):
        service = MultimodalConsultationService()
        # Must upload/process first to have image in memory
        proc_res = await service.process_consultation_image(
            user_id=1, file_name="x.jpg", file_size=10, content_type="x", process_type="ocr"
        )
        image_id = proc_res["image_id"]
        
        result = await service.continue_consultation(image_id, "合同风险吗？")
        assert result["success"] is True
        assert result["based_on_image"] is True
        assert "我理解您的问题是：合同风险吗？" in result["response"]
        assert len(result["suggested_questions"]) > 0

    async def test_continue_consultation_not_found(self):
        service = MultimodalConsultationService()
        result = await service.continue_consultation(999, "question")
        assert result["success"] is False
        assert result["error"] == "图片不存在"

@pytest.mark.asyncio
class TestConvenienceFunctions:
    async def test_process_consultation_image_wrapper(self):
        # We need to ensure the global 'multimodal_service' state is clean or handled
        # But for 'process' it just adds a new image, so it's fine.
        result = await process_consultation_image(
            user_id=2, 
            file_name="wrapper.jpg", 
            file_size=200, 
            content_type="image/png"
        )
        assert result["can_continue_to_consultation"] is True
        assert result["image_id"] is not None

    async def test_continue_consultation_wrapper(self):
        # First ensure there's an image. The global service instance is shared.
        # We can use the result from previous test if order guaranteed, or create new.
        res_proc = await process_consultation_image(
            user_id=2, file_name="wrapper2.jpg", file_size=200, content_type="image/png"
        )
        img_id = res_proc["image_id"]
        
        result = await continue_consultation(img_id, "wrapper question")
        assert result["success"] is True
        assert "wrapper question" in result["response"]

    async def test_analyze_contract_risk_wrapper(self):
        # We need a contract first in the global service
        # The contract parser in global service is `multimodal_service.contract_parser`
        # We can trigger it via process_consultation_image with process_type='contract'
        res_proc = await process_consultation_image(
            user_id=2, file_name="contract_w.jpg", file_size=200, content_type="image/png", 
            process_type="contract"
        )
        # Verify it created a contract
        contract_info = res_proc.get("contract_info")
        assert contract_info is not None
        contract_id = contract_info["contract_id"]
        
        result = await analyze_contract_risk(contract_id)
        assert result["success"] is True
        # The mock risk might be low or whatever based on mock text
        assert "risk_level" in result
