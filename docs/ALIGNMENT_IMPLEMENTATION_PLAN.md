# 百姓助手项目 - 前后端深度对齐实施方案

**日期**: 2026-02-11  
**目标**: 前端深度使用后端服务，后端完善前端需求  
**优先级**: 核心业务模块优先
**状态**: ✅ 已完成

---

## ✅ 完成情况

### 已完成的对齐工作

| 模块 | 完成状态 | 说明 |
|------|---------|------|
| **settlement** (结算) | ✅ 完成 | 移除mock，对接真实API |
| **payment** (支付) | ✅ 完成 | 移除mock，对接真实API |
| **ai_quality** | ✅ 完成 | 实现筛选和分页逻辑 |
| **news-admin** | ✅ 完成 | 对接删除评论API |

### 修改的文件

1. `src/features/settlement/hooks/useSettlements.ts` - 移除mock，使用真实API
2. `src/features/settlement/components/SettlementList/index.tsx` - 重构展示逻辑
3. `src/features/payment/hooks/usePayments.ts` - 移除mock，使用真实API
4. `src/features/payment/components/OrderList/index.tsx` - 适配分页数据
5. `src/features/ai_quality/pages/AIQualityPage.tsx` - 实现筛选和分页
6. `src/features/news-admin/api/index.ts` - 添加删除评论API
7. `src/features/news-admin/hooks/useNewsAdmin.ts` - 添加删除评论Hook
8. `src/features/news-admin/pages/NewsCommentsPage.tsx` - 对接删除评论功能

---

## 📊 现状分析

### 关键发现

#### 1. 前端核心业务使用Mock数据 ✅ 已解决

| 模块 | 前端状态 | 后端状态 | 缺口 |
|------|---------|---------|------|
| **settlement** (结算) | ✅ 已对接 | ✅ 完整实现 | **已解决** |
| **payment** (支付) | ✅ 已对接 | ✅ 完整实现 | **已解决** |
| **ai_quality** | ✅ 已完成 | ✅ 已实现 | **已解决** |
| **news-admin** | ✅ 已完成 | ✅ 已实现 | **已解决** |

#### 2. 后端未充分利用的服务

**已实现但前端未使用的服务**:
- ✅ 支付订单系统 (`payment/orders.py`)
- ✅ 钱包余额系统 (`settlement/wallet.py`)
- ✅ 提现系统 (`settlement/withdrawal.py`)
- ✅ 收入记录系统 (`settlement/income.py`)
- ✅ 银行账户管理 (`settlement/bank_account.py`)
- ✅ 支付回调处理 (`payment/callbacks.py`)
- ✅ 退款系统 (`payment/refunds.py`)

---

## 🎯 深度对齐方案

### Phase 1: 核心业务对接（立即执行）

#### 任务1: 对接支付系统 (payment)

**前端改造**:
```typescript
// 当前: src/features/payment/hooks/usePayments.ts
// 使用mock数据

// 目标: 对接后端 /payment/orders 等端点
// 后端端点:
// - POST /payment/orders - 创建订单
// - GET /payment/orders - 获取订单列表
// - GET /payment/orders/{order_no} - 查询订单
// - POST /payment/orders/{order_no}/cancel - 取消订单
// - POST /payment/orders/wechat/jsapi - 微信支付
// - POST /payment/orders/alipay/page - 支付宝支付
```

**实施步骤**:
1. 更新 `payment/api/index.ts` - 对接真实API
2. 更新 `payment/hooks/usePayments.ts` - 使用真实hooks
3. 更新支付页面 - 调用真实API
4. 测试支付流程

**预期收益**: 用户可真实下单支付

---

#### 任务2: 对接结算系统 (settlement)

**前端改造**:
```typescript
// 当前: src/features/settlement/hooks/useSettlements.ts
// 使用mock数据

// 目标: 对接后端 /settlement/* 端点
// 后端端点:
// - GET /settlement/wallet - 获取钱包余额
// - GET /settlement/wallet/transactions - 交易记录
// - GET /settlement/lawyer/income - 收入记录
// - GET /settlement/lawyer/withdrawals - 提现记录
// - POST /settlement/lawyer/withdrawals - 申请提现
// - GET /settlement/bank-accounts - 银行账户列表
```

**实施步骤**:
1. 更新 `settlement/api/index.ts` - 对接真实API
2. 更新 `settlement/hooks/useSettlements.ts` - 使用真实hooks
3. 更新结算页面 - 调用真实API
4. 测试结算流程

