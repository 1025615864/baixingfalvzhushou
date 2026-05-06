"""档案库向量存储模块 - 支持本地Embedding和远程Embedding服务"""
import os
import logging
from typing import Optional, List, Dict
import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1536

USE_REMOTE_EMBEDDING = os.getenv("USE_REMOTE_EMBEDDING", "false").lower() in {"true", "1", "yes"}
REMOTE_EMBEDDING_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8006")


class ChineseEmbeddingFunction:
    """本地中文Embedding函数"""

    def __init__(self):
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer("shibing624/text2vec-base-chinese")
        except Exception as e:
            logger.warning(f"Failed to load local embedding model: {e}")

    def __call__(self, texts):
        if self.model is None:
            return [[0.0] * EMBEDDING_DIM for _ in texts]
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        if self.model is None:
            return [0.0] * EMBEDDING_DIM
        embedding = self.model.encode(text)
        return embedding.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self.model is None:
            return [[0.0] * EMBEDDING_DIM for _ in texts]
        embeddings = self.model.encode(texts)
        return embeddings.tolist()


class RemoteEmbeddingFunction:
    """远程Embedding服务客户端"""

    def __init__(self, base_url: str = REMOTE_EMBEDDING_URL):
        self.base_url = base_url
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def embed_documents(self, texts: list[str], normalize: bool = True) -> list[list[float]]:
        """批量获取文档embedding"""
        try:
            client = await self._get_client()
            response = await client.post(
                "/embed/texts",
                json={"texts": texts, "normalize": normalize}
            )
            response.raise_for_status()
            data = response.json()
            return data["embeddings"]
        except Exception as e:
            logger.error(f"Remote embedding failed: {e}")
            return [[0.0] * EMBEDDING_DIM for _ in texts]

    async def embed_query(self, query: str, normalize: bool = True) -> list[float]:
        """获取查询embedding"""
        try:
            client = await self._get_client()
            response = await client.post(
                "/embed/query",
                json={"query": query, "normalize": normalize}
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]
        except Exception as e:
            logger.error(f"Remote embedding failed: {e}")
            return [0.0] * EMBEDDING_DIM


_local_embedding = None
_remote_embedding = None


def get_local_embedding() -> ChineseEmbeddingFunction:
    global _local_embedding
    if _local_embedding is None:
        _local_embedding = ChineseEmbeddingFunction()
    return _local_embedding


def get_remote_embedding() -> RemoteEmbeddingFunction:
    global _remote_embedding
    if _remote_embedding is None:
        _remote_embedding = RemoteEmbeddingFunction()
    return _remote_embedding


_chroma_store_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "chroma_archive"
)

_chroma_client = None
_chroma_collection = None
_pgvector_store = None


def get_vector_store_type() -> str:
    """获取向量存储类型: pgvector 或 chromadb"""
    return os.getenv("VECTOR_STORE_TYPE", "chroma").lower()


def is_remote_embedding_enabled() -> bool:
    """是否启用远程embedding"""
    return USE_REMOTE_EMBEDDING


def get_pgvector_store():
    """获取pgvector存储实例"""
    global _pgvector_store
    if _pgvector_store is not None:
        return _pgvector_store

    try:
        from shared.vector.pgvector_store import get_vector_store

        database_url = os.getenv("ARCHIVE_DATABASE_URL")
        if not database_url:
            logger.warning("ARCHIVE_DATABASE_URL not set, using ChromaDB")
            return None

        _pgvector_store = get_vector_store(
            store_type="pgvector",
            database_url=database_url.replace("postgresql://", "postgresql+asyncpg://"),
            table_name="archive_vectors",
            embedding_dim=EMBEDDING_DIM
        )
        logger.info("pgvector store initialized for archive service")
        return _pgvector_store
    except Exception as e:
        logger.warning(f"Failed to initialize pgvector store: {e}")
        return None


