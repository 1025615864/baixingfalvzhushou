/**
 * ContentRecommendation - 内容推荐组件
 */

import { useState } from 'react';

import type { RecommendationCategory, EnhancedContentRecommendation } from '../types';
import { useContentRecommendations, useFeedbackRecommendation } from '../hooks/useForumAssistant';

interface ContentRecommendationProps {
  className?: string;
  defaultCategory?: RecommendationCategory;
  limit?: number;
  onItemClick?: (item: EnhancedContentRecommendation) => void;
}

const categoryLabels: Record<RecommendationCategory, string> = {
  trending: '热门推荐',
  related: '相关推荐',
  expert: '专家推荐',
  new: '最新内容',
  recommended: '为您推荐',
};

const categoryIcons: Record<RecommendationCategory, JSX.Element> = {
  trending: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  related: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
    </svg>
  ),
  expert: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  ),
  new: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  recommended: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

/**
 * 内容推荐组件
 */
export function ContentRecommendation({
  className = '',
  defaultCategory = 'recommended',
  limit = 5,
  onItemClick,
}: ContentRecommendationProps): JSX.Element {
  const [activeCategory, setActiveCategory] = useState<RecommendationCategory>(defaultCategory);
  const [feedbackItems, setFeedbackItems] = useState<Set<string>>(new Set());

  const { data: recommendations, isLoading, error } = useContentRecommendations(activeCategory, limit);
  const feedbackMutation = useFeedbackRecommendation();

  const categories: RecommendationCategory[] = ['recommended', 'trending', 'related', 'expert', 'new'];

  /**
   * 提交反馈
   */
  const handleFeedback = async (recommendationId: string, feedback: 'useful' | 'not_useful'): Promise<void> => {
    if (feedbackItems.has(recommendationId)) return;

    try {
      await feedbackMutation.mutateAsync({
        recommendationId,
        feedback,
      });
      setFeedbackItems(new Set([...feedbackItems, recommendationId]));
    } catch {
      // 错误已在 hook 中处理
    }
  };

  /**
   * 获取类型标签
   */
  const getTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      post: '帖子',
      article: '文章',
      question: '问答',
      expert: '专家',
    };
    return labels[type] || type;
  };

  /**
   * 获取类型颜色
   */
  const getTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      post: 'bg-blue-100 text-blue-700',
      article: 'bg-green-100 text-green-700',
      question: 'bg-yellow-100 text-yellow-700',
      expert: 'bg-purple-100 text-purple-700',
    };
    return colors[type] || 'bg-gray-100 text-gray-700';
  };

  /**
   * 获取推荐原因图标
   */
  const getReasonIcon = (type: string): JSX.Element => {
    const icons: Record<string, JSX.Element> = {
      similar_content: (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      trending: (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      ),
      expert_recommendation: (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      ),
      user_interest: (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
      ),
      related_topic: (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
        </svg>
      ),
    };
    return icons[type] || null;
  };

  return (
    <div className={`bg-white rounded-xl shadow-sm p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          内容推荐
        </h3>
      </div>

      {/* 分类标签 */}
      <div className="flex flex-wrap gap-2 mb-4">
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => setActiveCategory(category)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-full transition-colors ${
              activeCategory === category
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {categoryIcons[category]}
            {categoryLabels[category]}
          </button>
        ))}
      </div>

      {/* 内容列表 */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((index) => (
            <div key={index} className="animate-pulse p-4 rounded-lg bg-gray-50">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
              <div className="h-3 bg-gray-200 rounded w-full mb-2" />
              <div className="h-3 bg-gray-200 rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-8 text-red-500">
          <svg className="w-12 h-12 mx-auto mb-3 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-sm">获取推荐内容失败</p>
          <p className="text-xs text-gray-400 mt-1">请稍后重试</p>
        </div>
      ) : !recommendations || recommendations.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <p className="text-sm">暂无推荐内容</p>
          <p className="text-xs text-gray-400 mt-1">切换分类查看其他内容</p>
        </div>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <div
              key={rec.item.id}
              className="group p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-sm transition-all cursor-pointer"
              onClick={() => onItemClick?.(rec)}
            >
              <div className="flex items-start gap-3">
                {/* 缩略图 */}
                {rec.item.thumbnailUrl && (
                  <div className="flex-shrink-0 w-20 h-20 rounded-lg bg-gray-100 overflow-hidden">
                    <img
                      src={rec.item.thumbnailUrl}
                      alt={rec.item.title}
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}

                <div className="flex-1 min-w-0">
                  {/* 类型标签和标题 */}
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${getTypeColor(rec.item.type)}`}>
                      {getTypeLabel(rec.item.type)}
                    </span>
                    {rec.reason && (
                      <span className="flex items-center gap-1 text-xs text-gray-400">
                        {getReasonIcon(rec.reason.type)}
                        {rec.reason.description}
                      </span>
                    )}
                  </div>

                  <h4 className="text-sm font-medium text-gray-900 line-clamp-2 group-hover:text-blue-600 transition-colors">
                    {rec.item.title}
                  </h4>

                  <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                    {rec.item.summary}
                  </p>

                  {/* 作者和统计信息 */}
                  <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center gap-2">
                      {rec.item.author && (
                        <>
                          {rec.item.author.avatar ? (
                            <img
                              src={rec.item.author.avatar}
                              alt={rec.item.author.name}
                              className="w-5 h-5 rounded-full"
                            />
                          ) : (
                            <div className="w-5 h-5 rounded-full bg-gray-200 flex items-center justify-center text-xs text-gray-500">
                              {rec.item.author.name.charAt(0)}
                            </div>
                          )}
                          <span className="text-xs text-gray-600">{rec.item.author.name}</span>
                          {rec.item.author.title && (
                            <span className="text-xs text-gray-400">· {rec.item.author.title}</span>
                          )}
                        </>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-xs text-gray-400">
                      <span className="flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        {rec.item.viewCount}
                      </span>
                      <span className="flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                        </svg>
                        {rec.item.likeCount}
                      </span>
                    </div>
                  </div>

                  {/* 标签 */}
                  {rec.item.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {rec.item.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="text-xs text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* 反馈按钮 */}
              <div className="flex items-center justify-end gap-2 mt-3 pt-3 border-t border-gray-100">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    void handleFeedback(rec.item.id, 'useful');
                  }}
                  disabled={feedbackItems.has(rec.item.id)}
                  className={`text-xs flex items-center gap-1 px-2 py-1 rounded transition-colors ${
                    feedbackItems.has(rec.item.id)
                      ? 'text-green-600 bg-green-50'
                      : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                  </svg>
                  {feedbackItems.has(rec.item.id) ? '已反馈' : '有用'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}