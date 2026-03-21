import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';

const Loading = lazy(() => import('@/shared/components/Loading').then(m => ({ default: m.Loading })));

const LazyLoad = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <Suspense fallback={<Loading fullScreen text="加载中..." />}>
    <Component />
  </Suspense>
);

const ForumHomePage = lazy(() => import('@/features/forum/pages/ForumHomePage').then(m => ({ default: m.ForumHomePage })));
const ForumPostDetailPage = lazy(() => import('@/features/forum/pages/PostDetailPage').then(m => ({ default: m.ForumPostDetailPage })));
const PostListPage = lazy(() => import('@/features/post/pages/PostListPage').then(m => ({ default: m.PostListPage })));
const PostDetailPage = lazy(() => import('@/features/post/pages/PostDetailPage').then(m => ({ default: m.PostDetailPage })));
const NewPostPage = lazy(() => import('@/features/post/pages/NewPostPage').then(m => ({ default: m.NewPostPage })));
const EditPostPage = lazy(() => import('@/features/post/pages/EditPostPage').then(m => ({ default: m.EditPostPage })));
const ForumAssistantPage = lazy(() => import('@/features/forum-assistant/pages/ForumAssistantPage').then(m => ({ default: m.ForumAssistantPage })));

export const forumRoutes: RouteObject[] = [
  { path: 'forum/home', element: LazyLoad(ForumHomePage) },
  { path: 'forum/post/:id', element: LazyLoad(ForumPostDetailPage) },
  { path: 'posts', element: LazyLoad(PostListPage) },
  { path: 'posts/new', element: LazyLoad(NewPostPage) },
  { path: 'posts/:id', element: LazyLoad(PostDetailPage) },
  { path: 'posts/:id/edit', element: LazyLoad(EditPostPage) },
  { path: 'forum-assistant', element: LazyLoad(ForumAssistantPage) },
];
