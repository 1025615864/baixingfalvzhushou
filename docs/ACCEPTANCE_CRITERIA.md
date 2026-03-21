# 百姓助手前端验收标准文档

> 本文档定义了百姓助手系统前端功能的验收标准，用于确保所有功能模块符合质量要求和用户体验标准。

---

## 1. 功能验收标准

### 1.1 会员中心模块 (`membership`)

| 验收项 | 验收标准 | 测试方法 | 优先级 |
|--------|----------|----------|--------|
| 会员价格展示 | - 价格数据从后端 API 正确获取并展示<br>- 支持月度/年度套餐切换<br>- 价格格式化正确（¥XX.XX） | 手动测试 + E2E | P0 |
| 会员权益对比 | - 三种会员等级（普通/VIP/SVIP）权益清晰对比<br>- 权益图标和描述正确<br>- 推荐标签展示正确 | 手动测试 | P0 |
| 会员升级流程 | - 点击升级后跳转支付页面<br>- 升级成功后会员状态实时更新<br>- 升级失败显示错误提示 | E2E 测试 | P0 |
| 支付集成 | - 支付宝/微信支付/IkunPay 支付方式可选<br>- 支付二维码正确生成<br>- 支付状态轮询正常<br>- 支付成功/失败回调处理正确 | 集成测试 | P0 |
| 会员卡展示 | - 当前会员等级和有效期展示<br>- 专属权益标识清晰<br>- 即将到期提醒功能 | 手动测试 | P1 |

**相关文件：**
- 页面：[`frontend-v2/src/features/membership/pages/VipPage.tsx`](frontend-v2/src/features/membership/pages/VipPage.tsx)
- 组件：[`frontend-v2/src/features/membership/components/`](frontend-v2/src/features/membership/components/)
- API：[`frontend-v2/src/features/membership/api/index.ts`](frontend-v2/src/features/membership/api/index.ts)

---

### 1.2 视频咨询模块 (`video-consultation`)

| 验收项 | 验收标准 | 测试方法 | 优先级 |
|--------|----------|----------|--------|
| 视频咨询列表 | - 可用时段列表正确加载<br>- 律师信息（头像、姓名、专长）展示<br>- 支持按日期筛选 | 手动测试 | P0 |
| 律师时段选择器 | - 日历组件正常工作<br>- 可选时段高亮显示<br>- 不可选时段置灰<br>- 选择后价格实时更新 | 手动测试 | P0 |
| 预约流程 | - 填写咨询主题（必填）<br>- 选择时段后确认预约<br>- 预约成功生成订单号<br>- 预约失败显示原因 | E2E 测试 | P0 |
| 视频咨询房间 | - WebRTC 连接正常建立<br>- 音视频双向通信正常<br>- 支持屏幕共享<br>- 网络状态指示器工作正常<br>- 咨询计时准确 | 集成测试 | P0 |
| 咨询记录 | - 历史咨询列表正确展示<br>- 咨询详情可查看<br>- 支持咨询评价 | 手动测试 | P1 |

**相关文件：**
- 页面：[`frontend-v2/src/features/video-consultation/pages/VideoConsultationPage.tsx`](frontend-v2/src/features/video-consultation/pages/VideoConsultationPage.tsx)
- 组件：[`frontend-v2/src/features/video-consultation/components/`](frontend-v2/src/features/video-consultation/components/)
- API：[`frontend-v2/src/features/video-consultation/api/index.ts`](frontend-v2/src/features/video-consultation/api/index.ts)

---

### 1.3 法律文书商城模块 (`legal-document-mall`)

| 验收项 | 验收标准 | 测试方法 | 优先级 |
|--------|----------|----------|--------|
| 文书分类展示 | - 分类树形结构正确<br>- 分类图标和名称匹配<br>- 点击分类筛选文书 | 手动测试 | P0 |
| 文书搜索功能 | - 支持关键词搜索<br>- 搜索结果高亮关键词<br>- 搜索历史记录<br>- 热门搜索推荐 | 手动测试 | P0 |
| 文书详情页 | - 文书预览正常展示<br>- 文书说明完整<br>- 价格和格式信息清晰<br>- 相关文书推荐 | 手动测试 | P1 |
| 购买流程 | - 选择格式后加入购物车<br>- 购物车数量和价格计算正确<br>- 结算流程完整<br>- 支付成功后可下载 | E2E 测试 | P0 |
| 收藏功能 | - 收藏/取消收藏状态切换<br>- 收藏列表正确展示<br>- 收藏状态持久化 | 手动测试 | P1 |

