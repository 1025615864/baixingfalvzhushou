# TypeScript 类型安全修复计划

## 背景
启用 TypeScript 严格模式后，发现了约 30 个类型错误。本文档记录修复计划。

## 已完成的配置更改
- `strict: true` - 启用严格模式
- `noImplicitAny: true` - 禁止隐式 any
- `strictNullChecks: true` - 严格空值检查

## 待修复的类型错误列表

### 高优先级（可能导致运行时错误）

| 文件 | 行号 | 错误类型 | 修复建议 |
|------|------|----------|----------|
| `useAIConsultation.ts` | 60 | `string \| undefined` 不能赋值给 `string` | 添加空值检查 |
| `useShare.ts` | 79 | 同上 | 添加空值检查 |
| `useKnowledge.ts` | 38 | 同上 | 添加空值检查 |
| `useSettlements.ts` | 85 | 同上 | 添加空值检查 |
| `useConsultationTemplates.ts` | 48 | `string \| null` 不能赋值给 `string` | 添加空值检查 |
| `useDocumentTemplates.ts` | 50 | 同上 | 添加空值检查 |
| `usePosts.ts` | 50 | 同上 | 添加空值检查 |
| `useWithdrawals.ts` | 52 | 同上 | 添加空值检查 |
| `useFAQ.ts` | 73 | `number \| null` 不能赋值给 `number` | 添加空值检查 |

### 中优先级（可能影响功能）

| 文件 | 行号 | 错误类型 | 修复建议 |
|------|------|----------|----------|
| `OrderCard/index.tsx` | 62 | `ikunpay` 属性不存在 | 添加类型定义 |
| `useNotification.ts` | 52 | 类型不兼容 | 统一类型定义 |
| `websocketService.ts` | 166 | 对象可能为 null | 添加空值检查 |
| `index.ts` (enterprise) | 589 | `configs` 可能为 undefined | 添加可选链 |
| `FeedbackAdminPage.tsx` | 210-218 | `params.page` 可能为 undefined | 添加默认值 |

### 低优先级（UI 相关）

| 文件 | 行号 | 错误类型 |
|------|------|----------|
| `MetricsChart.tsx` | 207, 245 | 类型不匹配 |
| `QualityDashboard.tsx` | 340 | percent 可能为 undefined |
| `PromotionStatsModal.tsx` | 180, 203, 220, 249 | trend 可能为 undefined |
| `NewsSourcesPage.tsx` | 345, 356 | null 不能赋值 |
| `NewsTopicsPage.tsx` | 241 | 同上 |
| `FAQForm.tsx` | 65 | null 不能赋值给 undefined |
| `KnowledgeAdminPage.tsx` | 307 | null 不能赋值给 Element |

## 修复模式示例

### 模式 1: 参数空值检查
```typescript
// 修复前
queryFn: () => apiGetSession(sessionId),

// 修复后
queryFn: () => sessionId ? apiGetSession(sessionId) : Promise.reject('No session ID'),
```

### 模式 2: 可选链操作符
```typescript
// 修复前
request.configs.map(...)

// 修复后
request.configs?.map(...) ?? []
```

### 模式 3: 默认值
```typescript
// 修复前
params.page

// 修复后
params.page ?? 1
```

### 模式 4: 类型守卫
```typescript
// 修复前
if (filters.maxPrice > 0) { ... }

// 修复后
if (filters.maxPrice && filters.maxPrice > 0) { ... }
```

## 执行计划

1. **阶段 1**: 修复高优先级错误（API 调用相关）
2. **阶段 2**: 修复中优先级错误（功能相关）
3. **阶段 3**: 修复低优先级错误（UI 相关）
4. **阶段 4**: 启用更严格的选项：
   - `noUnusedLocals: true`
   - `noUnusedParameters: true`
   - `noImplicitReturns: true`
   - `noUncheckedIndexedAccess: true`

## 注意事项

- 每次修复后运行 `npm run type-check` 验证
- 修复时保持向后兼容
- 对于复杂类型，考虑使用类型守卫函数
