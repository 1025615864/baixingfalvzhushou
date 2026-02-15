"""
AI知识库管理高级测试

测试覆盖：
- LegalKnowledgeBase公共方法
- 文档添加功能
- 搜索功能
- 质量控制搜索
- 边界条件和错误处理
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import cast
from app.services.ai.knowledge_base import LegalKnowledgeBase


class TestLegalKnowledgeBaseInitialization:
    """LegalKnowledgeBase初始化测试类"""

    def test_init_default_values(self):
        """测试默认初始化值"""
        # Act
        kb = LegalKnowledgeBase()
        
        # Assert
        assert kb.embeddings is None
        assert kb.vector_store is None
        assert kb.text_splitter is not None
        assert kb._initialized is False
        assert kb.RELEVANCE_THRESHOLD == 0.5
        assert kb.MIN_REFERENCES == 1
        assert kb.MAX_REFERENCES == 5

    def test_initialize_without_api_key(self):
        """测试没有API键时的初始化"""
        # Arrange
        kb = LegalKnowledgeBase()
        
        with patch('app.services.ai.knowledge_base.get_settings') as mock_settings:
            settings = MagicMock()
            settings.openai_api_key = None
            settings.openai_base_url = None
            settings.chroma_persist_dir = "/tmp/test"
            mock_settings.return_value = settings
            
            # Act
            kb.initialize()
            
            # Assert
            assert kb._initialized is True
            assert kb.embeddings is None
            assert kb.vector_store is None

    def test_initialize_with_api_key(self):
        """测试有API键时的初始化"""
        # Arrange
        kb = LegalKnowledgeBase()
        
        with patch('app.services.ai.knowledge_base.settings') as mock_settings:
            with patch('app.services.ai.knowledge_base.OpenAIEmbeddings') as mock_embeddings:
                with patch('app.services.ai.knowledge_base.Chroma') as mock_chroma:
                    mock_settings.openai_api_key = "test-key"
                    mock_settings.openai_base_url = "https://api.openai.com/v1"
                    mock_settings.chroma_persist_dir = "/tmp/test"
                    kb._initialized = False  # 重置initialized flag
                    
                    # Act
                    kb.initialize()
                    
                    # Assert
                    assert kb._initialized is True
                    # 验证是否被调用
                    assert mock_embeddings.called or mock_chroma.called

    def test_initialize_idempotent(self):
        """测试初始化的幂等性"""
        # Arrange
        kb = LegalKnowledgeBase()
        
        # Act - 初始化两次
        kb.initialize()
        kb.initialize()
        
        # Assert - 第二次应该不执行任何操作
        assert kb._initialized is True


class TestLegalKnowledgeBaseAddDocuments:
    """LegalKnowledgeBase文档添加测试类"""

    @pytest.fixture
    def mock_kb(self):
        """创建带有mock vector_store的知识库"""
        kb = LegalKnowledgeBase()
        kb.initialize()
        
        # Mock vector_store
        kb.vector_store = MagicMock()
        kb.vector_store.add_texts = MagicMock()
        
        return kb

    def test_add_law_documents_empty_list(self, mock_kb):
        """测试添加空文档列表"""
        # Act
        mock_kb.add_law_documents([])
        
        # Assert - 不应该调用add_texts
        mock_kb.vector_store.add_texts.assert_not_called()

    def test_add_law_documents_single_document(self, mock_kb):
        """测试添加单个文档"""
        # Arrange
        documents = [
            {
                "law_name": "测试法",
                "article": "第一条",
                "content": "这是测试内容",
                "source": "test_source",
                "source_url": "http://test.url",
                "source_version": "v1",
                "source_hash": "abc123",
                "ingest_batch_id": "batch001",
                "knowledge_id": "kb001"
            }
        ]
        
        # Act
        mock_kb.add_law_documents(documents)
        
        # Assert
        mock_kb.vector_store.add_texts.assert_called_once()
        call_args = mock_kb.vector_store.add_texts.call_args
        texts = call_args.kwargs['texts']
        metadatas = call_args.kwargs['metadatas']
        
        assert len(texts) == 1
        assert "【测试法】第一条" in texts[0]
        assert "这是测试内容" in texts[0]
        
        assert len(metadatas) == 1
        assert metadatas[0]["law_name"] == "测试法"
        assert metadatas[0]["article"] == "第一条"
        assert metadatas[0]["source"] == "test_source"

    def test_add_law_documents_multiple_documents(self, mock_kb):
        """测试添加多个文档"""
        # Arrange
        documents = [
            {
                "law_name": "法律A",
                "article": "第一条",
                "content": "内容A"
            },
            {
                "law_name": "法律B",
                "article": "第二条",
                "content": "内容B"
            }
        ]
        
        # Act
        mock_kb.add_law_documents(documents)
        
        # Assert
        call_args = mock_kb.vector_store.add_texts.call_args
        texts = call_args.kwargs['texts']
        metadatas = call_args.kwargs['metadatas']
        
        assert len(texts) == 2
        assert "【法律A】第一条" in texts[0]
        assert "【法律B】第二条" in texts[1]

    def test_add_law_documents_missing_fields(self, mock_kb):
        """测试文档缺少字段时的处理"""
        # Arrange
        documents = [
            {
                "law_name": "测试法",
                "content": "内容"
                # 缺少article, source等字段
            }
        ]
        
        # Act
        mock_kb.add_law_documents(documents)
        
        # Assert - 应该成功处理，缺失字段使用默认值
        call_args = mock_kb.vector_store.add_texts.call_args
        metadatas = call_args.kwargs['metadatas']
        
        assert len(metadatas) == 1
        assert metadatas[0]["law_name"] == "测试法"
        assert metadatas[0]["article"] == ""
        assert metadatas[0]["source"] == ""

    def test_add_law_documents_without_vector_store(self):
        """测试没有vector_store时添加文档"""
        # Arrange
        kb = LegalKnowledgeBase()
        kb._initialized = False
        
        with patch.object(kb, 'initialize') as mock_init:
            documents = [{"law_name": "测试法", "article": "第一条", "content": "内容"}]
            
            # Act
            kb.add_law_documents(documents)
            
            # Assert - 应该调用initialize
            mock_init.assert_called_once()

    def test_add_law_documents_text_format(self, mock_kb):
        """测试文档文本格式"""
        # Arrange
        documents = [
            {
                "law_name": "劳动法",
                "article": "第10条",
                "content": "内容描述"
            }
        ]
        
        # Act
        mock_kb.add_law_documents(documents)
        
        # Assert
        call_args = mock_kb.vector_store.add_texts.call_args
        texts = call_args.kwargs['texts']
        
        assert "【劳动法】第10条" in texts[0]
        assert "内容描述" in texts[0]
        assert "\n" in texts[0]


class TestLegalKnowledgeBaseSearch:
    """LegalKnowledgeBase搜索测试类"""

    @pytest.fixture
    def mock_kb_with_results(self):
        """创建带有mock搜索结果的知识库"""
        kb = LegalKnowledgeBase()
        kb.initialize()
        
        # Mock vector_store and search results
        kb.vector_store = MagicMock()
        
        # 创建mock文档对象
        mock_doc1 = MagicMock()
        mock_doc1.page_content = "劳动法第一条内容"
        mock_doc1.metadata = {"law_name": "劳动法", "article": "第1条"}
        
        mock_doc2 = MagicMock()
        mock_doc2.page_content = "劳动法第二条内容"
        mock_doc2.metadata = {"law_name": "劳动法", "article": "第2条"}
        
        kb.vector_store.similarity_search_with_score = MagicMock(
            return_value=[(mock_doc1, 0.1), (mock_doc2, 0.2)]
        )
        
        return kb

    def test_search_without_vector_store(self):
        """测试没有vector_store时的搜索"""
        # Arrange
        kb = LegalKnowledgeBase()
        kb._initialized = False
        
        # Act
        results = kb.search("劳动纠纷", k=5)
        
        # Assert
        assert results == []

    def test_search_default_k(self, mock_kb_with_results):
        """测试使用默认k值搜索"""
        # Act
        results = mock_kb_with_results.search("劳动纠纷")
        
        # Assert
        assert len(results) == 2
        assert "劳动法第一条内容" in results[0][0]
        assert "劳动法第二条内容" in results[1][0]

    def test_search_custom_k(self, mock_kb_with_results):
        """测试使用自定义k值搜索"""
        # Arrange
        mock_kb_with_results.vector_store.similarity_search_with_score = MagicMock(
            return_value=[(MagicMock(page_content="内容1", metadata={}), 0.1)]
        )
        
        # Act
        results = mock_kb_with_results.search("查询", k=1)
        
        # Assert
        assert len(results) == 1

    def test_search_score_to_similarity_zero(self, mock_kb_with_results):
        """测试score为0时的相似度转换"""
        # Arrange
        mock_kb_with_results.vector_store.similarity_search_with_score = MagicMock(
            return_value=[(MagicMock(page_content="内容", metadata={}), 0.0)]
        )
        
        # Act
        results = mock_kb_with_results.search("查询")
        
        # Assert
        assert results[0][2] == 1.0  # score=0, similarity=1.0

    def test_search_score_to_similarity_one(self, mock_kb_with_results):
        """测试score为1时的相似度转换"""
        # Arrange
        mock_kb_with_results.vector_store.similarity_search_with_score = MagicMock(
            return_value=[(MagicMock(page_content="内容", metadata={}), 1.0)]
        )
        
        # Act
        results = mock_kb_with_results.search("查询")
        
        # Assert
        assert results[0][2] == 0.0  # score=1, similarity=0.0

    def test_search_score_to_similarity_greater_than_one(self, mock_kb_with_results):
        """测试score大于1时的相似度转换"""
        # Arrange
        mock_kb_with_results.vector_store.similarity_search_with_score = MagicMock(
            return_value=[(MagicMock(page_content="内容", metadata={}), 2.0)]
        )
        
        # Act
        results = mock_kb_with_results.search("查询")
        
        # Assert - score=2, similarity=1/(1+2)=0.333
        assert abs(results[0][2] - 1.0/3.0) < 0.001

    def test_search_exception_handling(self):
        """测试搜索异常处理"""
        # Arrange
        kb = LegalKnowledgeBase()
        kb.vector_store = MagicMock()
        kb.vector_store.similarity_search_with_score = MagicMock(
            side_effect=Exception("搜索失败")
        )
        
        # Act
        results = kb.search("查询")
        
        # Assert - 应该返回空列表
        assert results == []

    def test_search_metadata_handling(self, mock_kb_with_results):
        """测试元数据处理"""
        # Act
        results = mock_kb_with_results.search("查询")
        
        # Assert
        assert isinstance(results[0][1], dict)
        assert results[0][1]["law_name"] == "劳动法"
        assert results[0][1]["article"] == "第1条"


class TestLegalKnowledgeBaseQualityControl:
    """LegalKnowledgeBase质量控制搜索测试类"""

    @pytest.fixture
    def mock_kb_for_quality(self):
        """创建用于质量测试的知识库"""
        kb = LegalKnowledgeBase()
        kb.initialize()
        kb.vector_store = MagicMock()
        
        # 创建不同相似度的结果
        mock_results = []
        for i, score in enumerate([0.3, 0.5, 0.7, 0.8, 0.9]):
            mock_doc = MagicMock()
            mock_doc.page_content = f"内容{i}"
            mock_doc.metadata = {"id": f"doc{i}"}
            mock_results.append((mock_doc, score))
        
        kb.vector_store.similarity_search_with_score = MagicMock(
            return_value=mock_results
        )
        
        return kb

    def test_search_with_quality_control_default_threshold(self, mock_kb_for_quality):
        """测试使用默认阈值的质量控制搜索"""
        # Act
        results, quality = mock_kb_for_quality.search_with_quality_control("查询")
        
        # Assert - 默认阈值是0.5
        assert len(results) <= 5  # MAX_REFERENCES
        assert all(r[2] >= 0.5 for r in results)  # 应该只包含>=0.5的结果
        assert quality.total_candidates == 5
        assert quality.qualified_count <= 5

    def test_search_with_quality_control_custom_threshold(self, mock_kb_for_quality):
        """测试使用自定义阈值的质量控制搜索"""
        # Act
        results, quality = mock_kb_for_quality.search_with_quality_control("查询", threshold=0.7)
        
        # Assert - 阈值0.7
        assert all(r[2] >= 0.7 for r in results)
        assert quality.qualified_count <= 2  # 只有0.7和0.8符合

    def test_search_with_quality_control_k_parameter(self, mock_kb_for_quality):
        """测试k参数限制返回结果"""
        # Act
        results, quality = mock_kb_for_quality.search_with_quality_control("查询", k=3)
        
        # Assert - k=3但fixture返回5个，total_candidates应该是5
        assert quality.total_candidates == 5
        assert len(results) <= 3

    def test_search_with_quality_control_high_confidence(self, mock_kb_for_quality):
        """测试高置信度计算"""
        # Arrange - 让搜索返回高相似度结果
        mock_results_high = [
            (MagicMock(page_content="内容1", metadata={}), 0.1),
            (MagicMock(page_content="内容2", metadata={}), 0.2)
        ]
        mock_kb_for_quality.vector_store.similarity_search_with_score = MagicMock(
            return_value=mock_results_high
        )
        
        # Act
        results, quality = mock_kb_for_quality.search_with_quality_control("查询")
        
        # Assert - 应该返回high或medium
        assert quality.confidence in ["high", "medium"]

    def test_search_with_quality_control_no_results(self, mock_kb_for_quality):
        """测试没有结果时的质量控制"""
        # Arrange
        mock_kb_for_quality.vector_store.similarity_search_with_score = MagicMock(
            return_value=[]
        )
        
        # Act
        results, quality = mock_kb_for_quality.search_with_quality_control("查询")
        
        # Assert
        assert results == []
        assert quality.total_candidates == 0
        assert quality.qualified_count == 0
        assert quality.avg_similarity == 0.0
        assert quality.confidence == "low"

    def test_search_with_quality_control_max_references_limit(self, mock_kb_for_quality):
        """测试MAX_REFERENCES限制"""
        # Arrange - 返回超过MAX_REFERENCES(5)的高相似度结果
        many_results = []
        for i in range(10):
            mock_doc = MagicMock()
            mock_doc.page_content = f"内容{i}"
            mock_doc.metadata = {}
            many_results.append((mock_doc, 0.1))  # 高相似度
        
        mock_kb_for_quality.vector_store.similarity_search_with_score = MagicMock(
            return_value=many_results
        )
        
        # Act
        results, quality = mock_kb_for_quality.search_with_quality_control("查询", k=10)
        
        # Assert - 应该只返回MAX_REFERENCES数量
        assert len(results) == 5  # MAX_REFERENCES
        assert quality.qualified_count == 5


class TestLegalKnowledgeBaseEdgeCases:
    """LegalKnowledgeBase边界条件测试类"""

    def test_calculate_confidence_empty_results(self):
        """测试空结果的置信度计算"""
        # Arrange
        kb = LegalKnowledgeBase()
        
        # Act
        confidence = kb._calculate_confidence([])
        
        # Assert
        assert confidence == "low"

    def test_calculate_confidence_two_results_high(self):
        """测试两个高相似度结果的置信度"""
        # Arrange
        kb = LegalKnowledgeBase()
        results = [("content1", {}, 0.86), ("content2", {}, 0.88)]
        
        # Act
        confidence = kb._calculate_confidence(results)
        
        # Assert - 平均0.87>=0.85且有2个结果
        assert confidence == "high"

    def test_score_to_similarity_negative(self):
        """测试负数的分数转换"""
        # Arrange
        kb = LegalKnowledgeBase()
        
        # Act
        similarity = kb._score_to_similarity(-1.0)
        
        # Assert - score<0应该返回1.0
        assert similarity == 1.0

    def test_score_to_similarity_high_score(self):
        """测试高分score的相似度计算"""
        # Arrange
        kb = LegalKnowledgeBase()
        
        # Act
        similarity = kb._score_to_similarity(100.0)
        
        # Assert - score=100, similarity = 1.0 / (1.0 + 100.0) = 0.0099
        assert abs(similarity - 0.00990099) < 0.001

    def test_score_to_similarity_clamp_high(self):
        """测试相似度上限截断"""
        # Arrange
        kb = LegalKnowledgeBase()
        
        # Act
        similarity = kb._score_to_similarity(-10.0)
        
        # Assert - 应该截断到1.0
        assert similarity == 1.0

    def test_search_with_special_characters(self):
        """测试含特殊字符的查询"""
        # Arrange
        kb = LegalKnowledgeBase()
        kb.initialize()
        kb.vector_store = MagicMock()
        kb.vector_store.similarity_search_with_score = MagicMock(
            return_value=[(MagicMock(page_content="结果", metadata={}), 0.1)]
        )
        
        # Act
        results = kb.search("查询！@#$%")
        
        # Assert
        assert len(results) == 1

    def test_add_documents_with_empty_content(self):
        """测试添加空内容的文档"""
        # Arrange
        kb = LegalKnowledgeBase()
        kb.initialize()
        kb.vector_store = MagicMock()
        kb.vector_store.add_texts = MagicMock()
        
        documents = [
            {
                "law_name": "测试法",
                "article": "第一条",
                "content": ""
            }
        ]
        
        # Act
        kb.add_law_documents(documents)
        
        # Assert - 应该成功添加
        kb.vector_store.add_texts.assert_called_once()
        texts = kb.vector_store.add_texts.call_args.kwargs['texts']
        assert "【测试法】第一条" in texts[0]

    def test_add_documents_with_none_values(self):
        """测试包含None值的文档"""
        # Arrange
        kb = LegalKnowledgeBase()
        kb.initialize()
        kb.vector_store = MagicMock()
        kb.vector_store.add_texts = MagicMock()
        
        documents = [
            {
                "law_name": None,
                "article": None,
                "content": "内容"
            }
        ]
        
        # Act
        kb.add_law_documents(documents)
        
        # Assert
        kb.vector_store.add_texts.assert_called_once()
        metadatas = kb.vector_store.add_texts.call_args.kwargs['metadatas']
        assert metadatas[0]["law_name"] == "None"
        assert metadatas[0]["article"] == "None"

    def test_search_with_filtered_results(self):
        """测试过滤后的质量控制"""
        # Arrange
        kb = LegalKnowledgeBase()
        kb.initialize()
        kb.vector_store = MagicMock()
        
        mock_results = [
            (MagicMock(page_content="内容1", metadata={}), 0.2),
            (MagicMock(page_content="内容2", metadata={}), 0.4),
            (MagicMock(page_content="内容3", metadata={}), 0.6)
        ]
        kb.vector_store.similarity_search_with_score = MagicMock(
            return_value=mock_results
        )
        
        # Act
        results, quality = kb.search_with_quality_control("查询")
        
        # Assert - 验证实际计算值
        # 只有score<=0.5的结果(similarity>=0.5)会被过滤
        # score 0.2 (similarity 0.8) 会被保留
        # score 0.4 (similarity 0.6) 会被保留
        # score 0.6 (similarity 0.4)  被过滤
        assert len(results) == 2
        assert abs(quality.avg_similarity - 0.7) < 0.01