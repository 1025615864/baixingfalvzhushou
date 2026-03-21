"""法律文书商城测试

测试覆盖：
- 文书列表查询
- 文书价格计算（含会员折扣）
- 积分购买功能
- 收藏功能
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.legal_document_service import LegalDocumentService
from app.models.legal_document import (
    LegalDocument,
    LegalDocumentOrder,
    LegalDocumentFavorite,
)
from app.models.user import User
from app.services.membership_service import MembershipTier


@pytest.fixture
def document_service():
    """创建法律文书服务实例"""
    return LegalDocumentService()


@pytest.fixture
def mock_user():
    """创建模拟用户"""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    return user


@pytest.fixture
def mock_document():
    """创建模拟法律文书"""
    doc = MagicMock(spec=LegalDocument)
    doc.id = 1
    doc.name = "离婚协议书模板"
    doc.description = "标准离婚协议书模板"
    doc.content = "离婚协议书内容..."
    doc.category = "contract_marriage"
    doc.price = 100
    doc.points_required = 100
    doc.member_prices = {"annual": 80, "lifetime": 50}
    doc.is_active = True
    doc.is_free = False
    doc.is_featured = True
    doc.view_count = 100
    doc.download_count = 50
    doc.rating = 4.5
    doc.tags = "离婚，协议，婚姻"
    return doc


class TestLegalDocumentServiceCategories:
    """分类相关测试"""

    @pytest.mark.asyncio
    async def test_list_categories(self, document_service):
        """测试获取分类列表"""
        categories = await document_service.list_categories()
        
        assert len(categories) == 3  # 合同范本、法律文书、企业文书
        
        # 检查分组
        group_names = [cat["name"] for cat in categories]
        assert "合同范本" in group_names
        assert "法律文书" in group_names
        assert "企业文书" in group_names
        
        # 检查合同范本分类
        contract_group = next(c for c in categories if c["name"] == "合同范本")
        assert len(contract_group["categories"]) == 5


class TestLegalDocumentServiceGetDocuments:
    """文书列表查询测试"""

    @pytest.mark.asyncio
    async def test_get_documents_basic(self, document_service, db, mock_document):
        """测试基本文书列表查询"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_document]
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1
        
        db.execute = AsyncMock(side_effect=[mock_result, mock_count])
        
        result = await document_service.get_documents(db, page=1, page_size=20)
        
        assert result["total"] == 1
        assert result["page"] == 1
        assert result["page_size"] == 20
        assert len(result["items"]) == 1
        assert result["items"][0]["name"] == "离婚协议书模板"

    @pytest.mark.asyncio
    async def test_get_documents_by_category(self, document_service, db, mock_document):
        """测试按分类查询文书"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_document]
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1
        
        db.execute = AsyncMock(side_effect=[mock_result, mock_count])
        
        result = await document_service.get_documents(
            db, category="contract_marriage", page=1, page_size=20
        )
        
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_get_documents_by_keyword(self, document_service, db, mock_document):
        """测试按关键词查询文书"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_document]
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1
        
        db.execute = AsyncMock(side_effect=[mock_result, mock_count])
        
        result = await document_service.get_documents(
            db, keyword="离婚", page=1, page_size=20
        )
        
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_get_documents_featured(self, document_service, db, mock_document):
        """测试查询推荐文书"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_document]
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1
        
        db.execute = AsyncMock(side_effect=[mock_result, mock_count])
        
        result = await document_service.get_documents(
            db, is_featured=True, page=1, page_size=20
        )
        
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_get_documents_free(self, document_service, db, mock_document):
        """测试查询免费文书"""
        mock_document.is_free = True
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_document]
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1
        
        db.execute = AsyncMock(side_effect=[mock_result, mock_count])
        
        result = await document_service.get_documents(
            db, is_free=True, page=1, page_size=20
        )
        
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_get_documents_empty(self, document_service, db):
        """测试空结果"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        
        db.execute = AsyncMock(side_effect=[mock_result, mock_count])
        
        result = await document_service.get_documents(db, page=1, page_size=20)
        
        assert result["total"] == 0
        assert len(result["items"]) == 0


class TestLegalDocumentServiceGetDocument:
    """文书详情查询测试"""

    @pytest.mark.asyncio
    async def test_get_document_success(self, document_service, db, mock_document):
        """测试获取文书详情成功"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_document
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await document_service.get_document(db, document_id=1)
        
        assert result is not None
        assert result["name"] == "离婚协议书模板"
        assert mock_document.view_count == 101  # 浏览次数 +1

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, document_service, db):
        """测试获取不存在的文书"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await document_service.get_document(db, document_id=999)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_document_inactive(self, document_service, db, mock_document):
        """测试获取已下架文书"""
        mock_document.is_active = False
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_document
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await document_service.get_document(db, document_id=1)
        
        assert result is None


