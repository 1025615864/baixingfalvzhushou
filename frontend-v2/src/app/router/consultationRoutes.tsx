import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';

const Loading = lazy(() => import('@/shared/components/Loading').then(m => ({ default: m.Loading })));

const LazyLoad = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <Suspense fallback={<Loading fullScreen text="加载中..." />}>
    <Component />
  </Suspense>
);

const ConsultationPage = lazy(() => import('@/pages/Consultation').then(m => ({ default: m.ConsultationPage })));
const ChatPage = lazy(() => import('@/pages/Chat').then(m => ({ default: m.ChatPage })));
const AIConsultationPage = lazy(() => import('@/features/ai-consultation/pages/AIConsultationPage').then(m => ({ default: m.AIConsultationPage })));
const ConsultationFormPage = lazy(() => import('@/features/ai-consultation/pages/ConsultationFormPage').then(m => ({ default: m.ConsultationFormPage })));
const ConsultationHistoryPage = lazy(() => import('@/features/ai-consultation/pages/ConsultationHistoryPage').then(m => ({ default: m.ConsultationHistoryPage })));
const LawyerSelectionPage = lazy(() => import('@/features/ai-consultation/pages/LawyerSelectionPage').then(m => ({ default: m.LawyerSelectionPage })));
const ConsultationChatPage = lazy(() => import('@/features/ai-consultation/pages/ConsultationChatPage').then(m => ({ default: m.ConsultationChatPage })));
const VideoConsultationPage = lazy(() => import('@/features/video-consultation/pages').then(m => ({ default: m.VideoConsultationPage })));
const LawyerMatchingPage = lazy(() => import('@/features/lawyer-matching/pages/LawyerMatchingPage').then(m => ({ default: m.LawyerMatchingPage })));
const AIChatPage = lazy(() => import('@/features/chat/pages/ChatPage').then(m => ({ default: m.ChatPage })));

export const consultationRoutes: RouteObject[] = [
  { path: 'chat', element: LazyLoad(ChatPage) },
  { path: 'consultation', element: LazyLoad(ConsultationPage) },
  { path: 'ai-chat', element: LazyLoad(AIChatPage) },
  { path: 'ai-chat/:sessionId', element: LazyLoad(AIChatPage) },
  { path: 'ai-consultation', element: LazyLoad(AIConsultationPage) },
  { path: 'ai-consultation/:sessionId', element: LazyLoad(AIConsultationPage) },
  { path: 'consultation/new', element: LazyLoad(ConsultationFormPage) },
  { path: 'consultation/history', element: LazyLoad(ConsultationHistoryPage) },
  { path: 'consultation/:id/select-lawyer', element: LazyLoad(LawyerSelectionPage) },
  { path: 'consultation/:id/chat', element: LazyLoad(ConsultationChatPage) },
  { path: 'video-consultation', element: LazyLoad(VideoConsultationPage) },
  { path: 'video-consultation/:id', element: LazyLoad(VideoConsultationPage) },
  { path: 'video-consultation/:id/:action', element: LazyLoad(VideoConsultationPage) },
  { path: 'lawyer-matching', element: LazyLoad(LawyerMatchingPage) },
];
