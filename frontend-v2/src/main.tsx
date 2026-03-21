/* eslint-disable react-refresh/only-export-components */
import { StrictMode, Suspense, lazy, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import { queryClient } from '@/shared/lib/query-client-core';
import { App } from '@/app/App';
import { ErrorBoundary } from '@/shared/components/ErrorBoundary';
import { ToastProvider } from '@/components/ui/ToastProvider';
import {
  addTokenChangeListener,
  getToken,
  removeTokenChangeListener,
} from '@/shared/lib/security/tokenStorage';
import '@/app/styles/index.css';

const LazyWebSocketProvider = lazy(() =>
  import('@/features/notification/context/WebSocketContext').then((module) => ({
    default: module.WebSocketProvider,
  }))
);

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

function RealtimeAppShell({ token }: { token: string | null }): JSX.Element {
  if (!token) {
    return <App />;
  }

  return (
    <Suspense fallback={<App />}>
      <LazyWebSocketProvider
        url={WS_URL}
        token={token}
        autoConnect={true}
        notificationConfig={{
          enableDesktopNotification: true,
          enableSound: false,
          maxDisplayCount: 5,
          displayDuration: 5000,
        }}
      >
        <App />
      </LazyWebSocketProvider>
    </Suspense>
  );
}

function AppProviders() {
  const [token, setToken] = useState<string | null>(() => getStoredToken());

  useEffect(() => {
    const handleTokenChange = () => {
      setToken(getStoredToken());
    };

    addTokenChangeListener(handleTokenChange);
    window.addEventListener('storage', handleTokenChange);

    return () => {
      removeTokenChangeListener(handleTokenChange);
      window.removeEventListener('storage', handleTokenChange);
    };
  }, []);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ToastProvider position="top-right" defaultDuration={5000}>
          <RealtimeAppShell token={token} />
        </ToastProvider>
        {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Failed to find the root element');
}

createRoot(rootElement).render(
  <StrictMode>
    <AppProviders />
  </StrictMode>
);