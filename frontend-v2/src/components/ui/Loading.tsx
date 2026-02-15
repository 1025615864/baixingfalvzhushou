/**
 * Loading 组件
 * 多种加载状态展示
 */

import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps): JSX.Element {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
  };

  return (
    <Loader2 className={`animate-spin text-primary-600 ${sizeClasses[size]} ${className}`} />
  );
}

interface LoadingDotsProps {
  className?: string;
}

export function LoadingDots({ className = '' }: LoadingDotsProps): JSX.Element {
  return (
    <div className={`flex items-center gap-1 ${className}`}>
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="w-2 h-2 bg-primary-600 rounded-full animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

interface LoadingOverlayProps {
  message?: string;
}

export function LoadingOverlay({ message = '加载中...' }: LoadingOverlayProps): JSX.Element {
  return (
    <div className="fixed inset-0 bg-white/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="text-center">
        <LoadingSpinner size="xl" className="mx-auto mb-4" />
        <p className="text-slate-600 font-medium">{message}</p>
      </div>
    </div>
  );
}

interface LoadingCardProps {
  className?: string;
}

export function LoadingCard({ className = '' }: LoadingCardProps): JSX.Element {
  return (
    <div className={`bg-white rounded-2xl p-6 shadow-soft border border-slate-100 ${className}`}>
      <div className="animate-pulse space-y-4">
        <div className="h-4 bg-slate-200 rounded-lg w-3/4" />
        <div className="h-4 bg-slate-200 rounded-lg w-1/2" />
        <div className="h-20 bg-slate-200 rounded-lg" />
      </div>
    </div>
  );
}

interface LoadingListProps {
  count?: number;
  className?: string;
}

export function LoadingList({ count = 3, className = '' }: LoadingListProps): JSX.Element {
  return (
    <div className={`space-y-4 ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-white rounded-xl p-4 shadow-soft border border-slate-100">
          <div className="animate-pulse flex items-center gap-4">
            <div className="w-12 h-12 bg-slate-200 rounded-xl" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-slate-200 rounded-lg w-1/3" />
              <div className="h-3 bg-slate-200 rounded-lg w-2/3" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

interface LoadingPageProps {
  message?: string;
}

export function LoadingPage({ message = '页面加载中...' }: LoadingPageProps): JSX.Element {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center">
        <div className="relative w-16 h-16 mx-auto mb-6">
          <div className="absolute inset-0 border-4 border-primary-200 rounded-full" />
          <div className="absolute inset-0 border-4 border-primary-600 rounded-full border-t-transparent animate-spin" />
        </div>
        <p className="text-slate-600 font-medium">{message}</p>
      </div>
    </div>
  );
}
