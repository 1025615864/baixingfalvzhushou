"""服务层单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestConsultationService:
    """咨询服务和单元测试"""

    @pytest.mark.asyncio
    async def test_create_consultation(self):
        """测试创建咨询"""
        from app.services.consultation_service import ConsultationService
        from app.schemas import ConsultationCreate

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = ConsultationService()
        service.db = mock_db

        data = ConsultationCreate(
            category="婚姻继承",
            title="离婚咨询",
            description="想要离婚..."
        )

        result = await service.create(
            db=mock_db,
            data=data,
            user_id=1
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_list_consultations(self):
        """测试获取咨询列表"""
        from app.services.consultation_service import ConsultationService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_db.execute = AsyncMock(return_value=mock_count_result)

        service = ConsultationService()
        service.db = mock_db

        items, total = await service.list(
            db=mock_db,
            skip=0,
            limit=20
        )

        assert isinstance(items, list)
        assert total == 0


class TestLawyerService:
    """律师服务单元测试"""

    @pytest.mark.asyncio
    async def test_create_lawyer(self):
        """测试创建律师"""
        from app.services.lawyer_service import LawyerService
        from app.schemas import LawyerCreate

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = LawyerService()

        data = LawyerCreate(
            user_id=1,
            name="张律师",
            title="合伙人",
            specialties=["刑事辩护"],
        )

        result = await service.create(
            db=mock_db,
            data=data
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_lawyer_by_id(self):
        """测试获取律师详情"""
        from app.services.lawyer_service import LawyerService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_lawyer = MagicMock()
        mock_lawyer.id = 1
        mock_lawyer.name = "张律师"
        mock_result.scalar_one_or_none.return_value = mock_lawyer
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = LawyerService()

        result = await service.get_by_id(db=mock_db, lawyer_id=1)

        assert result is not None
        assert result.id == 1


class TestAppointmentService:
    """预约服务单元测试"""

    @pytest.mark.asyncio
    async def test_create_appointment(self):
        """测试创建预约"""
        from app.services.appointment_service import AppointmentService
        from app.schemas import AppointmentCreate

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        service = AppointmentService()

        data = AppointmentCreate(
            consultation_id=1,
            lawyer_id=1,
            appointment_type="video",
            scheduled_at=datetime.now(),
        )

        result = await service.create(
            db=mock_db,
            data=data,
            user_id=1
        )

        assert result is not None


class TestReviewService:
    """评价服务单元测试"""

    @pytest.mark.asyncio
    async def test_create_review(self):
        """测试创建评价"""
        from app.services.review_service import ReviewService
        from app.schemas import ReviewCreate

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        service = ReviewService()

        data = ReviewCreate(
            consultation_id=1,
            lawyer_id=1,
            rating=5,
            content="服务很好"
        )

        result = await service.create(
            db=mock_db,
            data=data,
            user_id=1
        )

        assert result is not None


class TestScheduleService:
    """排班服务单元测试"""

    @pytest.mark.asyncio
    async def test_create_schedule(self):
        """测试创建排班"""
        from app.services.schedule_service import ScheduleService
        from app.schemas import ScheduleCreate

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        service = ScheduleService()

        data = ScheduleCreate(
            lawyer_id=1,
            date="2024-01-15",
            start_time="09:00",
            end_time="10:00"
        )

        result = await service.create(
            db=mock_db,
            data=data
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_update_schedule_availability(self):
        """测试更新排班可用性"""
        from app.services.schedule_service import ScheduleService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_schedule = MagicMock()
        mock_schedule.id = 1
        mock_schedule.is_available = True
        mock_result.scalar_one_or_none.return_value = mock_schedule
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        service = ScheduleService()

        result = await service.update_availability(
            db=mock_db,
            schedule_id=1,
            is_available=False
        )

        assert result is not None


class TestDocumentService:
    """文书服务单元测试"""

    @pytest.mark.asyncio
    async def test_create_document(self):
        """测试创建文书"""
        from app.services.document_service import DocumentService
        from app.schemas import DocumentCreate

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        service = DocumentService()

        data = DocumentCreate(
            consultation_id=1,
            document_type="合同",
            title="离婚协议",
            content="...",
            generated_by_ai=False
        )

        result = await service.create(
            db=mock_db,
            data=data,
            user_id=1
        )

        assert result is not None


class TestFirmService:
    """律所服务单元测试"""

    @pytest.mark.asyncio
    async def test_create_firm(self):
        """测试创建律所"""
        from app.services.firm_service import FirmService
        from app.schemas import FirmCreate

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        service = FirmService()

        data = FirmCreate(
            name="XX律师事务所",
            license_no="12345678",
            province="北京",
            city="北京",
            address="XX路XX号"
        )

        result = await service.create(
            db=mock_db,
            data=data
        )

        assert result is not None


class TestMatchingService:
    """匹配服务单元测试"""

    @pytest.mark.asyncio
    async def test_match_lawyers(self):
        """测试匹配律师"""
        from app.services.matching_service import MatchingService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = MatchingService()

        result = await service.match_lawyers(
            db=mock_db,
            consultation_id=1,
            category="婚姻继承",
            city="北京"
        )

        assert isinstance(result, list)
