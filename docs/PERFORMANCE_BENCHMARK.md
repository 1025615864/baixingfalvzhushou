# 前端性能基准测试文档

## 概述

本文档定义了百姓助手前端应用的性能基准指标、测试方法、各模块性能目标以及优化建议。所有性能测试和优化工作应以此文档为基准。

---

## 1. 性能指标定义

### 1.1 核心 Web 指标 (Core Web Vitals)

| 指标 | 全称 | 目标值 | 说明 |
|------|------|--------|------|
| **FCP** | First Contentful Paint | < 1.8s | 首次内容绘制时间，从页面加载开始到首次渲染任何内容的时间 |
| **LCP** | Largest Contentful Paint | < 2.5s | 最大内容绘制时间，从页面加载开始到渲染最大可见内容元素的时间 |
| **FID** | First Input Delay | < 100ms | 首次输入延迟，用户首次交互到浏览器响应的时间 |
| **CLS** | Cumulative Layout Shift | < 0.1 | 累积布局偏移，衡量视觉稳定性，分数越低越好 |

### 1.2 Lighthouse 性能分数

| 指标 | 目标值 | 优先级 |
|------|--------|--------|
| Performance | >= 90 | 高 |
| Accessibility | >= 95 | 高 |
| Best Practices | >= 90 | 中 |
| SEO | >= 90 | 中 |
| PWA | >= 80 | 低 |

### 1.3 其他关键指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| **TTI** (Time to Interactive) | < 3.8s | 页面完全可交互时间 |
| **TBT** (Total Blocking Time) | < 200ms | 总阻塞时间 |
| **SI** (Speed Index) | < 3.4s | 速度指数，内容填充速度 |
| **FMP** (First Meaningful Paint) | < 2.0s | 首次有意义绘制 |

---

## 2. 测试方法

### 2.1 Lighthouse 测试

#### 本地测试
```bash
# 使用 Chrome DevTools
# 1. 打开 Chrome 开发者工具 (F12)
# 2. 切换到 Lighthouse 面板
# 3. 选择 Performance、Accessibility、Best Practices、SEO
# 4. 点击 "Analyze page load"

# 使用 CLI
npx lighthouse http://localhost:5173 --output=html --output-path=./lighthouse-report.html
```

#### CI/CD 集成测试
```yaml
# .github/workflows/performance.yml
name: Performance Tests
on: [push, pull_request]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Lighthouse CI
        uses: treosh/lighthouse-ci-action@v9
        with:
          urls: |
            http://localhost:5173/
            http://localhost:5173/consultation
            http://localhost:5173/membership
          budgetPath: ./performance-budget.json
          uploadArtifacts: true
```

### 2.2 Chrome DevTools Performance

#### 性能分析步骤
1. 打开 Chrome DevTools (F12)
2. 切换到 **Performance** 面板
3. 点击 **Record** 按钮开始录制
4. 执行需要测试的用户操作
5. 停止录制并分析结果

#### 重点关注
- **Main Thread**：长任务 (>50ms) 分析
- **Network**：资源加载瀑布图
- **Memory**：内存泄漏检测
- **Coverage**：未使用的 CSS/JS 代码

### 2.3 WebPageTest 测试

#### 测试配置
```json
{
  "testUrl": "https://baixing.com",
  "location": "Dulles_MotoG5:Motorola G5 - Chrome",
  "browser": "Chrome",
  "connection": "4G",
  "runs": 5,
  "firstViewOnly": true,
  "video": true,
  "timeline": true,
  "keepua": true
}
```

#### 测试场景
| 场景 | 设备 | 网络 | 位置 |
|------|------|------|------|
| 桌面端 | Desktop Chrome | Cable | 上海 |
| 移动端 4G | Mobile Chrome | 4G | 上海 |
| 移动端弱网 | Mobile Chrome | 3G Slow | 上海 |

---

## 3. 各模块性能目标

### 3.1 会员中心模块 (Membership)

