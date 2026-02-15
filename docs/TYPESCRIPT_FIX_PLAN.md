# TypeScript类型错误修复计划

## 概述
启用strict模式后，前端存在约90行类型错误，主要分为以下几类：

## 错误分类

### 1. `string | undefined` 不能赋值给 `string` (最常见)
**修复方案**: 使用空值合并运算符 `?? ''` 或非空断言 `!`

**示例修复**:
```typescript
// 修复前
date: reminder.dueAt.split('T')[0]

// 修复后
date: reminder.dueAt?.split('T')[0] ?? ''
```

### 2. `Object is possibly 'undefined'`
**修复方案**: 添加可选链 `?.` 或类型守卫

**示例修复**:
```typescript
// 修复前
params.page

// 修复后
params?.page ?? 1
```

### 3. 未使用变量 (`noUnusedLocals`, `noUnusedParameters`)
**修复方案**: 删除未使用变量或添加下划线前缀

**示例修复**:
```typescript
// 修复前
const _handleSort = () => {}

// 修复后
// 删除或实际使用
```

## 按模块划分的修复优先级

### 高优先级（核心功能）
1. `src/features/document/` - 文档模块
2. `src/features/calendar/` - 日历模块
3. `src/features/ai-consultation/` - AI咨询

### 中优先级
4. `src/features/analytics/` - 分析模块
5. `src/features/ai_quality/` - AI质量

### 低优先级
6. `src/features/enterprise/` - 企业功能
7. `src/features/faq/` - FAQ

## 快速修复命令

### 查找所有类型错误
```bash
cd frontend-v2 && npm run type-check
```

### 批量替换常见模式
```bash
# 在VSCode中使用正则替换
# 查找: \.split\('T'\)\[0\]
# 替换: ?.split('T')[0] ?? ''
```

## 渐进式修复策略

### 阶段1: 启用部分严格检查 ✅ (已完成)
```json
{
  "strict": true,
  "noUnusedLocals": false,
  "noUnusedParameters": false,
  "noUncheckedIndexedAccess": false
}
```

### 阶段2: 修复核心模块类型错误 (进行中)
- 修复document模块
- 修复calendar模块
- 修复ai-consultation模块

### 阶段3: 启用完整严格检查
```json
{
  "noUnusedLocals": true,
  "noUnusedParameters": true,
  "noUncheckedIndexedAccess": true
}
```

## 自动化工具推荐

1. **ESLint自动修复**: `npm run lint:fix`
2. **TypeScript自动修复**: 使用VSCode的TypeScript插件
3. **批量替换**: 使用sed或VSCode正则替换

## 注意事项

1. 每次修复后运行 `npm run type-check` 验证
2. 不要过度使用 `as any` 或 `!` 非空断言
3. 优先修复核心业务逻辑模块
4. 保持代码可读性，避免过度复杂的类型体操

---
**创建时间**: 2026-02-11
**状态**: 进行中