def get_chroma_client():
    """获取ChromaDB客户端"""
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(_chroma_store_path, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=_chroma_store_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
    return _chroma_client


def get_chroma_collection():
    """获取ChromaDB Collection"""
    global _chroma_collection
    if _chroma_collection is None:
        client = get_chroma_client()
        _chroma_collection = client.get_or_create_collection(
            name="archive_cases",
            embedding_function=get_local_embedding()
        )
    return _chroma_collection


def _get_embedding_func():
    """获取embedding函数（本地或远程）"""
    if is_remote_embedding_enabled():
        return get_remote_embedding()
    return get_local_embedding()


async def search_archive_async(query: str, top_k: int = 5) -> list[dict]:
    """异步搜索档案库 - 自动选择pgvector或ChromaDB"""
    store_type = get_vector_store_type()

    if store_type == "pgvector":
        return await _search_pgvector_async(query, top_k)
    else:
        return await _search_chroma_async(query, top_k)


def search_archive(query: str, top_k: int = 5) -> list[dict]:
    """搜索档案库（同步版本，使用本地embedding）"""
    store_type = get_vector_store_type()

    if store_type == "pgvector":
        return _search_pgvector_sync(query, top_k)
    else:
        return _search_chroma_sync(query, top_k)


async def _search_pgvector_async(query: str, top_k: int) -> list[dict]:
    """使用pgvector异步搜索"""
    store = get_pgvector_store()
    if not store:
        logger.warning("pgvector not available, falling back to ChromaDB")
        return await _search_chroma_async(query, top_k)

    try:
        embed_func = _get_embedding_func()
        if is_remote_embedding_enabled():
            query_vector = await embed_func.embed_query(query)
        else:
            query_vector = embed_func.embed_query(query)

        results = await store.search(query_vector, top_k=top_k)

        docs = []
        for result in results:
            docs.append({
                "id": result.id,
                "content": result.content,
                "metadata": result.metadata,
                "distance": result.distance
            })
        return docs
    except Exception as e:
        logger.error(f"pgvector search failed: {e}")
        return await _search_chroma_async(query, top_k)


def _search_pgvector_sync(query: str, top_k: int) -> list[dict]:
    """使用pgvector同步搜索"""
    store = get_pgvector_store()
    if not store:
        logger.warning("pgvector not available, falling back to ChromaDB")
        return _search_chroma_sync(query, top_k)

    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            embed_func = get_local_embedding()
            query_vector = embed_func.embed_query(query)
            results = loop.run_until_complete(store.search(query_vector, top_k=top_k))

            docs = []
            for result in results:
                docs.append({
                    "id": result.id,
                    "content": result.content,
                    "metadata": result.metadata,
                    "distance": result.distance
                })
            return docs
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"pgvector search failed: {e}")
        return _search_chroma_sync(query, top_k)


async def _search_chroma_async(query: str, top_k: int) -> list[dict]:
    """使用ChromaDB异步搜索"""
    try:
        embed_func = _get_embedding_func()

        if is_remote_embedding_enabled():
            query_vector = await embed_func.embed_query(query)
            collection = get_chroma_collection()
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k
            )
        else:
            collection = get_chroma_collection()
            results = collection.query(
                query_texts=[query],
                n_results=top_k
            )

        docs = []
        if results and results.get("documents"):
            ids = results.get("ids", [[]])[0]
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[{}]])[0]
            distances = results.get("distances", [[]])[0]

            for i, doc in enumerate(documents):
                docs.append({
                    "id": ids[i] if i < len(ids) else f"doc_{i}",
                    "content": doc,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else 0.0
                })
        return docs
    except Exception as e:
        logger.error(f"ChromaDB search failed: {e}")
        return []


def _search_chroma_sync(query: str, top_k: int) -> list[dict]:
    """使用ChromaDB同步搜索"""
    try:
        collection = get_chroma_collection()
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )

        docs = []
        if results and results.get("documents"):
            ids = results.get("ids", [[]])[0]
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[{}]])[0]
            distances = results.get("distances", [[]])[0]

            for i, doc in enumerate(documents):
                docs.append({
                    "id": ids[i] if i < len(ids) else f"doc_{i}",
                    "content": doc,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else 0.0
                })
        return docs
    except Exception as e:
        logger.error(f"ChromaDB search failed: {e}")
        return []


async def add_archive_async(documents: list[dict], ids: list[str]):
    """异步添加档案文档"""
    store_type = get_vector_store_type()

    if store_type == "pgvector":
        await _add_archive_pgvector_async(documents, ids)
    else:
        await _add_archive_chroma_async(documents, ids)


def add_archive(documents: list[dict], ids: list[str]):
    """同步添加档案文档（使用本地embedding）"""
    store_type = get_vector_store_type()

    if store_type == "pgvector":
        _add_archive_pgvector_sync(documents, ids)
    else:
        _add_archive_chroma_sync(documents, ids)


async def _add_archive_pgvector_async(documents: list[dict], ids: list[str]):
    """使用pgvector异步添加文档"""
    store = get_pgvector_store()
    if not store:
        logger.warning("pgvector not available, falling back to ChromaDB")
        await _add_archive_chroma_async(documents, ids)
        return

    try:
        embed_func = _get_embedding_func()
        texts = [doc["content"] for doc in documents]

        if is_remote_embedding_enabled():
            embeddings = await embed_func.embed_documents(texts)
        else:
            embeddings = embed_func.embed_documents(texts)

        vectors = []
        for i, doc in enumerate(documents):
            vectors.append({
                "id": ids[i],
                "embedding": embeddings[i],
                "content": doc["content"],
                "metadata": doc.get("metadata", {})
            })

        await store.add_vectors(vectors)
        logger.info(f"Added {len(vectors)} documents to pgvector")
    except Exception as e:
        logger.error(f"Failed to add to pgvector: {e}")
        await _add_archive_chroma_async(documents, ids)


