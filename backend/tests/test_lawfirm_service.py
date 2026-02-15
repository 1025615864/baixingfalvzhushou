"""Lawfirm services tests - 律所服务测试"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.lawfirm import (
    LawFirmService,
    LawyerService,
    LawyerConsultationService,
    ConsultationStatus,
    ReviewService,
    LawyerStatsService,
    LawyerScheduleService,
    LawyerVerificationService,
)
from app.models.lawfirm import LawFirm, Lawyer, LawyerConsultation, LawyerReview, LawyerSchedule, LawyerVerification


class TestLawFirmService:
    """律所服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def service(self):
        """创建律所服务实例"""
        return LawFirmService()

    @pytest.fixture
    def mock_firm(self):
        """创建模拟律所"""
        firm = MagicMock(spec=LawFirm)
        firm.id = 1
        firm.name = "测试律所"
        firm.city = "北京"
        firm.is_active = True
        firm.is_verified = True
        firm.rating = 4.5
        return firm

    @pytest.mark.asyncio
    async def test_create_firm(self, service, mock_db):
        """测试创建律所"""
        from app.schemas.lawfirm import LawFirmCreate

        data = LawFirmCreate(name="测试律所", city="北京")
        mock_db.refresh = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.create(mock_db, data)

        assert result.name == "测试律所"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_firm_by_id(self, service, mock_db, mock_firm):
        """测试获取律所"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_firm
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_by_id(mock_db, 1)

        assert result is not None
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_firm_list(self, service, mock_db, mock_firm):
        """测试获取律所列表"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_firm]
        mock_db.execute = AsyncMock(return_value=mock_result)

        firms, total = await service.get_list(mock_db, page=1, page_size=20)

        assert len(firms) == 1
        assert total >= 0

    @pytest.mark.asyncio
    async def test_get_firm_list_with_filters(self, service, mock_db, mock_firm):
        """测试带过滤条件的律所列表"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_firm]
        mock_db.execute = AsyncMock(return_value=mock_result)

        firms, total = await service.get_list(
            mock_db, page=1, page_size=20, city="北京", keyword="测试"
        )

        assert len(firms) == 1

    @pytest.mark.asyncio
    async def test_get_lawyer_count(self, service, mock_db):
        """测试获取律所律师数量"""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db.execute = AsyncMock(return_value=mock_result)

        count = await service.get_lawyer_count(mock_db, 1)

        assert count == 5


class TestLawyerService:
    """律师服务测试类"""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def service(self):
        return LawyerService()

    @pytest.fixture
    def mock_lawyer(self):
        lawyer = MagicMock(spec=Lawyer)
        lawyer.id = 1
        lawyer.name = "张律师"
        lawyer.title = "高级合伙人"
        lawyer.is_active = True
        lawyer.case_count = 50
        lawyer.rating = 4.8
        lawyer.review_count = 20
        return lawyer

    @pytest.mark.asyncio
    async def test_create_lawyer(self, service, mock_db):
        """测试创建律师"""
        from app.schemas.lawfirm import LawyerCreate

        data = LawyerCreate(name="张律师", title="高级合伙人")
        mock_db.refresh = AsyncMock()

        result = await service.create(mock_db, data, user_id=1)

        assert result.name == "张律师"
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_lawyer_by_id(self, service, mock_db, mock_lawyer):
        """测试获取律师"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_lawyer
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_by_id(mock_db, 1)

        assert result is not None
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_lawyer_by_user_id(self, service, mock_db, mock_lawyer):
        """测试通过用户ID获取律师"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_lawyer
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_by_user_id(mock_db, 1)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_lawyer_list(self, service, mock_db, mock_lawyer):
        """测试获取律师列表"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_lawyer]
        mock_db.execute = AsyncMock(return_value=mock_result)

        lawyers, total = await service.get_list(mock_db, page=1, page_size=20)

        assert len(lawyers) == 1
        assert total >= 0

    @pytest.mark.asyncio
    async def test_get_lawyer_list_with_filters(self, service, mock_db, mock_lawyer):
        """测试带过滤条件的律师列表"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_lawyer]
        mock_db.execute = AsyncMock(return_value=mock_result)

        lawyers, total = await service.get_list(
            mock_db, page=1, page_size=20, city="北京", specialty="刑事"
        )

        assert len(lawyers) == 1

    @pytest.mark.asyncio
    async def test_get_ranking(self, service, mock_db, mock_lawyer):
        """测试获取律师排行榜"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_lawyer]
        mock_db.execute = AsyncMock(return_value=mock_result)

        ranking = await service.get_ranking(mock_db, limit=10)

        assert len(ranking) == 1
        assert ranking[0]["name"] == "张律师"


