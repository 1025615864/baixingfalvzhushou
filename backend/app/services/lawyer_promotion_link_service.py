"""律师推广链接服务"""
import secrets
import string
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.lawfirm import Lawyer, LawyerPromotionLink
from ..schemas.lawfirm import LawyerPromotionLinkCreate, LawyerPromotionLinkUpdate


class LawyerPromotionLinkService:
    """律师推广链接服务"""

    @staticmethod
    def _generate_link_code() -> str:
        """
        生成推广链接码

        Returns:
            8位随机字符串（大小写字母+数字）
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(8))

    @staticmethod
    async def create(
        db: AsyncSession,
        lawyer_id: int,
        data: LawyerPromotionLinkCreate,
    ) -> LawyerPromotionLink:
        """
        创建律师推广链接

        Args:
            db: 数据库会话
            lawyer_id: 律师ID
            data: 推广链接数据

        Returns:
            创建的推广链接记录

        Raises:
            ValueError: 如果律师不存在
        """
        # 检查律师是否存在
        lawyer_result = await db.execute(
            select(Lawyer).where(Lawyer.id == lawyer_id)
        )
        lawyer = lawyer_result.scalar_one_or_none()
        if not lawyer:
            raise ValueError("律师不存在")

        # 生成唯一的链接码
        link_code = LawyerPromotionLinkService._generate_link_code()
        while True:
            existing_result = await db.execute(
                select(LawyerPromotionLink).where(
                    LawyerPromotionLink.link_code == link_code)
            )
            if not existing_result.scalar_one_or_none():
                break
            link_code = LawyerPromotionLinkService._generate_link_code()

        # 创建推广链接
        promotion_link = LawyerPromotionLink(
            lawyer_id=lawyer_id,
            link_code=link_code,
            link_name=data.link_name,
            description=data.description,
            is_active=True,
        )
        db.add(promotion_link)
        await db.commit()
        await db.refresh(promotion_link)
        return promotion_link

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        link_id: int,
        lawyer_id: int | None = None,
    ) -> LawyerPromotionLink | None:
        """
        根据ID获取推广链接

        Args:
            db: 数据库会话
            link_id: 推广链接ID
            lawyer_id: 律师ID（可选，用于权限验证）

        Returns:
            推广链接记录或None
        """
        query = select(LawyerPromotionLink).where(
            LawyerPromotionLink.id == link_id)
        if lawyer_id is not None:
            query = query.where(LawyerPromotionLink.lawyer_id == lawyer_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_code(
        db: AsyncSession,
        link_code: str,
    ) -> LawyerPromotionLink | None:
        """
        根据链接码获取推广链接

        Args:
            db: 数据库会话
            link_code: 推广链接码

        Returns:
            推广链接记录或None
        """
        result = await db.execute(
            select(LawyerPromotionLink).where(
                LawyerPromotionLink.link_code == link_code,
                LawyerPromotionLink.is_active,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(
        db: AsyncSession,
        lawyer_id: int,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LawyerPromotionLink], int]:
        """
        获取律师的推广链接列表

        Args:
            db: 数据库会话
            lawyer_id: 律师ID
            is_active: 是否启用筛选
            page: 页码
            page_size: 每页数量

        Returns:
            (推广链接列表, 总数)
        """
        query = select(LawyerPromotionLink).where(
            LawyerPromotionLink.lawyer_id == lawyer_id)
        count_query = select(func.count(LawyerPromotionLink.id)).where(
            LawyerPromotionLink.lawyer_id == lawyer_id
        )

        if is_active is not None:
            query = query.where(LawyerPromotionLink.is_active == is_active)
            count_query = count_query.where(
                LawyerPromotionLink.is_active == is_active)

        query = query.order_by(LawyerPromotionLink.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        links = (await db.execute(query)).scalars().all()
        total = int((await db.execute(count_query)).scalar() or 0)

        return list(links), total

    @staticmethod
    async def update(
        db: AsyncSession,
        link_id: int,
        lawyer_id: int,
        data: LawyerPromotionLinkUpdate,
    ) -> LawyerPromotionLink | None:
        """
        更新推广链接

        Args:
            db: 数据库会话
            link_id: 推广链接ID
            lawyer_id: 律师ID
            data: 更新数据

        Returns:
            更新后的推广链接记录或None
        """
        result = await db.execute(
            select(LawyerPromotionLink).where(
                LawyerPromotionLink.id == link_id,
                LawyerPromotionLink.lawyer_id == lawyer_id,
            )
        )
        promotion_link = result.scalar_one_or_none()
        if not promotion_link:
            return None

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(promotion_link, field, value)

        await db.commit()
        await db.refresh(promotion_link)
        return promotion_link

    @staticmethod
    async def delete(
        db: AsyncSession,
        link_id: int,
        lawyer_id: int,
    ) -> bool:
        """
        删除推广链接

        Args:
            db: 数据库会话
            link_id: 推广链接ID
            lawyer_id: 律师ID

        Returns:
            是否删除成功
        """
        result = await db.execute(
            select(LawyerPromotionLink).where(
                LawyerPromotionLink.id == link_id,
                LawyerPromotionLink.lawyer_id == lawyer_id,
            )
        )
        promotion_link = result.scalar_one_or_none()
        if not promotion_link:
            return False

        await db.delete(promotion_link)
        await db.commit()
        return True

    @staticmethod
    async def increment_click_count(
        db: AsyncSession,
        link_id: int,
    ) -> bool:
        """
        增加点击次数

        Args:
            db: 数据库会话
            link_id: 推广链接ID

        Returns:
            是否更新成功
        """
        result = await db.execute(
            select(LawyerPromotionLink).where(
                LawyerPromotionLink.id == link_id)
        )
        promotion_link = result.scalar_one_or_none()
        if not promotion_link:
            return False

        promotion_link.click_count += 1
        await db.commit()
        return True

    @staticmethod
    async def increment_consultation_count(
        db: AsyncSession,
        link_id: int,
    ) -> bool:
        """
        增加咨询次数

        Args:
            db: 数据库会话
            link_id: 推广链接ID

        Returns:
            是否更新成功
        """
        result = await db.execute(
            select(LawyerPromotionLink).where(
                LawyerPromotionLink.id == link_id)
        )
        promotion_link = result.scalar_one_or_none()
        if not promotion_link:
            return False

        promotion_link.consultation_count += 1
        await db.commit()
        return True

    @staticmethod
    async def increment_conversion_count(
        db: AsyncSession,
        link_id: int,
    ) -> bool:
        """
        增加转化次数

        Args:
            db: 数据库会话
            link_id: 推广链接ID

        Returns:
            是否更新成功
        """
        result = await db.execute(
            select(LawyerPromotionLink).where(
                LawyerPromotionLink.id == link_id)
        )
        promotion_link = result.scalar_one_or_none()
        if not promotion_link:
            return False

        promotion_link.conversion_count += 1
        await db.commit()
        return True

    @staticmethod
    async def get_stats(
        db: AsyncSession,
        link_id: int,
        lawyer_id: int | None = None,
    ) -> dict[str, int | float | str | None] | None:
        """
        获取推广链接统计

        Args:
            db: 数据库会话
            link_id: 推广链接ID
            lawyer_id: 律师ID（可选，用于权限验证）

        Returns:
            统计数据或None
        """
        query = select(LawyerPromotionLink).where(
            LawyerPromotionLink.id == link_id)
        if lawyer_id is not None:
            query = query.where(LawyerPromotionLink.lawyer_id == lawyer_id)
        result = await db.execute(query)
        promotion_link = result.scalar_one_or_none()
        if not promotion_link:
            return None

        conversion_rate = 0.0
        if promotion_link.click_count > 0:
            conversion_rate = promotion_link.conversion_count / promotion_link.click_count

        return {
            "link_id": promotion_link.id,
            "link_code": promotion_link.link_code,
            "link_name": promotion_link.link_name,
            "click_count": promotion_link.click_count,
            "consultation_count": promotion_link.consultation_count,
            "conversion_count": promotion_link.conversion_count,
            "conversion_rate": round(conversion_rate, 4),
        }
