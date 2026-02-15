import { Outlet, useLocation } from 'react-router-dom';
import { useEffect } from 'react';

import { Navbar } from '@/widgets/Navbar';
import { Footer } from '@/widgets/Footer';

export function RootLayout(): JSX.Element {
  const location = useLocation();

  // 页面切换时滚动到顶部
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [location.pathname]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* 导航栏 */}
      <Navbar />

      {/* 主内容区域 */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* 页脚 */}
      <Footer />

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
      onClick={scrollToTop}
      className="fixed bottom-6 right-6 w-12 h-12 bg-primary-600 text-white rounded-full shadow-lg shadow-primary-500/30 hover:bg-primary-700 hover:shadow-xl hover:shadow-primary-500/40 transition-all duration-300 flex items-center justify-center group z-40"
      aria-label="返回顶部"
    >
      <svg
        className="w-5 h-5 transform group-hover:-translate-y-0.5 transition-transform"
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
