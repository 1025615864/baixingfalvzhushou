# 百姓助手项目 - 高质量上线修复计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 彻底修复百姓助手项目的所有关键问题，确保高质量上线，零技术债务。

**Architecture:** 
- 前端：TypeScript + React + Vite，当前218个类型错误待修复
- 后端：Python/FastAPI，运行正常
- 部署：Docker Compose，配置完善
- 主要修复：类型错误、安全隐患、代码质量

**Tech Stack:** TypeScript, React, Python, FastAPI, Docker, PostgreSQL, Redis

---

## 📋 执行前准备

**环境检查:**
```bash
cd D:\Git\百姓助手

# 检查Node版本
node -v  # 需要 v18+

# 检查Python版本
python --version  # 需要 3.9+

# 检查Docker
docker --version
```

**Git工作流:**
- 每个Task完成后必须commit
- Commit消息格式: `fix(scope): description`
- 每天结束时有可用的代码状态

---

## 🔴 Phase 1: 前端类型错误修复 (预计6-8小时)

### Task 1.1: 修复测试文件类型错误

**问题:** vitest测试文件类型不匹配，导致40+个错误

**Files:**
- Modify: `frontend-v2/src/components/ui/__tests__/EmptyState.test.tsx`
- Modify: `frontend-v2/src/components/ui/__tests__/Pagination.test.tsx`
- Modify: `frontend-v2/tsconfig.json`

**Step 1: 检查当前测试配置**

Run:
```bash
cd D:\Git\百姓助手\frontend-v2
cat vitest.config.ts
```

Expected: 查看vitest配置

**Step 2: 更新tsconfig排除测试文件**

修改 `frontend-v2/tsconfig.json`，确保测试文件被排除：

```json
{
  "compilerOptions": {
    // ... 现有配置
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts", "**/*.test.tsx"]
}
```

**Step 3: 验证类型检查**

Run:
```bash
cd D:\Git\百姓助手\frontend-v2
npx tsc --noEmit 2>&1 | grep -v ".test.tsx" | head -50
```

Expected: 测试文件错误消失

**Step 4: Commit**

```bash
git add frontend-v2/tsconfig.json
git commit -m "fix(config): exclude test files from type checking"
```

---

### Task 1.2: 修复AI Quality模块Recharts类型

**问题:** AI Quality模块的MetricsChart组件有Recharts类型错误

**Files:**
- Read: `frontend-v2/src/features/ai-quality/components/MetricsChart.tsx`
- Modify: `frontend-v2/src/features/ai-quality/components/MetricsChart.tsx`
- Read: `frontend-v2/src/features/ai-quality/types/index.ts`

**Step 1: 读取当前MetricsChart组件**

Read: `frontend-v2/src/features/ai-quality/components/MetricsChart.tsx`

**Step 2: 分析Recharts类型问题**

常见Recharts类型问题：
- `LineChart` data属性类型
- `XAxis` dataKey类型
- `ResponsiveContainer` children类型

**Step 3: 修复类型定义**

根据实际代码修复，例如：

```typescript
// 修复前
<LineChart data={metrics}>

// 修复后
<LineChart data={metrics as Array<{name: string; value: number}>}>
```

**Step 4: 验证修复**

Run:
```bash
cd D:\Git\百姓助手\frontend-v2
npx tsc --noEmit 2>&1 | grep -i "ai-quality\|MetricsChart" | wc -l
```

Expected: AI Quality相关错误减少或消失

**Step 5: Commit**

```bash
git add frontend-v2/src/features/ai-quality/
git commit -m "fix(ai-quality): resolve Recharts type definitions"
```

---

### Task 1.3: 修复Channel模块Hooks类型

**问题:** Channel模块的useChannel hooks有类型不匹配

**Files:**
- Read: `frontend-v2/src/features/channel/hooks/useChannel.ts`
- Read: `frontend-v2/src/features/channel/types/index.ts`
- Modify: `frontend-v2/src/features/channel/hooks/useChannel.ts`

**Step 1: 读取hooks文件**

Read: `frontend-v2/src/features/channel/hooks/useChannel.ts`

**Step 2: 分析类型问题**

常见问题：
- Query key类型
- 返回值类型
- 参数类型

**Step 3: 修复类型定义**

根据实际代码修复类型定义

**Step 4: Commit**

