# 前端上线部署检查清单

> 百姓助手前端 V2 版本部署检查文档
> 
> 最后更新：2026-02-18

---

## 目录

1. [部署前检查清单](#1-部署前检查清单)
2. [构建验证](#2-构建验证)
3. [部署配置验证](#3-部署配置验证)
4. [上线后验证](#4-上线后验证)
5. [回滚方案](#5-回滚方案)

---

## 1. 部署前检查清单

### 1.1 环境变量配置检查

#### 必需环境变量

| 变量名 | 说明 | 示例值 | 检查状态 |
|--------|------|--------|----------|
| `VITE_API_BASE_URL` | API 基础路径 | `/api` 或 `https://api.example.com` | ☐ |
| `VITE_API_TIMEOUT` | API 请求超时时间（毫秒） | `30000` | ☐ |
| `VITE_WS_URL` | WebSocket 连接地址 | `wss://api.example.com/ws` | ☐ |
| `VITE_TOKEN_REFRESH_INTERVAL` | Token 刷新间隔（毫秒） | `300000` | ☐ |

#### 功能开关变量

| 变量名 | 说明 | 生产环境建议值 | 检查状态 |
|--------|------|----------------|----------|
| `VITE_ENABLE_AI_CHAT` | AI 聊天功能 | `true` | ☐ |
| `VITE_ENABLE_PAYMENT` | 支付功能 | `true` | ☐ |
| `VITE_ENABLE_FORUM` | 论坛功能 | `true` | ☐ |
| `VITE_ENABLE_MOCK` | Mock 数据 | `false` （生产必须关闭）| ☐ |

#### 环境变量检查命令

```bash
# 检查 .env.production 文件是否包含所有必需变量
cat frontend-v2/.env.production | grep -E "^VITE_"

# 或使用 Node.js 脚本验证
node -e "
const required = ['VITE_API_BASE_URL', 'VITE_WS_URL'];
const env = process.env;
const missing = required.filter(key => !env[key]);
if (missing.length) {
  console.error('缺少环境变量:', missing.join(', '));
  process.exit(1);
}
console.log('环境变量检查通过');
"
```

### 1.2 构建配置检查

#### Node.js 版本要求

```bash
# 检查 Node.js 版本（要求 >= 18.0.0）
node -v

# 检查 npm 版本（要求 >= 9.0.0）
npm -v
```

#### package.json 配置验证

- [ ] 确认 `version` 字段已更新为正确版本号
- [ ] 确认 `engines` 字段配置正确（`node >= 18.0.0`, `npm >= 9.0.0`）
- [ ] 确认所有依赖版本已锁定（使用 `package-lock.json`）

#### 构建配置文件检查

| 文件 | 检查项 | 状态 |
|------|--------|------|
| `vite.config.ts` | 构建优化配置、代码分割策略 | ☐ |
| `tsconfig.json` | TypeScript 严格模式配置 | ☐ |
| `tailwind.config.js` | CSS 生产环境优化 | ☐ |
| `.env.production` | 生产环境变量配置 | ☐ |

### 1.3 依赖版本检查

```bash
# 进入前端目录
cd frontend-v2

# 检查过时依赖
npm outdated

# 检查安全漏洞
npm audit

# 修复可自动修复的漏洞
npm audit fix

# 生成依赖报告
npm list --depth=0
```

#### 核心依赖版本确认

| 依赖 | 当前版本 | 最低要求 | 检查状态 |
|------|----------|----------|----------|
| react | ^18.2.0 | 18.0.0 | ☐ |
| react-dom | ^18.2.0 | 18.0.0 | ☐ |
| react-router-dom | ^6.20.0 | 6.0.0 | ☐ |
| @tanstack/react-query | ^5.8.0 | 5.0.0 | ☐ |
| axios | ^1.7.0 | 1.0.0 | ☐ |
| antd | ^5.21.3 | 5.0.0 | ☐ |
| zustand | ^4.4.0 | 4.0.0 | ☐ |

### 1.4 安全配置检查

#### 代码安全检查

```bash
# 运行安全扫描
npm audit --audit-level=moderate

# 检查敏感信息泄露
grep -r "password\|secret\|api_key\|token" frontend-v2/src --include="*.ts" --include="*.tsx" | grep -v "type\|interface\|//"
```

#### 安全检查清单

- [ ] 确认 `.env` 文件未被提交到 Git
- [ ] 确认 `.env.production` 中的敏感信息使用环境变量注入
- [ ] 确认没有硬编码的 API 密钥或密码
- [ ] 确认 CSP（内容安全策略）配置正确
- [ ] 确认 CORS 配置限制为生产域名

#### `.gitignore` 检查

```bash
# 确认敏感文件已被忽略
cat frontend-v2/.gitignore | grep -E "\.env|\.key|\.pem"
```

---

## 2. 构建验证

### 2.1 生产构建命令

#### 本地构建

```bash
# 进入前端目录
cd frontend-v2

# 清理旧的构建产物
rm -rf dist

# 安装依赖（使用 lockfile 确保版本一致）
npm ci --legacy-peer-deps

# 执行类型检查
npm run type-check

# 执行代码检查
npm run lint

# 执行生产构建
npm run build
```

#### Docker 构建

```bash
# 构建生产镜像
docker build \
  --build-arg VITE_API_BASE_URL=/api \
  --build-arg VITE_WS_URL=wss://api.example.com/ws \
  -t baixing-assistant-frontend-v2:latest \
  -f frontend-v2/Dockerfile \
  frontend-v2

# 查看镜像大小
docker images | grep baixing-assistant-frontend-v2
```

### 2.2 构建产物验证

#### 构建产物检查清单

```bash
# 检查 dist 目录结构
ls -la frontend-v2/dist/

# 检查主要文件是否存在
ls -la frontend-v2/dist/index.html
ls -la frontend-v2/dist/assets/
```

| 文件/目录 | 说明 | 检查状态 |
|-----------|------|----------|
| `dist/index.html` | 入口 HTML 文件 | ☐ |
| `dist/assets/*.js` | JavaScript 打包文件 | ☐ |
| `dist/assets/*.css` | CSS 样式文件 | ☐ |
| `dist/favicon.svg` | 网站图标 | ☐ |

#### 构建大小检查

```bash
# 分析构建产物大小
du -sh frontend-v2/dist/

# 检查 JS 文件大小（建议单文件 < 500KB）
ls -lh frontend-v2/dist/assets/*.js

# 检查 CSS 文件大小（建议 < 100KB）
ls -lh frontend-v2/dist/assets/*.css
```

#### 构建大小限制

| 资源类型 | 建议大小限制 | 警告阈值 | 检查状态 |
|----------|--------------|----------|----------|
| 单个 JS 文件 | < 500KB | > 1MB | ☐ |
| 单个 CSS 文件 | < 100KB | > 200KB | ☐ |
| 总构建大小 | < 5MB | > 10MB | ☐ |
| 首屏资源 | < 1MB | > 2MB | ☐ |

#### 本地预览验证

```bash
# 本地预览构建产物
cd frontend-v2
npm run preview

# 访问 http://localhost:4173 验证页面是否正常
```

### 2.3 Source Map 配置

#### 生产环境 Source Map 配置

在生产环境中，Source Map 应该：
- 不部署到 CDN（仅用于错误追踪服务）
- 或使用隐藏模式（`hidden-source-map`）

#### vite.config.ts 配置建议

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    // 生产环境生成 Source Map 用于错误追踪
    sourcemap: process.env.NODE_ENV === 'production' ? 'hidden' : true,
    
    // 代码分割配置
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          antd: ['antd'],
          query: ['@tanstack/react-query'],
        },
      },
    },
  },
})
```

#### Source Map 检查

```bash
# 检查是否生成了 Source Map 文件
find frontend-v2/dist -name "*.map" -type f

