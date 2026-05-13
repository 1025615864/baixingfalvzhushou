# 档案库服务

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | archive-service |
| 端口 | 8013 |
| 基础路径 | /api/v1/archives |
| 技术栈 | FastAPI + SQLAlchemy + PostgreSQL + ChromaDB |
| 数据库 | archive_service |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/ready |

## 服务描述

档案库服务负责法律案例档案的全生命周期管理，包括案例的创建、审核、发布、向量化索引和检索。支持全文搜索和向量语义搜索，为 AI 法律咨询提供案例参考数据源。

## API 端点

### 案例管理 (archive.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/archive | 创建案例 | 是 |
| GET | /api/v1/archive/{case_id} | 获取案例详情 | 是 |
| PUT | /api/v1/archive/{case_id} | 更新案例 | 是 |
| DELETE | /api/v1/archive/{case_id} | 删除案例（软删除） | 是 |
| POST | /api/v1/archive/{case_id}/publish | 发布案例 | 是 |
| POST | /api/v1/archive/{case_id}/unpublish | 下线案例 | 是 |
| POST | /api/v1/archive/{case_id}/submit-review | 提交案例审核 | 是 |

### 案例检索 (search.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/archive/search | 多维度检索案例（支持法院级别、案由、类型等筛选） | 否 |

### 向量操作 (vector_ops.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/vector/rebuild | 全量重建向量索引 | 否 |
| POST | /api/v1/vector/rebuild/{case_id} | 重建单个案例向量索引 | 否 |

### 向量搜索 (vector_search.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/cases/vector/search | 向量语义搜索（供AI服务HTTP调用） | 否 |

### 批量操作 (batch.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/archive/batch-import | 批量导入案例（最多200条） | 否 |
| GET | /api/v1/archive/export | 导出案例（支持筛选和分页） | 否 |

### 统计信息 (stats.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /api/v1/archive/stats | 获取档案库统计信息 | 否 |
| GET | /api/v1/archive/vector-info | 获取向量库信息 | 否 |
| GET | /api/v1/archive/list | 获取案例列表（分页） | 否 |
| GET | /api/v1/archive/categories | 获取案例分类列表 | 否 |
| GET | /api/v1/archive/case-types | 获取案例类型统计 | 否 |

### 案例分类管理 (case_categories.py)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/archive/case-categories | 创建案例分类 | 否 |
| GET | /api/v1/archive/case-categories | 获取分类列表 | 否 |
| GET | /api/v1/archive/case-categories/{category_id} | 获取分类详情 | 否 |
| PUT | /api/v1/archive/case-categories/{category_id} | 更新分类 | 否 |
| DELETE | /api/v1/archive/case-categories/{category_id} | 删除分类（软删除） | 否 |

## 数据模型

### LegalCase

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| case_number | String(100) | 案号（唯一） |
| case_type | String(50) | 案件类型（索引） |
| title | String(500) | 案例标题 |
| facts | Text | 事实描述 |
| legal_basis | Text | 法律依据 |
| judgment | Text | 判决内容 |
| result | Text | 判决结果 |
| category | String(200) | 分类（索引） |
| keywords | String(500) | 关键词 |
| court | String(200) | 审理法院（索引） |
| court_level | String(50) | 法院级别 |
| judge_date | DateTime | 判决日期（索引） |
| cause_of_action | String(100) | 案由（索引） |
| judgment_result | String(100) | 判决结果类型 |
| key_points | Text | 关键要点 |
| applicable_laws | Text | 适用法律 |
| source | String(200) | 来源 |
| source_url | String(500) | 来源URL |
| is_guiding_case | Boolean | 是否为指导性案例（索引） |
| is_vectorized | Boolean | 是否已向量化（索引） |
| vector_id | String(200) | 向量ID |
| vector_indexed | Boolean | 是否已索引 |
| status | String(20) | 状态（draft/pending_review/published/archived） |
| version | Integer | 版本号 |
| weight | Integer | 权重 |
| is_active | Boolean | 是否激活（索引） |
| is_deleted | Boolean | 是否删除（索引） |

### CaseCategory

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
| ai-service | HTTP | AI 服务调用向量搜索接口获取案例参考 |
| embedding-service | HTTP | 调用嵌入服务生成文本向量 |
| knowledge-service | 相似模式 | 同类知识管理服务，架构模式一致 |
| backend-bff | HTTP | 通过 BFF 代理层对外提供 API |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| DATABASE_URL | postgresql://user:pass@localhost:5432/archive_service | 数据库连接URL |
| ENVIRONMENT | development | 运行环境 |
| VECTOR_STORE_PATH | ./data/chroma_archive | 向量数据存储路径 |
| EMBEDDING_MODEL | shibing624/text2vec-base-chinese | 嵌入模型名称 |
| CORS_ORIGINS | http://localhost:3000,http://localhost:8080 | 允许的CORS来源 |

## 部署信息

- Dockerfile: services/archive-service/Dockerfile
- 健康检查: /health
- 资源限制: CPU 0.5核 / 内存 512MB