**预期收益**: 律师可查看真实收入、申请提现

---

### Phase 2: 功能完善（本周内）

#### 任务3: 完善AI质量监控 (ai_quality)

**前端TODO**:
- AIQualityPage.tsx: "// TODO: 实现筛选逻辑"
- AIQualityPage.tsx: "// TODO: 实现分页逻辑"

**后端已有**:
- `/ai_quality/alerts` - 告警列表
- `/ai_quality/metrics` - 质量指标
- `/ai_quality/feedback` - 反馈处理

**实施**: 完成前端筛选和分页逻辑

---

#### 任务4: 完善新闻评论管理 (news-admin)

**前端TODO**:
- NewsCommentsPage.tsx: "// TODO: 实现删除评论 API"

**后端已有**:
- DELETE `/news/admin/comments/{comment_id}`

**实施**: 对接删除评论API

---

### Phase 3: 服务整合优化（下周）

#### 任务5: 移除冗余代码

**前端**:
- 删除所有mock数据
- 删除未使用的hooks
- 清理console.log

**后端**:
- 保留所有服务（前端将逐步使用）
- 优化未使用的端点

#### 任务6: 统一错误处理

**实施**:
- 前端统一错误提示
- 后端统一错误码

---

## 📋 具体实施计划

### 第1天: 支付系统对接

#### 上午: 更新支付API层
```typescript
// src/features/payment/api/index.ts
import { api } from '@/shared/lib/api/client';

// 创建订单
export async function createOrder(data: CreateOrderDTO) {
  return api.post('/payment/orders', data);
}

// 获取订单列表
export async function getOrders() {
  return api.get('/payment/orders');
}

// 查询订单
export async function getOrder(orderNo: string) {
  return api.get(`/payment/orders/${orderNo}`);
}

// 取消订单
export async function cancelOrder(orderNo: string) {
  return api.post(`/payment/orders/${orderNo}/cancel`);
}

// 创建微信支付订单
export async function createWechatOrder(data: CreateOrderDTO) {
  return api.post('/payment/orders/wechat/jsapi', data);
}

// 创建支付宝订单
export async function createAlipayOrder(data: CreateOrderDTO) {
  return api.post('/payment/orders/alipay/page', data);
}
```

#### 下午: 更新支付Hooks
```typescript
// src/features/payment/hooks/usePayments.ts
import { useQuery, useMutation } from '@tanstack/react-query';
import { createOrder, getOrders, getOrder, cancelOrder } from '../api';

export function useOrders() {
  return useQuery({
    queryKey: ['orders'],
    queryFn: getOrders,
  });
}

export function useCreateOrder() {
  return useMutation({
    mutationFn: createOrder,
  });
}

export function useOrder(orderNo: string) {
  return useQuery({
    queryKey: ['order', orderNo],
    queryFn: () => getOrder(orderNo),
    enabled: !!orderNo,
  });
}

export function useCancelOrder() {
  return useMutation({
    mutationFn: cancelOrder,
  });
}
```

#### 晚上: 测试支付流程

---

### 第2天: 结算系统对接

#### 上午: 更新结算API层
```typescript
// src/features/settlement/api/index.ts
import { api } from '@/shared/lib/api/client';

// 获取钱包余额
export async function getWalletBalance() {
  return api.get('/settlement/wallet');
}

// 获取交易记录
export async function getTransactions(params?: PaginationParams) {
  return api.get('/settlement/wallet/transactions', { params });
}

// 获取收入记录
export async function getIncomeRecords(params?: PaginationParams) {
  return api.get('/settlement/lawyer/income', { params });
}

// 获取提现记录
export async function getWithdrawals(params?: PaginationParams) {
  return api.get('/settlement/lawyer/withdrawals', { params });
}

// 申请提现
export async function createWithdrawal(data: WithdrawalCreateDTO) {
  return api.post('/settlement/lawyer/withdrawals', data);
}

// 获取银行账户
export async function getBankAccounts() {
  return api.get('/settlement/bank-accounts');
}
```

