# 百姓法律助手 v3.0 迭代计划

> 版本：v3.0
> 创建日期：2026-05-10
> 产品经理：AI PM
> 目标：补齐微服务短板、统一基础设施、提升前端质量、完成生产就绪

---

## 一、项目当前进度报备

### 1.1 整体完成度

| 层级 | 完成度 | 说明 |
|------|--------|------|
| BFF 层 (backend) | 85% | 90个路由端点、28个服务、27个模型，核心业务完整 |
| 微服务集群 | 55% | 14个服务中4个达到70%+，5个低于50% |
| 前端 (frontend-v2) | 60% | 30+页面、50+功能模块，TS类型错误较多 |
| 基础设施 | 70% | Docker/K8s/监控基本就绪，部分服务缺配置 |
| 测试体系 | 45% | BFF测试较完整，微服务测试覆盖不足 |

### 1.2 各微服务完成度明细

| 微服务 | 路由数 | 模型数 | 代码行 | Dockerfile | .env示例 | 测试 | 完成度 |
|--------|--------|--------|--------|------------|----------|------|--------|
| legal-service | 80 | 13 | 13100 | ✅ | ✅ | 12文件 | 80% |
| user-service | 51 | 2 | 8900 | ✅ | ✅ | 17文件 | 75% |
| ai-service | 41 | 3 | 7200 | ✅ | ✅ | 4文件 | 70% |
| community-service | 94 | 17 | 11200 | ✅ ❌缺.env | 8文件 | 65% |
| knowledge-service | 27 | 2 | 3800 | ✅ | ✅ | 4文件 | 65% |
| archive-service | 33 | 2 | 3300 | ✅ | ✅ | 4文件 | 60% |
| news-service | 18 | 0 | 2500 | ✅ | ❌ | 2文件 | 55% |
| points-service | 3 | 0 | 1300 | ✅ | ❌ | 2文件 | 50% |
| notification-service | 12 | 0 | 1500 | ✅ | ✅ | 2文件 | 50% |
| order-service | 7 | 2 | 1000 | ✅ | ❌ | 2文件 | 45% |
| payment-channel-service | 5 | 0 | 1200 | ✅ | ❌ | ❌ | 45% |
| recommendation-service | 6 | 0 | 1600 | ✅ | ❌ | 2文件 | 40% |
| search-service | 3 | 0 | 1900 | ✅ | ❌ | 2文件 | 35% |
| embedding-service | 0 | 0 | 500 | ❌ | ✅ | ❌ | 30% |

### 1.3 前端完成度明细

| 模块 | 页面/组件数 | 状态 |
|------|------------|------|
| 认证 (auth) | 登录/注册 | ✅ 功能完整 |
| AI咨询 (chat) | 消息列表/输入 | ✅ 功能完整 |
| 律师 (lawyer) | 列表/详情/匹配 | ⚠️ TS类型错误 |
| 新闻 (news) | 列表/详情 | ⚠️ TS类型错误 |
| 支付 (payment) | 订单/支付弹窗 | ⚠️ TS类型错误 |
| 积分 (points) | 余额/商城/签到 | ⚠️ TS类型错误 |
| 知识库 (knowledge) | 卡片/列表 | ⚠️ TS类型错误 |
| 论坛 (forum/post) | 帖子/评论 | ⚠️ TS类型错误 |
| 社区管理 (forum-admin) | 用户管理 | ⚠️ TS类型错误 |
| 企业合规 (enterprise) | 合规面板/报告 | ⚠️ TS类型错误 |
| 推广 (promotion) | 推广链接/统计 | ⚠️ TS类型错误 |
| 结算 (settlement) | 结算卡片 | ⚠️ TS类型错误 |
| 管理后台 (admin) | 概览/内容/配置 | ✅ 基本完整 |
| UI组件库 | 8个基础组件 | ✅ 完整 |

### 1.4 基础设施完成度