def _add_archive_pgvector_sync(documents: list[dict], ids: list[str]):
    """使用pgvector同步添加文档"""
    store = get_pgvector_store()
    if not store:
        logger.warning("pgvector not available, falling back to ChromaDB")
        _add_archive_chroma_sync(documents, ids)
        return

    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            embed_func = get_local_embedding()
            texts = [doc["content"] for doc in documents]
            embeddings = embed_func.embed_documents(texts)

            vectors = []
            for i, doc in enumerate(documents):
                vectors.append({
                    "id": ids[i],
                    "embedding": embeddings[i],
                    "content": doc["content"],
                    "metadata": doc.get("metadata", {})
                })

            loop.run_until_complete(store.add_vectors(vectors))
            logger.info(f"Added {len(vectors)} documents to pgvector")
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Failed to add to pgvector: {e}")
        _add_archive_chroma_sync(documents, ids)


async def _add_archive_chroma_async(documents: list[dict], ids: list[str]):
    """使用ChromaDB异步添加文档"""
    try:
        collection = get_chroma_collection()
        texts = [doc["content"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]

        if is_remote_embedding_enabled():
            embed_func = get_remote_embedding()
            embeddings = await embed_func.embed_documents(texts)
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas
            )
        else:
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
        logger.info(f"Added {len(documents)} documents to ChromaDB")
    except Exception as e:
        logger.error(f"Failed to add to ChromaDB: {e}")


def _add_archive_chroma_sync(documents: list[dict], ids: list[str]):
    """使用ChromaDB同步添加文档"""
    try:
        collection = get_chroma_collection()
        texts = [doc["content"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]

        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(documents)} documents to ChromaDB")
    except Exception as e:
        logger.error(f"Failed to add to ChromaDB: {e}")


async def delete_archive_async(ids: list[str]):
    """异步删除档案文档"""
    store_type = get_vector_store_type()

    if store_type == "pgvector":
        await _delete_archive_pgvector_async(ids)
    else:
        _delete_archive_chroma_sync(ids)


def delete_archive(ids: list[str]):
    """同步删除档案文档"""
    store_type = get_vector_store_type()

    if store_type == "pgvector":
        _delete_archive_pgvector_sync(ids)
    else:
        _delete_archive_chroma_sync(ids)


async def _delete_archive_pgvector_async(ids: list[str]):
    """使用pgvector异步删除"""
    store = get_pgvector_store()
    if not store:
        logger.warning("pgvector not available, falling back to ChromaDB")
        _delete_archive_chroma_sync(ids)
        return

    try:
        await store.delete(ids)
        logger.info(f"Deleted {len(ids)} documents from pgvector")
    except Exception as e:
        logger.error(f"Failed to delete from pgvector: {e}")


def _delete_archive_pgvector_sync(ids: list[str]):
    """使用pgvector同步删除"""
    store = get_pgvector_store()
    if not store:
        logger.warning("pgvector not available, falling back to ChromaDB")
        _delete_archive_chroma_sync(ids)
        return

    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(store.delete(ids))
            logger.info(f"Deleted {len(ids)} documents from pgvector")
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Failed to delete from pgvector: {e}")


def _delete_archive_chroma_sync(ids: list[str]):
    """使用ChromaDB删除"""
    try:
        collection = get_chroma_collection()
        collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents from ChromaDB")
    except Exception as e:
        logger.error(f"Failed to delete from ChromaDB: {e}")


async def get_collection_count_async() -> int:
    """异步获取向量库文档数量"""
    store_type = get_vector_store_type()

    if store_type == "pgvector":
        store = get_pgvector_store()
        if store:
            try:
                return await store.count()
            except Exception:
                pass

    try:
        collection = get_chroma_collection()
        return collection.count()
    except Exception:
        return 0


def get_collection_count() -> int:
    """同步获取向量库文档数量"""
    store_type = get_vector_store_type()

    if store_type == "pgvector":
        store = get_pgvector_store()
        if store:
            import asyncio
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(store.count())
                finally:
                    loop.close()
            except Exception:
                pass

    try:
        collection = get_chroma_collection()
        return collection.count()
    except Exception:
        return 0
