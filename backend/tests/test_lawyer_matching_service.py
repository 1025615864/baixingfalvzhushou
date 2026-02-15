"""律师匹配服务测试"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.lawyer_matching_service import (
    LawyerMatchingService,
    get_lawyer_matching_service,
)
from app.models.lawfirm import Lawyer


class TestLawyerMatchingServiceCore:
    """律师匹配服务核心逻辑测试"""

    @pytest.fixture
    def service(self):
        return LawyerMatchingService()

    @pytest.fixture
    def mock_db(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_lawyer(self):
        lawyer = MagicMock(spec=Lawyer)
        lawyer.id = 1
        lawyer.name = "张律师"
        lawyer.specialties = "劳动 合同 争议"
        lawyer.rating = 4.8
        lawyer.is_verified = True
        lawyer.is_active = True
        return lawyer

    def test_calculate_specialty_match_no_specialties(self, service):
        score = service._calculate_specialty_match("", ["劳动"], ["合同"])
        assert score == 0.0

    def test_calculate_specialty_match_keywords_and_domains(self, service):
        score = service._calculate_specialty_match(
            "劳动 合同 争议",
            ["劳动", "合同"],
            ["劳动"],
        )
        assert score == 1.0

    def test_calculate_specialty_match_domains_only(self, service):
        score = service._calculate_specialty_match("劳动法", [], ["劳动"])
        assert score == 0.4

    def test_calculate_overall_score(self, service):
        score = service._calculate_overall_score(1.0, 5.0, 0)
        assert score == 80.0

    def test_calculate_overall_score_with_completed(self, service):
        score = service._calculate_overall_score(0.5, 0.0, 99)
        assert score == 35.0

    def test_generate_match_reasons(self, service):
        reasons = service._generate_match_reasons(
            specialties="劳动 合同 争议",
            keywords=["劳动", "合同", "仲裁", "赔偿"],
            domains=["劳动"],
            rating=4.6,
            completed_count=120,
        )
        assert any("专长包含" in r for r in reasons)
        assert any("擅长领域" in r for r in reasons)
        assert any("高评分律师" in r for r in reasons)
        assert any("经验丰富" in r for r in reasons)

    @pytest.mark.asyncio
    async def test_calculate_lawyer_match(self, service, mock_db, mock_lawyer):
        mock_count = MagicMock()
        mock_count.scalar.return_value = 10
        mock_db.execute = AsyncMock(return_value=mock_count)

        result = await service._calculate_lawyer_match(
            mock_db,
            mock_lawyer,
            keywords=["劳动"],
            domains=["合同"],
        )

        assert result.lawyer_id == 1
        assert result.match_score > 0
        assert result.overall_score > 0
        assert "劳动" in result.specialties

    @pytest.mark.asyncio
    async def test_match_lawyers_by_keywords_empty(self, service, mock_db):
        result = await service.match_lawyers_by_keywords(mock_db, [], [])
        assert result == []

    @pytest.mark.asyncio
    async def test_match_lawyers_by_keywords_filters(self, service, mock_db):
        lawyer_a = MagicMock(spec=Lawyer)
        lawyer_a.id = 1
        lawyer_a.name = "张律师"
        lawyer_a.specialties = "劳动 合同"
        lawyer_a.rating = 4.7
        lawyer_a.is_verified = True
        lawyer_a.is_active = True

        lawyer_b = MagicMock(spec=Lawyer)
        lawyer_b.id = 2
        lawyer_b.name = "李律师"
        lawyer_b.specialties = ""
        lawyer_b.rating = 4.9
        lawyer_b.is_verified = True
        lawyer_b.is_active = True

        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [lawyer_a, lawyer_b]

        count_a = MagicMock()
        count_a.scalar.return_value = 30
        count_b = MagicMock()
        count_b.scalar.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[list_result, count_a, count_b])

        results = await service.match_lawyers_by_keywords(
            mock_db,
            keywords=["劳动"],
            domains=["合同"],
            limit=5,
        )

        assert len(results) == 1
        assert results[0].lawyer_name == "张律师"

    @pytest.mark.asyncio
    async def test_recommend_lawyers(self, service, mock_db):
        service.keyword_service = MagicMock()
        service.keyword_service.extract_with_confidence.return_value = {
            "keywords": ["劳动"],
            "domains": ["合同"],
        }
        service.match_lawyers_by_keywords = AsyncMock(return_value=[MagicMock()])

        result = await service.recommend_lawyers(mock_db, "劳动纠纷", limit=3)

        assert len(result) == 1
        service.match_lawyers_by_keywords.assert_awaited_once()


class TestLawyerMatchingServiceSingleton:
    def test_get_lawyer_matching_service_singleton(self):
        service1 = get_lawyer_matching_service()
        service2 = get_lawyer_matching_service()
        assert service1 is service2