# 如果生成了，确保不会被部署到生产环境
# 或配置 Sentry 等服务上传 Source Map
```

---

## 3. 部署配置验证

### 3.1 Nginx 配置检查

#### 前端容器内置 Nginx 配置验证

检查 `frontend-v2/Dockerfile` 中的 Nginx 配置是否包含：

| 配置项 | 说明 | 检查状态 |
|--------|------|----------|
| Gzip 压缩 | 静态资源压缩 | ☐ |
| 安全头 | X-Frame-Options, X-Content-Type-Options | ☐ |
| 静态资源缓存 | JS/CSS/图片缓存策略 | ☐ |
| SPA 路由支持 | try_files 回退到 index.html | ☐ |
| API 代理 | /api 代理到后端服务 | ☐ |
| WebSocket 代理 | /ws WebSocket 代理 | ☐ |
| 健康检查 | /health 端点 | ☐ |

#### 独立 Nginx 配置示例

如果使用独立的 Nginx 反向代理：

```nginx
# /etc/nginx/conf.d/baixing.conf

# 上游服务定义
upstream frontend {
    server frontend:3000;
}

upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name example.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;
    
    # SSL 证书配置
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;
    
    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml;
    gzip_comp_level 6;
    
    # 前端静态文件
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # 健康检查
    location /health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
