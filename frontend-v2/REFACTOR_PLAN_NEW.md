# 前端功能模块重构计划

## 重构原则

### 1. 不迁移，直接重构
- ✅ 使用最新技术栈重新实现
- ✅ Feature-Based 架构
- ✅ 零 any 类型
- ✅ 完整类型定义
- ✅ 测试驱动开发

### 2. 技术栈
- **React 18.2** - 函数组件 + Hooks
- **TypeScript 5.3** - 严格模式
- **React Query** - 服务端状态管理
- **Zustand** - 客户端状态管理
- **Tailwind CSS** - 样式
- **Vitest + MSW** - 测试

### 3. 架构模式

```
src/features/[module]/
├── api/
│   └── index.ts              # API 调用函数
├── components/
│   ├── [ComponentName].tsx   # 组件
│   └── index.ts              # 导出
├── hooks/
│   ├── use[HookName].ts      # React Query Hooks
│   └── index.ts              # 导出
├── pages/
│   └── [PageName].tsx        # 页面组件
├── store/
│   └── [module]Store.ts      # Zustand Store (可选)
├── types/
│   └── index.ts              # 类型定义
└── __tests__/
    └── [test].test.tsx       # 测试文件
```

## 重构模块清单

### Phase 1: Payment 模块 (优先级: 高)
**功能范围**:
- ✅ 订单管理 (创建、查询、取消)
- ✅ 支付流程 (微信、支付宝)
- ✅ 钱包系统 (充值、余额查询)
- ✅ 退款管理

**核心组件**:
1. `OrderList` - 订单列表
2. `OrderCard` - 订单卡片
3. `PaymentMethodSelector` - 支付方式选择
4. `WalletBalance` - 钱包余额
5. `RechargeModal` - 充值弹窗

**API Endpoints**:
```typescript
// 订单
GET    /api/payment/orders           # 获取订单列表
POST   /api/payment/orders           # 创建订单
GET    /api/payment/orders/:id       # 获取订单详情
POST   /api/payment/orders/:id/cancel # 取消订单

// 支付
POST   /api/payment/pay              # 发起支付
POST   /api/payment/callback         # 支付回调

// 钱包
GET    /api/payment/wallet/balance   # 获取余额
POST   /api/payment/wallet/recharge  # 充值
GET    /api/payment/wallet/history   # 交易记录

// 退款
POST   /api/payment/refund           # 申请退款
GET    /api/payment/refund/:id       # 退款详情
```

**类型定义**:
```typescript
// types/index.ts
export type PaymentMethod = 'wechat' | 'alipay' | 'wallet';
export type OrderStatus = 'pending' | 'paid' | 'cancelled' | 'refunded';

export interface Order {
  id: string;
  amount: number;
  status: OrderStatus;
  paymentMethod?: PaymentMethod;
  createdAt: string;
  updatedAt: string;
}

export interface Wallet {
  balance: number;
  frozenAmount: number;
}

export interface PaymentConfig {
  wechatEnabled: boolean;
  alipayEnabled: boolean;
  minAmount: number;
  maxAmount: number;
}
```

### Phase 2: Lawyer 模块 (优先级: 高)
**功能范围**:
- ✅ 律师信息管理
- ✅ 预约系统
- ✅ 评价系统
- ✅ 律师工作台

**核心组件**:
1. `LawyerCard` - 律师卡片
2. `LawyerList` - 律师列表
3. `BookingModal` - 预约弹窗
4. `ReviewModal` - 评价弹窗
5. `LawyerProfile` - 律师主页

**API Endpoints**:
```typescript
// 律师信息
GET    /api/lawyers                  # 律师列表
GET    /api/lawyers/:id              # 律师详情
GET    /api/lawyers/:id/schedule     # 律师日程

// 预约
POST   /api/bookings                 # 创建预约
GET    /api/bookings                 # 预约列表
PUT    /api/bookings/:id             # 更新预约
DELETE /api/bookings/:id             # 取消预约

// 评价
POST   /api/reviews                  # 创建评价
GET    /api/reviews                  # 评价列表
```

**类型定义**:
```typescript
export interface Lawyer {
  id: string;
  name: string;
  avatar?: string;
  specialty: string[];
  experience: number; // 年
  rating: number;
  consultationCount: number;
  bio?: string;
  verified: boolean;
}

export interface Booking {
  id: string;
  lawyerId: string;
  userId: string;
  scheduledAt: string;
  duration: number; // 分钟
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled';
  notes?: string;
}

export interface Review {
  id: string;
  lawyerId: string;
  userId: string;
  rating: number;
  comment?: string;
  createdAt: string;
}
```

### Phase 3: Consultation 模块 (优先级: 中)
**功能范围**:
- ✅ AI 咨询增强
- ✅ 律师咨询预约
- ✅ 咨询记录管理

**核心组件**:
1. `ConsultationChat` - 咨询对话
2. `ConsultationHistory` - 历史记录
3. `ConsultationDetail` - 详情页

### Phase 4: Document 模块 (优先级: 中)
**功能范围**:
- ✅ 文档生成
- ✅ 模板管理
- ✅ 文档历史

### Phase 5: News 模块 (优先级: 低)
**功能范围**:
- ✅ 新闻资讯
- ✅ 分类管理
- ✅ 收藏功能

### Phase 6: Forum 模块 (优先级: 低)
**功能范围**:
- ✅ 帖子管理
- ✅ 评论系统
- ✅ 点赞收藏

## 实施步骤

### Step 1: 准备工作
1. ✅ 修复现有测试
2. ✅ 完善 TypeScript 类型
3. ✅ 建立重构标准

### Step 2: Payment 模块重构
1. 定义类型 (types/index.ts)
2. 实现 API 层 (api/index.ts)
3. 创建 React Query Hooks (hooks/usePayment.ts)
4. 实现组件 (components/*)
5. 编写测试 (__tests__/*)
6. 集成到路由

### Step 3-6: 其他模块 (重复步骤2)

## 质量标准

### 代码质量
- ✅ TypeScript 严格模式通过
- ✅ ESLint 零错误零警告
- ✅ 测试覆盖率 >80%
- ✅ 组件单元测试通过
- ✅ API mock 测试通过

### 性能标准
- ✅ 组件懒加载
- ✅ React Query 缓存策略
- ✅ 虚拟滚动 (长列表)
- ✅ 图片懒加载

### 安全标准
- ✅ XSS 防护
- ✅ CSRF Token
- ✅ 输入验证
- ✅ 敏感数据加密

### 用户体验
- ✅ Loading 状态
- ✅ 错误处理
- ✅ 空状态展示
- ✅ 响应式设计

---

**创建时间**: 2026-02-14
**预计完成**: 2-4周
**当前阶段**: Step 1 准备工作