| 组件 | 状态 | 说明 |
|------|------|------|
| Docker Compose (dev) | ✅ | docker-compose.yml + docker-compose.dev.yml |
| Docker Compose (prod) | ✅ | docker-compose.prod.yml |
| Docker Compose (微服务) | ✅ | docker-compose.microservices.yml |
| Docker Compose (监控) | ✅ | docker-compose.monitoring.yml |
| Kubernetes Helm | ✅ | helm/baixing-assistant/ |
| APISIX 网关 | ✅ | apisix/config.yaml + routes.yaml |
| Nginx | ✅ | nginx.conf + SSL配置 |
| Prometheus | ✅ | 5个告警规则文件 |
| Grafana | ✅ | 业务指标面板 |
| Alertmanager | ✅ | 告警管理 |
| CI/CD | ✅ | 4个GitHub Actions工作流 |
| Kafka | ✅ | topics-init.yaml |

### 1.5 关键风险项

| 风险 | 严重程度 | 说明 |
|------|----------|------|
| 前端TS类型错误 | 🔴 高 | 200+处类型错误，影响构建和可维护性 |
| 微服务测试覆盖不足 | 🔴 高 | 多数服务仅有2个测试文件 |
| 认证系统双轨制 | 🟡 中 | BFF和微服务使用不同认证实现 |
| 部分服务缺.env示例 | 🟡 中 | 6个服务缺少环境变量模板 |
| BFF层业务逻辑未完全剥离 | 🟡 中 | main.py仍含结算/微信支付定时任务 |

---

## 二、v3.0 迭代目标

### 总体目标

将项目从"功能基本可用"推进到"生产就绪"，重点补齐短板、统一标准、提升质量。

| 编号 | 目标 | 优先级 | 验收标准 |
|------|------|--------|---------|
| G1 | 修复前端全部TS类型错误 | P0 | `tsc --noEmit` 零错误 |
| G2 | 补齐微服务核心功能 | P0 | 5个低完成度服务达到60%+ |
| G3 | 统一认证体系 | P0 | 全服务使用JWTKeyManager + RS256 |
| G4 | 补齐微服务测试 | P1 | 每个服务至少10个测试用例 |
| G5 | 补齐基础设施配置 | P1 | 所有服务有Dockerfile + .env.example |
| G6 | BFF层瘦身 | P1 | main.py < 400行，业务逻辑迁移至微服务 |
| G7 | 前端E2E测试覆盖 | P2 | 核心流程E2E测试通过 |
| G8 | 性能基准建立 | P2 | API P95 < 500ms，首页加载 < 2s |

---

## 三、迭代计划

### Phase 1: 质量修复 (第1-2周)

> 目标：消除阻塞性质量问题，建立统一标准

#### 任务 1.1: 修复前端TypeScript类型错误

| 子任务 | 涉及模块 | 说明 |
|--------|----------|------|
| 1.1.1 | knowledge | 修复KnowledgeItem/KnowledgeSearchFilters类型缺失 |
| 1.1.2 | lawyer | 修复Lawyer类型缺失字段(status/lawFirm/bio/pricePerHour) |
| 1.1.3 | news | 修复News/NewsFilters类型缺失 |
| 1.1.4 | payment | 修复PaymentOrder缺失字段 + CreateOrderDTO/WalletBalance/Transaction |
| 1.1.5 | document | 修复Document类型缺失(type/fileType/description/tags) |
| 1.1.6 | settlement | 修复SettlementRecord/IncomeRecord/WithdrawalRequest类型 |
| 1.1.7 | promotion | 修复PromotionStats缺失字段 + 缺失组件模块 |
| 1.1.8 | points | 修复PaginationProps/PointsBalanceProps属性不匹配 |
| 1.1.9 | post | 修复CreatePostRequest/UpdatePostRequest类型兼容 |
| 1.1.10 | 全局 | 安装@types/qrcode，修复lucide-react类型声明 |

**验收标准**：
- [ ] `npx tsc --noEmit` 零错误
- [ ] `npm run build` 成功
- [ ] 所有页面正常渲染

#### 任务 1.2: 统一认证体系