| 页面/功能 | FCP | LCP | TTI | 备注 |
|-----------|-----|-----|-----|------|
| VIP 首页 | < 1.5s | < 2.0s | < 3.0s | 静态内容为主 |
| 权益对比页 | < 1.8s | < 2.5s | < 3.5s | 包含对比表格 |
| 购买流程 | < 1.5s | < 2.0s | < 3.0s | 关键转化路径 |
| 支付结果页 | < 1.0s | < 1.5s | < 2.0s | 极简页面 |

**关键优化点：**
- 会员卡片图片预加载
- 权益图标使用 SVG Sprite
- 价格计算逻辑懒加载

### 3.2 视频咨询模块 (Video Consultation)

| 页面/功能 | FCP | LCP | TTI | 备注 |
|-----------|-----|-----|-----|------|
| 预约列表页 | < 1.8s | < 2.5s | < 3.5s | 包含日历组件 |
| 律师选择页 | < 1.5s | < 2.2s | < 3.0s | 卡片列表 |
| 视频通话页 | < 1.0s | < 1.5s | < 2.0s | WebRTC 初始化 |
| 预约详情页 | < 1.5s | < 2.0s | < 3.0s | 包含地图组件 |

**关键优化点：**
- WebRTC SDK 按需加载
- 日历组件虚拟化
- 律师头像懒加载
- 地图组件延迟加载

### 3.3 法律文书商城模块 (Legal Document Mall)

| 页面/功能 | FCP | LCP | TTI | 备注 |
|-----------|-----|-----|-----|------|
| 商城首页 | < 1.5s | < 2.0s | < 3.0s | 分类导航 |
| 文书列表页 | < 1.8s | < 2.5s | < 3.5s | 分页加载 |
| 文书详情页 | < 1.5s | < 2.2s | < 3.0s | 富文本内容 |
| 预览/下载 | < 1.0s | < 1.5s | < 2.0s | PDF 渲染 |

**关键优化点：**
- 文书缩略图 CDN 加速
- PDF 预览器 Web Worker
- 长列表虚拟滚动
- 分类数据本地缓存

---

## 4. 性能优化建议

### 4.1 代码分割策略

#### 路由级别分割
```typescript
// 使用 React.lazy 进行路由级别懒加载
const MembershipPage = React.lazy(() => import('./features/membership/pages/VipPage'));
const VideoConsultationPage = React.lazy(() => import('./features/video-consultation/pages/VideoConsultationPage'));
const LegalDocumentMallPage = React.lazy(() => import('./features/legal-document-mall/pages/LegalDocumentMallPage'));
```

#### 组件级别分割
```typescript
// 重型组件动态导入
const PDFViewer = React.lazy(() => import('./components/PDFViewer'));
const VideoPlayer = React.lazy(() => import('./components/VideoPlayer'));
const CalendarComponent = React.lazy(() => import('./components/Calendar'));
```

#### 第三方库分割
```typescript
// vite.config.ts 配置
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui': ['@tanstack/react-query', 'zustand'],
          'vendor-utils': ['dayjs', 'lodash-es'],
          'vendor-rich': ['@tiptap/react', '@tiptap/starter-kit'],
        },
      },
    },
  },
});
```

### 4.2 图片优化

#### 图片格式选择
| 场景 | 推荐格式 | 备注 |
|------|----------|------|
| 照片/复杂图像 | WebP / AVIF | 压缩率高 |
| 图标/Logo | SVG | 矢量无损 |
| 简单图形 | PNG | 透明背景 |
| 动画 | WebM / Lottie | 替代 GIF |

#### 图片加载策略
```typescript
// 懒加载配置
<img 
  src={imageUrl} 
  loading="lazy" 
  decoding="async"
  alt={description}
/>

// 响应式图片
<picture>
  <source srcSet={`${image}@2x.webp 2x, ${image}.webp`} type="image/webp" />
  <source srcSet={`${image}@2x.jpg 2x, ${image}.jpg`} type="image/jpeg" />
  <img src={`${image}.jpg`} alt={description} loading="lazy" />
</picture>
```

#### 图片压缩标准
| 类型 | 质量设置 | 最大文件大小 |
|------|----------|--------------|
| 缩略图 | 75% | 20KB |
| 列表图 | 80% | 50KB |
| 详情图 | 85% | 150KB |
| 全屏图 | 90% | 300KB |