```

### 3.2 CDN 配置检查

#### CDN 配置清单

| 配置项 | 说明 | 检查状态 |
|--------|------|----------|
| 静态资源加速 | JS/CSS/图片 CDN 分发 | ☐ |
| 缓存规则 | 静态资源长期缓存 | ☐ |
| Gzip/Brotli | CDN 层压缩 | ☐ |
| HTTPS | 全站 HTTPS | ☐ |
| HTTP/2 或 HTTP/3 | 协议升级 | ☐ |

#### 静态资源缓存策略

```
# 建议的缓存策略
*.js, *.css     -> Cache-Control: public, max-age=31536000, immutable
*.png, *.jpg    -> Cache-Control: public, max-age=31536000, immutable
*.svg, *.woff   -> Cache-Control: public, max-age=31536000, immutable
index.html      -> Cache-Control: no-cache, no-store, must-revalidate
```

#### CDN 节点健康检查

```bash
# 检查 CDN 节点响应
curl -I https://cdn.example.com/assets/index.js

# 检查缓存状态
curl -I -H "Cache-Control: no-cache" https://cdn.example.com/assets/index.js | grep -i "x-cache"
```

### 3.3 HTTPS 配置检查

#### SSL/TLS 配置检查

```bash
# 使用 testssl.sh 检查 SSL 配置
./testssl.sh https://example.com

# 或使用在线工具
# https://www.ssllabs.com/ssltest/
```

#### HTTPS 配置清单

| 检查项 | 期望值 | 检查状态 |
|--------|--------|----------|
| SSL 证书有效期 | > 30 天 | ☐ |
| TLS 版本 | TLS 1.2 / TLS 1.3 | ☐ |
| HSTS 头 | 已启用 | ☐ |
| 证书链 | 完整 | ☐ |
| 混合内容 | 无 | ☐ |

#### HTTP 到 HTTPS 重定向验证

```bash
# 验证 HTTP 重定向到 HTTPS
curl -I http://example.com

# 期望输出包含 301 或 302 重定向到 https://
```

---

## 4. 上线后验证

### 4.1 功能冒烟测试

#### 核心功能验证清单

| 功能模块 | 测试点 | 检查状态 |
|----------|--------|----------|
| **用户认证** | | |
| 登录 | 用户名密码登录成功 | ☐ |
| 注册 | 新用户注册流程 | ☐ |
| Token 刷新 | 自动刷新机制 | ☐ |
| 退出登录 | 清除用户状态 | ☐ |
| **首页** | | |
| 页面加载 | 首页正常显示 | ☐ |
| 导航菜单 | 菜单链接正常 | ☐ |
| **AI 咨询** | | |
| 咨询表单 | 表单提交正常 | ☐ |
| AI 对话 | 消息发送接收正常 | ☐ |
| 历史记录 | 历史记录显示正常 | ☐ |
| **支付功能** | | |
| 订单创建 | 订单创建流程 | ☐ |
| 支付流程 | 微信/支付宝支付 | ☐ |
| 支付回调 | 支付结果处理 | ☐ |
| **用户中心** | | |
| 个人信息 | 查看/编辑个人信息 | ☐ |
| 订单列表 | 订单历史查看 | ☐ |
| 积分中心 | 积分余额和记录 | ☐ |
| **论坛功能** | | |
| 帖子列表 | 帖子加载显示 | ☐ |
| 发帖 | 发帖功能正常 | ☐ |
| 评论 | 评论功能正常 | ☐ |

#### API 健康检查

```bash
# 检查后端 API 健康状态
curl -f https://api.example.com/health