class TestLegalDocumentServiceCalculatePrice:
    """文书价格计算测试"""

    @pytest.mark.asyncio
    async def test_calculate_price_free_document(self, document_service, db, mock_document, mock_user):
        """测试免费文书价格计算"""
        mock_document.is_free = True
        
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = mock_document
        
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user
        
        db.execute = AsyncMock(side_effect=[mock_doc_result, mock_user_result])
        
        result = await document_service.calculate_price(db, document_id=1, user_id=1)
        
        assert result["price"] == 0
        assert result["original_price"] == 100
        assert result["discount"] == 100
        assert result["is_free"] is True
        assert result["payment_method"] == "free"

    @pytest.mark.asyncio
    async def test_calculate_price_free_user(self, document_service, db, mock_document, mock_user):
        """测试免费用户（未登录）价格计算"""
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = mock_document
        
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = None
        
        db.execute = AsyncMock(side_effect=[mock_doc_result, mock_user_result])
        
        result = await document_service.calculate_price(db, document_id=1, user_id=999)
        
        assert "error" in result
        assert result["error"] == "用户不存在"

    @pytest.mark.asyncio
    async def test_calculate_price_lifetime_member(self, document_service, db, mock_document, mock_user):
        """测试终身会员价格计算"""
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = mock_document
        
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user
        
        db.execute = AsyncMock(side_effect=[mock_doc_result, mock_user_result])
        
        with patch('app.services.legal_document_service.membership_service') as mock_membership:
            mock_membership.get_user_tier = AsyncMock(return_value=MembershipTier.LIFETIME.value)
            
            result = await document_service.calculate_price(db, document_id=1, user_id=1)
            
            assert result["price"] == 50  # 终身会员价
            assert result["original_price"] == 100
            assert result["discount"] == 50
            assert result["tier"] == MembershipTier.LIFETIME.value

    @pytest.mark.asyncio
    async def test_calculate_price_annual_member(self, document_service, db, mock_document, mock_user):
        """测试年度会员价格计算"""
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = mock_document
        
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user
        
        db.execute = AsyncMock(side_effect=[mock_doc_result, mock_user_result])
        
        with patch('app.services.legal_document_service.membership_service') as mock_membership:
            mock_membership.get_user_tier = AsyncMock(return_value=MembershipTier.ANNUAL.value)
            
            result = await document_service.calculate_price(db, document_id=1, user_id=1)
            
            assert result["price"] == 80  # 年度会员价
            assert result["original_price"] == 100
            assert result["discount"] == 20

    @pytest.mark.asyncio
    async def test_calculate_price_free_member(self, document_service, db, mock_document, mock_user):
        """测试会员免费文书价格计算"""
        # 设置会员免费价格
        mock_document.member_prices = {"lifetime": 0}
        
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = mock_document
        
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user
        
        db.execute = AsyncMock(side_effect=[mock_doc_result, mock_user_result])
        
        with patch('app.services.legal_document_service.membership_service') as mock_membership:
            mock_membership.get_user_tier = AsyncMock(return_value=MembershipTier.LIFETIME.value)
            
            result = await document_service.calculate_price(db, document_id=1, user_id=1)
            
            assert result["price"] == 0
            assert result["is_free"] is True
            assert result["payment_method"] == "member_free"

    @pytest.mark.asyncio
    async def test_calculate_price_no_member_discount(self, document_service, db, mock_document, mock_user):
        """测试非会员价格计算"""
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = mock_document
        
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user
        
        db.execute = AsyncMock(side_effect=[mock_doc_result, mock_user_result])
        
        with patch('app.services.legal_document_service.membership_service') as mock_membership:
            mock_membership.get_user_tier = AsyncMock(return_value=MembershipTier.FREE.value)
            
            result = await document_service.calculate_price(db, document_id=1, user_id=1)
            
            assert result["price"] == 100  # 原价
            assert result["original_price"] == 100
            assert result["discount"] == 0