**相关文件：**
- 页面：[`frontend-v2/src/features/legal-document-mall/pages/LegalDocumentMallPage.tsx`](frontend-v2/src/features/legal-document-mall/pages/LegalDocumentMallPage.tsx)
- 组件：[`frontend-v2/src/features/legal-document-mall/components/`](frontend-v2/src/features/legal-document-mall/components/)
- API：[`frontend-v2/src/features/legal-document-mall/api/index.ts`](frontend-v2/src/features/legal-document-mall/api/index.ts)

---

### 1.4 AI 咨询模块 (`ai-consultation`)

| 验收项 | 验收标准 | 测试方法 | 优先级 |
|--------|----------|----------|--------|
| AI 对话功能 | - 消息发送和接收正常<br>- 流式响应正确展示<br>- Markdown 渲染正确<br>- 代码块语法高亮 | 手动测试 | P0 |
| 文件上传 | - 支持 PDF/Word/图片格式<br>- 文件大小限制提示<br>- 上传进度显示<br>- 上传失败重试 | 手动测试 | P0 |
| 语音输入 | - 录音功能正常<br>- 语音转文字准确<br>- 支持长按录音 | 手动测试 | P1 |
| 咨询历史 | - 历史会话列表正确<br>- 会话详情可查看<br>- 支持删除历史 | 手动测试 | P1 |
| 律师转接 | - AI 推荐律师列表展示<br>- 律师信息完整<br>- 一键转接功能正常 | 手动测试 | P1 |

**相关文件：**
- 页面：[`frontend-v2/src/features/ai-consultation/pages/`](frontend-v2/src/features/ai-consultation/pages/)
- API：[`frontend-v2/src/features/ai-consultation/api/index.ts`](frontend-v2/src/features/ai-consultation/api/index.ts)

---

### 1.5 积分系统模块 (`points`)

| 验收项 | 验收标准 | 测试方法 | 优先级 |
|--------|----------|----------|--------|
| 积分余额展示 | - 当前积分正确显示<br>- 积分变动动画效果<br>- 即将过期积分提醒 | 手动测试 | P0 |
| 每日签到 | - 签到按钮状态正确<br>- 连续签到天数显示<br>- 签到奖励弹窗<br>- 签到日历展示 | 手动测试 | P0 |
| 积分商城 | - 商品列表正确加载<br>- 商品详情完整<br>- 兑换流程完整<br>- 库存状态实时更新 | E2E 测试 | P0 |
| 积分历史 | - 流水记录正确展示<br>- 支持按类型筛选<br>- 分页加载正常 | 手动测试 | P1 |

**相关文件：**
- 页面：[`frontend-v2/src/features/points/pages/`](frontend-v2/src/features/points/pages/)
- 组件：[`frontend-v2/src/features/points/components/`](frontend-v2/src/features/points/components/)
- API：[`frontend-v2/src/features/points/api/index.ts`](frontend-v2/src/features/points/api/index.ts)

---

### 1.6 支付模块 (`payment`)

| 验收项 | 验收标准 | 测试方法 | 优先级 |
|--------|----------|----------|--------|
| 支付方式选择 | - 支付宝/微信/IkunPay 可选<br>- 支付方式图标正确<br>- 推荐支付方式标识 | 手动测试 | P0 |
| 订单创建 | - 订单信息正确<br>- 价格计算准确<br>- 优惠券正确应用 | 集成测试 | P0 |
| 支付流程 | - 支付二维码生成<br>- 支付状态轮询<br>- 超时处理<br>- 支付结果展示 | E2E 测试 | P0 |
| 订单管理 | - 订单列表正确展示<br>- 订单详情完整<br>- 支持取消订单<br>- 支持申请退款 | 手动测试 | P1 |

**相关文件：**
- 页面：[`frontend-v2/src/features/payment/pages/OrdersPage.tsx`](frontend-v2/src/features/payment/pages/OrdersPage.tsx)
- 组件：[`frontend-v2/src/features/payment/components/`](frontend-v2/src/features/payment/components/)
- API：[`frontend-v2/src/features/payment/api/index.ts`](frontend-v2/src/features/payment/api/index.ts)

---

### 1.7 通知模块 (`notification`)