# 检查前端健康端点
curl -f https://example.com/health

# 检查 WebSocket 连接
wscat -c wss://api.example.com/ws
```

### 4.2 性能指标验证

#### Core Web Vitals 指标

| 指标 | 说明 | 良好阈值 | 检查值 | 状态 |
|------|------|----------|--------|------|
| LCP (Largest Contentful Paint) | 最大内容绘制时间 | < 2.5s | ___s | ☐ |
| FID (First Input Delay) | 首次输入延迟 | < 100ms | ___ms | ☐ |
| CLS (Cumulative Layout Shift) | 累积布局偏移 | < 0.1 | ___ | ☐ |
| INP (Interaction to Next Paint) | 交互到下一次绘制 | < 200ms | ___ms | ☐ |

#### 其他性能指标

| 指标 | 说明 | 目标值 | 检查值 | 状态 |
|------|------|--------|--------|------|
| FCP (First Contentful Paint) | 首次内容绘制 | < 1.8s | ___s | ☐ |
| TTFB (Time to First Byte) | 首字节时间 | < 600ms | ___ms | ☐ |
| TTI (Time to Interactive) | 可交互时间 | < 3.8s | ___s | ☐ |

#### 性能测试命令

```bash
# 使用 Lighthouse CLI 测试
npx lighthouse https://example.com \
  --only-categories=performance \
  --output=json \
  --output-path=./lighthouse-report.json

# 使用 webpagetest.org API
# 或使用 Chrome DevTools
```

#### 性能监控工具

- **Google PageSpeed Insights**: https://pagespeed.web.dev/
- **WebPageTest**: https://www.webpagetest.org/
- **Lighthouse**: Chrome DevTools 或 CLI
- **Grafana Dashboard**: http://localhost:3000 (内部监控)

### 4.3 错误监控配置

#### Sentry 配置验证

```bash
# 检查 Sentry DSN 配置
echo $SENTRY_DSN

# 验证错误上报（发送测试错误）
curl -X POST "https://sentry.io/api/envelope/" \
  -H "Content-Type: application/x-sentry-envelope" \
  -d '{"dsn":"YOUR_DSN","event_id":"test","message":"Deployment verification"}'
```

#### 监控配置清单

| 监控项 | 配置位置 | 检查状态 |
|--------|----------|----------|
| 前端错误监控 | Sentry | ☐ |
| 后端错误监控 | Sentry | ☐ |
| 性能监控 | Prometheus + Grafana | ☐ |
| 日志收集 | Docker Logs | ☐ |
| 告警通知 | Alertmanager | ☐ |

#### Grafana Dashboard 验证

访问 Grafana 监控面板验证以下指标：

1. **前端性能面板**
   - 页面加载时间
   - API 响应时间
   - 错误率

2. **后端性能面板**
   - 请求 QPS
   - 响应时间 P50/P95/P99
   - 错误率

3. **基础设施面板**
   - CPU 使用率
   - 内存使用率
   - 网络流量

---

## 5. 回滚方案

### 5.1 快速回滚步骤

#### Docker 部署回滚

```bash
# 1. 查看当前运行版本
docker ps | grep baixing-frontend

# 2. 查看镜像历史版本
docker images | grep baixing-assistant-frontend-v2

# 3. 停止当前容器
docker stop baixing_frontend_prod

