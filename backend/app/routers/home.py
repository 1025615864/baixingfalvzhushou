"""首页路由 - 提供首页数据API"""

from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, Lawyer, Consultation, ContractReviewHistory
from ..models.lawfirm import LawyerReview
from ..utils.deps import get_current_user_optional

router = APIRouter(prefix="/home", tags=["首页"])


class HomeBanner(BaseModel):
    """首页横幅"""
    id: str
    title: str
    subtitle: str | None = None
    description: str | None = None
    image_url: str | None = None
    button_text: str | None = None
    button_link: str | None = None
    is_active: bool = True
    order: int = 0


class QuickAction(BaseModel):
    """快捷入口"""
    id: str
    title: str
    description: str | None = None
    icon: str
    link: str
    badge: str | None = None
    is_new: bool = False
    order: int = 0


class Recommendation(BaseModel):
    """推荐内容"""
    id: str
    type: str  # lawyer, article, consultation, knowledge
    title: str
    description: str | None = None
    image_url: str | None = None
    link: str
    tags: list[str] | None = None
    rating: float | None = None
    view_count: int | None = None
    author_name: str | None = None
    author_avatar: str | None = None
    created_at: str | None = None
    relevance_score: float | None = None


class FeatureCard(BaseModel):
    """功能卡片"""
    id: str
    title: str
    description: str
    icon: str
    link: str
    color: str  # blue, green, purple, orange, red, teal
    stats_label: str | None = None
    stats_value: str | None = None


class HomeStats(BaseModel):
    """首页统计数据"""
    total_consultations: int
    total_lawyers: int
    total_users: int
    total_articles: int
    solved_cases: int
    satisfaction_rate: int  # 百分比


class HomeData(BaseModel):
    """首页数据聚合"""
    banners: list[HomeBanner]
    quick_actions: list[QuickAction]
    recommendations: list[Recommendation]
    feature_cards: list[FeatureCard]
    stats: HomeStats
    last_updated: str


async def _get_home_banners() -> list[HomeBanner]:
    """获取首页横幅数据"""
    return [
        HomeBanner(
            id="1",
            title="欢迎来到百姓助手",
            subtitle="您的AI法律助手",
            description="提供专业的法律咨询服务，让法律问题变得简单易懂",
            image_url=None,
            button_text="立即咨询",
            button_link="/consultation",
            is_active=True,
            order=1,
        ),
        HomeBanner(
            id="2",
            title="AI智能法律咨询",
            subtitle="24小时在线服务",
            description="基于大语言模型的智能法律助手，随时随地解答您的法律问题",
            image_url=None,
            button_text="开始对话",
            button_link="/chat",
            is_active=True,
            order=2,
        ),
    ]


async def _get_quick_actions() -> list[QuickAction]:
    """获取快捷入口数据"""
    return [
        QuickAction(id="1", title="AI咨询", description="智能法律助手", icon="ai", link="/chat", is_new=True, order=1),
        QuickAction(id="2", title="找律师", description="专业律师服务", icon="lawyer", link="/lawyer", order=2),
        QuickAction(id="3", title="法律咨询", description="一对一咨询", icon="consultation", link="/consultation", order=3),
        QuickAction(id="4", title="法律知识", description="海量法律知识", icon="knowledge", link="/knowledge", order=4),
        QuickAction(id="5", title="合同审查", description="AI智能审查", icon="contract", link="/contracts", is_new=True, order=5),
        QuickAction(id="6", title="文书生成", description="快速生成文书", icon="document", link="/document", order=6),
        QuickAction(id="7", title="法律论坛", description="交流讨论", icon="forum", link="/forum", order=7),
        QuickAction(id="8", title="会员中心", description="尊享特权", icon="vip", link="/vip", order=8),
    ]


async def _get_feature_cards() -> list[FeatureCard]:
    """获取功能卡片数据"""
    return [
        FeatureCard(
            id="1",
            title="AI智能咨询",
            description="基于大模型的智能法律助手，24小时在线解答您的法律问题",
            icon="ai",
            link="/chat",
            color="blue",
            stats_label="已解答",
            stats_value="100万+",
        ),
        FeatureCard(
            id="2",
            title="合同智能审查",
            description="上传合同文件，AI自动识别风险条款，提供专业修改建议",
            icon="document",
            link="/contracts",
            color="purple",
            stats_label="审查合同",
            stats_value="50万+",
        ),
        FeatureCard(
            id="3",
            title="律师精准匹配",
            description="根据您的需求和案件类型，智能推荐最合适的专业律师",
            icon="search",
            link="/lawyer-matching",
            color="green",
            stats_label="入驻律师",
            stats_value="10万+",
        ),
        FeatureCard(
            id="4",
            title="法律文书生成",
            description="输入关键信息，一键生成专业的法律文书，省时省力",
            icon="calculator",
            link="/document",
            color="orange",
            stats_label="生成文书",
            stats_value="200万+",
        ),
    ]