| 验收项 | 验收标准 | 测试方法 | 优先级 |
|--------|----------|----------|--------|
| 通知列表 | - 通知正确分类（系统/交易/互动）<br>- 未读/已读状态区分<br>- 分页加载正常 | 手动测试 | P0 |
| 实时推送 | - WebSocket 连接正常<br>- 新消息实时接收<br>- 连接断开重连机制 | 集成测试 | P0 |
| 通知设置 | - 通知开关可配置<br>- 设置保存成功<br>- 免打扰时段设置 | 手动测试 | P1 |

**相关文件：**
- 页面：[`frontend-v2/src/features/notification/pages/NotificationCenter.tsx`](frontend-v2/src/features/notification/pages/NotificationCenter.tsx)
- 服务：[`frontend-v2/src/features/notification/services/websocketService.ts`](frontend-v2/src/features/notification/services/websocketService.ts)

---

### 1.8 用户中心模块 (`user`)

| 验收项 | 验收标准 | 测试方法 | 优先级 |
|--------|----------|----------|--------|
| 个人信息 | - 头像上传和裁剪<br>- 昵称修改<br>- 个人简介编辑<br>- 修改保存成功 | 手动测试 | P0 |
| 账户安全 | - 密码修改流程<br>- 手机/邮箱绑定<br>- 双因素认证设置 | 手动测试 | P0 |
| 登录/注册 | - 手机号登录<br>- 微信登录<br>- 验证码发送和校验<br>- 登录状态持久化 | E2E 测试 | P0 |

**相关文件：**
- 页面：[`frontend-v2/src/pages/Profile/index.tsx`](frontend-v2/src/pages/Profile/index.tsx)
- 认证：[`frontend-v2/src/pages/auth/Login/index.tsx`](frontend-v2/src/pages/auth/Login/index.tsx)

---

## 2. 技术验收标准

### 2.1 API 响应格式规范

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| 响应结构 | 统一响应格式：`{ code, data, message, request_id }` | 单元测试 |
| 错误码 | 错误码定义清晰，前端正确处理 | 单元测试 |
| 分页格式 | 分页数据包含：`{ items, total, page, page_size }` | 单元测试 |
| 时间格式 | 统一使用 ISO 8601 格式 | 单元测试 |

### 2.2 错误处理机制

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| 网络错误 | 显示网络异常提示，支持重试 | 手动测试 |
| 业务错误 | 根据错误码显示对应提示信息 | 单元测试 |
| 超时处理 | 请求超时后显示超时提示 | 单元测试 |
| 全局异常 | 未捕获异常被 ErrorBoundary 捕获 | 手动测试 |

**相关文件：**
- 错误处理：[`frontend-v2/src/utils/errorHandler.ts`](frontend-v2/src/utils/errorHandler.ts)
- 错误边界：[`frontend-v2/src/components/ui/ErrorBoundary.tsx`](frontend-v2/src/components/ui/ErrorBoundary.tsx)

### 2.3 状态管理

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| 全局状态 | Zustand store 状态正确更新 | 单元测试 |
| 服务端状态 | React Query 缓存策略正确配置 | 单元测试 |
| 状态持久化 | 关键状态正确持久化到 localStorage | 手动测试 |
| 状态同步 | 多标签页状态同步 | 手动测试 |

### 2.4 缓存策略

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| API 缓存 | 静态数据缓存 5 分钟，动态数据缓存 30 秒 | 单元测试 |
| 图片缓存 | 静态资源正确配置缓存头 | 手动测试 |
| 缓存失效 | 数据更新后正确失效相关缓存 | 单元测试 |
| 离线缓存 | Service Worker 缓存关键资源 | 手动测试 |

---

## 3. UI/UX 验收标准

### 3.1 页面布局

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| 整体布局 | 页面结构清晰，符合设计稿 | 视觉检查 |
| 导航栏 | 导航项正确，高亮状态准确 | 手动测试 |
| 侧边栏 | 收起/展开功能正常 | 手动测试 |
| 页脚 | 链接正确，版权信息准确 | 手动测试 |

### 3.2 响应式设计

| 断点 | 宽度范围 | 验收标准 |
|------|----------|----------|
| 移动端 | < 768px | 单列布局，隐藏次要元素，触摸友好 |
| 平板 | 768px - 1024px | 两列布局，侧边栏可收起 |
| 桌面 | > 1024px | 完整布局，显示所有元素 |

**测试方法：** 使用 Chrome DevTools 设备模拟器测试

