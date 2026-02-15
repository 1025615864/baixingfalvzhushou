"""律师匹配服务增强版测试

测试增强版律师推荐算法的各项功能
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.lawyer_matching_service_enhanced import (
    LawyerMatchingServiceEnhanced,
    LawyerMatchResultEnhanced,
    get_lawyer_matching_service_enhanced,
)


class TestLawyerMatchingServiceEnhanced:
    """律师匹配服务增强版测试"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return LawyerMatchingServiceEnhanced()

    @pytest.fixture
    def mock_lawyer(self):
        """创建模拟律师对象"""
        lawyer = Mock()
        lawyer.id = 1
        lawyer.name = "张律师"
        lawyer.specialties = "劳动纠纷,合同纠纷,婚姻家庭"
        lawyer.rating = 4.5
        lawyer.is_verified = True
        lawyer.is_active = True
        return lawyer

    @pytest.fixture
    def mock_db_session(self):
        """创建模拟数据库会话"""
        session = Mock(spec=AsyncSession)
        return session

    def test_calculate_profession_match_full_match(self, service):
        """测试专业领域完全匹配"""
        specialties = "劳动纠纷,合同纠纷,婚姻家庭"
        keywords = ["劳动纠纷", "合同纠纷"]
        domains = ["婚姻家庭"]

        score = service._calculate_profession_match(
            specialties, keywords, domains
        )

        # 2个关键词匹配: 2/2 * 0.6 = 0.6
        # 1个领域匹配: 1/1 * 0.4 = 0.4
        # 总分: 1.0
        assert score == 1.0

    def test_calculate_profession_match_partial_match(self, service):
        """测试专业领域部分匹配"""
        specialties = "劳动纠纷,合同纠纷"
        keywords = ["劳动纠纷", "婚姻纠纷"]
        domains = ["合同纠纷"]

        score = service._calculate_profession_match(
            specialties, keywords, domains
        )

        # 1个关键词匹配: 1/2 * 0.6 = 0.3
        # 1个领域匹配: 1/1 * 0.4 = 0.4
        # 总分: 0.7
        assert score == 0.7

    def test_calculate_profession_match_no_match(self, service):
        """测试专业领域无匹配"""
        specialties = "劳动纠纷,合同纠纷"
        keywords = ["房产纠纷", "刑事辩护"]
        domains = ["知识产权"]

        score = service._calculate_profession_match(
            specialties, keywords, domains
        )

        assert score == 0.0

    def test_calculate_profession_match_no_requirements(self, service):
        """测试无需求时返回1.0"""
        specialties = "劳动纠纷,合同纠纷"
        keywords = []
        domains = []

        score = service._calculate_profession_match(
            specialties, keywords, domains
        )

        assert score == 1.0

    def test_calculate_response_time_score(self, service):
        """测试响应速度评分"""
        # 测试不同完成数量和评分的组合

        # 高完成数量 + 高评分
        score1 = service._calculate_response_time_score(
            completed_count=100, rating=5.0
        )
        assert 70 <= score1 <= 100

        # 中等完成数量 + 中等评分
        score2 = service._calculate_response_time_score(
            completed_count=10, rating=4.0
        )
        assert 40 <= score2 <= 70

        # 低完成数量 + 低评分
        score3 = service._calculate_response_time_score(
            completed_count=1, rating=2.0
        )
        assert 0 <= score3 <= 40

        # 无完成记录 + 无评分
        score4 = service._calculate_response_time_score(
            completed_count=0, rating=0.0
        )
        assert score4 >= 0

    def test_calculate_case_similarity_high(self, service):
        """测试案例相似度高的情况"""
        specialties = "劳动纠纷,合同纠纷,婚姻家庭,交通事故"
        keywords = ["劳动纠纷", "合同纠纷"]

        score = service._calculate_case_similarity(
            specialties, keywords
        )

        # 2个关键词匹配: 2 * 10 = 20分
        assert score == 20.0

    def test_calculate_case_similarity_low(self, service):
        """测试案例相似度低的情况"""
        specialties = "劳动纠纷,合同纠纷"
        keywords = ["劳动纠纷"]

        score = service._calculate_case_similarity(
            specialties, keywords
        )

        # 1个关键词匹配: 1 * 10 = 10分
        assert score == 10.0

    def test_calculate_case_similarity_no_match(self, service):
        """测试案例无相似的情况"""
        specialties = "劳动纠纷,合同纠纷"
        keywords = ["房产纠纷", "刑事辩护"]

        score = service._calculate_case_similarity(
            specialties, keywords
        )

        assert score == 50.0  # 无匹配给中等分

    def test_calculate_cold_start_score(self, service):
        """测试冷启动评分"""
        # 完全匹配
        score1 = service._calculate_cold_start_score(
            profession_match=1.0
        )
        # 基础分65分的60% + 匹配分100分的40% = 39 + 40 = 79
        assert abs(score1 - 79.0) < 0.01

        # 部分匹配
        score2 = service._calculate_cold_start_score(
            profession_match=0.5
        )
        # 基础分65分的60% + 匹配分50分的40% = 39 + 20 = 59
        assert abs(score2 - 59.0) < 0.01

        # 无匹配
        score3 = service._calculate_cold_start_score(
            profession_match=0.0
        )
        # 基础分65分的60% + 匹配分0分的40% = 39 + 0 = 39
        assert abs(score3 - 39.0) < 0.01

    def test_generate_match_reasons_high_rating(self, service):
        """测试生成高分律师的匹配原因"""
        reasons = service._generate_match_reasons(
            specialties="劳动纠纷,合同纠纷",
            keywords=["劳动纠纷"],
            domains=["婚姻家庭"],
            rating=4.8,
            completed_count=100,
            response_time_score=90.0,
            case_similarity_score=80.0,
            is_cold_start=False,
        )

        assert any("高评分律师" in reason for reason in reasons)
        assert any("专长包含" in reason for reason in reasons)
        assert any("经验丰富" in reason for reason in reasons)
        assert any("响应迅速" in reason for reason in reasons)
        assert any("案例高度相似" in reason for reason in reasons)

    def test_generate_match_reasons_cold_start(self, service):
        """测试生成冷启动律师的匹配原因"""
        reasons = service._generate_match_reasons(
            specialties="劳动纠纷,合同纠纷",
            keywords=["劳动纠纷"],
            domains=[],
            rating=0.0,
            completed_count=0,
            response_time_score=0.0,
            case_similarity_score=0.0,
            is_cold_start=True,
        )

        assert any("新入驻律师" in reason for reason in reasons)
        assert any("专长包含" in reason for reason in reasons)
        # 不应该包含"经验丰富"等经验相关的原因
        assert not any("经验" in reason for reason in reasons)
        assert not any("高评分" in reason for reason in reasons)

    def test_sort_lawyers_by_score(self, service):
        """测试律师排序逻辑"""
        lawyers = [
            LawyerMatchResultEnhanced(
                lawyer_id=1, lawyer_name="律师1", specialties="劳动纠纷",
                rating=4.0, completed_count=50, match_score=0.8,
                response_time_score=60.0, case_similarity_score=50.0,
                overall_score=80.0, match_reasons=[], is_cold_start=False,
            ),
            LawyerMatchResultEnhanced(
                lawyer_id=2, lawyer_name="律师2", specialties="合同纠纷",
                rating=5.0, completed_count=100, match_score=0.9,
                response_time_score=80.0, case_similarity_score=70.0,
                overall_score=90.0, match_reasons=[], is_cold_start=False,
            ),
            LawyerMatchResultEnhanced(
                lawyer_id=3, lawyer_name="律师3", specialties="婚姻家庭",
                rating=0.0, completed_count=0, match_score=0.7,
                response_time_score=0.0, case_similarity_score=0.0,
                overall_score=70.0, match_reasons=[], is_cold_start=True,
            ),
            LawyerMatchResultEnhanced(
                lawyer_id=4, lawyer_name="律师4", specialties="刑事辩护",
                rating=4.5, completed_count=80, match_score=0.8,
                response_time_score=70.0, case_similarity_score=60.0,
                overall_score=80.0, match_reasons=[], is_cold_start=False,
            ),
        ]

        sorted_lawyers = service._sort_lawyers_by_score(lawyers)

        # 按综合分数降序
        # 同分数时，非冷启动优先，高评分优先
        assert sorted_lawyers[0].lawyer_id == 2  # 90分
        assert sorted_lawyers[1].lawyer_id == 4  # 80分, non-cold, 4.5
        assert sorted_lawyers[2].lawyer_id == 1  # 80分, non-cold, 4.0
        assert sorted_lawyers[3].lawyer_id == 3  # 70分, cold

    def test_generate_cache_key(self, service):
        """测试缓存键生成"""
        key1 = service._generate_cache_key(
            keywords=["劳动纠纷", "合同纠纷"],
            domains=["婚姻家庭"],
            limit=10,
            experiment_id="A",
        )

        key2 = service._generate_cache_key(
            keywords=["合同纠纷", "劳动纠纷"],  # 不同顺序
            domains=["婚姻家庭"],
            limit=10,
            experiment_id="A",
        )

        key3 = service._generate_cache_key(
            keywords=["劳动纠纷", "合同纠纷"],
            domains=["婚姻家庭"],
            limit=10,
            experiment_id="B",  # 不同实验ID
        )

        # 相同参数应该生成相同的键
        assert key1 == key2

        # 不同参数应该生成不同的键
        assert key1 != key3

    @pytest.mark.asyncio
    async def test_calculate_lawyer_match_normal(self, service, mock_lawyer, mock_db_session):
        """测试计算正常律师的匹配分数"""
        # 模拟数据库查询
        mock_execute_result = Mock()
        mock_execute_result.scalar.return_value = 50  # 完成数量
        mock_db_session.execute.return_value = mock_execute_result

        result = await service._calculate_lawyer_match(
            db=mock_db_session,
            lawyer=mock_lawyer,
            keywords=["劳动纠纷", "合同纠纷"],
            domains=["婚姻家庭"],
            experiment_id=None,
        )

        assert result.lawyer_id == 1
        assert result.lawyer_name == "张律师"
        assert result.rating == 4.5
        assert result.completed_count == 50
        assert result.match_score > 0  # 有匹配
        assert not result.is_cold_start  # 不是冷启动
        assert 0 <= result.overall_score <= 100  # 分数在合理范围
        assert len(result.match_reasons) > 0  # 有匹配原因

    @pytest.mark.asyncio
    async def test_calculate_lawyer_match_cold_start(self, service, mock_db_session):
        """测试计算冷启动律师的匹配分数"""
        # 创建冷启动律师
        lawyer = Mock()
        lawyer.id = 2
        lawyer.name = "李律师"
        lawyer.specialties = "劳动纠纷,合同纠纷"
        lawyer.rating = 0.0
        lawyer.is_verified = True
        lawyer.is_active = True

        # 模拟数据库查询
        mock_execute_result = Mock()
        mock_execute_result.scalar.return_value = 0  # 完成数量为0
        mock_db_session.execute.return_value = mock_execute_result

        result = await service._calculate_lawyer_match(
            db=mock_db_session,
            lawyer=lawyer,
            keywords=["劳动纠纷"],
            domains=[],
            experiment_id=None,
        )

        assert result.lawyer_id == 2
        assert result.rating == 0.0
        assert result.completed_count == 0
        assert result.is_cold_start  # 是冷启动
        # 冷启动基础分应该在65分左右
        assert 60 <= result.overall_score <= 80
        assert any("新入驻律师" in reason for reason in result.match_reasons)

    def test_weight_configuration(self, service):
        """测试评分权重配置"""
        # 验证权重总和为1.0
        total_weight = (
            service.WEIGHT_PROFESSION_MATCH +
            service.WEIGHT_USER_RATING +
            service.WEIGHT_RESPONSE_TIME +
            service.WEIGHT_CASE_SIMILARITY
        )
        assert abs(total_weight - 1.0) < 0.01

        # 验证各权重在合理范围
        assert 0 < service.WEIGHT_PROFESSION_MATCH <= 1.0
        assert 0 < service.WEIGHT_USER_RATING <= 1.0
        assert 0 < service.WEIGHT_RESPONSE_TIME <= 1.0
        assert 0 < service.WEIGHT_CASE_SIMILARITY <= 1.0

    def test_get_lawyer_matching_service_enhanced_singleton(self):
        """测试服务单例模式"""
        service1 = get_lawyer_matching_service_enhanced()
        service2 = get_lawyer_matching_service_enhanced()

        # 应该返回同一个实例
        assert service1 is service2
        assert isinstance(service1, LawyerMatchingServiceEnhanced)


class TestLawyerMatchingServiceIntegration:
    """律师匹配服务集成测试"""

    @pytest.mark.asyncio
    async def test_full_recommendation_flow(self):
        """测试完整的推荐流程"""
        # 注意：这是一个示例，实际集成测试需要真实的数据库连接
        # 这里只是展示测试结构

        service = LawyerMatchingServiceEnhanced()

        # 模拟数据库会话
        mock_session = Mock(spec=AsyncSession)

        # 由于这是集成测试的示例，我们跳过实际执行
        # 实际测试中，应该:
        # 1. 准备测试数据（律师、关键词等）
        # 2. 调用match_lawyers_by_keywords
        # 3. 验证返回结果
        # 4. 验证数据库查询
        # 5. 验证缓存操作

        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])