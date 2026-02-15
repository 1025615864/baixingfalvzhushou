"""律师主页定制服务"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.lawfirm import Lawyer, LawyerHomepage
from ..schemas.lawfirm import LawyerHomepageCreate, LawyerHomepageUpdate, LawyerHomepagePublicResponse


class LawyerHomepageService:
    """律师主页定制服务"""

    @staticmethod
    async def create(
        db: AsyncSession,
        lawyer_id: int,
        data: LawyerHomepageCreate,
    ) -> LawyerHomepage:
        """
        创建律师主页

        Args:
            db: 数据库会话
            lawyer_id: 律师ID
            data: 主页数据

        Returns:
            创建的主页记录

        Raises:
            ValueError: 如果律师不存在或已存在主页
        """
        # 检查律师是否存在
        lawyer_result = await db.execute(
            select(Lawyer).where(Lawyer.id == lawyer_id)
        )
        lawyer = lawyer_result.scalar_one_or_none()
        if not lawyer:
            raise ValueError("律师不存在")

        # 检查是否已存在主页
        existing_result = await db.execute(
            select(LawyerHomepage).where(LawyerHomepage.lawyer_id == lawyer_id)
        )
        if existing_result.scalar_one_or_none():
            raise ValueError("律师主页已存在，请使用更新接口")

        # 创建主页
        homepage = LawyerHomepage(
            lawyer_id=lawyer_id,
            banner_image=data.banner_image,
            profile_image=data.profile_image,
            slogan=data.slogan,
            bio=data.bio,
            specialties_display=data.specialties_display,
            achievements=data.achievements,
            education=data.education,
            service_areas=data.service_areas,
            service_hours=data.service_hours,
            response_time=data.response_time,
            contact_phone=data.contact_phone,
            contact_email=data.contact_email,
            wechat_qrcode=data.wechat_qrcode,
            weibo_url=data.weibo_url,
            linkedin_url=data.linkedin_url,
            zhihu_url=data.zhihu_url,
            case_studies=data.case_studies,
            video_url=data.video_url,
            video_cover=data.video_cover,
            seo_title=data.seo_title,
            seo_description=data.seo_description,
            seo_keywords=data.seo_keywords,
            theme_color=data.theme_color,
            background_color=data.background_color,
            is_published=data.is_published,
        )
        db.add(homepage)
        await db.commit()
        await db.refresh(homepage)
        return homepage

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        homepage_id: int,
    ) -> LawyerHomepage | None:
        """
        根据ID获取主页

        Args:
            db: 数据库会话
            homepage_id: 主页ID

        Returns:
            主页记录或None
        """
        result = await db.execute(
            select(LawyerHomepage).where(LawyerHomepage.id == homepage_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_lawyer_id(
        db: AsyncSession,
        lawyer_id: int,
    ) -> LawyerHomepage | None:
        """
        根据律师ID获取主页

        Args:
            db: 数据库会话
            lawyer_id: 律师ID

        Returns:
            主页记录或None
        """
        result = await db.execute(
            select(LawyerHomepage).where(LawyerHomepage.lawyer_id == lawyer_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession,
        lawyer_id: int,
        data: LawyerHomepageUpdate,
    ) -> LawyerHomepage | None:
        """
        更新律师主页

        Args:
            db: 数据库会话
            lawyer_id: 律师ID
            data: 更新数据

        Returns:
            更新后的主页记录或None

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

        # 获取主页
        result = await db.execute(
            select(LawyerHomepage).where(LawyerHomepage.lawyer_id == lawyer_id)
        )
        homepage = result.scalar_one_or_none()
        if not homepage:
            return None

        # 更新字段
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(homepage, field, value)

        await db.commit()
        await db.refresh(homepage)
        return homepage

    @staticmethod
    async def delete(
        db: AsyncSession,
        lawyer_id: int,
    ) -> bool:
        """
        删除律师主页

        Args:
            db: 数据库会话
            lawyer_id: 律师ID

        Returns:
            是否删除成功
        """
        result = await db.execute(
            select(LawyerHomepage).where(LawyerHomepage.lawyer_id == lawyer_id)
        )
        homepage = result.scalar_one_or_none()
        if not homepage:
            return False

        await db.delete(homepage)
        await db.commit()
        return True

    @staticmethod
    async def increment_view_count(
        db: AsyncSession,
        homepage_id: int,
    ) -> bool:
        """
        增加主页浏览量

        Args:
            db: 数据库会话
            homepage_id: 主页ID

        Returns:
            是否更新成功
        """
        result = await db.execute(
            select(LawyerHomepage).where(LawyerHomepage.id == homepage_id)
        )
        homepage = result.scalar_one_or_none()
        if not homepage:
            return False

        homepage.view_count += 1
        await db.commit()
        return True

    @staticmethod
    async def publish(
        db: AsyncSession,
        lawyer_id: int,
    ) -> LawyerHomepage | None:
        """
        发布律师主页

        Args:
            db: 数据库会话
            lawyer_id: 律师ID

        Returns:
            发布后的主页记录或None
        """
        result = await db.execute(
            select(LawyerHomepage).where(LawyerHomepage.lawyer_id == lawyer_id)
        )
        homepage = result.scalar_one_or_none()
        if not homepage:
            return None

        homepage.is_published = True
        await db.commit()
        await db.refresh(homepage)
        return homepage

    @staticmethod
    async def unpublish(
        db: AsyncSession,
        lawyer_id: int,
    ) -> LawyerHomepage | None:
        """
        取消发布律师主页

        Args:
            db: 数据库会话
            lawyer_id: 律师ID

        Returns:
            取消发布后的主页记录或None
        """
        result = await db.execute(
            select(LawyerHomepage).where(LawyerHomepage.lawyer_id == lawyer_id)
        )
        homepage = result.scalar_one_or_none()
        if not homepage:
            return None

        homepage.is_published = False
        await db.commit()
        await db.refresh(homepage)
        return homepage

    @staticmethod
    async def get_public_homepage(
        db: AsyncSession,
        lawyer_id: int,
    ) -> LawyerHomepagePublicResponse | None:
        """
        获取律师公开主页（用于用户查看）

        Args:
            db: 数据库会话
            lawyer_id: 律师ID

        Returns:
            公开主页数据或None
        """
        # 获取律师信息
        lawyer_result = await db.execute(
            select(Lawyer).where(Lawyer.id == lawyer_id)
        )
        lawyer = lawyer_result.scalar_one_or_none()
        if not lawyer:
            return None

        # 获取主页
        homepage_result = await db.execute(
            select(LawyerHomepage).where(
                LawyerHomepage.lawyer_id == lawyer_id,
                LawyerHomepage.is_published
            )
        )
        homepage = homepage_result.scalar_one_or_none()
        if not homepage:
            return None

        # 增加浏览量
        homepage.view_count += 1
        await db.commit()

        # 构建公开响应
        return LawyerHomepagePublicResponse(
            id=homepage.id,
            lawyer_id=homepage.lawyer_id,
            lawyer_name=lawyer.name,
            lawyer_avatar=lawyer.avatar,
            lawyer_title=lawyer.title,
            lawyer_specialties=lawyer.specialties,
            lawyer_experience_years=lawyer.experience_years,
            lawyer_rating=lawyer.rating,
            lawyer_review_count=lawyer.review_count,
            lawyer_consultation_fee=lawyer.consultation_fee,
            banner_image=homepage.banner_image,
            profile_image=homepage.profile_image,
            slogan=homepage.slogan,
            bio=homepage.bio,
            specialties_display=homepage.specialties_display,
            achievements=homepage.achievements,
            education=homepage.education,
            service_areas=homepage.service_areas,
            service_hours=homepage.service_hours,
            response_time=homepage.response_time,
            contact_phone=homepage.contact_phone,
            contact_email=homepage.contact_email,
            wechat_qrcode=homepage.wechat_qrcode,
            weibo_url=homepage.weibo_url,
            linkedin_url=homepage.linkedin_url,
            zhihu_url=homepage.zhihu_url,
            case_studies=homepage.case_studies,
            video_url=homepage.video_url,
            video_cover=homepage.video_cover,
            view_count=homepage.view_count,
            created_at=homepage.created_at,
            updated_at=homepage.updated_at,
        )
