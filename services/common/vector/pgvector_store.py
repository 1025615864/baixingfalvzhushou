"""pgvector向量存储服务 - 统一接口"""
import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """向量搜索结果"""
    id: str
    content: str
    metadata: Dict[str, Any]
    distance: float
    score: float


class VectorStore(ABC):
    """向量存储抽象接口"""

    @abstractmethod
    async def add_vectors(self, vectors: List[Dict]) -> bool:
        pass

    @abstractmethod
    async def search(self, query_vector: List[float], top_k: int = 5, filters: Optional[Dict] = None) -> List[VectorSearchResult]:
        pass

    @abstractmethod
    async def delete(self, ids: List[str]) -> bool:
        pass

    @abstractmethod
    async def count(self) -> int:
        pass


class PGVectorStore(VectorStore):
    """PostgreSQL pgvector实现"""

    def __init__(
        self,
        database_url: str,
        table_name: str,
        embedding_dim: int = 1536,
        metadata_json_column: str = "metadata",
        content_column: str = "content"
    ):
        self.database_url = database_url
        self.table_name = table_name
        self.embedding_dim = embedding_dim
        self.metadata_json_column = metadata_json_column
        self.content_column = content_column
        self._pool = None

    async def _get_pool(self):
        if self._pool is None:
            try:
                import asyncpg
                self._pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=2,
                    max_size=10
                )
            except ImportError:
                logger.warning("asyncpg not installed, using sync fallback")
                self._pool = None
        return self._pool

    async def add_vectors(self, vectors: List[Dict]) -> bool:
        pool = await self._get_pool()
        if not pool:
            logger.error("No database pool available")
            return False

        async with pool.acquire() as conn:
            try:
                values = []
                for vec in vectors:
                    embedding = vec.get("embedding", [])
                    if len(embedding) != self.embedding_dim:
                        logger.warning(f"Skipping vector with wrong dimension: {len(embedding)}")
                        continue

                    values.append((
                        vec.get("id"),
                        f"[{','.join(map(str, embedding))}]",
                        vec.get("content", ""),
                        vec.get("metadata", {})
                    ))

                if values:
                    await conn.executemany(
                        f"""
                        INSERT INTO {self.table_name} (id, embedding, {self.content_column}, {self.metadata_json_column})
                        VALUES ($1, $2::vector, $3, $4)
                        ON CONFLICT (id) DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            {self.content_column} = EXCLUDED.{self.content_column},
                            {self.metadata_json_column} = EXCLUDED.{self.metadata_json_column},
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        values
                    )
                return True
            except Exception as e:
                logger.error(f"Failed to add vectors: {e}")
                return False

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[VectorSearchResult]:
        pool = await self._get_pool()
        if not pool:
            return []

        async with pool.acquire() as conn:
            try:
                embedding_str = f"[{','.join(map(str, query_vector))}]"

                where_clause = ""
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        conditions.append(f"metadata->>'{key}' = '{value}'")
                    where_clause = "WHERE " + " AND ".join(conditions)

                rows = await conn.fetch(
                    f"""
                    SELECT id, {self.content_column}, {self.metadata_json_column},
                           embedding <=> $1::vector AS distance
                    FROM {self.table_name}
                    {where_clause}
                    ORDER BY embedding <=> $1::vector
                    LIMIT {top_k}
                    """,
                    embedding_str
                )

                results = []
                for row in rows:
                    distance = float(row['distance'])
                    results.append(VectorSearchResult(
                        id=str(row['id']),
                        content=row[self.content_column] or "",
                        metadata=dict(row[self.metadata_json_column] or {}),
                        distance=distance,
                        score=1.0 - distance
                    ))
                return results
            except Exception as e:
                logger.error(f"Failed to search vectors: {e}")
                return []

    async def delete(self, ids: List[str]) -> bool:
        pool = await self._get_pool()
        if not pool:
            return False

        async with pool.acquire() as conn:
            try:
                await conn.execute(
                    f"DELETE FROM {self.table_name} WHERE id = ANY($1)",
                    ids
                )
                return True
            except Exception as e:
                logger.error(f"Failed to delete vectors: {e}")
                return False

    async def count(self) -> int:
        pool = await self._get_pool()
        if not pool:
            return 0

        async with pool.acquire() as conn:
            try:
                result = await conn.fetchval(f"SELECT COUNT(*) FROM {self.table_name}")
                return result or 0
            except Exception as e:
                logger.error(f"Failed to count vectors: {e}")
                return 0


def get_vector_store(
    store_type: str = "pgvector",
    **kwargs
) -> VectorStore:
    """获取向量存储实例"""
    if store_type == "pgvector":
        return PGVectorStore(**kwargs)
    else:
        raise ValueError(f"Unknown vector store type: {store_type}")