### 4.3 缓存策略

#### HTTP 缓存配置
```nginx
# nginx.conf
location /static/ {
  expires 1y;
  add_header Cache-Control "public, immutable";
}

location /assets/ {
  expires 1y;
  add_header Cache-Control "public, immutable";
}

location ~* \.(html)$ {
  expires -1;
  add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

#### Service Worker 缓存
```typescript
// sw.js
const STATIC_CACHE = 'static-v1';
const DYNAMIC_CACHE = 'dynamic-v1';

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/static/js/main.js',
  '/static/css/main.css',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request).then((fetchResponse) => {
        return caches.open(DYNAMIC_CACHE).then((cache) => {
          cache.put(event.request.url, fetchResponse.clone());
          return fetchResponse;
        });
      });
    })
  );
});
```

#### React Query 缓存配置
```typescript
// 查询客户端配置
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5分钟
      cacheTime: 10 * 60 * 1000, // 10分钟
      refetchOnWindowFocus: false,
      retry: 2,
    },
  },
});
```

---

## 5. 性能监控配置

### 5.1 生产环境性能监控

#### Web Vitals 上报
```typescript
// utils/performance.ts
import { onCLS, onFID, onLCP, onFCP, onTTFB } from 'web-vitals';

interface PerformanceMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  timestamp: number;
}

const sendToAnalytics = (metric: PerformanceMetric) => {
  const body = JSON.stringify({
    ...metric,
    page: window.location.pathname,
    userAgent: navigator.userAgent,
  });

  // 使用 sendBeacon 确保数据发送
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/v1/analytics/performance', body);
  } else {
    fetch('/api/v1/analytics/performance', {
      method: 'POST',
      body,
      keepalive: true,
    });
  }
};

export const initPerformanceMonitoring = () => {
  onCLS(sendToAnalytics);
  onFID(sendToAnalytics);
  onLCP(sendToAnalytics);
  onFCP(sendToAnalytics);
  onTTFB(sendToAnalytics);
};
```

#### 自定义性能标记
```typescript
// 使用 Performance API 标记关键节点
export const markPerformance = (name: string) => {
  if (typeof performance !== 'undefined') {
    performance.mark(name);
  }
};

export const measurePerformance = (name: string, startMark: string, endMark: string) => {
  if (typeof performance !== 'undefined') {
    try {
      performance.measure(name, startMark, endMark);
      const measure = performance.getEntriesByName(name, 'measure')[0];
      return measure?.duration || 0;
    } catch (e) {
      console.warn('Performance measure failed:', e);
      return 0;
    }
  }
  return 0;
};

// 使用示例
markPerformance('page-load-start');
// ... 页面加载逻辑
markPerformance('page-load-end');
const loadTime = measurePerformance('page-load', 'page-load-start', 'page-load-end');
```

### 5.2 性能指标上报

#### 上报数据结构
```typescript
interface PerformanceReport {
  // 基础信息
  timestamp: number;
  page: string;
  route: string;
  userAgent: string;
  
  // Core Web Vitals
  metrics: {
    fcp: number;
    lcp: number;
    fid: number;
    cls: number;
    ttfb: number;
  };
  
  // 自定义指标
  custom: {
    apiResponseTime: number;
    renderTime: number;
    interactionTime: number;
  };
  
  // 环境信息
  environment: {
    connection: string;
    memory: number;
    cpuCores: number;
  };
}
```

#### 错误与慢请求上报
```typescript
// 慢请求检测
const SLOW_API_THRESHOLD = 3000; // 3秒

