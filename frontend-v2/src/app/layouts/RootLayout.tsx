import { Outlet, useLocation } from 'react-router-dom';
import { lazy, Suspense, useEffect } from 'react';

const LazyNavbar = lazy(() => import('@/widgets/Navbar').then((module) => ({ default: module.Navbar })));
const LazyFooter = lazy(() => import('@/widgets/Footer').then((module) => ({ default: module.Footer })));

function NavbarFallback(): JSX.Element {
  return <div className="h-16 lg:h-18" aria-hidden="true" />;
}

function FooterFallback(): JSX.Element {
  return <div className="h-80" aria-hidden="true" />;
}

export function RootLayout(): JSX.Element {
  const location = useLocation();

  // 页面切换时滚动到顶部
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [location.pathname]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* 导航栏 */}
      <Suspense fallback={<NavbarFallback />}>
        <LazyNavbar />
      </Suspense>

      {/* 主内容区域 */}
      <main key={location.pathname} className="flex-1 w-full">
        <Outlet />
      </main>

      {/* 页脚 */}
      <Suspense fallback={<FooterFallback />}>
        <LazyFooter />
      </Suspense>

      {/* 全局返回顶部按钮 */}
      <ScrollToTopButton />
    </div>
  );
}

// 返回顶部按钮组件
function ScrollToTopButton(): JSX.Element {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <button
      type="button"
      onClick={scrollToTop}
      className="fixed bottom-6 right-6 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-primary-600 text-white shadow-lg shadow-primary-500/30 transition-all duration-300 hover:scale-105 hover:bg-primary-700 hover:shadow-xl hover:shadow-primary-500/40 active:scale-95"
      aria-label="返回顶部"
    >
      <svg
        className="w-5 h-5 transition-transform duration-200 hover:-translate-y-0.5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M5 10l7-7m0 0l7 7m-7-7v18"
        />
      </svg>
    </button>
  );
}