class TestConsultationService:
    """咨询服务测试类"""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def service(self):
        return LawyerConsultationService()

    @pytest.fixture
    def mock_consultation(self):
        consultation = MagicMock(spec=LawyerConsultation)
        consultation.id = 1
        consultation.user_id = 1
        consultation.lawyer_id = 1
        consultation.status = ConsultationStatus.PENDING.value
        return consultation

    @pytest.mark.asyncio
    async def test_create_consultation(self, service, mock_db):
        """测试创建咨询"""
        data = {"lawyer_id": 1, "subject": "法律咨询", "description": "婚姻问题"}
        mock_db.refresh = AsyncMock()

        result = await service.create(mock_db, user_id=1, data=data)

        assert result.user_id == 1
        assert result.status == ConsultationStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_accept_consultation(self, service, mock_db, mock_consultation):
        """测试律师接单"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_consultation
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock()

        result = await service.accept(mock_db, consultation_id=1, lawyer_id=1)

        assert result is not None
        assert result.status == ConsultationStatus.ACCEPTED.value

    @pytest.mark.asyncio
    async def test_complete_consultation(self, service, mock_db, mock_consultation):
        """测试完成咨询"""
        mock_consultation.status = ConsultationStatus.ACCEPTED.value
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_consultation
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock()

        result = await service.complete(mock_db, consultation_id=1)

        assert result is not None
        assert result.status == ConsultationStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_get_user_consultations(self, service, mock_db, mock_consultation):
        """测试获取用户咨询列表"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_consultation]
        mock_db.execute = AsyncMock(return_value=mock_result)

        consultations, total = await service.get_user_consultations(mock_db, user_id=1)

        assert len(consultations) == 1
        assert total >= 0

    @pytest.mark.asyncio
    async def test_get_lawyer_consultations(self, service, mock_db, mock_consultation):
        """测试获取律师咨询列表"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_consultation]
        mock_db.execute = AsyncMock(return_value=mock_result)

        consultations, total = await service.get_lawyer_consultations(mock_db, lawyer_id=1)

        assert len(consultations) == 1
        assert total >= 0


class TestReviewService:
    """评价服务测试类"""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def service(self):
        return ReviewService()

    @pytest.fixture
    def mock_review(self):
        review = MagicMock(spec=LawyerReview)
        review.id = 1
        review.lawyer_id = 1
        review.user_id = 1
        review.rating = 5
        review.content = "服务很好"
        return review

    @pytest.mark.asyncio
    async def test_create_review(self, service, mock_db):
        """测试创建评价"""
        mock_db.refresh = AsyncMock()
        mock_db.commit = AsyncMock()

        result = await service.create(
            mock_db,
            consultation_id=1,
            lawyer_id=1,
            user_id=1,
            rating=5,
            content="服务很好",
            dimensions=None
        )

        assert result.rating == 5

    @pytest.mark.asyncio
    async def test_get_lawyer_reviews(self, service, mock_db, mock_review):
        """测试获取律师评价列表"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_review]
        mock_db.execute = AsyncMock(return_value=mock_result)

        reviews, total = await service.get_lawyer_reviews(mock_db, lawyer_id=1)

        assert len(reviews) == 1
        assert total >= 0

    @pytest.mark.asyncio
    async def test_get_average_rating(self, service, mock_db):
        """测试获取平均评分"""
        mock_result = MagicMock()
        # 模拟 one() 返回带属性访问的 Row 对象
        mock_row = MagicMock()
        mock_row.avg_rating = 4.5
        mock_row.total_count = 10
        mock_result.one.return_value = mock_row
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_average_rating(mock_db, lawyer_id=1)

        assert result["average_rating"] == 4.5
        assert result["total_count"] == 10

        # 验证返回结构
        assert "dimension_ratings" in result