#### 下午: 更新结算Hooks
```typescript
// src/features/settlement/hooks/useSettlements.ts
import { useQuery, useMutation } from '@tanstack/react-query';
import { getWalletBalance, getTransactions, getIncomeRecords, getWithdrawals, createWithdrawal } from '../api';

export function useWalletBalance() {
  return useQuery({
    queryKey: ['wallet', 'balance'],
    queryFn: getWalletBalance,
  });
}

export function useTransactions(params?: PaginationParams) {
  return useQuery({
    queryKey: ['transactions', params],
    queryFn: () => getTransactions(params),
  });
}

export function useIncomeRecords(params?: PaginationParams) {
  return useQuery({
    queryKey: ['income', params],
    queryFn: () => getIncomeRecords(params),
  });
}

export function useWithdrawals(params?: PaginationParams) {
  return useQuery({
    queryKey: ['withdrawals', params],
    queryFn: () => getWithdrawals(params),
  });
}

export function useCreateWithdrawal() {
  return useMutation({
    mutationFn: createWithdrawal,
  });
}
```

#### 晚上: 测试结算流程

---

### 第3天: 完善TODO功能

#### 上午: AI质量监控完善
- 实现筛选逻辑
- 实现分页逻辑

#### 下午: 新闻评论管理完善
- 对接删除评论API

#### 晚上: 整体测试

---

## 🔧 技术细节

### 后端服务清单

#### 支付服务 (payment)
```
POST   /payment/orders                 - 创建订单
GET    /payment/orders                 - 获取订单列表
GET    /payment/orders/{order_no}      - 查询订单
POST   /payment/orders/{order_no}/cancel - 取消订单
POST   /payment/orders/wechat/jsapi    - 微信支付JSAPI
POST   /payment/orders/wechat/native   - 微信支付Native
POST   /payment/orders/alipay/page     - 支付宝电脑网站
POST   /payment/orders/alipay/wap      - 支付宝手机网站
GET    /payment/orders/{order_no}/query/wechat - 查询微信订单
GET    /payment/orders/{order_no}/query/alipay - 查询支付宝订单
POST   /payment/refunds                - 申请退款
GET    /payment/refunds                - 获取退款列表
POST   /payment/cards                  - 添加银行卡
GET    /payment/cards                  - 获取银行卡列表
```

#### 结算服务 (settlement)
```
GET    /settlement/wallet              - 获取钱包余额
GET    /settlement/wallet/transactions - 获取交易记录
GET    /settlement/lawyer/income       - 获取收入记录
GET    /settlement/lawyer/withdrawals  - 获取提现记录
POST   /settlement/lawyer/withdrawals  - 申请提现
GET    /settlement/bank-accounts       - 获取银行账户
POST   /settlement/bank-accounts       - 添加银行账户
PUT    /settlement/bank-accounts/{id}  - 更新银行账户
DELETE /settlement/bank-accounts/{id}  - 删除银行账户
```

### 前端API层结构

```
src/features/payment/
├── api/
│   └── index.ts          - API函数
├── hooks/
│   └── usePayments.ts    - React Query hooks
├── types/
│   └── index.ts          - 类型定义
└── pages/
    └── PaymentPage.tsx   - 支付页面

src/features/settlement/
├── api/
│   └── index.ts          - API函数
├── hooks/
│   └── useSettlements.ts - React Query hooks
├── types/
│   └── index.ts          - 类型定义
└── pages/
    └── SettlementPage.tsx - 结算页面
```

---

## 📈 预期收益

### 立即收益
1. ✅ 用户可以真实下单支付
2. ✅ 律师可以查看真实收入
3. ✅ 律师可以申请提现
4. ✅ 平台可以处理真实资金流转

### 长期收益
1. ✅ 数据真实性提升用户信任
2. ✅ 完整业务流程支持商业化
3. ✅ 减少mock数据维护成本
4. ✅ 前后端完全对齐

---

## ⚠️ 风险提示

### 技术风险
1. **支付回调处理** - 需要确保回调URL可访问
2. **数据一致性** - 支付状态同步需要可靠
3. **错误处理** - 需要完善的错误处理机制

### 业务风险
1. **资金安全** - 需要严格测试支付流程
2. **权限控制** - 确保用户只能访问自己的数据
3. **合规性** - 确保符合支付相关法规

### 缓解措施
1. 充分测试所有支付场景
2. 添加详细的日志记录
3. 实现幂等性保证
4. 设置支付限额和风控

---

## 🚀 开始实施

**建议顺序**:
1. 先实施结算系统（风险较低）
2. 再实施支付系统（风险较高，需要充分测试）
3. 最后完善TODO功能

**预计时间**: 3天完成核心对接

---

**方案制定**: 2026-02-11 12:45  
**版本**: v2.0.0-alignment-implementation
