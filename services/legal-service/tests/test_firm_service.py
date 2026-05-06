"""FirmService 单元测试"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.firm_service import FirmService
from app.models import LawFirm, LawFirmVerification, Lawyer


class TestFirmService:
    """FirmService 测试类"""

    @pytest.mark.asyncio
    async def test_create_firm(self, db_session: AsyncSession):
        """测试创建律所"""
        service = FirmService(db_session)
        firm = await service.create_firm(
            user_id=1,
            name="测试律所",
            license_no="LIC123456",
            province="北京",
            city="北京市",
            address="朝阳区某街道1号",
            phone="010-12345678",
            email="test@lawfirm.com",
            description="这是测试律所",
        )

        assert firm.id is not None
        assert firm.name == "测试律所"
        assert firm.user_id == 1
        assert firm.status == "pending"
        assert firm.license_no == "LIC123456"

    @pytest.mark.asyncio
    async def test_list_firms(self, db_session: AsyncSession):
        """测试获取律所列表"""
        service = FirmService(db_session)
        await service.create_firm(user_id=1, name="律所A", province="北京")
        await service.create_firm(user_id=2, name="律所B", province="上海")

        firms, total = await service.list_firms(page=1, page_size=10)

        assert total >= 2
        assert len(firms) >= 2

    @pytest.mark.asyncio
    async def test_list_firms_filter_by_province(self, db_session: AsyncSession):
        """测试按省份筛选律所"""
        service = FirmService(db_session)
        await service.create_firm(user_id=1, name="北京律所", province="北京")
        await service.create_firm(user_id=2, name="上海律所", province="上海")

        firms, total = await service.list_firms(province="北京", status=None)

        assert all(f.province == "北京" for f in firms)

    @pytest.mark.asyncio
    async def test_approve_firm(self, db_session: AsyncSession):
        """测试审核通过律所"""
        service = FirmService(db_session)
        firm = await service.create_firm(user_id=1, name="待审核律所")

        await service.submit_verification(firm_id=firm.id)
        approved_firm = await service.approve_firm(firm_id=firm.id, reviewed_by_user_id=100)

        assert approved_firm.status == "verified"

        verification = await service.get_verification_status(firm.id)
        assert verification is not None
        assert verification.status == "approved"

    @pytest.mark.asyncio
    async def test_approve_firm_not_found(self, db_session: AsyncSession):
        """测试审核不存在的律所"""
        service = FirmService(db_session)

        with pytest.raises(ValueError, match="律所不存在"):
            await service.approve_firm(firm_id=99999, reviewed_by_user_id=100)

    @pytest.mark.asyncio
    async def test_reject_firm(self, db_session: AsyncSession):
        """测试审核拒绝律所"""
        service = FirmService(db_session)
        firm = await service.create_firm(user_id=1, name="待拒绝律所")

        await service.submit_verification(firm_id=firm.id)
        rejected_firm = await service.reject_firm(
            firm_id=firm.id,
            reviewed_by_user_id=100,
            reason="资质不符合要求"
        )

        assert rejected_firm.status == "rejected"

        verification = await service.get_verification_status(firm.id)
        assert verification is not None
        assert verification.status == "rejected"
        assert verification.rejection_reason == "资质不符合要求"

    @pytest.mark.asyncio
    async def test_reject_firm_not_found(self, db_session: AsyncSession):
        """测试拒绝不存在的律所"""
        service = FirmService(db_session)

        with pytest.raises(ValueError, match="律所不存在"):
            await service.reject_firm(
                firm_id=99999,
                reviewed_by_user_id=100,
                reason="测试原因"
            )
