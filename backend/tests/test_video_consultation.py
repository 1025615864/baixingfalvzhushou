"""视频咨询功能测试

测试覆盖：
- 视频咨询预约创建
- 律师排班管理
- 会员折扣计算
- 视频咨询使用次数追踪
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.video_consultation import (
    VideoConsultationService,
    VideoScheduleService,
    VideoConsultationStatus,
)
from app.models.video_consultation import (
    VideoConsultation,
    VideoConsultationUsage,
    VideoSchedule,
)
from app.models.user import User
from app.models.lawfirm import Lawyer
from app.models.membership import Membership
from app.services.membership_service import MembershipTier


@pytest.fixture
def video_service():
    """创建视频咨询服务实例"""
    return VideoConsultationService()


@pytest.fixture
def schedule_service():
    """创建排班服务实例"""
    return VideoScheduleService()


@pytest.fixture
def mock_user():
    """创建模拟用户"""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    return user


@pytest.fixture
def mock_lawyer():
    """创建模拟律师"""
    lawyer = MagicMock(spec=Lawyer)
    lawyer.id = 1
    lawyer.name = "张律师"
    lawyer.consultation_fee = 0  # 使用默认费用
    return lawyer


class TestVideoConsultationService:
    """视频咨询服务测试类"""

    @pytest.mark.asyncio
    async def test_generate_meeting_id(self, video_service):
        """测试生成会议房间 ID"""
        meeting_id = video_service._generate_meeting_id()
        assert meeting_id.startswith("VC")
        assert len(meeting_id) == 14  # VC + 12 个十六进制字符

    @pytest.mark.asyncio
    async def test_generate_meeting_password(self, video_service):
        """测试生成会议密码"""
        password = video_service._generate_meeting_password()
        assert len(password) == 6
        assert password.isdigit()

    @pytest.mark.asyncio
    async def test_get_video_consultation_fee_default(self, video_service, db):
        """测试获取默认视频咨询费用"""
        # 模拟律师不存在
        result = await video_service.get_video_consultation_fee(db, lawyer_id=999)
        
        assert result["fee"] == 99.0  # 默认费用
        assert result["duration"] == 30  # 默认 30 分钟
        assert result["enabled"] is False

    @pytest.mark.asyncio
    async def test_get_video_consultation_fee_with_lawyer(self, video_service, db, mock_lawyer):
        """测试获取律师视频咨询费用"""
        # 设置律师咨询费用
        mock_lawyer.consultation_fee = 150.0
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_lawyer
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await video_service.get_video_consultation_fee(db, lawyer_id=1)
        
        assert result["fee"] == 150.0
        assert result["duration"] == 30
        assert result["enabled"] is True

    @pytest.mark.asyncio
    async def test_calculate_member_discount_free_tier(self, video_service, db, mock_user):
        """测试免费会员折扣计算"""
        mock_user.vip_expires_at = None
        mock_user.vip_level = None
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        db.execute = AsyncMock(return_value=mock_result)
        
        with patch('app.services.video_consultation.membership_service') as mock_membership:
            mock_membership.get_user_tier = AsyncMock(return_value=MembershipTier.FREE.value)
            mock_membership.get_benefits.return_value = {
                "tier": MembershipTier.FREE.value,
                "video_consultation_discount": 1.0,
                "free_video_consultations_per_month": 0,
            }
            
            result = await video_service.calculate_member_discount(db, mock_user)
            
            assert result["tier"] == MembershipTier.FREE.value
            assert result["discount_rate"] == 1.0
            assert result["free_monthly_count"] == 0
            assert result["is_free"] is False

    @pytest.mark.asyncio
    async def test_calculate_member_discount_premium_tier(self, video_service, db, mock_user):
        """测试高级会员折扣计算"""
        mock_user.vip_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        db.execute = AsyncMock(return_value=mock_result)
        
        with patch('app.services.video_consultation.membership_service') as mock_membership:
            mock_membership.get_user_tier = AsyncMock(return_value=MembershipTier.ANNUAL.value)
            mock_membership.get_benefits.return_value = {
                "tier": MembershipTier.ANNUAL.value,
                "video_consultation_discount": 0.0,
                "free_video_consultations_per_month": 3,
            }
            
            result = await video_service.calculate_member_discount(db, mock_user)
            
            assert result["tier"] == MembershipTier.ANNUAL.value
            assert result["discount_rate"] == 0.5
            assert result["free_monthly_count"] == 3
            assert result["is_free"] is False

    @pytest.mark.asyncio
    async def test_get_user_usage_new_user(self, video_service, db):
        """测试新用户使用情况"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        
        with patch('app.services.video_consultation.membership_service') as mock_membership:
            mock_membership.get_user_tier = AsyncMock(return_value=MembershipTier.FREE.value)
            mock_membership.get_benefits.return_value = {
                "free_video_consultations_per_month": 0,
            }
            
            result = await video_service.get_user_usage(db, user_id=1)
            
            now = datetime.now(timezone.utc)
            year_month = now.strftime("%Y-%m")
            assert result["year_month"] == year_month
            assert result["free_used"] == 0
            assert result["paid_count"] == 0
            assert result["remaining_free"] == 0

    @pytest.mark.asyncio
    async def test_get_user_usage_with_history(self, video_service, db):
        """测试有使用记录的情况"""
        mock_usage = MagicMock(spec=VideoConsultationUsage)
        mock_usage.free_used = 2
        mock_usage.paid_count = 1
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [mock_usage, MagicMock()]  # 第一次返回 usage，第二次返回 user
        db.execute = AsyncMock(return_value=mock_result)
        
        with patch('app.services.video_consultation.membership_service') as mock_membership:
            mock_membership.get_user_tier = AsyncMock(return_value=MembershipTier.ANNUAL.value)
            mock_membership.get_benefits.return_value = {
                "free_video_consultations_per_month": 3,
            }
            
            result = await video_service.get_user_usage(db, user_id=1)
            
            assert result["free_used"] == 2
            assert result["paid_count"] == 1
            assert result["remaining_free"] == 3  # 5 - 2

    @pytest.mark.asyncio
    async def test_create_booking_success(self, video_service, db, mock_user, mock_lawyer):
        """测试成功创建视频咨询预约"""
        # 设置模拟数据
        mock_lawyer_result = MagicMock()
        mock_lawyer_result.scalar_one_or_none.return_value = mock_lawyer
        
        mock_fee_result = MagicMock()
        mock_fee_result.scalar_one_or_none.return_value = None  # 无使用记录
        
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user
        
        db.execute = AsyncMock(side_effect=[
            mock_lawyer_result,  # 获取律师
            mock_fee_result,     # 获取使用记录
            mock_user_result,    # 获取用户
        ])
        
        scheduled_time = datetime.now(timezone.utc) + timedelta(days=1)
        
        with patch.object(video_service, 'get_video_consultation_fee', return_value={
            "fee": 99.0,
            "duration": 30,
            "enabled": True,
        }):
            with patch.object(video_service, 'calculate_member_discount', return_value={
                "tier": MembershipTier.FREE.value,
                "discount_rate": 1.0,
                "free_monthly_count": 0,
                "is_free": False,
            }):
                with patch.object(video_service, 'get_user_usage', return_value={
                    "remaining_free": 0,
                }):
                    with patch.object(video_service, '_use_free_次数'):
                        result = await video_service.create_booking(
                            db,
                            user=mock_user,
                            lawyer_id=1,
                            scheduled_time=scheduled_time,
                            subject="离婚咨询",
                            description="想了解离婚财产分割问题",
                            category="婚姻家庭",
                        )
        
        assert result["id"] is not None
        assert result["lawyer_id"] == 1
        assert result["lawyer_name"] == "张律师"
        assert result["subject"] == "离婚咨询"
        assert result["base_fee"] == 99.0
        assert result["actual_fee"] == 99.0
        assert result["is_free"] is False

    @pytest.mark.asyncio
    async def test_create_booking_lawyer_not_found(self, video_service, db, mock_user):
        """测试创建预约时律师不存在"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        
        scheduled_time = datetime.now(timezone.utc) + timedelta(days=1)
        
        with pytest.raises(ValueError, match="律师不存在"):
            await video_service.create_booking(
                db,
                user=mock_user,
                lawyer_id=999,
                scheduled_time=scheduled_time,
                subject="咨询",
            )

    @pytest.mark.asyncio
    async def test_confirm_booking(self, video_service, db):
        """测试确认预约"""
        consultation = VideoConsultation(
            id=1,
            user_id=1,
            lawyer_id=1,
            subject="测试咨询",
            status=VideoConsultationStatus.PENDING.value,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await video_service.confirm_booking(db, consultation_id=1)
        
        assert result is not None
        assert result.status == VideoConsultationStatus.CONFIRMED.value

    @pytest.mark.asyncio
    async def test_confirm_booking_invalid_status(self, video_service, db):
        """测试确认已确认的预约"""
        consultation = VideoConsultation(
            id=1,
            user_id=1,
            lawyer_id=1,
            subject="测试咨询",
            status=VideoConsultationStatus.CONFIRMED.value,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        db.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(ValueError, match="只能确认待确认状态的预约"):
            await video_service.confirm_booking(db, consultation_id=1)

    @pytest.mark.asyncio
    async def test_start_consultation(self, video_service, db):
        """测试开始视频咨询"""
        consultation = VideoConsultation(
            id=1,
            user_id=1,
            lawyer_id=1,
            subject="测试咨询",
            status=VideoConsultationStatus.CONFIRMED.value,
            meeting_room_id="VC123456",
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await video_service.start_consultation(db, consultation_id=1)
        
        assert result is not None
        assert result.status == VideoConsultationStatus.IN_PROGRESS.value
        assert result.meeting_url is not None

    @pytest.mark.asyncio
    async def test_end_consultation(self, video_service, db):
        """测试结束视频咨询"""
        consultation = VideoConsultation(
            id=1,
            user_id=1,
            lawyer_id=1,
            subject="测试咨询",
            status=VideoConsultationStatus.IN_PROGRESS.value,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await video_service.end_consultation(db, consultation_id=1)
        
        assert result is not None
        assert result.status == VideoConsultationStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_cancel_booking(self, video_service, db):
        """测试取消预约"""
        consultation = VideoConsultation(
            id=1,
            user_id=1,
            lawyer_id=1,
            subject="测试咨询",
            status=VideoConsultationStatus.CONFIRMED.value,
            is_free=False,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await video_service.cancel_booking(db, consultation_id=1, user_id=1)
        
        assert result is not None
        assert result.status == VideoConsultationStatus.CANCELLED.value

    @pytest.mark.asyncio
    async def test_cancel_booking_unauthorized(self, video_service, db):
        """测试无权取消他人预约"""
        consultation = VideoConsultation(
            id=1,
            user_id=1,
            lawyer_id=1,
            subject="测试咨询",
            status=VideoConsultationStatus.CONFIRMED.value,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        db.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(ValueError, match="无权操作"):
            await video_service.cancel_booking(db, consultation_id=1, user_id=2)

    @pytest.mark.asyncio
    async def test_get_user_bookings(self, video_service, db):
        """测试获取用户预约列表"""
        consultations = [
            VideoConsultation(id=1, user_id=1, lawyer_id=1, subject="咨询 1"),
            VideoConsultation(id=2, user_id=1, lawyer_id=1, subject="咨询 2"),
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = consultations
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 2
        
        db.execute = AsyncMock(side_effect=[mock_result, mock_count])
        
        result, total = await video_service.get_user_bookings(db, user_id=1, page=1, page_size=20)
        
        assert len(result) == 2
        assert total == 2

    @pytest.mark.asyncio
    async def test_use_free_count_new_record(self, video_service, db):
        """测试使用免费次数（新记录）"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        
        await video_service._use_free_次数(db, user_id=1)
        
        # 验证调用了 db.commit
        assert db.commit.called

    @pytest.mark.asyncio
    async def test_use_free_count_existing_record(self, video_service, db):
        """测试使用免费次数（已有记录）"""
        mock_usage = MagicMock(spec=VideoConsultationUsage)
        mock_usage.free_used = 1
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_usage
        db.execute = AsyncMock(return_value=mock_result)
        
        await video_service._use_free_次数(db, user_id=1)
        
        assert mock_usage.free_used == 2

    @pytest.mark.asyncio
    async def test_refund_free_count(self, video_service, db):
        """测试退还免费次数"""
        mock_usage = MagicMock(spec=VideoConsultationUsage)
        mock_usage.free_used = 2
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_usage
        db.execute = AsyncMock(return_value=mock_result)
        
        await video_service._refund_free_次数(db, user_id=1)
        
        assert mock_usage.free_used == 1