class TestScheduleService:
    """日程服务测试类"""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def service(self):
        return LawyerScheduleService()

    @pytest.fixture
    def mock_schedule(self):
        schedule = MagicMock(spec=LawyerSchedule)
        schedule.id = 1
        schedule.lawyer_id = 1
        schedule.title = "会议"
        return schedule

    @pytest.mark.asyncio
    async def test_create_schedule(self, service, mock_db):
        """测试创建日程"""
        from app.schemas.lawfirm import LawyerScheduleCreate

        data = LawyerScheduleCreate(
            date=datetime.now(timezone.utc),
            start_time="09:00",
            end_time="10:00",
            note="会议"
        )
        mock_db.refresh = AsyncMock()

        result = await service.create(mock_db, lawyer_id=1, data=data)

        assert result.note == "会议"

    @pytest.mark.asyncio
    async def test_get_schedule_by_id(self, service, mock_db, mock_schedule):
        """测试获取日程"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_schedule
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_by_id(mock_db, 1)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_lawyer_id(self, service, mock_db, mock_schedule):
        """测试获取律师日程列表"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_schedule]
        mock_db.execute = AsyncMock(return_value=mock_result)

        schedules, total = await service.get_by_lawyer_id(mock_db, lawyer_id=1)

        assert len(schedules) == 1
        assert total >= 0

    @pytest.mark.asyncio
    async def test_delete_schedule(self, service, mock_db, mock_schedule):
        """测试删除日程"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_schedule
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.delete(mock_db, schedule_id=1)

        assert result is True


class TestVerificationService:
    """认证服务测试类"""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def service(self):
        return LawyerVerificationService()

    @pytest.fixture
    def mock_verification(self):
        verification = MagicMock(spec=LawyerVerification)
        verification.id = 1
        verification.user_id = 1
        verification.status = "pending"
        return verification

    def test_validate_id_card_valid(self, service):
        """测试有效身份证号校验"""
        is_valid, error = service._validate_id_card_no("110101199001011234")
        assert is_valid is True
        assert error == ""

    def test_validate_id_card_invalid(self, service):
        """测试无效身份证号校验"""
        is_valid, error = service._validate_id_card_no("123")
        assert is_valid is False
        assert "身份证号格式不正确" in error

    def test_validate_license_valid(self, service):
        """测试有效执业证号校验"""
        is_valid, error = service._validate_license_no("1234567890")
        assert is_valid is True
        assert error == ""

    def test_validate_license_invalid(self, service):
        """测试无效执业证号校验"""
        is_valid, error = service._validate_license_no("123")
        assert is_valid is False
        assert "执业证号格式不正确" in error

    @pytest.mark.asyncio
    async def test_get_verification_by_id(self, service, mock_db, mock_verification):
        """测试获取认证申请"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_verification
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_by_id(mock_db, 1)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_list(self, service, mock_db, mock_verification):
        """测试获取认证列表"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_verification]
        mock_db.execute = AsyncMock(return_value=mock_result)

        verifications, total = await service.get_list(mock_db)

        assert len(verifications) == 1

    @pytest.mark.asyncio
    async def test_create_verification(self, service, mock_db):
        """测试创建认证申请"""
        from app.schemas.lawfirm import VerificationCreate
        data = VerificationCreate(
            real_name="张三",
            id_card_no="110101199001011234",
            license_no="12345678901234",
            firm_name="测试律所"
        )
        mock_db.refresh = AsyncMock()
        mock_db.commit = AsyncMock()
        
        # Mock db.execute to return None (no existing verification)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.create(mock_db, user_id=1, data=data)

        assert result is not None
        assert result.user_id == 1

    @pytest.mark.asyncio
    async def test_approve_verification(self, service, mock_db, mock_verification):
        """测试通过认证"""
        mock_verification.status = "pending"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_verification
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock()

        result = await service.approve(mock_db, verification_id=1, admin_id=1)

        assert result is not None
        assert result.status == "approved"

    @pytest.mark.asyncio
    async def test_reject_verification(self, service, mock_db, mock_verification):
        """测试拒绝认证"""
        mock_verification.status = "pending"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_verification
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock()

        result = await service.reject(mock_db, verification_id=1, admin_id=1, reason="资料不完整")

        assert result is not None
        assert result.status == "rejected"


class TestLawyerStatsService:
    """律师统计服务测试类"""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def service(self):
        return LawyerStatsService()

    @pytest.mark.asyncio
    async def test_get_dashboard(self, service, mock_db):
        """测试获取律师工作台数据"""
        # 模拟咨询统计
        mock_consult_result = MagicMock()
        mock_consult_result.one.return_value = MagicMock(
            total=100,
            completed=80,
            in_progress=10
        )

        # 模拟收入统计
        mock_income_result = MagicMock()
        mock_income_result.one.return_value = MagicMock(
            total_income=5000.0,
            transaction_count=20
        )

        # 模拟评价统计
        mock_review_result = MagicMock()
        mock_review_result.one.return_value = MagicMock(
            avg_rating=4.5,
            review_count=15
        )

        mock_db.execute = AsyncMock(side_effect=[mock_consult_result, mock_income_result, mock_review_result])

        dashboard = await service.get_dashboard(mock_db, lawyer_id=1)

        assert dashboard is not None
        assert dashboard["consultations"]["total"] == 100
        assert dashboard["consultations"]["completed"] == 80
        assert dashboard["income"]["total"] == 5000.0
        assert dashboard["reviews"]["average_rating"] == 4.5

    @pytest.mark.asyncio
    async def test_get_income_trend(self, service, mock_db):
        """测试获取收入趋势"""
        mock_result = MagicMock()
        mock_result.all.return_value = [
            MagicMock(date=MagicMock(isoformat=lambda: "2024-01-01"), daily_income=100.0),
            MagicMock(date=MagicMock(isoformat=lambda: "2024-01-02"), daily_income=150.0),
        ]
        mock_db.execute = AsyncMock(return_value=mock_result)

        trend = await service.get_income_trend(mock_db, lawyer_id=1, days=30)

        assert trend is not None
        assert len(trend) == 2
        assert trend[0]["income"] == 100.0

    @pytest.mark.asyncio
    async def test_get_consultation_stats(self, service, mock_db):
        """测试获取咨询统计"""
        # 模拟状态统计
        mock_status_result = MagicMock()
        mock_status_result.all.return_value = [
            MagicMock(status="completed", count=80),
            MagicMock(status="pending", count=20),
        ]

        # 模拟平均完成时间
        mock_duration_result = MagicMock()
        mock_duration_result.one.return_value = MagicMock(avg_duration=30.5)

        mock_db.execute = AsyncMock(side_effect=[mock_status_result, mock_duration_result])

        stats = await service.get_consultation_stats(mock_db, lawyer_id=1, days=30)

        assert stats is not None
        assert "by_status" in stats
        assert stats["average_duration_minutes"] == 30.5

    @pytest.mark.asyncio
    async def test_get_lawyer_performance(self, service, mock_db):
        """测试获取律师绩效"""
        # 模拟各种查询结果 (需要8个结果，对应8次 db.execute 调用)
        mock_results = [
            MagicMock(scalar=lambda: 100),  # total consultations
            MagicMock(scalar=lambda: 80),   # completed
            MagicMock(scalar=lambda: 5),    # cancelled
            MagicMock(scalar=lambda: 5000.0),  # total_income
            MagicMock(scalar=lambda: 20),   # review_count
            MagicMock(scalar=lambda: 4.5),  # avg_rating
            MagicMock(scalar=lambda: 15.0),  # avg_response_time_minutes
            MagicMock(all=lambda: []),  # daily stats
        ]

        mock_db.execute = AsyncMock(side_effect=mock_results)

        performance = await service.get_lawyer_performance(mock_db, lawyer_id=1, days=30)

        assert performance is not None
        assert performance["consultation"]["total"] == 100
        assert performance["consultation"]["completed"] == 80
        assert performance["income"]["total"] == 5000.0
        assert performance["review"]["avg_rating"] == 4.5