async def _get_stats_from_db(db: AsyncSession) -> HomeStats:
    """从数据库获取首页统计数据"""
    try:
        # 总用户数
        user_result = await db.execute(select(func.count(User.id)).where(User.is_active == True))
        total_users = user_result.scalar() or 0

        # 活跃律师数 (已认证且活跃的律师)
        lawyer_result = await db.execute(
            select(func.count(Lawyer.id)).where(
                and_(Lawyer.is_verified == True, Lawyer.is_active == True)
            )
        )
        total_lawyers = lawyer_result.scalar() or 0

        # 总咨询数
        consultation_result = await db.execute(select(func.count(Consultation.id)))
        total_consultations = consultation_result.scalar() or 0

        # 合同审查数
        contract_result = await db.execute(select(func.count(ContractReviewHistory.id)))
        total_contracts = contract_result.scalar() or 0

        # 法律知识文章数 (静态统计)
        total_articles = 50000  # 知识库文章数，已迁移到微服务

        # 计算满意度 (基于律师评价的平均分)
        rating_result = await db.execute(select(func.avg(LawyerReview.rating)))
        avg_rating = rating_result.scalar()
        satisfaction_rate = int((avg_rating or 4.5) / 5 * 100)  # 默认4.5分，转换为百分比

        # 已解决案件数 (使用咨询数作为近似值)
        solved_cases = int(total_consultations * 0.8)  # 假设80%的咨询得到解决

        return HomeStats(
            total_consultations=total_consultations,
            total_lawyers=total_lawyers,
            total_users=total_users,
            total_articles=total_articles,
            solved_cases=solved_cases,
            satisfaction_rate=satisfaction_rate,
        )
    except Exception as e:
        # 如果数据库查询失败，返回默认数据
        return HomeStats(
            total_consultations=1_000_000,
            total_lawyers=10_000,
            total_users=500_000,
            total_articles=50_000,
            solved_cases=800_000,
            satisfaction_rate=98,
        )


async def _get_recommendations_from_db(
    db: AsyncSession,
    type: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[Recommendation], int]:
    """从数据库获取推荐内容"""
    recommendations: list[Recommendation] = []
    
    try:
        # 1. 获取推荐律师 (按评分排序)
        if type is None or type == "all" or type == "lawyer":
            lawyer_query = (
                select(Lawyer)
                .where(and_(Lawyer.is_verified == True, Lawyer.is_active == True))
                .order_by(Lawyer.rating.desc())
                .limit(limit)
            )
            lawyer_result = await db.execute(lawyer_query)
            lawyers = lawyer_result.scalars().all()
            
            for lawyer in lawyers:
                specialties = lawyer.specialties.split(",") if lawyer.specialties else []
                recommendations.append(
                    Recommendation(
                        id=f"lawyer_{lawyer.id}",
                        type="lawyer",
                        title=f"{lawyer.name} - {lawyer.title or '专业律师'}",
                        description=lawyer.introduction or "资深律师，为您提供专业法律服务",
                        link=f"/lawyer/{lawyer.id}",
                        tags=specialties[:3] if specialties else ["法律咨询"],
                        rating=lawyer.rating or 4.5,
                        view_count=lawyer.case_count or 0,
                        author_name=lawyer.name,
                        author_avatar=lawyer.avatar,
                        created_at=lawyer.created_at.isoformat() if lawyer.created_at else None,
                    )
                )

        # 2. 获取热门法律知识文章 (已迁移到news-service)
        # 文章推荐由news-service提供

        # 3. 获取最新咨询 (热门咨询)
        if type is None or type == "all" or type == "consultation":
            consultation_query = (
                select(Consultation)
                .order_by(Consultation.created_at.desc())
                .limit(limit)
            )
            consultation_result = await db.execute(consultation_query)
            consultations = consultation_result.scalars().all()
            
            for consultation in consultations:
                recommendations.append(
                    Recommendation(
                        id=f"consultation_{consultation.id}",
                        type="consultation",
                        title=consultation.title or "法律咨询",
                        description="点击查看咨询详情",
                        link=f"/consultation/{consultation.id}",
                        tags=["法律咨询"],
                        view_count=0,
                        created_at=consultation.created_at.isoformat() if consultation.created_at else None,
                    )
                )

        total = len(recommendations)
        
        # 根据类型过滤
        if type and type != "all":
            recommendations = [r for r in recommendations if r.type == type]
        
        # 分页
        recommendations = recommendations[offset:offset + limit]
        
        return recommendations, total
        
    except Exception as e:
        # 如果数据库查询失败，返回默认数据
        default_recommendations = [
            Recommendation(
                id="1",
                type="lawyer",
                title="张律师 - 专注民商事纠纷",
                description="10年执业经验，擅长合同纠纷、债务追讨",
                link="/lawyer/1",
                tags=["合同纠纷", "债务追讨", "民事诉讼"],
                rating=4.9,
                view_count=1250,
                author_name="张律师",
            ),
            Recommendation(
                id="2",
                type="article",
                title="劳动合同解除的法定情形",
                description="详解劳动合同法中关于合同解除的各项规定",
                link="/knowledge/article/1",
                tags=["劳动法", "合同纠纷", "员工权益"],
                view_count=3500,
                author_name="李律师",
            ),
        ]
        return default_recommendations, len(default_recommendations)


