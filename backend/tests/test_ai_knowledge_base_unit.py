"""Unit tests for LegalKnowledgeBase in app/services/ai/knowledge_base.py"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.ai.knowledge_base import LegalKnowledgeBase

class TestLegalKnowledgeBase:
    @pytest.fixture
    def kb(self):
        return LegalKnowledgeBase()

    def test_score_to_similarity_logic(self, kb):
        # score <= 0 -> 1.0
        assert kb._score_to_similarity(-0.1) == 1.0
        assert kb._score_to_similarity(0.0) == 1.0
        
        # 0 < score <= 1 -> 1.0 - score
        assert kb._score_to_similarity(0.25) == 0.75
        assert kb._score_to_similarity(1.0) == 0.0
        
        # score > 1 -> 1.0 / (1.0 + score)
        assert kb._score_to_similarity(2.0) == pytest.approx(1.0 / (1.0 + 2.0))
        assert kb._score_to_similarity(9.0) == 0.1
        
        # Extreme results
        # If score is very large, similarity should be > 0 and <= 1
        assert 0 < kb._score_to_similarity(999999) <= 1.0

    def test_calculate_confidence_thresholds(self, kb):
        # Empty results -> low
        assert kb._calculate_confidence([]) == "low"
        
        # avg >= 0.85 and len >= 2 -> high
        results_high = [
            ("c1", {}, 0.9),
            ("c2", {}, 0.8), # avg = 0.85
        ]
        assert kb._calculate_confidence(results_high) == "high"
        
        # avg >= 0.7 -> medium
        results_med = [
            ("c1", {}, 0.7),
        ]
        assert kb._calculate_confidence(results_med) == "medium"
        
        # otherwise -> low
        results_low = [
            ("c1", {}, 0.5),
        ]
        assert kb._calculate_confidence(results_low) == "low"

    @patch("app.services.ai.knowledge_base.OpenAIEmbeddings")
    @patch("app.services.ai.knowledge_base.Chroma")
    @patch("app.services.ai.knowledge_base.settings")
    def test_initialize_with_api_key(self, mock_settings, mock_chroma, mock_embeddings, kb):
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_base_url = "http://test"
        mock_settings.chroma_persist_dir = "/tmp/chroma"
        
        kb.initialize()
        
        assert kb._initialized is True
        mock_embeddings.assert_called_once()
        mock_chroma.assert_called_once()
        assert kb.embeddings is not None
        assert kb.vector_store is not None

    @patch("app.services.ai.knowledge_base.settings")
    def test_initialize_without_api_key(self, mock_settings, kb):
        mock_settings.openai_api_key = None
        
        kb.initialize()
        
        assert kb._initialized is True
        assert kb.embeddings is None
        assert kb.vector_store is None

    @patch("app.services.ai.knowledge_base.Chroma")
    def test_add_law_documents_assembles_correct_metadata(self, mock_chroma_class, kb):
        mock_vector_store = MagicMock()
        kb.vector_store = mock_vector_store
        
        docs = [
            {
                "law_name": "民法典",
                "article": "101",
                "content": "隐私权保护",
                "source": "official"
            }
        ]
        
        kb.add_law_documents(docs)
        
        # Check if add_texts was called
        mock_vector_store.add_texts.assert_called_once()
        args, kwargs = mock_vector_store.add_texts.call_args
        
        texts = kwargs.get("texts") or args[0]
        metadatas = kwargs.get("metadatas") or args[1]
        
        assert "【民法典】101" in texts[0]
        assert metadatas[0]["law_name"] == "民法典"
        assert metadatas[0]["source"] == "official"

    def test_search_returns_empty_when_no_vector_store(self, kb):
        kb.vector_store = None
        # Mock initialize to prevent actual init
        with patch.object(kb, "initialize"):
            results = kb.search("query")
            assert results == []

    @patch.object(LegalKnowledgeBase, "initialize")
    def test_search_logic_packs_results_correctly(self, mock_init, kb):
        mock_vector_store = MagicMock()
        kb.vector_store = mock_vector_store
        
        # Mock what Chroma returns: List of docs and scores
        mock_doc = MagicMock()
        mock_doc.page_content = "extracted law text"
        mock_doc.metadata = {"law_name": "Law1"}
        
        mock_vector_store.similarity_search_with_score.return_value = [
            (mock_doc, 0.2) # similarity = 1 - 0.2 = 0.8
        ]
        
        results = kb.search("test query", k=1)
        
        assert len(results) == 1
        content, metadata, similarity = results[0]
        assert content == "extracted law text"
        assert metadata["law_name"] == "Law1"
        assert similarity == 0.8

    @patch.object(LegalKnowledgeBase, "search")
    def test_search_with_quality_control_filters_by_threshold(self, mock_search, kb):
        # Return 3 results with different similarities
        mock_search.return_value = [
            ("High", {}, 0.9),
            ("Med", {}, 0.6),
            ("Low", {}, 0.3),
        ]
        
        # Test with threshold 0.5
        results, quality = kb.search_with_quality_control("query", threshold=0.5)
        
        assert len(results) == 2 # 0.9 and 0.6
        assert results[0][0] == "High"
        assert results[1][0] == "Med"
        
        assert quality.total_candidates == 3
        assert quality.qualified_count == 2
        assert quality.confidence in ["medium", "high", "low"]
        assert quality.avg_similarity == (0.9 + 0.6) / 2

    @patch.object(LegalKnowledgeBase, "search")
    def test_search_with_quality_control_respects_max_references(self, mock_search, kb):
        kb.MAX_REFERENCES = 2
        mock_search.return_value = [
            ("R1", {}, 0.9),
            ("R2", {}, 0.8),
            ("R3", {}, 0.7),
        ]
        
        results, _ = kb.search_with_quality_control("query", threshold=0.1)
        assert len(results) == 2
