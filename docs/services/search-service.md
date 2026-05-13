# 搜索服务 (Search Service)

## 服务概览

| 属性 | 值 |
|------|-----|
| 服务名称 | search-service |
| 端口 | 8009 |
| 基础路径 | /api/v1/search |
| 技术栈 | FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis |
| 数据库 | search_service |
| 健康检查 | GET /health |
| 就绪检查 | GET /health/ready |
| 存活检查 | GET /health/live |

## 服务描述

搜索服务提供跨服务聚合搜索能力，支持对新闻、帖子、律师、知识文章等多种内容类型的全文检索。内置搜索历史、搜索建议、热门搜索等功能，通过 Redis 缓存提升搜索性能。

## API 端点

### 搜索路由 (search_router)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | / | 全局搜索（跨类型聚合） | 否 |
| GET | /by-type/{item_type} | 按类型搜索 | 否 |
| GET | /history | 获取搜索历史 | 是 |
| GET | /suggestions | 获取搜索建议 | 否 |
| GET | /hot | 获取热门搜索词 | 否 |

## 数据模型

| 模型 | 说明 |
|------|------|
| SearchIndex | 搜索索引（类型、标题、内容摘要、关联ID） |
| SearchHistory | 搜索历史（用户ID、关键词、搜索时间） |

## 关联服务

| 关联服务 | 通信方式 | 说明 |
|----------|----------|------|
| news-service | HTTP | 搜索新闻内容 |
| community-service | HTTP | 搜索帖子内容 |
| legal-service | HTTP | 搜索律师/律所 |
| knowledge-service | HTTP | 搜索知识文章 |
| user-service | HTTP | 获取用户信息 |
| backend-bff | HTTP | BFF 聚合搜索接口 |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| APP_NAME | search-service | 服务名称 |
| DATABASE_URL | - | PostgreSQL 连接串 |
| CORS_ORIGINS | * | CORS 允许源 |

## 部署信息

- Dockerfile: services/search-service/Dockerfile
- 健康检查: /health
- 资源限制: CPU 0.5核 / 内存 512MB