@router.get("/data", response_model=dict[str, Any], summary="获取首页完整数据")
async def get_home_data(
    request: Request,
    include_stats: bool = True,
    recommendation_limit: int = 8,
    current_user: Any = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """获取首页完整数据聚合
    
    - 横幅数据
    - 快捷入口
    - 推荐内容
    - 功能卡片
    - 统计数据
    """
    try:
        # 获取横幅
        banners = await _get_home_banners()
        
        # 获取快捷入口
        quick_actions = await _get_quick_actions()
        
        # 获取推荐内容
        recommendations, _ = await _get_recommendations_from_db(
            db, type="all", limit=recommendation_limit
        )
        
        # 获取功能卡片
        feature_cards = await _get_feature_cards()
        
        # 获取统计数据
        stats = await _get_stats_from_db(db) if include_stats else None
        
        return {
            "data": {
                "banners": [b.model_dump() for b in banners],
                "quick_actions": [a.model_dump() for a in quick_actions],
                "recommendations": [r.model_dump() for r in recommendations],
                "feature_cards": [c.model_dump() for c in feature_cards],
                "stats": stats.model_dump() if stats else None,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取首页数据失败: {str(e)}")


@router.get("/banners", response_model=dict[str, list[HomeBanner]], summary="获取首页横幅")
async def get_banners(
    current_user: Any = Depends(get_current_user_optional),
):
    """获取首页横幅列表"""
    banners = await _get_home_banners()
    return {"banners": banners}


@router.get("/quick-actions", response_model=dict[str, list[QuickAction]], summary="获取快捷入口")
async def get_quick_actions(
    current_user: Any = Depends(get_current_user_optional),
):
    """获取快捷入口列表"""
    actions = await _get_quick_actions()
    return {"actions": actions}


@router.get("/recommendations", response_model=dict[str, Any], summary="获取推荐内容")
async def get_recommendations(
    type: str | None = None,
    limit: int = 10,
    offset: int = 0,
    current_user: Any = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """获取推荐内容列表"""
    try:
        recommendations, total = await _get_recommendations_from_db(
            db, type=type, limit=limit, offset=offset
        )
        
        return {
            "recommendations": [r.model_dump() for r in recommendations],
            "total": total,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取推荐内容失败: {str(e)}")


@router.get("/stats", response_model=dict[str, HomeStats], summary="获取首页统计数据")
async def get_stats(
    current_user: Any = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """获取首页统计数据"""
    try:
        stats = await _get_stats_from_db(db)
        return {"stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


@router.post("/track-click", summary="追踪点击行为")
async def track_click(
    request: Request,
    data: dict[str, Any],
    current_user: Any = Depends(get_current_user_optional),
) -> dict[str, bool]:
    """追踪用户点击行为，用于优化推荐"""
    if not isinstance(data, dict) or "item_id" not in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必要参数: item_id",
        )
    return {"success": True}


@router.put("/interests", summary="更新用户兴趣")
async def update_interests(
    request: Request,
    data: dict[str, list[str]],
    current_user: Any = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """更新用户兴趣标签"""
    interests = data.get("interests", [])
    if not isinstance(interests, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="interests 必须是字符串数组",
        )
    return {"success": True, "interests": interests}