| 子任务 | 涉及文件 | 说明 |
|--------|----------|------|
| 1.2.1 | services/common/middleware/auth.py | 移除HS256硬编码默认密钥 |
| 1.2.2 | services/common/security/jwt_manager.py | 统一使用JWTKeyManager |
| 1.2.3 | backend/app/utils/deps.py | 对齐common认证实现 |
| 1.2.4 | 所有微服务 | 更新认证中间件引用 |

**验收标准**：
- [ ] 无硬编码JWT密钥
- [ ] 所有服务使用RS256或统一的HS256+密钥管理
- [ ] Token在服务间可验证

#### 任务 1.3: 补齐服务环境配置

| 子任务 | 涉及服务 | 说明 |
|--------|----------|------|
| 1.3.1 | community-service | 创建.env.example |
| 1.3.2 | news-service | 创建.env.example |
| 1.3.3 | order-service | 创建requirements.txt + .env.example |
| 1.3.4 | points-service | 创建.env.example |
| 1.3.5 | payment-channel-service | 创建.env.example |
| 1.3.6 | recommendation-service | 创建.env.example |
| 1.3.7 | search-service | 创建.env.example |
| 1.3.8 | embedding-service | 创建Dockerfile |

**验收标准**：
- [ ] 所有14个微服务有Dockerfile
- [ ] 所有14个微服务有.env.example
- [ ] 所有14个微服务有requirements.txt

---

### Phase 2: 功能补齐 (第3-5周)

> 目标：将低完成度服务提升到可用水平

#### 任务 2.1: search-service 功能补齐 (35% → 65%)

| 子任务 | 说明 |
|--------|------|
| 2.1.1 | 实现全局搜索API（用户/律师/帖子/新闻/知识库） |
| 2.1.2 | 实现搜索建议API（热门搜索/联想词） |
| 2.1.3 | 集成PostgreSQL全文搜索 + pgvector向量检索 |
| 2.1.4 | 添加搜索结果缓存（Redis） |

#### 任务 2.2: recommendation-service 功能补齐 (40% → 65%)

| 子任务 | 说明 |
|--------|------|
| 2.2.1 | 实现律师推荐API（基于专业度/评分/距离） |
| 2.2.2 | 实现新闻推荐API（基于用户兴趣/热点） |
| 2.2.3 | 实现首页综合推荐API |
| 2.2.4 | 添加用户行为事件消费（Kafka） |

#### 任务 2.3: points-service 功能补齐 (50% → 70%)

| 子任务 | 说明 |
|--------|------|
| 2.3.1 | 实现积分增减/流水查询完整API |
| 2.3.2 | 实现积分商城/兑换订单API |
| 2.3.3 | 实现签到/每日任务API |
| 2.3.4 | 添加Kafka事件消费（支付成功→积分增加） |

#### 任务 2.4: order-service 功能补齐 (45% → 70%)

| 子任务 | 说明 |
|--------|------|
| 2.4.1 | 实现订单创建/查询/取消API |
| 2.4.2 | 集成Saga编排（订单→支付→积分→通知） |
| 2.4.3 | 实现订单状态机 |
| 2.4.4 | 添加订单超时自动取消 |

#### 任务 2.5: payment-channel-service 功能补齐 (45% → 70%)

| 子任务 | 说明 |
|--------|------|
| 2.5.1 | 实现支付宝/微信支付通道适配器 |
| 2.5.2 | 实现支付回调验签 |
| 2.5.3 | 实现退款流程 |
| 2.5.4 | 添加幂等控制（Redis分布式锁） |

#### 任务 2.6: embedding-service 功能补齐 (30% → 60%)

| 子任务 | 说明 |
|--------|------|
| 2.6.1 | 创建Dockerfile |
| 2.6.2 | 实现文本嵌入API |
| 2.6.3 | 实现批量嵌入API |
| 2.6.4 | 添加健康检查端点 |

---

### Phase 3: 质量提升 (第6-7周)

> 目标：提升测试覆盖率，BFF层瘦身

#### 任务 3.1: 补齐微服务测试

