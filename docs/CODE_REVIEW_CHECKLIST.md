# 前端代码审查与优化检查清单

本文档为前端代码审查提供全面的检查清单和优化建议，确保代码质量、安全性和可维护性。

## 目录

- [代码审查检查清单](#代码审查检查清单)
  - [TypeScript 类型安全](#typescript-类型安全)
  - [React 组件最佳实践](#react-组件最佳实践)
  - [性能优化检查](#性能优化检查)
  - [安全检查](#安全检查)
  - [可访问性检查](#可访问性检查)
- [新增模块审查要点](#新增模块审查要点)
  - [会员中心模块](#会员中心模块)
  - [视频咨询模块](#视频咨询模块)
  - [法律文书商城模块](#法律文书商城模块)
- [优化建议](#优化建议)
  - [代码重复检测](#代码重复检测)
  - [未使用代码清理](#未使用代码清理)
  - [依赖更新建议](#依赖更新建议)
- [代码规范验证](#代码规范验证)
  - [ESLint 规则检查](#eslint-规则检查)
  - [Prettier 格式化检查](#prettier-格式化检查)
  - [命名规范检查](#命名规范检查)

---

## 代码审查检查清单

### TypeScript 类型安全

#### 基础类型检查

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 禁止使用 `any` 类型 | 使用具体类型或泛型替代 | ⬜ |
| [ ] 避免类型断言 | 优先使用类型守卫 | ⬜ |
| [ ] 明确函数返回类型 | 所有函数都应有明确的返回类型 | ⬜ |
| [ ] 使用严格空值检查 | 启用 `strictNullChecks` | ⬜ |
| [ ] 避免隐式 `any` | 为回调函数参数明确类型 | ⬜ |

#### 接口与类型定义

```typescript
// ✅ 正确示例：明确的类型定义
interface UserProfile {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

// ❌ 错误示例：使用 any
const getUser = (id: string): any => { ... }

// ✅ 正确示例：明确的返回类型
const getUser = (id: string): Promise<UserProfile> => { ... }
```

#### 类型导出规范

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 类型定义集中管理 | 在 `types/index.ts` 中统一导出 | ⬜ |
| [ ] 避免重复定义 | 共享类型应放在公共目录 | ⬜ |
| [ ] 使用 `type` vs `interface` | 根据场景合理选择 | ⬜ |

#### API 响应类型

```typescript
// ✅ 正确示例：API 响应类型定义
interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

interface PaginatedResponse<T> extends ApiResponse<T[]> {
  total: number;
  page: number;
  pageSize: number;
}
```

---

### React 组件最佳实践

#### 组件结构

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 单一职责原则 | 每个组件只负责一个功能 | ⬜ |
| [ ] 组件拆分 | 复杂组件拆分为子组件 | ⬜ |
| [ ] Props 类型定义 | 使用 TypeScript 接口定义 Props | ⬜ |
| [ ] 默认 Props | 为可选 Props 提供默认值 | ⬜ |
| [ ] 组件文档 | 复杂组件添加 JSDoc 注释 | ⬜ |

#### 函数组件规范

```typescript
// ✅ 正确示例：规范的函数组件
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
}

/**
 * 通用按钮组件
 * @param props - 按钮属性
 * @returns 按钮组件
 */
export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  children,
}) => {
  return (
    <button
      className={`btn btn-${variant} btn-${size}`}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
};
```

#### Hooks 使用规范

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] Hooks 顶层调用 | 不在条件语句中调用 Hooks | ⬜ |
| [ ] 依赖数组完整 | `useEffect` 等依赖数组完整 | ⬜ |
| [ ] 自定义 Hooks | 复杂逻辑封装为自定义 Hooks | ⬜ |
| [ ] useCallback/useMemo | 合理使用避免不必要的渲染 | ⬜ |
| [ ] 状态提升 | 共享状态提升到共同父组件 | ⬜ |

#### 状态管理

```typescript
// ✅ 正确示例：使用 Zustand 状态管理
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  login: (user) => set({ user, isAuthenticated: true }),
  logout: () => set({ user: null, isAuthenticated: false }),
}));
```

#### 错误处理

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 错误边界 | 使用 ErrorBoundary 捕获错误 | ⬜ |
| [ ] 异常捕获 | 异步操作使用 try-catch | ⬜ |
| [ ] 错误提示 | 用户友好的错误提示 | ⬜ |
| [ ] 错误日志 | 记录错误日志便于排查 | ⬜ |

---

### 性能优化检查

#### 渲染优化

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] React.memo | 纯组件使用 memo 避免重渲染 | ⬜ |
| [ ] 虚拟列表 | 长列表使用虚拟滚动 | ⬜ |
| [ ] 懒加载 | 组件和路由懒加载 | ⬜ |
| [ ] 图片优化 | 图片懒加载、压缩、WebP | ⬜ |
| [ ] 防抖节流 | 频繁操作使用防抖节流 | ⬜ |

#### 代码示例

```typescript
// ✅ 懒加载组件
const LazyComponent = React.lazy(() => import('./HeavyComponent'));

// ✅ 虚拟列表
import { FixedSizeList } from 'react-window';

// ✅ 图片懒加载
<img loading="lazy" src={imageUrl} alt={description} />

// ✅ 防抖处理
const debouncedSearch = useDebounce(searchTerm, 300);
```

#### 网络优化

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 请求缓存 | 使用 React Query 缓存 | ⬜ |
| [ ] 请求合并 | 批量请求减少网络开销 | ⬜ |
| [ ] 数据分页 | 大数据集分页加载 | ⬜ |
| [ ] 请求取消 | 组件卸载取消未完成请求 | ⬜ |
| [ ] Gzip 压缩 | 服务器启用压缩 | ⬜ |

#### 包体积优化

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] Tree Shaking | 按需导入组件库 | ⬜ |
| [ ] 代码分割 | 路由级别代码分割 | ⬜ |
| [ ] 依赖分析 | 检查大型依赖 | ⬜ |
| [ ] 外部化 | 大型库使用 CDN | ⬜ |

```bash
# 分析包体积
npm run build -- --analyze
```

---

### 安全检查

#### XSS 防护

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 避免 dangerouslySetInnerHTML | 优先使用安全的渲染方式 | ⬜ |
| [ ] 用户输入转义 | 对用户输入进行过滤 | ⬜ |
| [ ] URL 参数验证 | 验证 URL 参数合法性 | ⬜ |
| [ ] CSP 配置 | 配置内容安全策略 | ⬜ |

#### 认证与授权

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] Token 安全存储 | 使用 httpOnly cookie 或安全存储 | ⬜ |
| [ ] Token 过期处理 | 处理 Token 过期刷新 | ⬜ |
| [ ] 权限校验 | 前端路由权限控制 | ⬜ |
| [ ] 敏感信息保护 | 不在前端存储敏感信息 | ⬜ |

#### API 安全

```typescript
// ✅ 正确示例：安全的 API 请求
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器添加 Token
apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器处理错误
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 处理未授权
      redirectToLogin();
    }
    return Promise.reject(error);
  }
);
```

#### 敏感数据处理

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 不记录敏感信息 | console.log 不输出敏感数据 | ⬜ |
| [ ] 表单自动完成 | 敏感字段禁用自动完成 | ⬜ |
| [ ] 密码字段 | 使用 type="password" | ⬜ |

---

### 可访问性检查

#### ARIA 属性

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 语义化标签 | 使用正确的 HTML 语义标签 | ⬜ |
| [ ] ARIA 标签 | 为交互元素添加 aria-label | ⬜ |
| [ ] 角色定义 | 为自定义组件定义 role | ⬜ |
| [ ] 状态通知 | 使用 aria-live 通知状态变化 | ⬜ |

#### 键盘导航

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] Tab 顺序 | 合理的 tab 顺序 | ⬜ |
| [ ] 焦点管理 | 模态框焦点管理 | ⬜ |
| [ ] 快捷键 | 支持常用快捷键 | ⬜ |
| [ ] 跳过链接 | 提供跳过导航链接 | ⬜ |

```typescript
// ✅ 可访问性示例
<button
  aria-label="关闭对话框"
  aria-pressed={isPressed}
  role="button"
  tabIndex={0}
  onClick={handleClose}
>
  <XIcon aria-hidden="true" />
</button>
```

#### 视觉辅助

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 颜色对比度 | 文本与背景对比度足够 | ⬜ |
| [ ] 不依赖颜色 | 信息不仅通过颜色传达 | ⬜ |
| [ ] 字体大小 | 可调整的字体大小 | ⬜ |
| [ ] 屏幕阅读器 | 支持屏幕阅读器 | ⬜ |

---

## 新增模块审查要点

### 会员中心模块

#### 文件结构检查

```
features/membership/
├── api/
│   └── index.ts          # API 请求函数
├── components/
│   ├── MembershipCard.tsx
│   ├── MembershipBenefits.tsx
│   ├── MembershipComparison.tsx
│   ├── PricingCard.tsx
│   ├── PurchaseFlow.tsx
│   └── UpgradePrompt.tsx
├── hooks/
│   └── useMembership.ts  # 自定义 Hooks
├── pages/
│   └── VipPage.tsx       # 页面组件
├── store/
│   └── membershipStore.ts # Zustand 状态
└── types/
    └── index.ts          # 类型定义
```

#### 功能检查清单

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 会员等级展示 | 正确展示会员等级和权益 | ⬜ |
| [ ] 购买流程 | 完整的购买流程和支付集成 | ⬜ |
| [ ] 权益对比 | 会员等级权益对比展示 | ⬜ |
| [ ] 升级提示 | 适时显示升级提示 | ⬜ |
| [ ] 状态同步 | 购买后状态实时更新 | ⬜ |
| [ ] 过期提醒 | 会员即将过期提醒 | ⬜ |

#### 代码质量检查

```typescript
// 检查 useMembership Hook
// ✅ 应包含的功能
interface UseMembershipReturn {
  membership: Membership | null;
  isLoading: boolean;
  error: Error | null;
  purchaseMembership: (tier: string) => Promise<void>;
  upgradeMembership: (tier: string) => Promise<void>;
  cancelMembership: () => Promise<void>;
}

// 检查 membershipStore
// ✅ 应包含的状态
interface MembershipState {
  currentTier: MembershipTier;
  expiresAt: string | null;
  benefits: Benefit[];
  isLoading: boolean;
  setMembership: (membership: Membership) => void;
  clearMembership: () => void;
}
```

#### 性能检查

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 权益列表懒加载 | 大量权益按需加载 | ⬜ |
| [ ] 价格计算缓存 | 价格计算结果缓存 | ⬜ |
| [ ] 图片优化 | 会员图标优化 | ⬜ |

---

### 视频咨询模块

#### 文件结构检查

```
features/video-consultation/
├── api/
│   └── index.ts
├── components/
│   ├── VideoConsultationBooking.tsx
│   ├── VideoConsultationCard.tsx
│   ├── VideoConsultationList.tsx
│   ├── VideoConsultationRoom.tsx
│   └── LawyerSchedulePicker.tsx
├── hooks/
│   └── useVideoConsultation.ts
├── pages/
│   └── VideoConsultationPage.tsx
├── store/
│   └── videoConsultationStore.ts
└── types/
    └── index.ts
```

#### 功能检查清单

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 律师日程展示 | 正确展示律师可预约时间 | ⬜ |
| [ ] 预约流程 | 完整的预约和支付流程 | ⬜ |
| [ ] 视频房间 | WebRTC 视频通话功能 | ⬜ |
| [ ] 实时通信 | WebSocket 消息同步 | ⬜ |
| [ ] 咨询记录 | 保存和查看咨询记录 | ⬜ |
| [ ] 评价功能 | 咨询后评价律师 | ⬜ |

#### 实时通信检查

```typescript
// ✅ WebSocket 连接管理
interface VideoConsultationSocket {
  connect: (consultationId: string) => void;
  disconnect: () => void;
  sendSignal: (signal: RTCSignal) => void;
  onSignal: (callback: (signal: RTCSignal) => void) => void;
  onStatusChange: (callback: (status: ConsultationStatus) => void) => void;
}

// ✅ WebRTC 连接管理
interface WebRTCManager {
  createOffer: () => Promise<RTCSessionDescriptionInit>;
  createAnswer: (offer: RTCSessionDescriptionInit) => Promise<RTCSessionDescriptionInit>;
  setRemoteDescription: (description: RTCSessionDescriptionInit) => void;
  addIceCandidate: (candidate: RTCIceCandidateInit) => void;
  getLocalStream: () => MediaStream | null;
  getRemoteStream: () => MediaStream | null;
}
```

#### 错误处理检查

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 网络断开处理 | 网络断开重连机制 | ⬜ |
| [ ] 设备权限处理 | 摄像头/麦克风权限拒绝处理 | ⬜ |
| [ ] 浏览器兼容性 | WebRTC 浏览器兼容性检查 | ⬜ |
| [ ] 超时处理 | 连接超时处理 | ⬜ |

---

### 法律文书商城模块

#### 文件结构检查

```
features/legal-document-mall/
├── api/
│   └── index.ts
├── components/
│   ├── DocumentCard.tsx
│   ├── DocumentCategoryList.tsx
│   ├── DocumentDetail.tsx
│   ├── DocumentGrid.tsx
│   └── DocumentPurchaseFlow.tsx
├── hooks/
│   └── useLegalDocuments.ts
├── pages/
│   └── LegalDocumentMallPage.tsx
└── types/
    └── index.ts
```

#### 功能检查清单

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 文书分类 | 按类型分类展示文书 | ⬜ |
| [ ] 搜索功能 | 文书搜索和筛选 | ⬜ |
| [ ] 文书预览 | 购买前预览部分内容 | ⬜ |
| [ ] 购买流程 | 完整的购买和支付流程 | ⬜ |
| [ ] 文书下载 | 购买后下载文书 | ⬜ |
| [ ] 使用指南 | 文书使用说明 | ⬜ |

#### 数据结构检查

```typescript
// ✅ 文书类型定义
interface LegalDocument {
  id: string;
  title: string;
  description: string;
  category: DocumentCategory;
  price: number;
  originalPrice?: number;
  preview: string;
  content: string;
  tags: string[];
  downloads: number;
  rating: number;
  createdAt: string;
  updatedAt: string;
}

// ✅ 购买流程状态
interface PurchaseState {
  document: LegalDocument | null;
  step: 'preview' | 'payment' | 'download';
  paymentMethod: PaymentMethod | null;
  transactionId: string | null;
}
```

#### 性能检查

| 检查项 | 描述 | 状态 |
|--------|------|------|
| [ ] 列表虚拟滚动 | 大量文书虚拟滚动 | ⬜ |
| [ ] 图片懒加载 | 文书封面懒加载 | ⬜ |
| [ ] 搜索防抖 | 搜索输入防抖处理 | ⬜ |
| [ ] 缓存策略 | 文书列表缓存 | ⬜ |

---

## 优化建议

### 代码重复检测

#### 检测工具

```bash
# 使用 jscpd 检测重复代码
npx jscpd src --min-lines 10 --reporters console,html

# 使用 ESLint 检测重复
npm run lint -- --rule 'no-duplicate-imports: error'
```

#### 常见重复模式

| 重复类型 | 检测方法 | 优化建议 |
|----------|----------|----------|
| API 请求函数 | 检查 `api/index.ts` | 提取通用请求封装 |
| 组件样式 | 检查 CSS 类名 | 提取为 Tailwind 类 |
| 类型定义 | 检查 `types/` 目录 | 合并共享类型 |
| 工具函数 | 检查 `utils/` 目录 | 提取到共享工具 |

#### 重复代码重构示例

```typescript
// ❌ 重复代码示例
// features/membership/api/index.ts
export const getMembership = async () => {
  const response = await fetch('/api/membership');
  return response.json();
};

// features/payment/api/index.ts
export const getPaymentHistory = async () => {
  const response = await fetch('/api/payments');
  return response.json();
};

// ✅ 重构后：通用请求函数
// shared/lib/api/client.ts
export const apiClient = {
  get: <T>(url: string): Promise<T> => 
    fetch(url).then(res => res.json()),
  post: <T>(url: string, data: unknown): Promise<T> =>
    fetch(url, { method: 'POST', body: JSON.stringify(data) }).then(res => res.json()),
};

// features/membership/api/index.ts
export const getMembership = () => apiClient.get<Membership>('/api/membership');
```

---

### 未使用代码清理

#### 检测工具

```bash
# 使用 ts-prune 检测未使用的导出
npx ts-prune src

# 使用 depcheck 检测未使用的依赖
npx depcheck

# 使用 ESLint 检测未使用变量
npm run lint -- --rule 'no-unused-vars: error'
```

#### 清理清单

| 清理类型 | 检查命令 | 操作 |
|----------|----------|------|
| 未使用的导入 | `npm run lint` | 移除未使用的 import |
| 未使用的变量 | `npm run lint` | 移除或添加 `_` 前缀 |
| 未使用的组件 | 手动检查 | 移除未使用的组件文件 |
| 未使用的样式 | PurgeCSS | 清理未使用的 CSS |
| 未使用的依赖 | `depcheck` | 卸载未使用的 npm 包 |

#### 清理脚本

```bash
#!/bin/bash
# cleanup-unused.sh

echo "检测未使用的依赖..."
npx depcheck

echo "检测未使用的导出..."
npx ts-prune src | grep "unused"

echo "运行 ESLint 检查..."
npm run lint -- --fix

echo "清理完成！"
```

---

### 依赖更新建议

#### 当前主要依赖版本

| 依赖 | 当前版本 | 建议版本 | 更新优先级 |
|------|----------|----------|------------|
| React | 18.x | 18.x | 稳定 |
| React Router | 6.x | 6.x | 稳定 |
| TanStack Query | 5.x | 5.x | 稳定 |
| Zustand | 4.x | 4.x | 稳定 |
| TypeScript | 5.x | 5.x | 稳定 |
| Vite | 5.x | 5.x | 稳定 |
| Tailwind CSS | 3.x | 3.x | 稳定 |

#### 更新检查命令

```bash
# 检查过时的依赖
npm outdated

# 安全漏洞检查
npm audit

# 交互式更新
npx npm-check-updates -i
```

#### 更新策略

1. **安全更新**：立即处理 `npm audit` 报告的高危漏洞
2. **补丁更新**：定期合并补丁版本更新
3. **次版本更新**：评估新功能后合并
4. **主版本更新**：充分测试后升级

#### 依赖更新流程

```bash
# 1. 检查更新
npm outdated

# 2. 创建更新分支
git checkout -b chore/update-dependencies

# 3. 更新依赖
npm update

# 4. 运行测试
npm run test

# 5. 构建验证
npm run build

# 6. 提交更改
git add package*.json
git commit -m "chore: update dependencies"
```

---

## 代码规范验证

### ESLint 规则检查

#### 项目 ESLint 配置

项目使用以下 ESLint 配置（参考 `.eslintrc.cjs`）：

```javascript
// 关键规则说明
{
  // TypeScript 严格规则
  '@typescript-eslint/no-explicit-any': 'error',
  '@typescript-eslint/no-unused-vars': 'error',
  '@typescript-eslint/no-floating-promises': 'error',
  
  // React 规则
  'react/prop-types': 'off',
  'react/react-in-jsx-scope': 'off',
  'react-refresh/only-export-components': 'warn',
  
  // 最佳实践
  'no-console': ['warn', { allow: ['warn', 'error'] }],
  'no-debugger': 'error',
  'prefer-const': 'error',
  'no-var': 'error',
  
  // Import 排序
  'import/order': 'error'
}
```

#### ESLint 检查命令

```bash
# 运行 ESLint 检查
npm run lint

# 自动修复
npm run lint -- --fix

# 检查特定文件
npx eslint src/features/membership/

# 生成报告
npm run lint -- --output-file eslint-report.json --format json
```

#### 常见问题修复

| 规则 | 问题 | 修复方法 |
|------|------|----------|
| `no-explicit-any` | 使用了 any 类型 | 定义具体类型或使用泛型 |
| `no-unused-vars` | 未使用的变量 | 移除或添加 `_` 前缀 |
| `no-floating-promises` | Promise 未处理 | 使用 `void` 或 `await` |
| `import/order` | 导入顺序错误 | 按规则重新排序 |

---

### Prettier 格式化检查

#### 项目 Prettier 配置

项目使用以下 Prettier 配置（参考 `prettier.config.js`）：

```javascript
{
  semi: true,              // 语句分号
  trailingComma: 'es5',    // 尾随逗号
  singleQuote: true,       // 单引号
  printWidth: 100,         // 行宽
  tabWidth: 2,             // 缩进宽度
  useTabs: false,          // 空格缩进
  bracketSpacing: true,    // 对象括号空格
  arrowParens: 'avoid',    // 箭头函数参数
  endOfLine: 'lf',         // 换行符
}
```

#### Prettier 检查命令

```bash
# 检查格式
npx prettier --check "src/**/*.{ts,tsx}"

# 自动格式化
npx prettier --write "src/**/*.{ts,tsx}"

# 格式化特定目录
npx prettier --write "src/features/membership/**/*.{ts,tsx}"
```

#### IDE 集成

推荐在 VSCode 中安装 Prettier 插件，并配置自动格式化：

```json
// .vscode/settings.json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  }
}
```

---

### 命名规范检查

#### 文件命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件文件 | PascalCase | `MembershipCard.tsx` |
| Hook 文件 | camelCase + use 前缀 | `useMembership.ts` |
| 工具函数 | camelCase | `formatPrice.ts` |
| 类型文件 | camelCase | `index.ts` (在 types 目录下) |
| 样式文件 | 与组件同名 | `MembershipCard.module.css` |
| 测试文件 | 与源文件同名 + .test | `MembershipCard.test.tsx` |

#### 变量命名规范

```typescript
// ✅ 正确示例

// 组件：PascalCase
const MembershipCard: React.FC = () => { ... };

// 函数：camelCase，动词开头
const fetchMembership = async () => { ... };
const handlePurchase = () => { ... };

// 变量：camelCase，名词
const membershipData = { ... };
const totalPrice = 100;

// 常量：UPPER_SNAKE_CASE
const MAX_RETRY_COUNT = 3;
const API_BASE_URL = 'https://api.example.com';

// 类型/接口：PascalCase
interface MembershipProps { ... }
type MembershipTier = 'basic' | 'premium' | 'enterprise';

// 枚举：PascalCase，值 UPPER_SNAKE_CASE
enum PaymentStatus {
  PENDING = 'PENDING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
}

// 私有变量/方法：下划线前缀
const _privateMethod = () => { ... };

// 布尔值：is/has/can 前缀
const isLoading = true;
const hasMembership = false;
const canUpgrade = true;
```

#### 命名检查脚本

```bash
#!/bin/bash
# check-naming.sh

echo "检查组件命名..."
find src -name "*.tsx" -not -name "[A-Z]*" -not -name "index.tsx"

echo "检查 Hook 命名..."
find src -name "use*.ts" -not -path "*/hooks/*"

echo "检查类型文件..."
find src/types -name "*.ts" -not -name "index.ts" -not -name "*.d.ts"

echo "命名检查完成！"
```

---

## 审查流程

### 提交前审查

1. **本地检查**
   ```bash
   npm run lint
   npm run type-check
   npm run test
   npm run build
   ```

2. **自查清单**
   - [ ] 所有 lint 错误已修复
   - [ ] TypeScript 类型检查通过
   - [ ] 单元测试通过
   - [ ] 构建成功

### 代码审查流程

```
┌─────────────────────────────────────────────────────────────┐
│                      代码审查流程                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 提交 PR ──────► 2. CI 自动检查 ──────► 3. 人工审查      │
│        │                   │                   │            │
│        │                   ▼                   │            │
│        │           ┌─────────────┐             │            │
│        │           │ Lint/Type   │             │            │
│        │           │ Test/Build  │             │            │
│        │           └─────────────┘             │            │
│        │                   │                   │            │
│        ▼                   ▼                   ▼            │
│  ┌─────────┐         ┌─────────┐         ┌─────────┐       │
│  │ 修改    │         │ 通过    │         │ 批准    │       │
│  └─────────┘         └─────────┘         └─────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 审查清单使用说明

1. **审查前**：复制本文档的检查清单到 PR 描述中
2. **审查中**：逐项检查并标记状态
3. **审查后**：记录发现的问题和建议
4. **跟进**：跟踪问题的修复情况

---

## 附录

### 相关文档

- [开发指南](./DEVELOPMENT.md)
- [架构文档](./ARCHITECTURE.md)
- [功能文档](./FEATURES.md)
- [API 文档](./API.md)

### 工具推荐

| 工具 | 用途 | 安装命令 |
|------|------|----------|
| ESLint | 代码检查 | `npm install -D eslint` |
| Prettier | 代码格式化 | `npm install -D prettier` |
| TypeScript | 类型检查 | `npm install -D typescript` |
| jscpd | 重复代码检测 | `npm install -D jscpd` |
| depcheck | 依赖检查 | `npm install -D depcheck` |
| ts-prune | 未使用导出检测 | `npm install -D ts-prune` |

### 参考资源

- [React 官方文档](https://react.dev/)
- [TypeScript 最佳实践](https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html)
- [ESLint 规则](https://eslint.org/docs/latest/rules/)
- [Web 可访问性指南](https://www.w3.org/WAI/WCAG21/quickref/)