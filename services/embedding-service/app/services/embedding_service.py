"""Embedding模型服务"""
import os
import logging
from typing import List, Optional, Union
import numpy as np

logger = logging.getLogger(__name__)

embedding_model = os.getenv("EMBEDDING_MODEL", "shibing624/text2vec-base-chinese")
embedding_device = os.getenv("EMBEDDING_DEVICE", "cpu")
EMBEDDING_DIM = 1536


class EmbeddingService:
    """统一的Embedding服务 - 单例模式"""

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
        """初始化模型"""
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(embedding_model, device=embedding_device)
            self._device = embedding_device
            logger.info(f"Embedding model loaded: {embedding_model} on {embedding_device}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self._model = None
            self._device = embedding_device

    @property
    def model_name(self) -> str:
        return embedding_model

    @property
    def embedding_dim(self) -> int:
        return EMBEDDING_DIM

    @property
    def device(self) -> str:
        return self._device or embedding_device

    def is_model_loaded(self) -> bool:
        return self._model is not None

    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True
    ) -> np.ndarray:
        """批量编码文本"""
        if self._model is None:
            logger.warning("Model not loaded, returning zero vectors")
            if isinstance(texts, str):
                return np.zeros(EMBEDDING_DIM)
            return np.zeros((len(texts), EMBEDDING_DIM))

        embeddings = self._model.encode(
            texts,
            normalize_embeddings=normalize,
            convert_to_numpy=True
        )
        return embeddings

    def encode_query(self, query: str, normalize: bool = True) -> np.ndarray:
        """编码查询文本"""
        return self.encode(query, normalize=normalize)

    def encode_documents(self, documents: List[str], normalize: bool = True) -> np.ndarray:
        """编码文档列表"""
        return self.encode(documents, normalize=normalize)

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """计算两个向量的余弦相似度"""
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(embedding1, embedding2) / (norm1 * norm2))

    def batch_encode(self, texts: List[str], batch_size: int = 32, normalize: bool = True) -> np.ndarray:
        """分批编码大量文本"""
        if self._model is None:
            logger.warning("Model not loaded, returning zero vectors")
            return np.zeros((len(texts), EMBEDDING_DIM))

        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100
        )
        return embeddings
