import { Skeleton } from './Skeleton';

export interface PageSkeletonProps {
  type?: 'dashboard' | 'list' | 'detail' | 'form' | 'profile';
  count?: number;
}

export function PageSkeleton({ type = 'dashboard', count = 1 }: PageSkeletonProps) {
  const renderSkeleton = () => {
    switch (type) {
      case 'dashboard':
        return (
          <div className="space-y-6 p-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Skeleton className="h-64" />
              <Skeleton className="h-64" />
            </div>
            <Skeleton className="h-96" />
          </div>
        );

      case 'list':
        return (
          <div className="space-y-4 p-6">
            <div className="flex justify-between items-center mb-4">
              <Skeleton className="w-48 h-8" />
              <Skeleton className="w-32 h-8" />
            </div>
            <div className="space-y-3">
              {Array.from({ length: count }).map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          </div>
        );

      case 'detail':
        return (
          <div className="space-y-6 p-6">
            <Skeleton className="w-3/4 h-10" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-32" />
              </div>
              <Skeleton className="h-64" />
            </div>
          </div>
        );

      case 'form':
        return (
          <div className="space-y-6 p-6 max-w-2xl">
            <Skeleton className="w-48 h-8" />
            <div className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-10 w-32" />
            </div>
          </div>
        );

      case 'profile':
        return (
          <div className="space-y-6 p-6">
            <div className="flex items-center gap-4">
              <Skeleton className="w-20 h-20 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="w-48 h-6" />
                <Skeleton className="w-32 h-4" />
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
            </div>
            <Skeleton className="h-64" />
          </div>
        );

      default:
        return <Skeleton className="h-96" />;
    }
  };

  return <>{renderSkeleton()}</>;
}
