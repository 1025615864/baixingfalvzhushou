import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import { queryClient } from '@/shared/lib/query-client';
import { App } from '@/app/App';
import { WebSocketProvider } from '@/features/notification/context/WebSocketContext';
import { ErrorBoundary } from '@/shared/components/ErrorBoundary';
import { getToken } from '@/shared/lib/security/tokenStorage';
import '@/app/styles/index.css';

// WebSocket 服务器配置
// 开发环境使用 Vite 代理，生产环境使用实际的 WebSocket 地址
const WS_URL = (import.meta.env.VITE_WS_URL as string | undefined) ||
  (window.location.protocol === 'https:'
    ? `wss://${window.location.host}/ws`
    : `ws://${window.location.host}/ws`);

// 获取存储的认证 token
const getStoredToken = (): string | null => {
  return getToken();
};

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Failed to find the root element');
}

createRoot(rootElement).render(
  <StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <WebSocketProvider
          url={WS_URL}
          token={getStoredToken()}
          autoConnect={true}
          notificationConfig={{
            enableDesktopNotification: true,
            enableSound: false,
            maxDisplayCount: 5,
            displayDuration: 5000,
          }}
        >
          <App />
        </WebSocketProvider>
        {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>
);