### 3.3 加载状态

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| 页面加载 | 显示骨架屏或加载动画 | 手动测试 |
| 按钮加载 | 提交按钮显示 loading 状态，禁用重复点击 | 手动测试 |
| 列表加载 | 显示加载占位符 | 手动测试 |
| 图片加载 | 显示占位图，加载失败显示错误图 | 手动测试 |

**相关组件：**
- 骨架屏：[`frontend-v2/src/components/ui/Skeleton.tsx`](frontend-v2/src/components/ui/Skeleton.tsx)
- 加载状态：[`frontend-v2/src/components/ui/Loading.tsx`](frontend-v2/src/components/ui/Loading.tsx)

### 3.4 错误状态

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| 空状态 | 显示友好的空状态提示和操作引导 | 手动测试 |
| 错误提示 | Toast 提示样式统一，3 秒后自动消失 | 手动测试 |
| 表单错误 | 字段级错误提示，红色边框标识 | 手动测试 |
| 页面错误 | 404/500 页面友好提示 | 手动测试 |

**相关组件：**
- 空状态：[`frontend-v2/src/components/ui/EmptyState.tsx`](frontend-v2/src/components/ui/EmptyState.tsx)
- Toast：[`frontend-v2/src/components/ui/Toast.tsx`](frontend-v2/src/components/ui/Toast.tsx)

### 3.5 交互反馈

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| 点击反馈 | 按钮点击有视觉反馈（缩放/颜色变化） | 手动测试 |
| 悬停效果 | 可交互元素有悬停效果 | 手动测试 |
| 焦点状态 | 表单元素聚焦有明显边框 | 手动测试 |
| 禁用状态 | 禁用元素样式区分明显 | 手动测试 |

---

## 4. 性能验收标准

### 4.1 加载性能

| 指标 | 目标值 | 测试工具 |
|------|--------|----------|
| 首屏加载时间 (FCP) | < 1.5s | Lighthouse |
| 最大内容绘制 (LCP) | < 2.5s | Lighthouse |
| 首次输入延迟 (FID) | < 100ms | Lighthouse |
| 累积布局偏移 (CLS) | < 0.1 | Lighthouse |
| 交互时间 (TTI) | < 3s | Lighthouse |

### 4.2 Lighthouse 分数

| 类别 | 最低分数 | 目标分数 |
|------|----------|----------|
| Performance | 80 | 90+ |
| Accessibility | 90 | 95+ |
| Best Practices | 90 | 95+ |
| SEO | 90 | 95+ |

**测试命令：**
```bash
npx lighthouse http://localhost:5173 --output html --output-path ./lighthouse-report.html
```

### 4.3 资源优化

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| 代码分割 | 路由级别懒加载，首屏 JS < 500KB | 构建分析 |
| 图片优化 | WebP 格式，懒加载，响应式图片 | 网络面板 |
| 字体优化 | 字体子集化，font-display: swap | 网络面板 |
| Gzip 压缩 | 静态资源启用 Gzip | 网络面板 |

### 4.4 内存管理

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| 无内存泄漏 | 页面切换后内存释放 | Chrome DevTools Memory |
| 事件清理 | 组件卸载时清理事件监听 | 代码审查 |
| 定时器清理 | 组件卸载时清理定时器 | 代码审查 |
| WebSocket 清理 | 页面离开时关闭连接 | 代码审查 |

---

## 5. 兼容性验收标准

### 5.1 浏览器兼容性

| 浏览器 | 版本要求 | 验收标准 |
|--------|----------|----------|
| Chrome | 最新两个主要版本 | 全功能支持 |
| Firefox | 最新两个主要版本 | 全功能支持 |
| Safari | 最新两个主要版本 | 全功能支持 |
| Edge | 最新两个主要版本 | 全功能支持 |

### 5.2 移动端适配

| 设备类型 | 验收标准 | 测试方法 |
|----------|----------|----------|
| iOS Safari | 功能正常，样式正确 | 真机测试 |
| Android Chrome | 功能正常，样式正确 | 真机测试 |
| 微信内置浏览器 | 基础功能正常 | 真机测试 |

### 5.3 屏幕适配

| 分辨率 | 验收标准 |
|--------|----------|
| 320px (小屏手机) | 内容可访问，无横向滚动 |
| 375px (iPhone SE) | 布局正常 |
| 414px (iPhone Plus) | 布局正常 |
| 768px (iPad 竖屏) | 平板布局 |
| 1024px (iPad 横屏) | 平板布局 |
| 1440px (桌面) | 桌面布局 |
| 1920px (大屏) | 内容居中，最大宽度限制 |

