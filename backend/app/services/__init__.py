"""Backend 服务层 - BFF 聚合层

⚠️ Backend 不再包含业务逻辑。
⚠️ 所有业务逻辑已迁移到对应的微服务中。
⚠️ Backend 仅作为 BFF（Backend for Frontend）层，负责：
  - API 路由转发
  - 数据聚合和转换
  - 认证和授权网关
  - 缓存管理
  - 限流和熔断

微服务列表:
- user-service: 用户认证、管理、画像
- legal-service: 法律咨询、律师、律所、预约
- ai-service: AI 对话、RAG 检索、向量存储
- community-service: 社区帖子、评论、话题
- archive-service: 案例档案、推荐
- knowledge-service: 法律知识库、向量检索
- news-service: 新闻资讯、订阅
- notification-service: 通知推送、消息队列消费
- order-service: 订单管理、Saga 编排
- payment-*/: 支付相关
- points-service: 积分系统
- recommendation-service: 推荐算法
- search-service: 全局搜索
- embedding-service: 向量嵌入服务
"""

__all__ = []
