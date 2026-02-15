import { Link, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { X, ChevronRight, User, Settings, Bell, Scale, Shield, MoreVertical } from 'lucide-react';

import { useAuthStore } from '@/features/auth/store/authStore';
import { useLogout } from '@/features/auth/hooks/useAuth';
import { NotificationBell } from '@/features/notification/components/NotificationBell';
import { useUnreadCount } from '@/features/notification/hooks/useNotifications';
import { Button } from '@/components/ui/Button';

interface NavItem {
  label: string;
  href: string;
  icon?: React.ReactNode;
  description?: string;
}

const navItems: NavItem[] = [
  { label: '首页', href: '/', description: '法律服务首页' },
  { label: 'AI咨询', href: '/chat', description: '智能法律助手' },
  { label: '找律师', href: '/lawyer', description: '专业律师推荐' },
  { label: '法律知识', href: '/knowledge', description: '法律法规库' },
  { label: '资讯', href: '/news', description: '法律新闻动态' },
  { label: '文档', href: '/document', description: '法律文书生成' },
];

export function Navbar(): JSX.Element {
  const { user, isAuthenticated } = useAuthStore();
  const { mutate: logout, isPending } = useLogout();
  const location = useLocation();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const { data: unreadData } = useUnreadCount(isAuthenticated);
  const unreadCount = unreadData?.unread_count ?? 0;

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    setIsMobileMenuOpen(false);
    setIsUserMenuOpen(false);
  }, [location.pathname]);

  const handleLogout = () => {
    logout();
    setIsUserMenuOpen(false);
  };

  const isActive = (href: string) => {
    if (href === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(href);
  };

  return (
    <>
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled
            ? 'bg-white/95 backdrop-blur-xl shadow-navbar border-b border-slate-100/80'
            : 'bg-white/80 backdrop-blur-md'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 lg:h-18">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3 group">
              {/* Logo 图标 - 天平造型，象征法律公正 */}
              <div className="relative">
                <div className="w-10 h-10 bg-gradient-hero rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30 group-hover:shadow-primary-500/50 transition-all duration-300 group-hover:scale-105">
                  <Scale className="w-5 h-5 text-white" />
                </div>
                {/* 装饰光效 */}
                <div className="absolute -inset-1 bg-primary-500/20 rounded-xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              </div>
              {/* Logo 文字 */}
              <div className="flex flex-col">
                <span className={`text-xl font-bold tracking-tight transition-colors ${
                  isScrolled ? 'text-slate-900' : 'text-slate-900'
                }`}>
                  <span className="text-primary-600">百姓</span>助手
                </span>
                <span className="text-[10px] text-slate-400 font-medium -mt-0.5 hidden sm:block">
                  专业法律服务平台
                </span>
              </div>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  to={item.href}
                  className={`relative px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 group ${
                    isActive(item.href)
                      ? 'text-primary-600 bg-primary-50'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  {item.label}
                  {/* 活动指示器 */}
                  {isActive(item.href) && (
                    <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-0.5 bg-primary-600 rounded-full" />
                  )}
                  {/* Hover 效果 */}
                  <span className="absolute inset-0 rounded-lg bg-primary-50 opacity-0 group-hover:opacity-100 transition-opacity -z-10" />
                </Link>
              ))}
            </div>

            {/* Right Section */}
            <div className="flex items-center gap-2 sm:gap-3">
              {/* Trust Badge - 仅桌面显示 */}
              {!isAuthenticated && (
                <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 bg-primary-50 text-primary-700 rounded-full text-xs font-medium">
                  <Shield className="w-3.5 h-3.5" />
                  <span>安全可靠</span>
                </div>
              )}

              {/* Notification Bell - Desktop */}
              {isAuthenticated && (
                <div className="hidden sm:block">
                  <NotificationBell size="md" />
                </div>
              )}

              {/* User Section */}
              {isAuthenticated ? (
                <div className="relative">
                  <button
                    onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                    className="flex items-center gap-2 p-1.5 rounded-xl hover:bg-slate-100 transition-all duration-200 group"
                  >
                    <div className="relative">
                      <div className="w-9 h-9 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center text-white font-semibold text-sm shadow-md group-hover:shadow-lg transition-shadow">
                        {user?.avatar ? (
                          <img
                            src={user.avatar}
                            alt={user.nickname || user.username}
                            className="w-9 h-9 rounded-xl object-cover"
                          />
                        ) : (
                          <span>{(user?.nickname || user?.username || 'U').charAt(0).toUpperCase()}</span>
                        )}
                      </div>
                      {/* 在线状态指示器 */}
                      <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 border-2 border-white rounded-full" />
                    </div>
                    <ChevronRight className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${isUserMenuOpen ? 'rotate-90' : ''}`} />
                  </button>

                  {/* User Dropdown Menu */}
                  {isUserMenuOpen && (
                    <>
                      <div
                        className="fixed inset-0 z-10"
                        onClick={() => setIsUserMenuOpen(false)}
                      />
                      <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-soft-lg border border-slate-100 py-2 z-20 animate-fade-in-up origin-top-right">
                        {/* 用户信息 */}
                        <div className="px-4 py-3 border-b border-slate-100">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center text-white font-semibold">
                              {user?.avatar ? (
                                <img src={user.avatar} alt="" className="w-10 h-10 rounded-xl object-cover" />
                              ) : (
                                <span>{(user?.nickname || user?.username || 'U').charAt(0).toUpperCase()}</span>
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-semibold text-slate-900 truncate">{user?.nickname || user?.username}</p>
                              <p className="text-xs text-slate-500 truncate">{user?.email}</p>
                            </div>
                          </div>
                        </div>

                        {/* 菜单项 */}
                        <div className="py-1.5">
                          <Link
                            to="/profile"
                            className="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors group"
                          >
                            <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center group-hover:bg-primary-100 group-hover:text-primary-600 transition-colors">
                              <User className="w-4 h-4" />
                            </div>
                            <span>个人中心</span>
                          </Link>
                          <Link
                            to="/payment"
                            className="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors group"
                          >
                            <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center group-hover:bg-gold-100 group-hover:text-gold-600 transition-colors">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                              </svg>
                            </div>
                            <span>支付中心</span>
                          </Link>
                          <Link
                            to="/notifications"
                            className="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors group sm:hidden"
                          >
                            <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center group-hover:bg-secondary-100 group-hover:text-secondary-600 transition-colors relative">
                              <Bell className="w-4 h-4" />
                              {unreadCount > 0 && (
                                <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center">
                                  {unreadCount > 9 ? '9+' : unreadCount}
                                </span>
                              )}
                            </div>
                            <span>消息通知</span>
                          </Link>
                          <Link
                            to="/settings"
                            className="flex items-center gap-3 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors group"
                          >
                            <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center group-hover:bg-slate-200 transition-colors">
                              <Settings className="w-4 h-4" />
                            </div>
                            <span>设置</span>
                          </Link>
                        </div>

                        {/* 退出登录 */}
                        <div className="border-t border-slate-100 pt-1.5 mt-1">
                          <button
                            onClick={handleLogout}
                            disabled={isPending}
                            className="flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors w-full group"
                          >
                            <div className="w-8 h-8 rounded-lg bg-red-50 flex items-center justify-center group-hover:bg-red-100 transition-colors">
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                              </svg>
                            </div>
                            <span>{isPending ? '退出中...' : '退出登录'}</span>
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <div className="hidden sm:flex items-center gap-2">
                  <Link to="/login">
                    <Button variant="ghost" size="sm">
                      登录
                    </Button>
                  </Link>
                  <Link to="/register">
                    <Button variant="primary" size="sm">
                      免费注册
                    </Button>
                  </Link>
                </div>
              )}

              {/* Mobile Menu Button */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="lg:hidden p-2 rounded-xl hover:bg-slate-100 transition-colors"
                aria-label="菜单"
              >
                {isMobileMenuOpen ? (
                  <X className="w-5 h-5 text-slate-600" />
                ) : (
                  <MoreVertical className="w-5 h-5 text-slate-600" />
                )}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          {/* 背景遮罩 */}
          <div
            className="absolute inset-0 bg-slate-900/20 backdrop-blur-sm"
            onClick={() => setIsMobileMenuOpen(false)}
          />

          {/* 菜单面板 */}
          <div className="absolute top-16 lg:top-18 left-0 right-0 bg-white border-b border-slate-100 shadow-soft-lg animate-slide-down">
            <div className="max-h-[calc(100vh-4rem)] overflow-y-auto">
              <div className="px-4 py-4 space-y-1">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    to={item.href}
                    className={`flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                      isActive(item.href)
                        ? 'text-primary-600 bg-primary-50'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                    }`}
                  >
                    <div>
                      <span>{item.label}</span>
                      {item.description && (
                        <p className={`text-xs mt-0.5 ${isActive(item.href) ? 'text-primary-400' : 'text-slate-400'}`}>
                          {item.description}
                        </p>
                      )}
                    </div>
                    <ChevronRight className={`w-4 h-4 ${isActive(item.href) ? 'text-primary-400' : 'text-slate-300'}`} />
                  </Link>
                ))}
              </div>

              {/* 未登录状态下的按钮 */}
              {!isAuthenticated && (
                <div className="px-4 py-4 border-t border-slate-100 space-y-2">
                  <Link to="/login" className="block">
                    <Button variant="outline" fullWidth size="md">
                      登录
                    </Button>
                  </Link>
                  <Link to="/register" className="block">
                    <Button variant="primary" fullWidth size="md">
                      免费注册
                    </Button>
                  </Link>
                </div>
              )}

              {/* 底部信任标识 */}
              <div className="px-4 py-3 border-t border-slate-100 bg-slate-50/50">
                <div className="flex items-center justify-center gap-4 text-xs text-slate-400">
                  <span className="flex items-center gap-1">
                    <Shield className="w-3.5 h-3.5" />
                    安全加密
                  </span>
                  <span className="flex items-center gap-1">
                    <Scale className="w-3.5 h-3.5" />
                    专业服务
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 占位符，防止内容被导航栏遮挡 */}
      <div className="h-16 lg:h-18" />
    </>
  );
}