---

## 6. 可访问性验收标准

### 6.1 键盘导航

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| Tab 导航 | 所有交互元素可通过 Tab 访问 | 手动测试 |
| 焦点顺序 | 焦点顺序符合视觉顺序 | 手动测试 |
| 焦点可见 | 聚焦元素有明显视觉指示 | 手动测试 |
| 快捷键 | 支持常用快捷键（Esc 关闭弹窗等） | 手动测试 |

### 6.2 屏幕阅读器

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| 图片 alt | 所有图片有描述性 alt 文本 | 代码审查 |
| ARIA 标签 | 交互元素有正确的 ARIA 属性 | 代码审查 |
| 语义化 | 使用语义化 HTML 标签 | 代码审查 |
| 区域标记 | 页面区域有正确的 landmark | 代码审查 |

**相关组件：**
- 跳过链接：[`frontend-v2/src/components/ui/SkipLink.tsx`](frontend-v2/src/components/ui/SkipLink.tsx)

---

## 7. 安全验收标准

### 7.1 XSS 防护

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| 输入过滤 | 用户输入正确转义 | 安全测试 |
| URL 参数 | URL 参数不直接插入 DOM | 代码审查 |
| innerHTML | 避免使用 innerHTML | 代码审查 |

### 7.2 CSRF 防护

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| Token 验证 | 关键请求携带 CSRF Token | 代码审查 |
| SameSite | Cookie 设置 SameSite 属性 | 配置检查 |

### 7.3 敏感信息

| 验收项 | 验收标准 | 测试方法 |
|--------|----------|----------|
| 密码显示 | 密码输入框默认隐藏 | 手动测试 |
| 日志脱敏 | 不在日志中输出敏感信息 | 代码审查 |
| 本地存储 | 敏感数据不存储在 localStorage | 代码审查 |

---

## 8. 验收流程

### 8.1 开发自测

1. 开发完成后，开发者根据本标准进行自测
2. 自测通过后提交代码审查
3. 代码审查通过后合并到开发分支

### 8.2 测试验收

1. 测试环境部署完成后，QA 团队进行功能测试
2. 执行 E2E 测试用例
3. 进行性能测试和兼容性测试
4. 发现问题提交 Bug 跟踪

### 8.3 验收通过标准

| 类别 | 通过条件 |
|------|----------|
| 功能测试 | 所有 P0 用例通过，P1 用例通过率 >= 95% |
| 性能测试 | 所有性能指标达标 |
| 兼容性测试 | 主流浏览器和设备功能正常 |
| 安全测试 | 无高危安全漏洞 |

---

## 附录

### A. E2E 测试文件列表

| 测试文件 | 覆盖模块 |
|----------|----------|
| [`e2e/membership.spec.ts`](frontend-v2/e2e/membership.spec.ts) | 会员模块 |
| [`e2e/video-consultation.spec.ts`](frontend-v2/e2e/video-consultation.spec.ts) | 视频咨询 |
| [`e2e/legal-document.spec.ts`](frontend-v2/e2e/legal-document.spec.ts) | 法律文书 |
| [`e2e/payment.spec.ts`](frontend-v2/e2e/payment.spec.ts) | 支付模块 |
| [`e2e/points.spec.ts`](frontend-v2/e2e/points.spec.ts) | 积分系统 |
| [`e2e/notification.spec.ts`](frontend-v2/e2e/notification.spec.ts) | 通知模块 |
| [`e2e/auth.spec.ts`](frontend-v2/e2e/auth.spec.ts) | 认证模块 |
| [`e2e/responsive.spec.ts`](frontend-v2/e2e/responsive.spec.ts) | 响应式测试 |

### B. 测试命令

```bash
# 运行单元测试
npm run test

# 运行 E2E 测试
npm run test:e2e

# 运行 Lighthouse
npm run lighthouse

# 类型检查
npm run type-check

# 代码检查
npm run lint
```

### C. 相关文档

- [API 文档](./API.md)
- [架构文档](./ARCHITECTURE.md)
- [功能清单](./FEATURES.md)
- [开发指南](./DEVELOPMENT.md)

---

*文档版本: 1.0.0*  
*创建日期: 2026-02-18*  
*项目: 百姓助手*