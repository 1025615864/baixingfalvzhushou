# 更新日志

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 安全
- 修复 SSRF 风险：微信登录回调地址白名单验证 (routers/wechat.py)
- 修复权限控制缺失：合同审查接口用户权限验证 (routers/contracts.py)
- 修复命令注入风险：运维脚本参数路径验证 (scripts/ops_manager.py)
- 修复竞态条件：内存缓存添加全局锁保护 (services/cache_service.py)
- 修复断路器调用错误：同步/异步调用修正 (utils/circuit_breaker.py)

### 改进
- 后端代码安全审计完成
- 更新项目工作状态文档
- 完善安全配置验证

### 代码质量
- 修复 IndexError 风险：openapi_exporter.py tags非空检查
- 完善异常处理：periodic_task_runner.py 捕获网络错误
- 完善异常处理：security.py 捕获缓存连接错误
- 完善异常处理：data_sanitizer.py 捕获JSON处理错误
- 修复列表操作问题：websocket_service.py 避免迭代时修改列表
- 完善异常处理：task_scheduler.py 捕获数据库连接错误
- 完善异常处理：voice_manager.py 捕获文件和API错误

### 安全修复（2026-02-02深度审计）
- 修复命令注入风险：performance_benchmark.py 参数验证 + 安全临时文件
- 修复 SSRF 风险：sherpa_asr_service.py URL白名单验证
- 修复 SSRF 风险：rss_ingest_service.py URL白名单验证
- 修复 SSRF 风险：news_workbench_service.py URL白名单验证
- 修复命令注入风险：e2e_test_tool.py 文件名白名单 + 路径验证
- 修复文件扩展名验证：sherpa_asr_service.py 扩展名白名单
- 新增 URL 安全验证工具：security.py validate_external_url()

## [1.0.0] - 2026-01-31

### 新增
- 初始版本发布
- AI 法律助手核心功能
- 用户认证系统（JWT）
- 社区论坛模块
- 新闻资讯模块
- 律所服务模块
- VIP 会员系统
- 积分商城
- 支付系统（微信、支付宝、酷家）
- 文档生成器
- 合同审查功能
- 管理后台

### 功能
- FastAPI 后端框架
- React 前端应用
- PostgreSQL/SQLite 数据库
- Redis 缓存
- Prometheus 监控
- Sentry 错误追踪
- Docker 容器化部署
- Kubernetes Helm Chart

### 修复
- CSRF 防护
- 支付回调幂等性
- 渠道追踪路由前缀
- 审计落库中间件

### 变更
- 升级到 Python 3.13
- 升级到 React 18
- 使用 TailwindCSS 4.x