| 服务 | 目标用例数 | 重点覆盖 |
|------|-----------|---------|
| search-service | 10+ | 搜索API、缓存逻辑 |
| recommendation-service | 10+ | 推荐算法、事件消费 |
| points-service | 15+ | 积分增减、并发安全、兑换流程 |
| order-service | 15+ | 订单状态机、Saga补偿 |
| payment-channel-service | 15+ | 支付流程、回调验签、幂等 |
| news-service | 10+ | 新闻CRUD、AI标注 |
| notification-service | 10+ | 通知发送、模板管理 |
| embedding-service | 5+ | 嵌入API、批量处理 |

#### 任务 3.2: BFF层瘦身

| 子任务 | 说明 |
|--------|------|
| 3.2.1 | 结算定时任务迁移到order-service |
| 3.2.2 | 微信支付证书刷新迁移到payment-channel-service |
| 3.2.3 | 审核SLA定时任务迁移到legal-service |
| 3.2.4 | health/detailed端点简化 |
| 3.2.5 | metrics逻辑移到common/monitoring |

**验收标准**：
- [ ] main.py < 400行
- [ ] BFF层无业务逻辑，仅做路由转发和数据聚合

#### 任务 3.3: 前端E2E测试

| 子任务 | 说明 |
|--------|------|
| 3.3.1 | 用户注册/登录流程 |
| 3.3.2 | AI咨询对话流程 |
| 3.3.3 | 律师搜索/预约流程 |
| 3.3.4 | 支付/订单流程 |
| 3.3.5 | 社区发帖/评论流程 |

---

### Phase 4: 生产就绪 (第8周)

> 目标：性能优化、安全加固、上线准备

#### 任务 4.1: 性能基准

| 指标 | 目标 | 测试方法 |
|------|------|---------|
| API P95响应时间 | < 500ms | k6/locust压测 |
| 首页加载时间 | < 2s | Lighthouse |
| 数据库慢查询 | < 100ms | 慢查询日志 |
| 并发用户支持 | 500+ | 压测 |

#### 任务 4.2: 安全加固

| 子任务 | 说明 |
|--------|------|
| 4.2.1 | OpenAPI敏感字段标记writeOnly |
| 4.2.2 | 限流降级策略（Redis不可用时内存限流） |
| 4.2.3 | 清理测试中硬编码密码 |
| 4.2.4 | 生产环境禁用openapi.json端点 |

#### 任务 4.3: 上线检查

| 子任务 | 说明 |
|--------|------|
| 4.3.1 | 所有Docker镜像构建成功 |
| 4.3.2 | docker-compose.prod.yml 全服务启动 |
| 4.3.3 | 健康检查端点全部正常 |
| 4.3.4 | 监控面板数据正常 |
| 4.3.5 | 告警规则触发验证 |

---

## 四、里程碑

| 里程碑 | 日期 | 交付物 |
|--------|------|--------|
| M1: 质量修复完成 | 第2周末 | TS零错误 + 认证统一 + 配置补齐 |
| M2: 功能补齐完成 | 第5周末 | 5个服务达到65%+ |
| M3: 质量提升完成 | 第7周末 | 测试覆盖 + BFF瘦身 + E2E |
| M4: 生产就绪 | 第8周末 | 性能达标 + 安全加固 + 上线 |

---

## 五、风险控制

| 风险 | 影响 | 概率 | 应对策略 |
|------|------|------|---------|
| TS类型修复引入新bug | 高 | 中 | 逐模块修复，每模块修复后运行vitest |
| 微服务功能补齐周期长 | 高 | 高 | 优先核心服务(search/points/order) |
| BFF瘦身导致功能回归 | 高 | 中 | 充分集成测试，灰度发布 |
| 认证统一影响现有Token | 高 | 低 | 支持双算法过渡期 |
| 前端E2E测试环境依赖 | 中 | 中 | 使用mock服务，减少外部依赖 |

---

## 六、资源需求

| 角色 | 人数 | 周期 |
|------|------|------|
| 后端开发 | 2-3 | 8周 |
| 前端开发 | 1-2 | 4周(Phase 1+3) |
| 测试 | 1 | 8周 |
| DevOps | 1 | 2周(Phase 4) |
