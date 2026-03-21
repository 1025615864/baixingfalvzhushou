/**
 * RecommendationPage - 个性化推荐主页
 * 展示个性化推荐内容、推荐理由、用户兴趣标签
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  User,
  FileText,
  Scale,
  TrendingUp,
  ChevronRight,
  Star,
  Eye,
  MessageSquare,
  ThumbsUp,
  RefreshCw,
  Settings,
} from 'lucide-react';


import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/Loading';
import { ScrollReveal } from '@/components/ui/PageTransition';

import { useRecommendationPageData, useRecordInteraction } from '../hooks/useRecommendation';
import type {
  LawyerRecommendation,
  PostRecommendation,
  NewsRecommendation,
} from '../types';

export function RecommendationPage(): JSX.Element {
  const { recommendations, weights, isLoading, isError, error, refetch } = useRecommendationPageData();
  const recordInteraction = useRecordInteraction();
  const [activeTab, setActiveTab] = useState<'all' | 'lawyers' | 'posts' | 'news'>('all');

  // 记录用户点击
  const handleClick = (contentId: string, contentType: string) => {
    recordInteraction.mutate({
      contentId,
      contentType,
      interactionType: 'clicked',
    });
  };

  // 渲染律师推荐卡片
  const renderLawyerCard = (lawyer: LawyerRecommendation) => (
    <Link
      key={lawyer.lawyerId}
      to={`/lawyer/${lawyer.lawyerId}`}
      onClick={() => handleClick(String(lawyer.lawyerId), 'lawyer')}
      className="block bg-white rounded-2xl p-6 shadow-soft border border-slate-100 hover:shadow-soft-lg hover:-translate-y-1 transition-all duration-300"
    >
      <div className="flex items-start gap-4">
        <div className="w-14 h-14 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-md flex-shrink-0">
          {lawyer.lawyerName.charAt(0)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-slate-900">{lawyer.lawyerName}</h3>
            {lawyer.isVerified && (
              <span className="px-2 py-0.5 bg-primary-50 text-primary-600 text-xs font-medium rounded-full">
                已认证
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500 mb-2">{lawyer.specialties || '法律咨询'}</p>
          <div className="flex items-center gap-4 text-sm text-slate-600">
            <span className="flex items-center gap-1">
              <Star className="w-4 h-4 text-gold-500 fill-gold-500" />
              {lawyer.rating.toFixed(1)}
            </span>
            <span>{lawyer.consultationCount} 次咨询</span>
          </div>
        </div>
      </div>
      <div className="mt-4 pt-4 border-t border-slate-100">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">匹配度</span>
          <div className="flex items-center gap-2">
            <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary-400 to-primary-600 rounded-full"
                style={{ width: `${lawyer.matchScore * 100}%` }}
              />
            </div>
            <span className="text-xs font-medium text-primary-600">
              {Math.round(lawyer.matchScore * 100)}%
            </span>
          </div>
        </div>
      </div>
    </Link>
  );

  // 渲染帖子推荐卡片
  const renderPostCard = (post: PostRecommendation) => (
    <Link
      key={post.postId}
      to={`/forum/post/${post.postId}`}
      onClick={() => handleClick(String(post.postId), 'post')}
      className="block bg-white rounded-2xl p-6 shadow-soft border border-slate-100 hover:shadow-soft-lg hover:-translate-y-1 transition-all duration-300"
    >
      <h3 className="font-semibold text-slate-900 mb-2 line-clamp-2">{post.title}</h3>
      {post.content && (
        <p className="text-sm text-slate-600 mb-4 line-clamp-2">{post.content}</p>
      )}
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-500">{post.authorName}</span>
        <div className="flex items-center gap-3 text-slate-500">
          <span className="flex items-center gap-1">
            <Eye className="w-4 h-4" />
            {post.viewCount}
          </span>
          <span className="flex items-center gap-1">
            <ThumbsUp className="w-4 h-4" />
            {post.likeCount}
          </span>
          <span className="flex items-center gap-1">
            <MessageSquare className="w-4 h-4" />
            {post.commentCount}
          </span>
        </div>
      </div>
      <div className="mt-4 pt-4 border-t border-slate-100">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">推荐指数</span>
          <span className="text-xs font-medium text-primary-600">
            {Math.round(post.matchScore * 100)}%
          </span>
        </div>
      </div>
    </Link>
  );

  // 渲染新闻推荐卡片
  const renderNewsCard = (news: NewsRecommendation) => (
    <Link
      key={news.newsId}
      to={`/news/${news.newsId}`}
      onClick={() => handleClick(String(news.newsId), 'news')}
      className="block bg-white rounded-2xl p-6 shadow-soft border border-slate-100 hover:shadow-soft-lg hover:-translate-y-1 transition-all duration-300"
    >
      <div className="flex items-start justify-between gap-4 mb-2">
        <h3 className="font-semibold text-slate-900 line-clamp-2">{news.title}</h3>
        {news.category && (
          <span className="px-2 py-1 bg-secondary-50 text-secondary-600 text-xs font-medium rounded-full flex-shrink-0">
            {news.category}
          </span>
        )}
      </div>
      {news.summary && (
        <p className="text-sm text-slate-600 mb-4 line-clamp-2">{news.summary}</p>
      )}
      <div className="flex items-center justify-between text-sm text-slate-500">
        <span className="flex items-center gap-1">
          <Eye className="w-4 h-4" />
          {news.viewCount} 阅读
        </span>
        <span>{new Date(news.createdAt).toLocaleDateString()}</span>
      </div>
      <div className="mt-4 pt-4 border-t border-slate-100">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">推荐指数</span>
          <span className="text-xs font-medium text-primary-600">
            {Math.round(news.matchScore * 100)}%
          </span>
        </div>
      </div>
    </Link>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="xl" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
          <RefreshCw className="w-8 h-8 text-red-500" />
        </div>
        <h2 className="text-xl font-semibold text-slate-900 mb-2">加载失败</h2>
        <p className="text-slate-600 mb-4">{error?.message || '请稍后重试'}</p>
        <Button variant="primary" onClick={() => refetch()}>
          重新加载
        </Button>
      </div>
    );
  }

  const lawyers = recommendations?.lawyers ?? [];
  const posts = recommendations?.posts ?? [];
  const news = recommendations?.news ?? [];

  const tabs = [
    { key: 'all' as const, label: '全部推荐', count: lawyers.length + posts.length + news.length },
    { key: 'lawyers' as const, label: '推荐律师', count: lawyers.length, icon: User },
    { key: 'posts' as const, label: '推荐帖子', count: posts.length, icon: FileText },
    { key: 'news' as const, label: '推荐新闻', count: news.length, icon: Scale },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* 页面头部 */}
      <div className="bg-gradient-hero text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">个性化推荐</h1>
              <p className="text-white/80">基于您的兴趣为您精选内容</p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="white"
                size="sm"
                onClick={() => refetch()}
                leftIcon={<RefreshCw className="w-4 h-4" />}
              >
                刷新
              </Button>
              <Link to="/recommendation/onboarding">
                <Button
                  variant="white"
                  size="sm"
                  leftIcon={<Settings className="w-4 h-4" />}
                >
                  设置兴趣
                </Button>
              </Link>
            </div>
          </div>

          {/* 兴趣标签 */}
          {weights && Object.keys(weights).length > 0 && (
            <div className="mt-6 flex flex-wrap gap-2">
              {Object.entries(weights)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 5)
                .map(([tag, weight]) => (
                  <span
                    key={tag}
                    className="px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full text-sm"
                  >
                    {tag}
                    <span className="ml-1 opacity-70">{Math.round(weight * 100)}%</span>
                  </span>
                ))}
            </div>
          )}
        </div>
      </div>

      {/* 标签页切换 */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-1 overflow-x-auto py-2">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                  activeTab === tab.key
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                {tab.icon && <tab.icon className="w-4 h-4" />}
                {tab.label}
                <span className={`px-2 py-0.5 rounded-full text-xs ${
                  activeTab === tab.key
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-slate-100 text-slate-600'
                }`}>
                  {tab.count}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 律师推荐 */}
        {(activeTab === 'all' || activeTab === 'lawyers') && lawyers.length > 0 && (
          <ScrollReveal>
            <section className="mb-10">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-primary-50 rounded-lg flex items-center justify-center">
                    <User className="w-4 h-4 text-primary-600" />
                  </div>
                  <h2 className="text-xl font-semibold text-slate-900">推荐律师</h2>
                </div>
                <Link
                  to="/lawyer"
                  className="flex items-center text-sm text-primary-600 hover:text-primary-700"
                >
                  查看全部
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {(activeTab === 'all' ? lawyers.slice(0, 3) : lawyers).map(renderLawyerCard)}
              </div>
            </section>
          </ScrollReveal>
        )}

        {/* 帖子推荐 */}
        {(activeTab === 'all' || activeTab === 'posts') && posts.length > 0 && (
          <ScrollReveal delay={0.1}>
            <section className="mb-10">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-secondary-50 rounded-lg flex items-center justify-center">
                    <FileText className="w-4 h-4 text-secondary-600" />
                  </div>
                  <h2 className="text-xl font-semibold text-slate-900">推荐帖子</h2>
                </div>
                <Link
                  to="/forum"
                  className="flex items-center text-sm text-primary-600 hover:text-primary-700"
                >
                  查看全部
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {(activeTab === 'all' ? posts.slice(0, 3) : posts).map(renderPostCard)}
              </div>
            </section>
          </ScrollReveal>
        )}

        {/* 新闻推荐 */}
        {(activeTab === 'all' || activeTab === 'news') && news.length > 0 && (
          <ScrollReveal delay={0.2}>
            <section className="mb-10">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-gold-50 rounded-lg flex items-center justify-center">
                    <Scale className="w-4 h-4 text-gold-600" />
                  </div>
                  <h2 className="text-xl font-semibold text-slate-900">推荐新闻</h2>
                </div>
                <Link
                  to="/news"
                  className="flex items-center text-sm text-primary-600 hover:text-primary-700"
                >
                  查看全部
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {(activeTab === 'all' ? news.slice(0, 3) : news).map(renderNewsCard)}
              </div>
            </section>
          </ScrollReveal>
        )}

        {/* 空状态 */}
        {lawyers.length === 0 && posts.length === 0 && news.length === 0 && (
          <div className="text-center py-16">
            <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <TrendingUp className="w-10 h-10 text-slate-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">暂无推荐内容</h3>
            <p className="text-slate-600 mb-6">完善您的兴趣标签，获取更精准的推荐</p>
            <Link to="/recommendation/onboarding">
              <Button variant="primary">设置兴趣标签</Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

export default RecommendationPage;