apiClient.interceptors.response.use(
  (response) => {
    const requestTime = response.config?.metadata?.startTime;
    if (requestTime) {
      const duration = Date.now() - requestTime;
      if (duration > SLOW_API_THRESHOLD) {
        reportSlowRequest({
          url: response.config.url,
          method: response.config.method,
          duration,
          statusCode: response.status,
        });
      }
    }
    return response;
  },
  (error) => {
    reportApiError({
      url: error.config?.url,
      method: error.config?.method,
      message: error.message,
      statusCode: error.response?.status,
    });
    return Promise.reject(error);
  }
);
```

### 5.3 监控告警配置

#### 告警规则
```yaml
# alertmanager/rules/performance.yml
groups:
  - name: performance_alerts
    rules:
      - alert: HighLCP
        expr: histogram_quantile(0.75, rate(lcp_seconds_bucket[5m])) > 2.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "LCP 超过阈值"
          description: "75分位 LCP 超过 2.5s，当前值: {{ $value }}s"

      - alert: HighFID
        expr: histogram_quantile(0.75, rate(fid_seconds_bucket[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "FID 超过阈值"
          description: "75分位 FID 超过 100ms，当前值: {{ $value }}s"

      - alert: HighCLS
        expr: histogram_quantile(0.75, rate(cls_bucket[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CLS 超过阈值"
          description: "75分位 CLS 超过 0.1，当前值: {{ $value }}"
```

#### Grafana 仪表盘
```json
{
  "dashboard": {
    "title": "Frontend Performance Dashboard",
    "panels": [
      {
        "title": "Core Web Vitals",
        "type": "graph",
        "targets": [
          { "expr": "histogram_quantile(0.5, rate(lcp_seconds_bucket[5m]))", "legendFormat": "LCP p50" },
          { "expr": "histogram_quantile(0.75, rate(lcp_seconds_bucket[5m]))", "legendFormat": "LCP p75" },
          { "expr": "histogram_quantile(0.95, rate(lcp_seconds_bucket[5m]))", "legendFormat": "LCP p95" }
        ]
      },
      {
        "title": "Page Load Time by Route",
        "type": "heatmap",
        "targets": [
          { "expr": "rate(page_load_seconds_bucket[5m])", "legendFormat": "{{route}}" }
        ]
      }
    ]
  }
}
```

---

## 6. 性能预算

### 6.1 资源预算

| 资源类型 | 预算限制 | 当前值 | 状态 |
|----------|----------|--------|------|
| JavaScript (gzip) | < 200KB | - | 待测 |
| CSS (gzip) | < 50KB | - | 待测 |
| Images (首屏) | < 300KB | - | 待测 |
| Fonts | < 100KB | - | 待测 |
| Total (首屏) | < 700KB | - | 待测 |

### 6.2 请求预算

| 请求类型 | 预算限制 | 备注 |
|----------|----------|------|
| 总请求数 | < 30 | 首屏 |
| 关键请求数 | < 10 | 阻塞渲染 |
| 第三方请求 | < 5 | 分析、监控等 |

### 6.3 时间预算

| 阶段 | 预算 | 备注 |
|------|------|------|
| DNS 查询 | < 100ms | - |
| TCP 连接 | < 100ms | - |
| TLS 握手 | < 100ms | - |
| TTFB | < 600ms | 服务器响应 |
| 资源下载 | < 1000ms | 首屏资源 |

---

## 7. 性能测试清单

### 7.1 发布前检查

- [ ] Lighthouse Performance 分数 >= 90
- [ ] Lighthouse Accessibility 分数 >= 95
- [ ] 所有 Core Web Vitals 指标达标
- [ ] JavaScript 包大小在预算内
- [ ] 无内存泄漏
- [ ] 首屏无长任务 (>50ms)
- [ ] 图片已优化 (WebP/AVIF)
- [ ] 关键 CSS 内联
- [ ] 非关键资源延迟加载

### 7.2 定期审查

- [ ] 每周审查性能监控数据
- [ ] 每月进行 WebPageTest 测试
- [ ] 每季度更新性能预算
- [ ] 每半年进行全面的性能审计

---

## 8. 参考资料

- [Web Vitals - Google](https://web.dev/vitals/)
- [Lighthouse Performance Scoring](https://web.dev/performance-scoring/)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
- [WebPageTest Documentation](https://docs.webpagetest.org/)
- [React Performance Optimization](https://react.dev/learn/render-and-commit)

---

**文档版本**: 1.0.0  
**最后更新**: 2024年1月  
**维护者**: 前端团队