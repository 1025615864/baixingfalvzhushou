import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.lawyer_share_card_service import LawyerShareCardService
from app.models.lawfirm import Lawyer, LawFirm
from app.models.user import User

class TestLawyerShareCardService:
    @pytest.fixture
    def mock_db(self):
        return AsyncMock(spec=AsyncSession)

    def test_get_template_colors(self):
        # Test simple template
        colors_simple = LawyerShareCardService._get_template_colors("simple")
        assert colors_simple["primary"] == (59, 130, 246)
        
        # Test default fallback
        colors_unknown = LawyerShareCardService._get_template_colors("unknown")
        assert colors_unknown == colors_simple

        # Test professional template
        colors_prof = LawyerShareCardService._get_template_colors("professional")
        assert colors_prof["background"] == (30, 41, 59)

    def test_wrap_text(self):
        # Mock font
        font = MagicMock()
        # Mock getbbox to return a width based on string length (simplified)
        # width = bbox[2] - bbox[0]
        # let's assume each char is 10px
        def getbbox(text):
            width = len(text) * 10
            return (0, 0, width, 10)
        font.getbbox.side_effect = getbbox

        text = "Hello World Test"
        # wrap at 60px (6 chars)
        # Hello (50) -> OK
        # Hello World (110) -> exceeds
        lines = LawyerShareCardService._wrap_text(text, font, max_width=60)
        
        # Expected: "Hello ", "World ", "Test"
        # "Hello ": 60px <= 60
        # "World ": 60px <= 60
        # "Test": 40px <= 60
        
        # If the code adds trailing space to width calculation, it might be tricky.
        # Code: test_line = current_line + word + " "
        # "Hello ": length 6 -> width 60
        # "Hello World ": length 12 -> width 120 > 60 -> wrap
        # New line: "World " -> length 6 -> width 60
        # "World Test ": length 11 -> width 110 > 60 -> wrap
        # New line: "Test " -> length 5 -> width 50
        
        assert len(lines) >= 3
        assert "Hello" in lines[0]

    @pytest.mark.asyncio
    async def test_generate_card_success(self, mock_db):
        # Mock DB data
        lawyer = Lawyer(
            id=1, name="张律师", firm_id=1, user_id=1,
            title="高级律师", rating=4.8, specialties="民法,刑法",
            experience_years=10, case_count=100, review_count=50
        )
        firm = LawFirm(id=1, name="测试律所")
        user = User(id=1)

        # Configure mock_db locally to filter queries.
        # But `db.execute` returns a Result object which has scalars strategy
        # Simplified: Use side_effect to return different results based on query?
        # Or just return a Mock that yields these in sequence if the order is deterministic.
        
        # Queries order: Lawyer, LawFirm (if firm_id), User
        result_lawyer = MagicMock()
        result_lawyer.scalar_one_or_none.return_value = lawyer
        
        result_firm = MagicMock()
        result_firm.scalar_one_or_none.return_value = firm
        
        result_user = MagicMock()
        result_user.scalar_one_or_none.return_value = user

        mock_db.execute.side_effect = [result_lawyer, result_firm, result_user]

        # Call generate_card
        image_bytes = await LawyerShareCardService.generate_card(mock_db, lawyer_id=1)

        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0
        # Check PNG signature
        assert image_bytes.startswith(b'\x89PNG\r\n\x1a\n')

    @pytest.mark.asyncio
    async def test_generate_card_lawyer_not_found(self, mock_db):
        result_lawyer = MagicMock()
        result_lawyer.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = result_lawyer

        with pytest.raises(ValueError, match="律师不存在"):
            await LawyerShareCardService.generate_card(mock_db, lawyer_id=999)

    @pytest.mark.asyncio
    async def test_get_card_url(self, mock_db):
        url = await LawyerShareCardService.get_card_url(mock_db, lawyer_id=1, template="elegant")
        assert "/api/lawyer/1/share-card?template=elegant" in url

    @pytest.mark.asyncio
    async def test_generate_card_professional_template(self, mock_db):
        """测试专业模板的卡片生成"""
        lawyer = Lawyer(
            id=2, name="李律师", firm_id=2, user_id=2,
            title="资深律师", rating=4.9, specialties="商法,经济法",
            experience_years=15, case_count=200, review_count=100
        )
        firm = LawFirm(id=2, name="专业律所")
        user = User(id=2)

        result_lawyer = MagicMock()
        result_lawyer.scalar_one_or_none.return_value = lawyer
        
        result_firm = MagicMock()
        result_firm.scalar_one_or_none.return_value = firm
        
        result_user = MagicMock()
        result_user.scalar_one_or_none.return_value = user

        mock_db.execute.side_effect = [result_lawyer, result_firm, result_user]

        # 使用 professional 模板
        image_bytes = await LawyerShareCardService.generate_card(
            mock_db, lawyer_id=2, template="professional"
        )

        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0
        assert image_bytes.startswith(b'\x89PNG\r\n\x1a\n')

    @pytest.mark.asyncio
    async def test_generate_card_elegant_template(self, mock_db):
        """测试优雅模板的卡片生成"""
        lawyer = Lawyer(
            id=3, name="王律师", firm_id=3, user_id=3,
            title="首席律师", rating=5.0, specialties="知识产权,涉外法律",
            experience_years=20, case_count=300, review_count=150
        )
        firm = LawFirm(id=3, name="优雅律所")
        user = User(id=3)

        result_lawyer = MagicMock()
        result_lawyer.scalar_one_or_none.return_value = lawyer
        
        result_firm = MagicMock()
        result_firm.scalar_one_or_none.return_value = firm
        
        result_user = MagicMock()
        result_user.scalar_one_or_none.return_value = user

        mock_db.execute.side_effect = [result_lawyer, result_firm, result_user]

        # 使用 elegant 模板
        image_bytes = await LawyerShareCardService.generate_card(
            mock_db, lawyer_id=3, template="elegant"
        )

        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0
        assert image_bytes.startswith(b'\x89PNG\r\n\x1a\n')

    @pytest.mark.asyncio
    async def test_generate_card_font_fallback(self, mock_db):
        """测试字体加载失败时的回退处理"""
        lawyer = Lawyer(
            id=4, name="赵律师", firm_id=None, user_id=4,
            title="律师", rating=4.5, specialties="劳动法",
            experience_years=5, case_count=50, review_count=25
        )
        user = User(id=4)

        result_lawyer = MagicMock()
        result_lawyer.scalar_one_or_none.return_value = lawyer
        
        result_user = MagicMock()
        result_user.scalar_one_or_none.return_value = user

        mock_db.execute.side_effect = [result_lawyer, result_user]

        # Mock ImageFont.truetype 抛出异常，但 load_default 能正常工作
        original_truetype = ImageFont.truetype
        original_load_default = ImageFont.load_default
        
        def mock_truetype(*args, **kwargs):
            # 只有当参数是系统字体路径时才抛异常
            if args and isinstance(args[0], str) and args[0].endswith('.ttc'):
                raise Exception("Font not found")
            # 其他情况（如load_default内部调用）使用原始函数
            return original_truetype(*args, **kwargs)
        
        with patch('PIL.ImageFont.truetype', side_effect=mock_truetype):
            with patch('PIL.ImageFont.load_default', return_value=original_load_default()):
                image_bytes = await LawyerShareCardService.generate_card(
                    mock_db, lawyer_id=4, template="simple"
                )

                assert isinstance(image_bytes, bytes)
                assert len(image_bytes) > 0
                assert image_bytes.startswith(b'\x89PNG\r\n\x1a\n')