class TestLegalDocumentServicePurchase:
    """文书购买测试"""

    @pytest.mark.asyncio
    async def test_purchase_document_not_found(self, document_service, db):
        """测试购买不存在的文书"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await document_service.purchase_document(db, document_id=999, user_id=1)
        
        assert result["success"] is False
        assert result["error"] == "文书不存在"

    @pytest.mark.asyncio
    async def test_purchase_document_inactive(self, document_service, db, mock_document):
        """测试购买已下架文书"""
        mock_document.is_active = False
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_document
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await document_service.purchase_document(db, document_id=1, user_id=1)
        
        assert result["success"] is False
        assert result["error"] == "文书已下架"

    @pytest.mark.asyncio
    async def test_purchase_document_already_purchased(self, document_service, db, mock_document):
        """测试重复购买"""
        mock_order = MagicMock(spec=LegalDocumentOrder)
        mock_order.id = 1
        
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = mock_document
        
        mock_order_result = MagicMock()
        mock_order_result.scalar_one_or_none.return_value = mock_order
        
        db.execute = AsyncMock(side_effect=[mock_doc_result, mock_order_result])
        
        result = await document_service.purchase_document(db, document_id=1, user_id=1)
        
        assert result["success"] is False
        assert result["error"] == "您已购买过此文书"

    @pytest.mark.asyncio
    async def test_purchase_document_free(self, document_service, db, mock_document):
        """测试免费文书购买"""
        mock_document.is_free = True
        
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = mock_document
        
        mock_order_result = MagicMock()
        mock_order_result.scalar_one_or_none.return_value = None
        
        db.execute = AsyncMock(side_effect=[mock_doc_result, mock_order_result])
        
        with patch.object(document_service, 'calculate_price', return_value={
            "price": 0,
            "original_price": 100,
            "discount": 100,
            "is_free": True,
            "payment_method": "free",
        }):
            result = await document_service.purchase_document(
                db, document_id=1, user_id=1, payment_method="free"
            )
        
        assert result["success"] is True
        assert "order_no" in result

    @pytest.mark.asyncio
    async def test_purchase_document_with_points(self, document_service, db, mock_document, mock_user):
        """测试积分购买"""
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = mock_document
        
        mock_order_result = MagicMock()
        mock_order_result.scalar_one_or_none.return_value = None
        
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user
        
        db.execute = AsyncMock(side_effect=[mock_doc_result, mock_order_result, mock_user_result])
        
        with patch.object(document_service, 'calculate_price', return_value={
            "price": 100,
            "original_price": 100,
            "discount": 0,
            "is_free": False,
            "payment_method": "points",
        }):
            with patch('app.services.legal_document_service.get_points_service') as mock_points_factory:
                mock_points_service = MagicMock()
                mock_points_service.get_balance = MagicMock(return_value=200)
                mock_points_service.redeem_points = AsyncMock(return_value=(True, None))
                mock_points_factory.return_value = mock_points_service
                
                result = await document_service.purchase_document(
                    db, document_id=1, user_id=1, payment_method="points"
                )
        
        assert result["success"] is True
        assert "order_no" in result

    @pytest.mark.asyncio
    async def test_purchase_document_insufficient_points(self, document_service, db, mock_document, mock_user):
        """测试积分不足"""
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = mock_document
        
        mock_order_result = MagicMock()
        mock_order_result.scalar_one_or_none.return_value = None
        
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = mock_user
        
        db.execute = AsyncMock(side_effect=[mock_doc_result, mock_order_result, mock_user_result])
        
        with patch.object(document_service, 'calculate_price', return_value={
            "price": 100,
            "original_price": 100,
            "discount": 0,
            "is_free": False,
            "payment_method": "points",
        }):
            with patch('app.services.legal_document_service.get_points_service') as mock_points_factory:
                mock_points_service = MagicMock()
                mock_points_service.get_balance = MagicMock(return_value=50)  # 积分不足
                mock_points_factory.return_value = mock_points_service
                
                result = await document_service.purchase_document(
                    db, document_id=1, user_id=1, payment_method="points"
                )
        
        assert result["success"] is False
        assert "积分不足" in result["error"]


class TestLegalDocumentServiceFavorites:
    """收藏功能测试"""

    @pytest.mark.asyncio
    async def test_add_favorite_success(self, document_service, db):
        """测试添加收藏成功"""
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = MagicMock()
        
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None
        
        db.execute = AsyncMock(side_effect=[mock_doc_result, mock_existing_result])
        
        result = await document_service.add_favorite(db, user_id=1, document_id=1)
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_add_favorite_document_not_found(self, document_service, db):
        """测试收藏不存在的文书"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await document_service.add_favorite(db, user_id=1, document_id=999)
        
        assert result["success"] is False
        assert result["error"] == "文书不存在"

    @pytest.mark.asyncio
    async def test_add_favorite_already_exists(self, document_service, db):
        """测试重复收藏"""
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = MagicMock()
        
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = MagicMock()
        
        db.execute = AsyncMock(side_effect=[mock_doc_result, mock_existing_result])
        
        result = await document_service.add_favorite(db, user_id=1, document_id=1)
        
        assert result["success"] is True
        assert result["message"] == "已收藏"

    @pytest.mark.asyncio
    async def test_remove_favorite_success(self, document_service, db):
        """测试取消收藏成功"""
        mock_favorite = MagicMock(spec=LegalDocumentFavorite)
        mock_favorite.id = 1
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_favorite
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await document_service.remove_favorite(db, user_id=1, document_id=1)
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_remove_favorite_not_found(self, document_service, db):
        """测试取消不存在的收藏"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await document_service.remove_favorite(db, user_id=1, document_id=1)
        
        assert result["success"] is False
        assert result["error"] == "未收藏"

    @pytest.mark.asyncio
    async def test_get_user_favorites(self, document_service, db, mock_document):
        """测试获取用户收藏列表"""
        mock_favorite = MagicMock(spec=LegalDocumentFavorite)
        mock_favorite.document_id = 1
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_favorite]
        
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = mock_document
        
        db.execute = AsyncMock(side_effect=[mock_result, mock_doc_result])
        
        result = await document_service.get_user_favorites(db, user_id=1)
        
        assert len(result) == 1
        assert result[0]["name"] == "离婚协议书模板"

    @pytest.mark.asyncio
    async def test_is_favorited_true(self, document_service, db):
        """测试检查已收藏"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await document_service.is_favorited(db, user_id=1, document_id=1)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_is_favorited_false(self, document_service, db):
        """测试检查未收藏"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await document_service.is_favorited(db, user_id=1, document_id=1)
        
        assert result is False


class TestLegalDocumentServiceUserOrders:
    """用户订单测试"""

    @pytest.mark.asyncio
    async def test_get_user_orders(self, document_service, db, mock_document):
        """测试获取用户购买记录"""
        mock_order = MagicMock(spec=LegalDocumentOrder)
        mock_order.order_no = "LD1234567890"
        mock_order.document_id = 1
        mock_order.points_spent = 100
        mock_order.payment_method = "points"
        mock_order.completed_at = datetime.now(timezone.utc)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_order]
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1
        
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = mock_document
        
        db.execute = AsyncMock(side_effect=[mock_result, mock_count, mock_doc_result])
        
        result = await document_service.get_user_orders(db, user_id=1, page=1, page_size=20)
        
        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0]["order_no"] == "LD1234567890"
        assert result["items"][0]["document_name"] == "离婚协议书模板"

    @pytest.mark.asyncio
    async def test_get_user_orders_empty(self, document_service, db):
        """测试空订单列表"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        
        db.execute = AsyncMock(side_effect=[mock_result, mock_count])
        
        result = await document_service.get_user_orders(db, user_id=1, page=1, page_size=20)
        
        assert result["total"] == 0
        assert len(result["items"]) == 0

    @pytest.mark.asyncio
    async def test_is_purchased_true(self, document_service, db):
        """测试检查已购买"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await document_service.is_purchased(db, user_id=1, document_id=1)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_is_purchased_false(self, document_service, db):
        """测试检查未购买"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await document_service.is_purchased(db, user_id=1, document_id=1)
        
        assert result is False