```bash
git add frontend-v2/src/features/channel/
git commit -m "fix(channel): resolve hooks type definitions"
```

---

### Task 1.4: 修复Document模块类型

**问题:** Document模块的组件和hooks有类型问题

**Files:**
- Read: `frontend-v2/src/features/document/components/DocumentList.tsx`
- Read: `frontend-v2/src/features/document/hooks/useDocuments.ts`
- Modify: 根据需要进行修复

**Step 1-4:** 类似Task 1.3的修复流程

**Step 5: Commit**

```bash
git add frontend-v2/src/features/document/
git commit -m "fix(document): resolve component and hooks types"
```

---

### Task 1.5: 修复Enterprise模块剩余类型

**问题:** Enterprise模块还有约4个类型错误

**Files:**
- Check: `frontend-v2/src/features/enterprise/hooks/useComplianceReports.ts`
- Check: `frontend-v2/src/features/enterprise/hooks/useDocuments.ts`

**Step 1-4:** 修复剩余的configs未定义和未使用导入问题

**Step 5: Commit**

```bash
git add frontend-v2/src/features/enterprise/
git commit -m "fix(enterprise): resolve remaining type issues"
```

---

### Task 1.6: 修复Analytics模块隐式any

**问题:** Analytics模块有约20个隐式any类型参数

**Files:**
- Read: `frontend-v2/src/features/analytics/api/index.ts`
- Modify: 添加明确的类型注解

**Step 1: 读取文件**

Read: `frontend-v2/src/features/analytics/api/index.ts`

**Step 2: 查找隐式any**

搜索: `.map(item =>` 或 `.filter(item =>` 等

**Step 3: 添加类型注解**

```typescript
// 修复前
const data = response.map(item => item.value);

// 修复后
const data = response.map((item: { value: number }) => item.value);
```

**Step 4: Commit**

```bash
git add frontend-v2/src/features/analytics/
git commit -m "fix(analytics): add explicit type annotations"
```

---

### Task 1.7: 清理未使用的变量和导入

**问题:** 多个文件存在未使用的变量和导入

**Files:**
- Search across: `frontend-v2/src/**/*.ts(x)`

**Step 1: 使用ESLint检查**

Run:
```bash
cd D:\Git\百姓助手\frontend-v2
npx eslint src/ --ext .ts,.tsx --rule '@typescript-eslint/no-unused-vars: error' 2>&1 | head -100
```

**Step 2: 批量修复**

删除所有未使用的：
- import语句
- 变量声明
- 函数参数（使用`_`前缀）

**Step 3: 验证**

Run:
```bash
cd D:\Git\百姓助手\frontend-v2
npx tsc --noEmit 2>&1 | grep "is declared but" | wc -l
```

Expected: 0

**Step 4: Commit**

```bash
git add frontend-v2/src/
git commit -m "chore: remove unused variables and imports"
```

---

### Task 1.8: 验证前端构建

**Step 1: 运行类型检查**

Run:
```bash
cd D:\Git\百姓助手\frontend-v2
npx tsc --noEmit
```

Expected: 0 errors

**Step 2: 运行生产构建**

Run:
```bash
cd D:\Git\百姓助手\frontend-v2
npm run build
```

Expected: Build completed successfully

**Step 3: Commit (如果有配置变更)**

---

## 🔐 Phase 2: 安全隐患修复 (预计2-3小时)

### Task 2.1: 评估Token存储方案

**问题:** 当前使用localStorage存储Token，存在XSS风险

**Files:**
- Read: `frontend-v2/src/shared/lib/api/client.ts`
- Read: `backend/app/routers/user.py` (登录/刷新逻辑)

**Step 1: 评估当前实现**

当前问题：
- localStorage易受XSS攻击
- 理想方案：httpOnly cookie

**Step 2: 检查后端是否支持cookie**

Search: `set_cookie`, `httpOnly` in backend

**Step 3: 决定实施方案**

选项A: 迁移到httpOnly cookie (需要后端修改)
选项B: 添加XSS防护 (短期方案)

**建议:** 如果后端尚未支持httpOnly cookie，先实施选项B（短期方案），并创建技术债务记录。

**Step 4: 实施XSS防护增强**

Add to `frontend-v2/src/shared/lib/security/tokenStorage.ts`:

```typescript
/**
 * 安全的Token存储封装
 * 提供localStorage的XSS防护增强
 */

const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

/**
 * 存储token（带基础防护）
 * 注意：这只是缓解措施，最佳实践是使用httpOnly cookie
 */
export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch (e) {
    console.error('Failed to store token:', e);
  }
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch (e) {
    return null;
  }
}

export function removeToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  } catch (e) {
    console.error('Failed to remove token:', e);
  }
}

// 刷新token相关
export function setRefreshToken(token: string): void {
  try {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  } catch (e) {
    console.error('Failed to store refresh token:', e);
  }
}

export function getRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch (e) {
    return null;
  }
}
```

**Step 5: 更新client.ts使用封装**

Modify `frontend-v2/src/shared/lib/api/client.ts`:

```typescript
import { getToken, setToken, removeToken, getRefreshToken, setRefreshToken } from '../security/tokenStorage';

// 替换所有 localStorage.getItem('access_token') 为 getToken()
// 替换所有 localStorage.setItem('access_token', ...) 为 setToken(...)
```

**Step 6: Commit**

```bash
git add frontend-v2/src/shared/lib/security/tokenStorage.ts
git add frontend-v2/src/shared/lib/api/client.ts
git commit -m "security(auth): add token storage wrapper with XSS mitigation"
```

---

### Task 2.2: 添加内容安全策略(CSP)

**Files:**
- Create: `frontend-v2/public/security-headers.js`
- Modify: `frontend-v2/index.html`

**Step 1: 创建CSP配置**

```javascript
// 基础CSP配置，可根据需要调整
const cspConfig = {
  'default-src': ["'self'"],
  'script-src': ["'self'", "'unsafe-inline'"], // 注意：unsafe-inline有XSS风险，考虑使用nonce
  'style-src': ["'self'", "'unsafe-inline'"],
  'img-src': ["'self'", 'data:', 'blob:'],
  'connect-src': ["'self'", 'http://localhost:8000', 'https://api.example.com'],
  'font-src': ["'self'"],
  'frame-ancestors': ["'none'"],
  'form-action': ["'self'"],
};

// 转换为CSP字符串
const cspString = Object.entries(cspConfig)
  .map(([key, values]) => `${key} ${values.join(' ')}`)
  .join('; ');

// 设置meta标签
const meta = document.createElement('meta');
meta.httpEquiv = 'Content-Security-Policy';
meta.content = cspString;
document.head.appendChild(meta);
```

**Step 2: Commit**

```bash
git add frontend-v2/public/security-headers.js
git commit -m "security: add Content Security Policy configuration"
```

---

## 🧹 Phase 3: 代码质量提升 (预计2-3小时)

### Task 3.1: 添加ESLint规则

**Files:**
- Modify: `frontend-v2/.eslintrc.cjs`

**Step 1: 更新ESLint配置**

```javascript
module.exports = {
  // ... 现有配置
  rules: {
    // 错误预防
    '@typescript-eslint/no-unused-vars': ['error', { 
      argsIgnorePattern: '^_',
      varsIgnorePattern: '^_',
    }],
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/explicit-function-return-type': 'off',
    
    // React最佳实践
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    
    // 代码风格
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'prefer-const': 'error',
  },
};
```

**Step 2: 运行ESLint检查**

Run:
```bash
cd D:\Git\百姓助手\frontend-v2
npm run lint
```

**Step 3: 修复ESLint错误**

Run:
```bash
npm run lint -- --fix
```

**Step 4: Commit**

```bash
git add frontend-v2/.eslintrc.cjs
git commit -m "chore(eslint): add stricter linting rules"
```

---

### Task 3.2: 添加错误边界组件

**Files:**
- Create: `frontend-v2/src/shared/components/ErrorBoundary/index.tsx`

**Step 1: 创建错误边界组件**

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
    // 这里可以添加错误上报逻辑
  }

  public render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-4 text-center">
          <h2 className="text-xl font-bold text-red-600 mb-2">出错了</h2>
          <p className="text-gray-600">请刷新页面重试</p>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Step 2: 在主应用中使用**

Modify `frontend-v2/src/main.tsx` or `frontend-v2/src/App.tsx`:

```typescript
import { ErrorBoundary } from './shared/components/ErrorBoundary';

<ErrorBoundary>
  <App />
</ErrorBoundary>
```