class TestVideoScheduleService:
    """律师排班服务测试类"""

    @pytest.mark.asyncio
    async def test_create_schedule(self, schedule_service, db):
        """测试创建排班"""
        date = datetime.now(timezone.utc).date()
        
        result = await schedule_service.create_schedule(
            db,
            lawyer_id=1,
            date=date,
            start_time="09:00",
            end_time="17:00",
            video_consultation_enabled=True,
            consultation_fee=100.0,
            max_bookings=5,
            note="工作日排班",
        )
        
        assert result is not None
        assert result.lawyer_id == 1
        assert result.start_time == "09:00"
        assert result.end_time == "17:00"
        assert result.video_consultation_enabled is True
        assert result.consultation_fee == 100.0
        assert result.max_bookings == 5

    @pytest.mark.asyncio
    async def test_get_available_slots(self, schedule_service, db):
        """测试获取可用时段"""
        date = datetime.now(timezone.utc)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        schedules = [
            VideoSchedule(
                id=1,
                lawyer_id=1,
                date=start_of_day,
                start_time="09:00",
                end_time="12:00",
                is_available=True,
                video_consultation_enabled=True,
                max_bookings=3,
                current_bookings=1,
                consultation_fee=100.0,
            ),
            VideoSchedule(
                id=2,
                lawyer_id=1,
                date=start_of_day,
                start_time="14:00",
                end_time="17:00",
                is_available=True,
                video_consultation_enabled=True,
                max_bookings=3,
                current_bookings=3,  # 已满
                consultation_fee=100.0,
            ),
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = schedules
        db.execute = AsyncMock(return_value=mock_result)
        
        slots = await schedule_service.get_available_slots(db, lawyer_id=1, date=date)
        
        # 只返回未满的时段
        assert len(slots) == 1
        assert slots[0]["schedule_id"] == 1
        assert slots[0]["available_count"] == 2  # 3 - 1

    @pytest.mark.asyncio
    async def test_book_slot_success(self, schedule_service, db):
        """测试预约时段成功"""
        schedule = VideoSchedule(
            id=1,
            lawyer_id=1,
            current_bookings=1,
            max_bookings=3,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = schedule
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await schedule_service.book_slot(db, schedule_id=1, consultation_id=1)
        
        assert result is not None
        assert result.current_bookings == 2

    @pytest.mark.asyncio
    async def test_book_slot_full(self, schedule_service, db):
        """测试预约已满时段"""
        schedule = VideoSchedule(
            id=1,
            lawyer_id=1,
            current_bookings=3,
            max_bookings=3,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = schedule
        db.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(ValueError, match="该时段已满"):
            await schedule_service.book_slot(db, schedule_id=1, consultation_id=1)

    @pytest.mark.asyncio
    async def test_release_slot(self, schedule_service, db):
        """测试释放时段"""
        schedule = VideoSchedule(
            id=1,
            lawyer_id=1,
            current_bookings=2,
            max_bookings=3,
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = schedule
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await schedule_service.release_slot(db, schedule_id=1)
        
        assert result is not None
        assert result.current_bookings == 1


class TestVideoConsultationIntegration:
    """视频咨询集成测试类"""

    @pytest.mark.asyncio
    async def test_full_booking_flow(self, video_service, db, mock_user, mock_lawyer):
        """测试完整的预约流程"""
        # 1. 创建预约
        mock_lawyer_result = MagicMock()
        mock_lawyer_result.scalar_one_or_none.return_value = mock_lawyer
        db.execute = AsyncMock(return_value=mock_lawyer_result)
        
        scheduled_time = datetime.now(timezone.utc) + timedelta(days=1)
        
        with patch.object(video_service, 'get_video_consultation_fee', return_value={
            "fee": 99.0,
            "duration": 30,
            "enabled": True,
        }):
            with patch.object(video_service, 'calculate_member_discount', return_value={
                "tier": MembershipTier.FREE.value,
                "discount_rate": 1.0,
                "free_monthly_count": 0,
                "is_free": False,
            }):
                with patch.object(video_service, 'get_user_usage', return_value={
                    "remaining_free": 0,
                }):
                    with patch.object(video_service, '_use_free_次数'):
                        result = await video_service.create_booking(
                            db,
                            user=mock_user,
                            lawyer_id=1,
                            scheduled_time=scheduled_time,
                            subject="离婚咨询",
                        )
        
        consultation_id = result["id"]
        
        # 2. 确认预约
        consultation = VideoConsultation(
            id=consultation_id,
            user_id=1,
            lawyer_id=1,
            subject="离婚咨询",
            status=VideoConsultationStatus.PENDING.value,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = consultation
        db.execute = AsyncMock(return_value=mock_result)
        
        confirmed = await video_service.confirm_booking(db, consultation_id)
        assert confirmed.status == VideoConsultationStatus.CONFIRMED.value
        
        # 3. 开始咨询
        consultation.status = VideoConsultationStatus.CONFIRMED.value
        started = await video_service.start_consultation(db, consultation_id)
        assert started.status == VideoConsultationStatus.IN_PROGRESS.value
        
        # 4. 结束咨询
        consultation.status = VideoConsultationStatus.IN_PROGRESS.value
        completed = await video_service.end_consultation(db, consultation_id)
        assert completed.status == VideoConsultationStatus.COMPLETED.value