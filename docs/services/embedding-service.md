# 向量嵌入服务 (Embedding Service)

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | embedding-service |
| 端口 | 8003 |
| 基础路径 | /api/v1/embeddings |
| 技术栈 | FastAPI + SentenceTransformer + NumPy |
| 数据库 | 无（无状态服务） |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/ready |

## 服务描述

向量嵌入服务是共享的 Embedding 模型微服务，基于 SentenceTransformer 加载中文文本向量模型，提供文本向量化、批量编码、语义相似度计算和向量检索功能。服务为无状态设计，所有端点需通过内部 API Key 认证，供 AI 服务、知识库服务、档案服务等调用。

## API 端点

### Embedding (embedding.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/embeddings/texts | 批量文本向量化，返回embeddings数组 | 内部API Key |
| POST | /api/v1/embeddings/query | 单条查询文本向量化 | 内部API Key |
| POST | /api/v1/embeddings/batch | 大批量文本向量化（支持自定义batch_size，1-512） | 内部API Key |
| POST | /api/v1/embeddings/similarity | 计算两段文本的语义相似度 | 内部API Key |
| POST | /api/v1/embeddings/search | 向量检索，从候选文本中返回top_k最相似结果 | 内部API Key |

### 服务信息

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | / | 服务信息（模型名/维度/设备/加载状态） | 否 |

## 核心能力

| 能力 | 说明 |
|------|------|
| 文本编码 | 支持单条和批量文本向量化，默认归一化 |
| 查询编码 | 专门为检索查询优化的编码接口 |
| 批量处理 | 支持自定义batch_size（1-512），自动分批处理 |
| 相似度计算 | 余弦相似度，返回0-1浮点值 |
| 向量检索 | 从候选文本中检索top_k最相似结果（1-100） |

## 数据模型

无数据库模型。服务为无状态设计，模型加载在内存中。

| 内部组件 | 说明 |
|----------|------|
| EmbeddingService | 单例模式，封装SentenceTransformer模型加载与推理 |
| 默认模型 | shibing624/text2vec-base-chinese |
| 默认维度 | 768 |
| 运行设备 | CPU（可配置GPU） |

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| ai-service | HTTP | AI对话中的RAG检索向量化 |
| knowledge-service | HTTP | 知识库文档向量化与检索 |
| archive-service | HTTP | 档案文档向量化与检索 |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| EMBEDDING_MODEL | shibing624/text2vec-base-chinese | SentenceTransformer模型名称 |
| EMBEDDING_DEVICE | cpu | 推理设备（cpu/cuda） |
| EMBEDDING_DIM | 768 | 向量维度 |
| DEFAULT_BATCH_SIZE | 32 | 默认批处理大小 |
| MAX_BATCH_SIZE | 512 | 最大批处理大小 |
| DEFAULT_TOP_K | 5 | 默认检索返回数量 |
| MAX_TOP_K | 100 | 最大检索返回数量 |
| SERVICE_PORT | 8003 | 服务端口 |
| ENVIRONMENT | development | 运行环境 |

## 部署信息

- Dockerfile: services/embedding-service/Dockerfile
- 健康检查: /health（含模型加载状态）
- 资源限制: CPU 1核 / 内存 2GB（模型加载需较大内存）
