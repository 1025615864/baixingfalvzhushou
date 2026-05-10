import logging
from typing import List, Optional, Union

import numpy as np

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None
    _model = None
    _device = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            self._init_model()

    def _init_model(self):
        settings = get_settings()
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                settings.EMBEDDING_MODEL, device=settings.EMBEDDING_DEVICE
            )
            self._device = settings.EMBEDDING_DEVICE
            actual_dim = self._model.get_sentence_embedding_dimension()
            self._embedding_dim = actual_dim
            logger.info(
                f"Embedding model loaded: {settings.EMBEDDING_MODEL} on {settings.EMBEDDING_DEVICE}, dim={actual_dim}"
            )
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self._model = None
            self._device = settings.EMBEDDING_DEVICE
            self._embedding_dim = settings.EMBEDDING_DIM

    @property
    def model_name(self) -> str:
        settings = get_settings()
        return settings.EMBEDDING_MODEL

    @property
    def embedding_dim(self) -> int:
        if self._model is not None and hasattr(self, "_embedding_dim"):
            return self._embedding_dim
        settings = get_settings()
        return settings.EMBEDDING_DIM

    @property
    def device(self) -> str:
        settings = get_settings()
        return self._device or settings.EMBEDDING_DEVICE

    def is_model_loaded(self) -> bool:
        return self._model is not None

    def encode(
        self, texts: Union[str, List[str]], normalize: bool = True
    ) -> np.ndarray:
        settings = get_settings()
        if self._model is None:
            logger.warning("Model not loaded, returning zero vectors")
            dim = self.embedding_dim
            if isinstance(texts, str):
                return np.zeros(dim)
            return np.zeros((len(texts), dim))

        embeddings = self._model.encode(
            texts, normalize_embeddings=normalize, convert_to_numpy=True
        )
        return embeddings

    def encode_query(self, query: str, normalize: bool = True) -> np.ndarray:
        return self.encode(query, normalize=normalize)

    def encode_documents(
        self, documents: List[str], normalize: bool = True
    ) -> np.ndarray:
        return self.encode(documents, normalize=normalize)

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(embedding1, embedding2) / (norm1 * norm2))

    def batch_encode(
        self, texts: List[str], batch_size: int = 32, normalize: bool = True
    ) -> np.ndarray:
        settings = get_settings()
        if self._model is None:
            logger.warning("Model not loaded, returning zero vectors")
            return np.zeros((len(texts), self.embedding_dim))

        batch_size = min(batch_size, settings.MAX_BATCH_SIZE)
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100,
        )
        return embeddings

    def search(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 5,
        normalize: bool = True,
    ) -> List[dict]:
        settings = get_settings()
        top_k = min(top_k, settings.MAX_TOP_K, len(candidates))

        query_embedding = self.encode(query, normalize=normalize)
        candidate_embeddings = self.encode(candidates, normalize=normalize)

        if normalize:
            scores = np.dot(candidate_embeddings, query_embedding)
        else:
            query_norm = np.linalg.norm(query_embedding)
            candidate_norms = np.linalg.norm(candidate_embeddings, axis=1)
            denom = candidate_norms * query_norm
            denom[denom == 0] = 1e-10
            scores = np.dot(candidate_embeddings, query_embedding) / denom

        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append(
                {"index": int(idx), "text": candidates[int(idx)], "score": float(scores[idx])}
            )
        return results


_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
