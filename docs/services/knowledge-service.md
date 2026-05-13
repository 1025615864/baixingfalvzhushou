# 知识库服务

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | knowledge-service |
| 端口 | 8081 |
| 基础路径 | /api/v1/knowledge |
| 技术栈 | FastAPI + SQLAlchemy + PostgreSQL + ChromaDB |
| 数据库 | knowledge_service |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/ready |

## 服务描述

知识库服务负责法律知识条目的全生命周期管理，包括法律条文、司法解释、法规等知识的创建、审核、发布、向量化索引和检索。支持全文搜索和向量语义搜索，为 AI 法律咨询提供法律知识参考数据源。

## API 端点

### 知识管理 (knowledge.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/knowledge | 创建知识 | 是 |
| GET | /api/v1/knowledge/{knowledge_id} | 获取知识详情 | 是 |
| PUT | /api/v1/knowledge/{knowledge_id} | 更新知识 | 是 |
| DELETE | /api/v1/knowledge/{knowledge_id} | 删除知识（软删除） | 是 |
| POST | /api/v1/knowledge/{knowledge_id}/publish | 发布知识 | 是 |
| POST | /api/v1/knowledge/{knowledge_id}/unpublish | 下线知识 | 是 |
| POST | /api/v1/knowledge/{knowledge_id}/submit-review | 提交知识审核 | 是 |

### 知识搜索 (search.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/knowledge/search | 全文搜索知识（支持分类、类型筛选） | 否 |

### 向量操作 (vector_ops.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/vector/rebuild/{knowledge_id} | 重建单个知识向量索引 | 否 |
| POST | /api/v1/vector/rebuild | 全量重建向量索引 | 否 |

### 向量搜索 (vector_search.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/knowledge/vector/search | 向量语义搜索（供AI服务HTTP调用） | 否 |

### 批量操作 (batch.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/knowledge/batch-import | 批量导入知识（最多500条） | 否 |
| GET | /api/v1/knowledge/export | 导出知识（支持筛选和分页） | 否 |

### 分类管理 (categories.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/knowledge/categories | 创建分类 | 否 |
| GET | /api/v1/knowledge/categories | 获取分类列表 | 否 |
| GET | /api/v1/knowledge/categories/{category_id} | 获取分类详情 | 否 |
| PUT | /api/v1/knowledge/categories/{category_id} | 更新分类 | 否 |
| DELETE | /api/v1/knowledge/categories/{category_id} | 删除分类（软删除） | 否 |

### 统计信息 (stats.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/knowledge/stats | 获取知识库统计信息 | 否 |
| GET | /api/v1/knowledge/vector-info | 获取向量库信息 | 否 |
| GET | /api/v1/knowledge/list | 获取知识列表（分页） | 否 |
| GET | /api/v1/knowledge/categories | 获取知识分类列表 | 否 |

## 数据模型

### LegalKnowledge

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| knowledge_type | String(50) | 知识类型（索引） |
| title | String(500) | 标题 |
| article_number | String(100) | 法条编号 |
| content | Text | 内容 |
| summary | Text | 摘要 |
| category | String(200) | 分类（索引） |
| keywords | String(500) | 关键词 |
| source | String(200) | 来源 |
| is_vectorized | Boolean | 是否已向量化（索引） |
| vector_id | String(200) | 向量ID |
| vector_indexed | Boolean | 是否已索引 |
| status | String(20) | 状态（draft/pending_review/published/archived） |
| version | Integer | 版本号 |
| effective_date | DateTime | 生效日期 |
| expiry_date | DateTime | 失效日期 |
| law_number | String(100) | 法律编号 |
| jurisdiction | String(100) | 管辖区域 |
| weight | Integer | 权重 |
| is_active | Boolean | 是否激活（索引） |
| is_deleted | Boolean | 是否删除（索引） |

### KnowledgeCategory

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String(100) | 分类名称（唯一） |
| parent_id | Integer | 父分类ID（索引） |
| description | Text | 描述 |
| icon | String(50) | 图标 |
| sort_order | Integer | 排序 |
| is_active | Boolean | 是否激活 |

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| ai-service | HTTP | AI 服务调用向量搜索接口获取法律知识参考 |
| embedding-service | HTTP | 调用嵌入服务生成文本向量 |
| archive-service | 相似模式 | 同类档案管理服务，架构模式一致 |
| backend-bff | HTTP | 通过 BFF 代理层对外提供 API |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| DATABASE_URL | postgresql://user:pass@localhost:5432/knowledge_service | 数据库连接URL |
| ENVIRONMENT | development | 运行环境 |
| VECTOR_STORE_PATH | ./data/chroma_knowledge | 向量数据存储路径 |
| EMBEDDING_MODEL | shibing624/text2vec-base-chinese | 嵌入模型名称 |
| CORS_ORIGINS | http://localhost:3000,http://localhost:8080 | 允许的CORS来源 |

## 部署信息

- Dockerfile: services/knowledge-service/Dockerfile
- 健康检查: /health
- 资源限制: CPU 0.5核 / 内存 512MB
