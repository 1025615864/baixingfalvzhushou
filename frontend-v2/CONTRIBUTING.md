# 百姓助手前端开发贡献规范

## 📋 目录

1. [开发哲学](#开发哲学)
2. [技术栈规范](#技术栈规范)
3. [目录结构规范](#目录结构规范)
4. [代码规范](#代码规范)
5. [组件开发规范](#组件开发规范)
6. [状态管理规范](#状态管理规范)
7. [API 层规范](#api-层规范)
8. [测试规范](#测试规范)
9. [Git 提交规范](#git-提交规范)
10. [代码审查规范](#代码审查规范)
11. [性能规范](#性能规范)
12. [安全规范](#安全规范)

---

## 开发哲学

### 核心原则

1. **简单优于复杂** - 优先选择简单直接的解决方案
2. **显式优于隐式** - 代码意图必须清晰明确
3. **组合优于继承** - 使用组合模式构建组件
4. **类型安全** - 零 `any` 类型，100% TypeScript 覆盖
5. **可测试性** - 所有代码必须易于单元测试

### 质量门禁

- ✅ ESLint 零错误
- ✅ TypeScript 严格模式零错误
- ✅ 单元测试覆盖率 > 80%
- ✅ 构建零警告
- ✅ Lighthouse 性能评分 > 90

---

## 技术栈规范

### 核心依赖 (固定版本)

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.20.0",
  "@tanstack/react-query": "^5.8.0",
  "zustand": "^4.4.0",
  "typescript": "^5.3.0",
  "vite": "^5.0.0"
}
```

### UI 组件库

- **Ant Design 5** - 基础组件库
- **Tailwind CSS** - 自定义样式工具类
- **CSS Modules** - 组件级样式隔离

### 开发工具

| 工具 | 用途 | 配置 |
|-----|------|------|
| ESLint | 代码检查 | 自定义规则集 |
| Prettier | 代码格式化 | 项目级配置 |
| Vitest | 单元测试 | 覆盖率 80%+ |
| Playwright | E2E 测试 | 核心流程覆盖 |
| Storybook | 组件开发 | 独立开发环境 |

---

## 目录结构规范

### 新目录结构 (Feature-Based Architecture)

```
src/
├── app/                    # 应用入口和全局配置
│   ├── App.tsx
│   ├── providers.tsx       # 全局 Provider 组合
│   └── router.tsx          # 路由配置
├── features/               # 功能模块 (按业务领域划分)
│   ├── auth/              # 认证功能
│   │   ├── api/           # API 调用
│   │   ├── components/    # 功能组件
│   │   ├── hooks/         # 自定义 hooks
│   │   ├── stores/        # 状态管理
│   │   ├── types/         # 类型定义
│   │   └── utils/         # 工具函数
│   ├── consultation/      # 咨询服务
│   ├── document/          # 文档生成
│   ├── payment/           # 支付系统
│   ├── news/              # 新闻资讯
│   └── lawyer/            # 律师工作台
├── shared/                # 共享资源
│   ├── components/        # 全局通用组件
│   ├── hooks/             # 全局通用 hooks
│   ├── lib/               # 第三方库封装
│   ├── types/             # 全局类型
│   └── utils/             # 工具函数
├── widgets/               # 独立功能组件 (跨页面复用)
└── pages/                 # 页面组件 (仅路由配置)
    ├── HomePage.tsx
    ├── ChatPage.tsx
    └── AdminPage.tsx
```

### 目录命名规范

| 类型 | 命名规则 | 示例 |
|-----|---------|------|
| 目录 | kebab-case | `user-profile/` |
| 组件 | PascalCase | `UserProfile.tsx` |
| Hooks | camelCase + use | `useUserProfile.ts` |
| 工具函数 | camelCase | `formatDate.ts` |
| 类型定义 | PascalCase | `UserTypes.ts` |
| 常量 | UPPER_SNAKE_CASE | `API_ENDPOINTS.ts` |

---

## 代码规范

### TypeScript 规范

#### 1. 严格类型 (Zero `any`)

```typescript
// ❌ 错误
function handleData(data: any) {
  return data.value;
}

// ✅ 正确
interface DataResponse {
  value: string;
  timestamp: number;
}

function handleData(data: DataResponse): string {
  return data.value;
}
```

#### 2. 类型定义位置

```typescript
// 组件 Props 类型 - 与组件同文件
interface UserCardProps {
  user: User;
  onSelect: (id: string) => void;
}

// 业务类型 - types/index.ts
export interface User {
  id: string;
  name: string;
  email: string;
}

// API 响应类型 - api/types.ts
export interface ApiResponse<T> {
  data: T;
  message: string;
  code: number;
}
```

#### 3. 类型推导优先

```typescript
// ✅ 使用类型推导
const users = await fetchUsers(); // 自动推导为 User[]

// ❌ 不必要的显式类型
const users: User[] = await fetchUsers();
```

### 导入/导出规范

#### 1. 导入顺序

```typescript
// 1. React 核心
import { useState, useCallback } from 'react';

// 2. 第三方库
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';

// 3. 共享模块 (绝对路径)
import { Button } from '@/shared/components';
import { useAuth } from '@/shared/hooks';

// 4. 功能模块 (相对路径)
import { useUserStore } from '../stores';
import type { User } from '../types';
```

#### 2. 导出规范

```typescript
// 默认导出 - 仅用于主组件
export default function UserCard() {}

// 命名导出 - 用于其他导出
export { useUserStore };
export type { User };

//  barrel 导出 - index.ts
export * from './types';
export * from './hooks';
export { default as UserCard } from './UserCard';
```

---

## 组件开发规范

### 组件结构模板

```typescript
// 1. 导入
import { useState, useCallback, memo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/shared/components';

// 2. 类型定义
interface UserProfileProps {
  userId: string;
  onUpdate?: (user: User) => void;
}

// 3. 组件实现
function UserProfile({ userId, onUpdate }: UserProfileProps) {
  // 3.1 Hooks (按执行顺序)
  const { data, isLoading } = useUser(userId);
  const [isEditing, setIsEditing] = useState(false);
  
  // 3.2 回调函数 (useCallback)
  const handleEdit = useCallback(() => {
    setIsEditing(true);
  }, []);
  
  // 3.3 副作用 (useEffect)
  useEffect(() => {
    document.title = data?.name ?? '用户资料';
  }, [data?.name]);
  
  // 3.4 渲染逻辑
  if (isLoading) return <Loading />;
  
  // 3.5 JSX
  return (
    <div className="user-profile">
      {/* ... */}
    </div>
  );
}

// 4. 导出
export default memo(UserProfile);
```

### 组件设计原则

#### 1. 单一职责 (SRP)

```typescript
// ❌ 错误 - 职责过多
function UserPage() {
  // 数据获取
  // 状态管理
  // UI 渲染
  // 副作用处理
}

// ✅ 正确 - 职责分离
function UserPage() {
  return (
    <UserProvider>
      <UserLayout>
        <UserHeader />
        <UserContent />
      </UserLayout>
    </UserProvider>
  );
}
```

#### 2. 受控与非受控

```typescript
// 受控组件 - 推荐
interface InputProps {
  value: string;
  onChange: (value: string) => void;
}

// 非受控组件 - 仅在特定场景使用
interface FileInputProps {
  onFileSelect: (file: File) => void;
}
```

#### 3. Props 设计

```typescript
// ✅ 好的 Props 设计
interface ButtonProps {
  // 必需的 props
  children: React.ReactNode;
  
  // 可选且有默认值的 props
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  
  // 事件处理器
  onClick?: (event: React.MouseEvent) => void;
  
  // 透传 HTML 属性
  className?: string;
  style?: React.CSSProperties;
}
```

### 性能优化规范

#### 1. 记忆化策略

```typescript
// 组件记忆化 - 仅当 props 频繁变化时使用
const ExpensiveComponent = memo(function ExpensiveComponent() {
  // ...
});

// 回调记忆化
const handleSubmit = useCallback(() => {
  // ...
}, [dep1, dep2]);

// 值记忆化
const computedValue = useMemo(() => {
  return expensiveComputation(data);
}, [data]);
```

#### 2. 懒加载

```typescript
// 路由级别懒加载
const AdminPage = lazy(() => import('./AdminPage'));

// 组件级别懒加载
const Chart = lazy(() => import('@/shared/components/Chart'));
```

---

## 状态管理规范

### 状态分类

| 状态类型 | 管理工具 | 使用场景 |
|---------|---------|---------|
| 服务端状态 | React Query | API 数据缓存 |
| 全局 UI 状态 | Zustand | 主题、弹窗、通知 |
| 表单状态 | React Hook Form | 表单处理 |
| 局部状态 | useState/useReducer | 组件内部 |

### React Query 规范

```typescript
// 1. Query Key 规范
const queryKeys = {
  user: {
    all: ['user'] as const,
    byId: (id: string) => ['user', id] as const,
    list: (params: UserListParams) => ['user', 'list', params] as const,
  },
};

// 2. Hook 封装
function useUser(userId: string) {
  return useQuery({
    queryKey: queryKeys.user.byId(userId),
    queryFn: () => fetchUser(userId),
    enabled: Boolean(userId),
    staleTime: 5 * 60 * 1000, // 5分钟
  });
}

// 3. Mutation 封装
function useUpdateUser() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: updateUser,
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.user.byId(variables.id),
      });
    },
  });
}
```

### Zustand Store 规范

```typescript
// stores/userStore.ts
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

interface UserState {
  user: User | null;
  isAuthenticated: boolean;
  
  // Actions
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useUserStore = create<UserState>()(
  immer((set) => ({
    user: null,
    isAuthenticated: false,
    
    setUser: (user) => set((state) => {
      state.user = user;
      state.isAuthenticated = Boolean(user);
    }),
    
    logout: () => set((state) => {
      state.user = null;
      state.isAuthenticated = false;
    }),
  }))
);
```

---

## API 层规范

### 目录结构

```
features/user/api/
├── client.ts          # axios 实例配置
├── types.ts           # API 相关类型
├── endpoints.ts       # API 端点定义
├── queries.ts         # React Query hooks
└── mutations.ts       # Mutation hooks
```

### 请求规范

```typescript
// client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 拦截器
apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### 类型安全 API

```typescript
// types.ts
export interface User {
  id: string;
  name: string;
  email: string;
}

export interface CreateUserRequest {
  name: string;
  email: string;
}

export interface CreateUserResponse {
  user: User;
  message: string;
}

// endpoints.ts
import { apiClient } from './client';
import type { CreateUserRequest, CreateUserResponse } from './types';

export const userEndpoints = {
  getById: (id: string) => apiClient.get<User>(`/users/${id}`),
  create: (data: CreateUserRequest) => 
    apiClient.post<CreateUserResponse>('/users', data),
  update: (id: string, data: Partial<User>) => 
    apiClient.patch<User>(`/users/${id}`, data),
  delete: (id: string) => apiClient.delete(`/users/${id}`),
};
```

---

## 测试规范

### 测试金字塔

```
       /\
      /  \     E2E 测试 (10%) - 核心流程
     /____\    
    /      \   集成测试 (30%) - 组件交互
   /________\  
  /          \ 单元测试 (60%) - 纯函数、hooks
 /____________\
```

### 单元测试规范

```typescript
// UserCard.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserCard } from './UserCard';

describe('UserCard', () => {
  // 1. 渲染测试
  it('renders user information correctly', () => {
    render(<UserCard user={mockUser} />);
    
    expect(screen.getByText(mockUser.name)).toBeInTheDocument();
    expect(screen.getByText(mockUser.email)).toBeInTheDocument();
  });

  // 2. 交互测试
  it('calls onSelect when clicked', async () => {
    const handleSelect = vi.fn();
    render(<UserCard user={mockUser} onSelect={handleSelect} />);
    
    await userEvent.click(screen.getByRole('button'));
    
    expect(handleSelect).toHaveBeenCalledWith(mockUser.id);
  });

  // 3. 边界测试
  it('handles missing optional fields', () => {
    render(<UserCard user={{ id: '1', name: 'Test' }} />);
    
    expect(screen.queryByTestId('avatar')).not.toBeInTheDocument();
  });
});
```

### 测试文件位置

| 被测试文件 | 测试文件位置 |
|-----------|-------------|
| `Component.tsx` | `Component.test.tsx` (同级) |
| `hooks/useAuth.ts` | `hooks/useAuth.test.ts` (同级) |
| `utils/format.ts` | `utils/format.test.ts` (同级) |

---

## Git 提交规范

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型 (Type)

| 类型 | 说明 | 示例 |
|-----|------|------|
| `feat` | 新功能 | `feat(auth): 添加微信登录` |
| `fix` | Bug 修复 | `fix(payment): 修复支付回调问题` |
| `docs` | 文档更新 | `docs(readme): 更新部署说明` |
| `style` | 代码格式 | `style(lint): 修复 ESLint 警告` |
| `refactor` | 重构 | `refactor(user): 优化用户状态管理` |
| `perf` | 性能优化 | `perf(list): 虚拟列表优化` |
| `test` | 测试相关 | `test(auth): 添加登录测试` |
| `chore` | 构建/工具 | `chore(deps): 升级 React 版本` |

### 提交示例

```bash
# 好的提交
git commit -m "feat(consultation): 添加律师预约功能

- 实现日历组件选择时间
- 集成支付流程
- 添加预约确认弹窗

Closes #123"

# 避免
git commit -m "update"
git commit -m "fix bug"
git commit -m "临时提交"
```

---

## 代码审查规范

### 审查清单

#### 功能性
- [ ] 代码是否实现了需求
- [ ] 边界条件是否处理
- [ ] 错误处理是否完善

#### 质量
- [ ] TypeScript 类型是否完整
- [ ] 是否有 `any` 类型
- [ ] 代码重复是否已提取
- [ ] 命名是否清晰有意义

#### 性能
- [ ] 不必要的重渲染
- [ ] 昂贵的计算是否使用 useMemo
- [ ] 图片是否优化

#### 安全
- [ ] 敏感信息是否硬编码
- [ ] XSS 漏洞检查
- [ ] 权限校验是否完善

#### 测试
- [ ] 单元测试是否覆盖
- [ ] 测试用例是否有意义
- [ ] 边界情况是否测试

### 审查原则

1. **建设性** - 提出问题同时提供解决方案
2. **尊重性** - 对代码不对人
3. **及时性** - 24 小时内完成审查
4. **彻底性** - 不遗漏关键问题

---

## 性能规范

### 性能预算

| 指标 | 目标 | 警告阈值 |
|-----|------|---------|
| FCP | < 1.5s | > 2s |
| LCP | < 2.5s | > 4s |
| FID | < 100ms | > 300ms |
| CLS | < 0.1 | > 0.25 |
| TTI | < 3.8s | > 5s |
| 包体积 | < 200KB (gzipped) | > 300KB |

### 性能优化检查表

- [ ] 使用 `React.lazy` 进行代码分割
- [ ] 图片使用 WebP 格式 + 懒加载
- [ ] 字体使用 `font-display: swap`
- [ ] 第三方脚本异步加载
- [ ] 使用 Service Worker 缓存
- [ ] 关键 CSS 内联

---

## 安全规范

### 前端安全清单

- [ ] **XSS 防护** - 使用 DOMPurify 净化 HTML
- [ ] **CSRF 防护** - 使用 SameSite Cookie
- [ ] **敏感数据** - 禁止在 localStorage 存储 token
- [ ] **依赖安全** - 定期运行 `npm audit`
- [ ] **输入验证** - 所有用户输入必须验证
- [ ] **HTTPS** - 强制 HTTPS 访问

### 代码安全示例

```typescript
// ✅ XSS 防护
import DOMPurify from 'dompurify';

function RichContent({ html }: { html: string }) {
  const cleanHtml = useMemo(() => DOMPurify.sanitize(html), [html]);
  return <div dangerouslySetInnerHTML={{ __html: cleanHtml }} />;
}

// ✅ 敏感操作确认
function DeleteButton({ onDelete }: { onDelete: () => void }) {
  const handleClick = () => {
    if (confirm('确定要删除吗？此操作不可恢复。')) {
      onDelete();
    }
  };
  
  return <button onClick={handleClick}>删除</button>;
}
```

---

## 附录

### 推荐的 VS Code 扩展

- ESLint
- Prettier
- TypeScript Importer
- Auto Rename Tag
- Tailwind CSS IntelliSense

### 常用命令

```bash
# 开发
npm run dev              # 启动开发服务器
npm run lint             # 运行 ESLint
npm run lint:fix         # 自动修复 ESLint
npm run format           # 运行 Prettier

# 测试
npm run test:unit        # 单元测试
npm run test:unit:watch  # 监听模式
npm run test:e2e         # E2E 测试

# 构建
npm run build            # 生产构建
npm run preview          # 预览生产构建
```

### 参考资源

- [React 官方文档](https://react.dev/)
- [TypeScript 严格模式指南](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)
- [React Query 最佳实践](https://tanstack.com/query/latest/docs/react/overview)
- [Web 性能优化](https://web.dev/performance-scoring/)

---

**最后更新**: 2026年2月6日

**维护者**: 前端团队

---

## 十三、旧前端迁移规范 (2026年2月新增)

### 13.1 迁移原则

1. **先文档后代码** - 迁移前先阅读旧前端代码，理解业务逻辑
2. **保持接口一致** - API 端点尽量保持不变
3. **渐进式迁移** - 逐个模块迁移，确保可运行
4. **借鉴优良设计** - 保留旧前端优秀的设计模式

### 13.2 迁移自旧前端的设计模式

#### 13.2.1 ApiException 统一错误类

```typescript
// shared/lib/api/exception.ts
export class ApiException extends Error {
  constructor(
    public readonly code: string,
    public readonly message: string,
    public readonly details?: unknown,
    public readonly requestId?: string,
    public readonly status?: number
  ) {
    super(message);
    this.name = 'ApiException';
  }
}

// 使用示例
try {
  await api.get('/users');
} catch (error) {
  if (error instanceof ApiException) {
    console.error(`[${error.code}] ${error.message}`);
  }
}
```

#### 13.2.2 内存 Token 存储

```typescript
// shared/lib/token.ts
// 比 localStorage 更安全，防止 XSS 攻击

let authToken: string | null = null;

export function getToken(): string | null {
  return authToken;
}

export function setToken(token: string | null): void {
  authToken = token;
}

export function clearToken(): void {
  authToken = null;
}
```

#### 13.2.3 流式请求 (SSE)

```typescript
// shared/lib/api/stream.ts
export interface StreamOptions {
  onData: (data: { eventType: string; data: unknown }) => void;
  onError: (error: ApiException) => void;
  onComplete?: () => void;
}

export function streamPost(
  url: string,
  data: unknown,
  options: StreamOptions
): AbortController {
  const abortController = new AbortController();
  // 实现 SSE 流式读取
  return abortController;
}
```

#### 13.2.4 Token 刷新队列

```typescript
// shared/lib/api/token-refresh.ts
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

export function subscribeTokenRefresh(callback: (token: string) => void): void {
  refreshSubscribers.push(callback);
}

export function onTokenRefreshed(newToken: string): void {
  refreshSubscribers.forEach((callback) => callback(newToken));
  refreshSubscribers = [];
}
```

### 13.3 迁移检查清单

迁移任何模块前，检查以下项目：

- [ ] **API 类型定义** - 所有请求/响应必须有类型
- [ ] **错误处理** - 使用 ApiException 统一处理
- [ ] **Query Keys** - 遵循 queryKeys 规范
- [ ] **组件类型** - 所有组件返回 `JSX.Element`
- [ ] **ESLint** - 零错误
- [ ] **测试覆盖** - 核心逻辑 >80%

### 13.4 迁移步骤

#### Step 1: 分析旧代码

```bash
# 查看旧前端模块结构
ls frontend/src/features/{module}/

# 识别核心文件
- api.ts        # API 调用
- hooks/       # React Query hooks
- types.ts     # 类型定义
- components/  # UI 组件
```

#### Step 2: 创建模块骨架

```bash
# 创建 Payment 模块
mkdir -p features/payment/{api,hooks,types,components,pages}
```

#### Step 3: 迁移 API 层

```typescript
// features/payment/api/index.ts
import { api } from '@/shared/lib/api/client';
import type { PaymentOrder, CreateOrderRequest } from '../types';

// 迁移自 frontend/src/features/payment/api.ts
export async function getOrders(params?: { page?: number }) {
  return api.get<PaymentOrder[]>('/payment/orders', { params });
}

export async function createOrder(data: CreateOrderRequest) {
  return api.post<PaymentOrder>('/payment/orders', data);
}
```

#### Step 4: 迁移 Hooks

```typescript
// features/payment/hooks/usePaymentOrders.ts
import { useQuery } from '@tanstack/react-query';
import { paymentApi } from '../api';

const paymentQueryKeys = {
  all: ['payment'] as const,
  orders: (params) => [...paymentQueryKeys.all, 'orders', params] as const,
};

export function usePaymentOrders(params?: { page?: number }) {
  return useQuery({
    queryKey: paymentQueryKeys.orders(params),
    queryFn: () => paymentApi.getOrders(params),
    staleTime: 30 * 1000,
  });
}
```

#### Step 5: 迁移组件

```typescript
// features/payment/components/PaymentList/index.tsx
import { usePaymentOrders } from '../../hooks';

export function PaymentList(): JSX.Element {
  const { data, isLoading } = usePaymentOrders();
  
  if (isLoading) return <Loading />;
  
  return (
    <div className="payment-list">
      {/* ... */}
    </div>
  );
}
```

### 13.5 常见问题

#### Q1: 旧前端使用相对路径导入，如何处理？

```typescript
// 旧代码
import { chatApi } from '../../../api/domains/chat';

// 新代码
import { chatApi } from '@/features/chat/api';
```

#### Q2: 旧前端类型定义不完整？

```typescript
// 补充缺失的类型
interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  // 从 API 响应推断并补充
}
```

#### Q3: 旧前端使用 class 组件？

```typescript
// 旧代码 (class)
class UserCard extends React.Component {}

// 新代码 (function + memo)
function UserCard() {}
export default memo(UserCard);
```

### 13.6 迁移优先级

| 优先级 | 模块 | 原因 |
|-------|------|------|
| P0 | Payment | 核心业务，支付功能 |
| P0 | Lawyer | 核心业务，律师工作台 |
| P1 | Chat 增强 | 分享、导出、评价 |
| P1 | Document | 用户核心需求 |
| P2 | Forum | 扩展功能 |
| P2 | News | 扩展功能 |

如有疑问，请联系 @frontend-team