# 4. 切换到上一版本镜像
docker tag baixing-assistant-frontend-v2:previous baixing-assistant-frontend-v2:rollback
docker-compose -f docker-compose.prod.yml up -d frontend

# 5. 验证回滚结果
curl -f https://example.com/health

# 6. 确认回滚成功后清理
docker rmi baixing-assistant-frontend-v2:rollback
```

#### Docker Compose 快速回滚

```bash
# 方法1：使用镜像标签回滚
cd /path/to/project

# 更新 docker-compose.prod.yml 中的镜像版本
# 将 image: baixing-assistant-frontend-v2:latest
# 改为 image: baixing-assistant-frontend-v2:v1.x.x

# 重新部署
docker-compose -f docker-compose.prod.yml up -d frontend

# 方法2：使用之前的容器
docker-compose -f docker-compose.prod.yml rollback frontend
```

### 5.2 版本回退命令

#### 镜像版本管理

```bash
# 构建并标记版本
docker build \
  --build-arg VITE_API_BASE_URL=/api \
  --build-arg VITE_WS_URL=wss://api.example.com/ws \
  -t baixing-assistant-frontend-v2:v2.0.0 \
  -t baixing-assistant-frontend-v2:latest \
  -f frontend-v2/Dockerfile \
  frontend-v2

# 推送到镜像仓库
docker push your-registry.com/baixing-assistant-frontend-v2:v2.0.0
docker push your-registry.com/baixing-assistant-frontend-v2:latest
```

#### Git 版本回退

```bash
# 查看提交历史
git log --oneline -10

# 回退到指定版本
git checkout <commit-hash>

# 重新构建
cd frontend-v2
npm ci --legacy-peer-deps
npm run build

# 重新构建 Docker 镜像
docker build -t baixing-assistant-frontend-v2:rollback .
```

#### Kubernetes 部署回滚（如适用）

```bash
# 查看部署历史
kubectl rollout history deployment/baixing-frontend -n production

# 回滚到上一版本
kubectl rollout undo deployment/baixing-frontend -n production

# 回滚到指定版本
kubectl rollout undo deployment/baixing-frontend -n production --to-revision=2

# 查看回滚状态
kubectl rollout status deployment/baixing-frontend -n production
```

### 5.3 回滚验证清单

| 验证项 | 说明 | 检查状态 |
|--------|------|----------|
| 页面可访问 | 首页正常加载 | ☐ |
| API 连通 | API 请求正常 | ☐ |
| 登录功能 | 用户可以正常登录 | ☐ |
| 核心功能 | 主要业务流程正常 | ☐ |
| 监控正常 | 无异常告警 | ☐ |
| 日志正常 | 无大量错误日志 | ☐ |

### 5.4 回滚后处理

1. **通知相关方**
   - 通知开发团队回滚原因
   - 通知运维团队监控状态
   - 如有必要，通知用户

2. **问题分析**
   - 收集错误日志
   - 分析回滚原因
   - 记录到问题追踪系统

3. **修复计划**
   - 创建修复分支
   - 制定修复时间表
   - 计划重新部署

---

## 附录

### A. 常用命令速查

```bash
# 前端构建
cd frontend-v2 && npm run build

# Docker 构建
docker-compose -f docker-compose.prod.yml build frontend

# Docker 部署
docker-compose -f docker-compose.prod.yml up -d frontend

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f frontend

# 健康检查
curl -f http://localhost/health

# 进入容器
docker exec -it baixing_frontend_prod sh

# 清理未使用镜像
docker image prune -f
```

### B. 联系人

| 角色 | 姓名 | 联系方式 |
|------|------|----------|
| 前端负责人 | - | - |
| 后端负责人 | - | - |
| 运维负责人 | - | - |
| 产品负责人 | - | - |

### C. 相关文档

- [API 文档](./API.md)
- [开发指南](./DEVELOPMENT.md)
- [架构设计](./ARCHITECTURE.md)
- [运维手册](./OPERATIONS.md)

---

> **注意**：部署前请确保所有检查项都已完成，并在测试环境验证通过后再进行生产环境部署。