class TestLegalDocumentServiceGetContent:
    """获取文书内容测试"""

    @pytest.mark.asyncio
    async def test_get_document_content_success(self, document_service, db, mock_document):
        """测试获取文书内容成功"""
        mock_order = MagicMock(spec=LegalDocumentOrder)
        mock_order.order_no = "LD1234567890"
        mock_order.status = "completed"
        mock_order.completed_at = datetime.now(timezone.utc)
        
        mock_order_result = MagicMock()
        mock_order_result.scalar_one_or_none.return_value = mock_order
        
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = mock_document
        
        db.execute = AsyncMock(side_effect=[mock_order_result, mock_doc_result])
        
        result = await document_service.get_document_content(db, document_id=1, user_id=1)
        
        assert result is not None
        assert result["id"] == 1
        assert result["content"] == "离婚协议书内容..."
        assert result["order_no"] == "LD1234567890"

    @pytest.mark.asyncio
    async def test_get_document_content_not_purchased(self, document_service, db):
        """测试获取未购买文书内容"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        
        result = await document_service.get_document_content(db, document_id=1, user_id=1)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_document_content_document_not_found(self, document_service, db):
        """测试获取不存在的文书内容"""
        mock_order = MagicMock(spec=LegalDocumentOrder)
        mock_order.status = "completed"
        
        mock_order_result = MagicMock()
        mock_order_result.scalar_one_or_none.return_value = mock_order
        
        mock_doc_result = MagicMock()
        mock_doc_result.scalar_one_or_none.return_value = None
        
        db.execute = AsyncMock(side_effect=[mock_order_result, mock_doc_result])
        
        result = await document_service.get_document_content(db, document_id=1, user_id=1)
        
        assert result is None