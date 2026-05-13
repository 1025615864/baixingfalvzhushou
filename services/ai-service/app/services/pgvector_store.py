import logging
import os
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class PgVectorStore:
    def __init__(self):
        self.database_url = os.getenv(
            "AI_DATABASE_URL",
            os.getenv("DATABASE_URL", ""),
        )
        self._engine = None
        self._session_factory = None
        self._initialized = False
        self._dimension = int(os.getenv("EMBEDDING_DIMENSION", "768"))

    async def initialize(self):
        if self._initialized:
            return

        if not self.database_url:
            logger.warning("No database URL configured for pgvector store")
            return

        try:
            self._engine = create_async_engine(self.database_url, echo=False)
            self._session_factory = sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False,
            )

            async with self._engine.begin() as conn:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                await conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS ai_vectors (
                        id SERIAL PRIMARY KEY,
                        content TEXT NOT NULL,
                        metadata JSONB DEFAULT '{{}}',
                        embedding vector({self._dimension}),
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_ai_vectors_embedding
                    ON ai_vectors USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """))

            self._initialized = True
            logger.info(f"PgVectorStore initialized with dimension={self._dimension}")
        except Exception as e:
            logger.error(f"Failed to initialize PgVectorStore: {e}")

    async def add_vectors(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: Optional[list[dict]] = None,
    ) -> list[int]:
        if not self._initialized:
            await self.initialize()

        if not self._session_factory:
            return []

        ids = []
        metadatas = metadatas or [{}] * len(texts)

        async with self._session_factory() as session:
            for text_content, embedding, meta in zip(texts, embeddings, metadatas):
                embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
                meta_str = str(meta).replace("'", '"')
                result = await session.execute(
                    text("""
                        INSERT INTO ai_vectors (content, metadata, embedding)
                        VALUES (:content, :metadata::jsonb, :embedding::vector)
                        RETURNING id
                    """),
                    {"content": text_content, "metadata": meta_str, "embedding": embedding_str},
                )
                row = result.fetchone()
                if row:
                    ids.append(row[0])
            await session.commit()

        return ids

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict]:
        if not self._initialized:
            await self.initialize()

        if not self._session_factory:
            return []

        embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        async with self._session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT id, content, metadata,
                           1 - (embedding <=> :query::vector) AS similarity
                    FROM ai_vectors
                    ORDER BY embedding <=> :query::vector
                    LIMIT :top_k
                """),
                {"query": embedding_str, "top_k": top_k},
            )
            rows = result.fetchall()

        return [
            {
                "id": row[0],
                "content": row[1],
                "metadata": row[2],
                "similarity": float(row[3]),
            }
            for row in rows
        ]

    async def delete(self, ids: list[int]) -> bool:
        if not self._initialized or not self._session_factory:
            return False

        async with self._session_factory() as session:
            await session.execute(
                text("DELETE FROM ai_vectors WHERE id = ANY(:ids)"),
                {"ids": ids},
            )
            await session.commit()
        return True

    async def close(self):
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._initialized = False


pgvector_store = PgVectorStore()
