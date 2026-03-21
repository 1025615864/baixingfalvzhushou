# 百姓助手前端完善与集成计划

> 基于后端核心优化成果（ApiResponse 统一响应格式、错误码体系、Onboarding 持久化等）的前端完善与集成规划

**文档版本**: 1.0  
**创建日期**: 2026-02-18  
**预计总周期**: 10 周  

---

## 目录

1. [背景与目标](#背景与目标)
2. [现状分析](#现状分析)
3. [五阶段实施计划](#五阶段实施计划)
   - [阶段一：前端 API 请求层重构（2 周）](#阶段一前端-api-请求层重构 2 周)
   - [阶段二：新功能模块前端落地（3 周）](#阶段二新功能模块前端落地 3 周)
   - [阶段三：状态管理优化与数据持久化（2 周）](#阶段三状态管理优化与数据持久化 2 周)
   - [阶段四：联调测试与验收（2 周）](#阶段四联调测试与验收 2 周)
   - [阶段五：性能优化与上线准备（1 周）](#阶段五性能优化与上线准备 1 周)
4. [关键技术决策](#关键技术决策)
5. [风险与应对](#风险与应对)
6. [验收标准](#验收标准)

---

## 背景与目标

### 背景

后端已完成以下核心优化：

1. **统一响应格式** - `ApiResponse<T>` 和 `PaginatedResponse<T>` 标准化响应结构
2. **错误码体系** - 完整的 `ErrorCode` 枚举（1000-9999 范围）
3. **Onboarding 持久化** - 用户引导流程数据持久化
4. **会员体系** - 会员中心、权益管理
5. **视频咨询** - 在线视频预约、咨询流程
6. **法律文书商城** - 文书浏览、购买、下载

### 目标

1. 完成前端与后端新 API 的全面对接
2. 实现会员中心、视频咨询、法律文书商城三大新功能模块
3. 优化状态管理与数据持久化机制
4. 通过完整的联调测试与 E2E 测试
5. 完成性能优化并上线

---

## 现状分析

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.x | UI 框架 |
| TypeScript | 5.x | 类型系统 |
| Zustand | 4.x | 状态管理 |
| React Query | 5.x | 服务端状态管理 |
| Axios | 1.x | HTTP 客户端 |
| Tailwind CSS | 3.x | 样式框架 |
| shadcn/ui | latest | UI 组件库 |

### 现有前端结构

```
frontend-v2/
├── src/
│   ├── features/          # 功能模块
│   │   ├── membership/    # 会员中心 (待完善)
│   │   ├── video-consultation/  # 视频咨询 (待完善)
│   │   ├── legal-document-mall/ # 法律文书商城 (待完善)
│   │   └── ...
│   ├── shared/
│   │   └── lib/
│   │       └── api/
│   │           ├── client.ts      # API 客户端
│   │           └── tokenManager.ts # Token 管理
│   └── utils/
│       └── errorHandler.ts  # 错误处理
```

### 需要改进的问题

1. **响应类型不匹配** - 前端 `ApiResponse<T>` 定义与后端不一致
2. **错误码未映射** - 前端未与后端 `ErrorCode` 建立映射关系
3. **分页参数不统一** - 前端分页响应格式与后端不一致
4. **新功能模块缺失** - 会员中心、视频咨询、法律文书商城 UI 组件待完善

---

## 五阶段实施计划

### 阶段一：前端 API 请求层重构（2 周）

#### 目标

建立与后端完全匹配的 API 请求层，包括统一响应类型、错误处理和分页机制。

#### 任务详情

| ID | 任务 | 工时 | 优先级 | 负责人 | 产出物 |
|----|------|------|--------|--------|--------|
| 1.1 | 统一定义 `ApiResponse<T>` 和 `PaginatedResponse<T>` 类型 | 2d | P0 | 前端 A | [`client.ts`](frontend-v2/src/shared/lib/api/client.ts) 类型定义 |
| 1.2 | 建立后端 `ErrorCode` 与前端错误消息的映射表 | 1d | P0 | 前端 B | [`errorCodeMap.ts`](frontend-v2/src/utils/errorCodeMap.ts) |
| 1.3 | 重构 API 客户端响应解包逻辑 | 2d | P0 | 前端 A | 统一的响应解包工具函数 |
| 1.4 | 实现全局错误拦截与 Toast 提示 | 2d | P0 | 前端 B | 错误处理中间件 |
| 1.5 | 分页参数统一（前端 `page/pageSize` ↔ 后端 `page/page_size`） | 1d | P1 | 前端 A | 参数转换器 |
| 1.6 | 请求/响应日志与性能监控 | 2d | P2 | 前端 B | 性能埋点代码 |

#### 技术实现

##### 1.1 统一响应类型定义

```typescript
// frontend-v2/src/shared/lib/api/types.ts

/**
 * 后端 ErrorCode 枚举映射
 * 对应 backend/app/core/response.py::ErrorCode
 */
export enum BackendErrorCode {
  // 通用错误 1000-1999
  SUCCESS = 0,
  INVALID_PARAMS = 1001,
  UNAUTHORIZED = 1002,
  FORBIDDEN = 1003,
  NOT_FOUND = 1004,
  INTERNAL_ERROR = 1005,
  CONFLICT = 1006,
  VALIDATION_ERROR = 1007,
  RATE_LIMIT_EXCEEDED = 1008,
  SERVICE_UNAVAILABLE = 1009,
  
  // 用户相关 2000-2999
  USER_NOT_FOUND = 2001,
  USER_ALREADY_EXISTS = 2002,
  INVALID_CREDENTIALS = 2003,
  TOKEN_EXPIRED = 2004,
  TOKEN_INVALID = 2005,
  
  // 支付相关 3000-3999
  PAYMENT_FAILED = 3001,
  PAYMENT_AMOUNT_MISMATCH = 3002,
  PAYMENT_ORDER_NOT_FOUND = 3003,
  PAYMENT_ORDER_ALREADY_PAID = 3004,
  PAYMENT_ORDER_CANCELLED = 3005,
  
  // AI 相关 4000-4999
  AI_SERVICE_UNAVAILABLE = 4001,
  AI_QUOTA_EXCEEDED = 4002,
  AI_REQUEST_TOO_LONG = 4003,
  AI_RESPONSE_INVALID = 4004,
  AI_TIMEOUT = 4005,
  
  // 会员相关 5100-5199
  MEMBERSHIP_NOT_FOUND = 5101,
  MEMBERSHIP_ALREADY_ACTIVE = 5102,
  MEMBERSHIP_EXPIRED = 5103,
  MEMBERSHIP_BENEFIT_NOT_AVAILABLE = 5104,
  
  // 视频咨询相关 5200-5299
  VIDEO_CONSULTATION_NOT_FOUND = 5201,
  VIDEO_CONSULTATION_ALREADY_BOOKED = 5202,
  VIDEO_CONSULTATION_TIME_CONFLICT = 5203,
  VIDEO_CONSULTATION_NOT_AVAILABLE = 5204,
  
  // 法律文书相关 5300-5399
  LEGAL_DOCUMENT_NOT_FOUND = 5301,
  LEGAL_DOCUMENT_ALREADY_PURCHASED = 5302,
  LEGAL_DOCUMENT_DOWNLOAD_EXPIRED = 5303,
}

/**
 * 分页信息
 * 对应 backend/app/core/response.py::PaginationInfo
 */
export interface PaginationInfo {
  page: number;        // 当前页码
  page_size: number;   // 每页大小
  total: number;       // 总记录数
  total_pages: number; // 总页数
}

/**
 * 统一 API 响应格式
 * 对应 backend/app/core/response.py::ApiResponse
 */
export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data: T | null;
  error_code: BackendErrorCode | null;
}

/**
 * 分页 API 响应格式
 * 对应 backend/app/core/response.py::PaginatedResponse
 */
export interface PaginatedResponse<T> {
  success: boolean;
  message: string;
  data: T[];
  pagination: PaginationInfo;
}
```

##### 1.2 错误码映射表

```typescript
// frontend-v2/src/utils/errorCodeMap.ts

import { BackendErrorCode } from '@/shared/lib/api/types';

export const ERROR_CODE_MESSAGES: Record<number, string> = {
  // 通用错误
  [BackendErrorCode.SUCCESS]: '操作成功',
  [BackendErrorCode.INVALID_PARAMS]: '请求参数无效',
  [BackendErrorCode.UNAUTHORIZED]: '未授权，请登录',
  [BackendErrorCode.FORBIDDEN]: '权限不足',
  [BackendErrorCode.NOT_FOUND]: '资源不存在',
  [BackendErrorCode.INTERNAL_ERROR]: '系统内部错误',
  [BackendErrorCode.CONFLICT]: '请求冲突',
  [BackendErrorCode.VALIDATION_ERROR]: '参数验证失败',
  [BackendErrorCode.RATE_LIMIT_EXCEEDED]: '请求过于频繁',
  [BackendErrorCode.SERVICE_UNAVAILABLE]: '服务不可用',
  
  // 用户错误
  [BackendErrorCode.USER_NOT_FOUND]: '用户不存在',
  [BackendErrorCode.USER_ALREADY_EXISTS]: '用户已存在',
  [BackendErrorCode.INVALID_CREDENTIALS]: '用户名或密码错误',
  [BackendErrorCode.TOKEN_EXPIRED]: '登录已过期，请重新登录',
  [BackendErrorCode.TOKEN_INVALID]: '无效的令牌',
  
  // 支付错误
  [BackendErrorCode.PAYMENT_FAILED]: '支付失败',
  [BackendErrorCode.PAYMENT_AMOUNT_MISMATCH]: '支付金额不匹配',
  [BackendErrorCode.PAYMENT_ORDER_NOT_FOUND]: '订单不存在',
  [BackendErrorCode.PAYMENT_ORDER_ALREADY_PAID]: '订单已支付',
  [BackendErrorCode.PAYMENT_ORDER_CANCELLED]: '订单已取消',
  
  // AI 错误
  [BackendErrorCode.AI_SERVICE_UNAVAILABLE]: 'AI 服务不可用',
  [BackendErrorCode.AI_QUOTA_EXCEEDED]: 'AI 配额已用完',
  [BackendErrorCode.AI_REQUEST_TOO_LONG]: '请求内容过长',
  [BackendErrorCode.AI_RESPONSE_INVALID]: 'AI 响应无效',
  [BackendErrorCode.AI_TIMEOUT]: 'AI 请求超时',
  
  // 会员错误
  [BackendErrorCode.MEMBERSHIP_NOT_FOUND]: '会员信息不存在',
  [BackendErrorCode.MEMBERSHIP_ALREADY_ACTIVE]: '会员已激活',
  [BackendErrorCode.MEMBERSHIP_EXPIRED]: '会员已过期',
  [BackendErrorCode.MEMBERSHIP_BENEFIT_NOT_AVAILABLE]: '会员权益不可用',
  
  // 视频咨询错误
  [BackendErrorCode.VIDEO_CONSULTATION_NOT_FOUND]: '视频咨询记录不存在',
  [BackendErrorCode.VIDEO_CONSULTATION_ALREADY_BOOKED]: '该时段已被预约',
  [BackendErrorCode.VIDEO_CONSULTATION_TIME_CONFLICT]: '时间冲突',
  [BackendErrorCode.VIDEO_CONSULTATION_NOT_AVAILABLE]: '律师该时段不可用',
  
  // 法律文书错误
  [BackendErrorCode.LEGAL_DOCUMENT_NOT_FOUND]: '文书不存在',
  [BackendErrorCode.LEGAL_DOCUMENT_ALREADY_PURCHASED]: '您已购买该文书',
  [BackendErrorCode.LEGAL_DOCUMENT_DOWNLOAD_EXPIRED]: '下载链接已过期',
};

/**
 * 根据错误码获取错误消息
 */
export function getErrorMessage(code: number): string {
  return ERROR_CODE_MESSAGES[code] || '未知错误，请稍后重试';
}
```

##### 1.3 API 客户端重构

```typescript
// frontend-v2/src/shared/lib/api/client.ts (重构后)

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import type { ApiResponse, PaginatedResponse } from './types';
import { getErrorMessage } from '@/utils/errorCodeMap';

// ... 现有代码保留 ...

/**
 * 解包 API 响应
 * 自动处理 success 字段和错误码
 */
function unwrapResponse<T>(response: AxiosResponse<ApiResponse<T>>): T {
  const { data } = response;
  
  if (!data.success) {
    const message = data.error_code 
      ? getErrorMessage(data.error_code) 
      : data.message || '请求失败';
    throw new ApiError(message, data.error_code);
  }
  
  return data.data as T;
}

/**
 * 解包分页响应
 */
function unwrapPaginatedResponse<T>(
  response: AxiosResponse<PaginatedResponse<T>>
): { items: T[]; pagination: PaginationInfo } {
  const { data } = response;
  
  if (!data.success) {
    const message = data.error_code 
      ? getErrorMessage(data.error_code) 
      : data.message || '请求失败';
    throw new ApiError(message, data.error_code);
  }
  
  return {
    items: data.data,
    pagination: data.pagination,
  };
}

export const api = {
  // 普通请求 - 自动解包
  get: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.get<ApiResponse<T>>(url, config).then(unwrapResponse),
  
  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.post<ApiResponse<T>>(url, data, config).then(unwrapResponse),
  
  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.put<ApiResponse<T>>(url, data, config).then(unwrapResponse),
  
  patch: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.patch<ApiResponse<T>>(url, data, config).then(unwrapResponse),
  
  delete: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.delete<ApiResponse<T>>(url, config).then(unwrapResponse),
  
  // 分页请求 - 自动解包并返回 { items, pagination }
  getList: <T>(url: string, config?: AxiosRequestConfig) =>
    apiClient.get<PaginatedResponse<T>>(url, config).then(unwrapPaginatedResponse),
};
```

#### 里程碑

- [ ] 完成所有类型定义文件
- [ ] API 客户端重构完成并通过单元测试
- [ ] 错误处理机制与后端 ErrorCode 完全映射
- [ ] 现有功能回归测试通过

---

### 阶段二：新功能模块前端落地（3 周）

#### 目标

完成会员中心、视频咨询、法律文书商城三大功能模块的 UI 组件实现和 API 对接。

#### 任务详情

##### 2.1 会员中心模块（1 周）

| ID | 任务 | 工时 | 优先级 | 产出物 |
|----|------|------|--------|--------|
| 2.1.1 | 会员价格展示组件 | 1d | P0 | [`MembershipPricing.tsx`](frontend-v2/src/features/membership/components/MembershipPricing.tsx) |
| 2.1.2 | 会员权益列表组件 | 1d | P0 | [`MembershipBenefits.tsx`](frontend-v2/src/features/membership/components/MembershipBenefits.tsx) |
| 2.1.3 | 会员状态卡片组件 | 1d | P0 | [`MembershipCard.tsx`](frontend-v2/src/features/membership/components/MembershipCard.tsx) |
| 2.1.4 | 会员升级流程 | 2d | P0 | 升级引导弹窗、支付对接 |
| 2.1.5 | 会员专享折扣展示 | 1d | P1 | 折扣标签、价格对比组件 |

##### 2.2 视频咨询模块（1 周）

| ID | 任务 | 工时 | 优先级 | 产出物 |
|----|------|------|--------|--------|
| 2.2.1 | 律师列表与筛选 | 1d | P0 | [`LawyerList.tsx`](frontend-v2/src/features/video-consultation/components/LawyerList.tsx) |
| 2.2.2 | 可用时段选择器 | 1.5d | P0 | [`TimeSlotPicker.tsx`](frontend-v2/src/features/video-consultation/components/TimeSlotPicker.tsx) |
| 2.2.3 | 预约表单与确认 | 1.5d | P0 | [`ConsultationBookingForm.tsx`](frontend-v2/src/features/video-consultation/components/ConsultationBookingForm.tsx) |
| 2.2.4 | 咨询记录列表 | 1d | P1 | [`ConsultationHistory.tsx`](frontend-v2/src/features/video-consultation/components/ConsultationHistory.tsx) |
| 2.2.5 | 视频房间集成 | 1d | P0 | 第三方视频 SDK 对接 |

##### 2.3 法律文书商城模块（1 周）

| ID | 任务 | 工时 | 优先级 | 产出物 |
|----|------|------|--------|--------|
| 2.3.1 | 文书分类导航 | 1d | P0 | [`DocumentCategories.tsx`](frontend-v2/src/features/legal-document-mall/components/DocumentCategories.tsx) |
| 2.3.2 | 文书列表与搜索 | 1d | P0 | [`DocumentList.tsx`](frontend-v2/src/features/legal-document-mall/components/DocumentList.tsx) |
| 2.3.3 | 文书详情页 | 1.5d | P0 | [`DocumentDetail.tsx`](frontend-v2/src/features/legal-document-mall/components/DocumentDetail.tsx) |
| 2.3.4 | 购买流程与支付 | 1.5d | P0 | 订单创建、支付对接 |
| 2.3.5 | 已购文书管理 | 1d | P1 | [`PurchasedDocuments.tsx`](frontend-v2/src/features/legal-document-mall/components/PurchasedDocuments.tsx) |

#### 组件示例

##### 会员中心 - 价格展示组件

```typescript
// frontend-v2/src/features/membership/components/MembershipPricing.tsx

import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

interface PricingPlan {
  id: string;
  name: string;
  price: number;
  originalPrice: number;
  durationDays: number;
  features: string[];
  popular?: boolean;
}

interface MembershipPricingProps {
  plans: PricingPlan[];
  onUpgrade: (planId: string) => void;
  currentPlanId?: string;
}

export function MembershipPricing({ 
  plans, 
  onUpgrade, 
  currentPlanId 
}: MembershipPricingProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {plans.map((plan) => (
        <Card 
          key={plan.id}
          className={`relative ${
            plan.popular ? 'border-primary ring-2 ring-primary/20' : ''
          } ${currentPlanId === plan.id ? 'opacity-50' : ''}`}
        >
          {plan.popular && (
            <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">
              最受欢迎
            </Badge>
          )}
          {currentPlanId === plan.id && (
            <Badge variant="secondary" className="absolute -top-3 left-1/2 -translate-x-1/2">
              当前套餐
            </Badge>
          )}
          <CardHeader>
            <h3 className="text-lg font-semibold">{plan.name}</h3>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold">¥{plan.price}</span>
              {plan.originalPrice > plan.price && (
                <span className="text-sm text-muted-foreground line-through">
                  ¥{plan.originalPrice}
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              有效期：{plan.durationDays}天
            </p>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 mb-4">
              {plan.features.map((feature, index) => (
                <li key={index} className="flex items-center gap-2 text-sm">
                  <CheckIcon className="w-4 h-4 text-green-500" />
                  {feature}
                </li>
              ))}
            </ul>
            <Button 
              className="w-full"
              onClick={() => onUpgrade(plan.id)}
              disabled={currentPlanId === plan.id}
            >
              {currentPlanId === plan.id ? '已开通' : '立即开通'}
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
```

#### 里程碑

- [ ] 会员中心模块 UI 完成并对接 API
- [ ] 视频咨询模块 UI 完成并对接 API
- [ ] 法律文书商城模块 UI 完成并对接 API
- [ ] 所有新功能模块通过功能测试

---

### 阶段三：状态管理优化与数据持久化（2 周）

#### 目标

优化 Zustand 状态管理结构，引入 React Query 缓存策略，实现本地数据持久化。

#### 任务详情

| ID | 任务 | 工时 | 优先级 | 产出物 |
|----|------|------|--------|--------|
| 3.1 | 重构 Zustand stores 结构 | 2d | P0 | 统一的 store 模块 |
| 3.2 | 集成 React Query 缓存策略 | 2d | P0 | Query Key 规范、缓存配置 |
| 3.3 | 实现本地数据持久化 | 2d | P1 | localStorage 持久化层 |
| 3.4 | 实现离线数据同步机制 | 2d | P2 | 离线队列、同步策略 |
| 3.5 | 添加状态变更日志与调试工具 | 2d | P2 | Redux DevTools 集成 |

#### 技术实现

##### 3.1 Zustand Store 重构

```typescript
// frontend-v2/src/shared/state/createStore.ts

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { StateCreator } from 'zustand';

interface PersistOptions<T> {
  name: string;
  partialize?: (state: T) => Partial<T>;
  version?: number;
}

/**
 * 创建带持久化的 Zustand store
 */
export function createPersistedStore<T extends object>(
  initializer: StateCreator<T, [], []>,
  options: PersistOptions<T>
) {
  return create<T>()(
    persist(initializer, {
      name: options.name,
      storage: createJSONStorage(() => localStorage),
      partialize: options.partialize,
      version: options.version ?? 1,
      onRehydrateStorage: () => (state, error) => {
        if (error) {
          console.error('[Zustand] 持久化数据恢复失败:', error);
        } else {
          console.log('[Zustand] 持久化数据恢复成功');
        }
      },
    })
  );
}
```

##### 3.2 React Query 缓存配置

```typescript
// frontend-v2/src/shared/lib/query-client.ts

import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 基础配置
      staleTime: 1000 * 60 * 5, // 5 分钟内数据视为新鲜
      gcTime: 1000 * 60 * 30,  // 30 分钟后清理缓存
      retry: 2,                 // 失败重试 2 次
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      
      // 错误处理
      throwOnError: false,
      
      // 网络依赖
      refetchOnWindowFocus: 'always',
      refetchOnReconnect: 'always',
    },
    mutations: {
      retry: 1,
      onError: (error) => {
        console.error('[React Query] Mutation error:', error);
      },
    },
  },
});

// Query Key 工厂
export const queryKeys = {
  // 用户相关
  user: {
    all: ['user'] as const,
    me: () => [...queryKeys.user.all, 'me'] as const,
    profile: () => [...queryKeys.user.all, 'profile'] as const,
  },
  
  // 会员相关
  membership: {
    all: ['membership'] as const,
    me: () => [...queryKeys.membership.all, 'me'] as const,
    pricing: () => [...queryKeys.membership.all, 'pricing'] as const,
  },
  
  // 视频咨询相关
  videoConsultation: {
    all: ['video-consultation'] as const,
    list: (filters?: Record<string, unknown>) => 
      [...queryKeys.videoConsultation.all, 'list', filters] as const,
    detail: (id: number) => 
      [...queryKeys.videoConsultation.all, id] as const,
    availableSlots: (lawyerId: number, date: string) => 
      [...queryKeys.videoConsultation.all, 'slots', lawyerId, date] as const,
  },
  
  // 法律文书相关
  legalDocument: {
    all: ['legal-document'] as const,
    list: (filters?: Record<string, unknown>) => 
      [...queryKeys.legalDocument.all, 'list', filters] as const,
    detail: (id: number) => 
      [...queryKeys.legalDocument.all, id] as const,
    categories: () => [...queryKeys.legalDocument.all, 'categories'] as const,
    purchased: () => [...queryKeys.legalDocument.all, 'purchased'] as const,
  },
};
```

#### 里程碑

- [ ] Zustand store 重构完成
- [ ] React Query 缓存策略配置完成
- [ ] 本地持久化机制运行正常
- [ ] 状态管理性能测试通过

---

### 阶段四：联调测试与验收（2 周）

#### 目标

完成前后端联调测试、E2E 测试完善和验收标准验证。

#### 任务详情

| ID | 任务 | 工时 | 优先级 | 产出物 |
|----|------|------|--------|--------|
| 4.1 | API 接口联调测试 | 3d | P0 | 联调测试报告 |
| 4.2 | E2E 测试用例编写 | 2d | P0 | Playwright 测试脚本 |
| 4.3 | E2E 测试执行与修复 | 2d | P0 | 测试通过率报告 |
| 4.4 | 性能基准测试 | 1d | P1 | 性能测试报告 |
| 4.5 | 验收标准验证 | 2d | P0 | 验收检查清单 |

#### E2E 测试用例规划

##### 会员中心测试

```typescript
// frontend-v2/e2e/membership.spec.ts

import { test, expect } from '@playwright/test';

test.describe('会员中心', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // 模拟登录
    await page.evaluate(() => {
      localStorage.setItem('access_token', 'test_token');
    });
    await page.reload();
  });

  test('查看会员价格', async ({ page }) => {
    await page.goto('/vip');
    
    // 验证价格卡片显示
    await expect(page.getByText('月度会员')).toBeVisible();
    await expect(page.getByText('年度会员')).toBeVisible();
    
    // 验证价格显示
    const monthlyPrice = page.getByText(/¥29\.90/);
    await expect(monthlyPrice).toBeVisible();
  });

  test('会员升级流程', async ({ page }) => {
    await page.goto('/vip');
    
    // 点击升级按钮
    await page.getByRole('button', { name: '立即开通' }).first().click();
    
    // 验证订单弹窗
    await expect(page.getByText('确认订单')).toBeVisible();
    
    // 模拟支付
    await page.getByRole('button', { name: '确认支付' }).click();
    
    // 验证支付成功
    await expect(page.getByText('支付成功')).toBeVisible({ timeout: 10000 });
  });
});
```

##### 视频咨询测试

```typescript
// frontend-v2/e2e/video-consultation.spec.ts

import { test, expect } from '@playwright/test';

test.describe('视频咨询', () => {
  test('预约视频咨询', async ({ page }) => {
    await page.goto('/video-consultation');
    
    // 选择律师
    await page.getByRole('button', { name: '预约咨询' }).first().click();
    
    // 选择日期
    await page.getByLabel('选择日期').click();
    await page.getByRole('gridcell', { name: '15' }).click();
    
    // 选择时段
    await page.getByRole('button', { name: '14:00' }).click();
    
    // 填写咨询信息
    await page.getByLabel('咨询主题').fill('合同纠纷咨询');
    await page.getByLabel('问题描述').fill('我想咨询劳动合同解除的问题');
    
    // 提交预约
    await page.getByRole('button', { name: '确认预约' }).click();
    
    // 验证预约成功
    await expect(page.getByText('预约成功')).toBeVisible();
  });
});
```

#### 里程碑

- [ ] 所有 API 接口联调通过
- [ ] E2E 测试通过率 ≥ 95%
- [ ] 性能基准测试完成
- [ ] 验收标准全部满足

---

### 阶段五：性能优化与上线准备（1 周）

#### 目标

完成性能优化、代码审查和上线部署检查。

#### 任务详情

| ID | 任务 | 工时 | 优先级 | 产出物 |
|----|------|------|--------|--------|
| 5.1 | 性能基准测试与分析 | 1d | P0 | Lighthouse 报告 |
| 5.2 | 代码审查与优化 | 2d | P0 | Code Review 报告 |
| 5.3 | 打包体积优化 | 1d | P1 | Bundle 分析报告 |
| 5.4 | 上线部署检查清单 | 1d | P0 | 部署检查表 |

#### 性能优化清单

- [ ] 首屏加载时间 < 2s
- [ ] Lighthouse 性能分数 ≥ 90
- [ ] 打包体积 < 500KB (gzipped)
- [ ] 图片资源 WebP 格式转换
- [ ] 代码分割与懒加载
- [ ] 缓存策略优化

#### 上线检查清单

- [ ] 环境变量配置正确
- [ ] API 地址配置正确
- [ ] Sentry 错误监控配置
- [ ] 性能监控配置
- [ ] 域名 SSL 证书有效
- [ ] CDN 配置完成
- [ ] 回滚方案准备

#### 里程碑

- [ ] 性能优化目标达成
- [ ] 代码审查问题全部修复
- [ ] 上线部署检查完成
- [ ] 项目正式上线

---

## 关键技术决策

### 决策 1：API 响应处理策略

**方案 A**：在 Axios 拦截器中统一解包
**方案 B**：在各业务模块中手动解包

**决策**：采用方案 A

**理由**：
- 统一处理，减少重复代码
- 便于错误集中处理
- 业务代码更简洁

### 决策 2：状态管理方案

**方案 A**：纯 Zustand
**方案 B**：Zustand + React Query

**决策**：采用方案 B

**理由**：
- React Query 处理服务端状态（缓存、同步、重试）
- Zustand 处理客户端状态（UI 状态、表单状态）
- 职责分离，便于维护

### 决策 3：错误码映射方式

**方案 A**：硬编码映射表
**方案 B**：从后端动态获取

**决策**：采用方案 A + 定期同步

**理由**：
- 前端可独立运行，不依赖后端
- 映射表可版本化管理
- 通过 CI/CD 定期同步后端变更

---

## 风险与应对

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| 后端 API 变更频繁 | 高 | 中 | 建立 API 变更通知机制，保持沟通 |
| 第三方视频 SDK 集成问题 | 高 | 中 | 提前调研，准备备选方案 |
| 性能优化不达标 | 中 | 低 | 预留优化时间，采用渐进式优化 |
| 测试覆盖率不足 | 中 | 中 | 设置覆盖率门槛，CI 强制检查 |

---

## 验收标准

### 功能验收

- [ ] 会员中心模块功能完整，可正常购买、查看权益
- [ ] 视频咨询模块功能完整，可正常预约、查看记录
- [ ] 法律文书商城功能完整，可正常浏览、购买、下载

### 技术验收

- [ ] API 响应格式与后端完全匹配
- [ ] 错误码映射完整，错误提示准确
- [ ] 分页功能正常工作
- [ ] 状态管理无内存泄漏
- [ ] 本地持久化正常工作

### 性能验收

- [ ] 首屏加载时间 < 2s
- [ ] Lighthouse 性能分数 ≥ 90
- [ ] 页面交互响应时间 < 100ms
- [ ] 列表滚动帧率 ≥ 55fps

### 质量验收

- [ ] E2E 测试通过率 ≥ 95%
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 无 P0/P1 级别 Bug
- [ ] 代码审查问题全部修复

---

## 附录

### A. 相关文件

- [后端 API 文档](./API.md)
- [后端架构说明](./ARCHITECTURE.md)
- [前端开发规范](frontend-v2/CONTRIBUTING.md)

### B. 联系方式

- 前端负责人：@frontend-lead
- 