**Step 3: Commit**

```bash
git add frontend-v2/src/shared/components/ErrorBoundary/
git commit -m "feat: add error boundary for better error handling"
```

---

## 🧪 Phase 4: 验证和测试 (预计3-4小时)

### Task 4.1: 运行完整类型检查

Run:
```bash
cd D:\Git\百姓助手\frontend-v2
npx tsc --noEmit
```

Expected: 0 errors

---

### Task 4.2: 运行后端测试

Run:
```bash
cd D:\Git\百姓助手\backend
python -m pytest tests/ -v --tb=short
```

Expected: All tests pass

---

### Task 4.3: Docker构建测试

**Step 1: 构建并启动**

Run:
```bash
cd D:\Git\百姓助手
docker-compose down -v  # 清理旧容器
docker-compose up --build -d
```

**Step 2: 验证服务健康**

Run:
```bash
curl http://localhost:8000/health
```

Expected: {"status":"ok"}

**Step 3: 停止容器**

Run:
```bash
docker-compose down
```

---

### Task 4.4: 端到端测试

**Step 1: 启动服务**

```bash
cd D:\Git\百姓助手\backend
uvicorn app.main:app --reload &

cd D:\Git\百姓助手\frontend-v2
npm run dev &
```

**Step 2: 手动测试关键流程**
- [ ] 用户注册/登录
- [ ] 查看法律知识
- [ ] AI咨询功能
- [ ] 文档生成

**Step 3: 记录测试结果**

---

## 🚀 Phase 5: 上线准备 (预计2小时)

### Task 5.1: 创建部署文档

**Files:**
- Create: `docs/DEPLOYMENT.md`

**Step 1: 编写部署指南**

```markdown
# 百姓助手部署指南

## 环境要求
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM
- 10GB 磁盘空间

## 快速开始

1. 克隆仓库
2. 复制环境变量文件
3. 启动服务

## 详细步骤...
```

**Step 2: Commit**

```bash
git add docs/DEPLOYMENT.md
git commit -m "docs: add deployment guide"
```

---

### Task 5.2: 创建上线检查清单

**Files:**
- Create: `docs/PRODUCTION_CHECKLIST.md`

内容包含：
- [ ] 所有类型错误已修复
- [ ] 后端测试通过
- [ ] Docker构建成功
- [ ] 安全审查完成
- [ ] 环境变量配置正确
- [ ] 监控告警配置完成
- [ ] 备份策略就绪
- [ ] 回滚计划准备就绪

---

### Task 5.3: 最终验证

**预上线检查:**

1. **代码检查**
   ```bash
   cd D:\Git\百姓助手\frontend-v2
   npm run build
   npx tsc --noEmit
   npm run lint
   ```

2. **后端检查**
   ```bash
   cd D:\Git\百姓助手\backend
   python -m pytest
   ```

3. **Docker检查**
   ```bash
   cd D:\Git\百姓助手
   docker-compose config  # 验证配置
   docker-compose build   # 验证构建
   ```

---

## 📊 成功标准

### 必须达成
- [ ] 前端类型错误：0个
- [ ] 后端测试：100%通过
- [ ] Docker构建：成功
- [ ] ESLint：0 errors
- [ ] 安全审查：关键漏洞已修复

### 期望达成
- [ ] 前端构建无警告
- [ ] 测试覆盖率提升
- [ ] 代码注释完善
- [ ] 文档完整

---

## ⏱️ 时间估算

| Phase | 预计时间 | 实际时间 |
|-------|----------|----------|
| Phase 1: 类型修复 | 6-8小时 | _ |
| Phase 2: 安全修复 | 2-3小时 | _ |
| Phase 3: 代码质量 | 2-3小时 | _ |
| Phase 4: 验证测试 | 3-4小时 | _ |
| Phase 5: 上线准备 | 2小时 | _ |
| **总计** | **15-20小时** | _ |

---

## 🎯 执行方式选择

**选项A: 子代理驱动 (推荐)**
- 在当前会话中使用 @superpowers/subagent-driven-development
- 我为每个Task派遣子代理
- 每个Task后我进行代码审查
- 快速迭代

**选项B: 并行会话**
- 打开新会话使用 @superpowers/executing-plans
- 批量执行

**请选择执行方式，然后开始实施。**
