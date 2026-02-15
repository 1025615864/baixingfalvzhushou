/**
 * 知识详情组件
 * 显示法律知识的完整内容
 */

import { useKnowledgeDetail } from '../../hooks/useKnowledge';
import { KnowledgeViewer } from '../KnowledgeViewer';

interface KnowledgeDetailProps {
  articleId: string;
  onClose?: () => void;
}

/**
 * 知识类型标签映射
 */
const knowledgeTypeLabels: Record<string, string> = {
  law: '法律条文',
  case: '案例',
  regulation: '法规',
  interpretation: '司法解释',
};

/**
 * 知识详情组件
 */
export function KnowledgeDetail({ articleId, onClose }: KnowledgeDetailProps): JSX.Element {
  const { data: article, isLoading, isError, error } = useKnowledgeDetail(articleId);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-24" />
          <div className="h-8 bg-gray-200 rounded w-3/4" />
          <div className="h-4 bg-gray-200 rounded w-1/2" />
          <div className="h-32 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center py-8">
          <h3 className="text-lg font-medium text-gray-900 mb-2">加载失败</h3>
          <p className="text-gray-500 mb-4">
            {error?.message || '无法加载知识详情，请稍后重试'}
          </p>
          {onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              返回列表
            </button>
          )}
        </div>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center py-8">
          <p className="text-gray-500">知识条目不存在</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* 头部信息 */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-2 mb-3">
          <span className="px-2 py-1 bg-primary-50 text-primary-700 text-xs font-medium rounded">
            {knowledgeTypeLabels[article.knowledgeType] || article.knowledgeType}
          </span>
          <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
            {article.category}
          </span>
          {article.articleNumber && (
            <span className="px-2 py-1 bg-amber-50 text-amber-700 text-xs rounded">
              {article.articleNumber}
            </span>
          )}
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {article.title}
        </h1>

        {article.summary && (
          <p className="text-gray-600 text-sm italic mb-4">
            {article.summary}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
          {article.source && (
            <span>来源：{article.source}</span>
          )}
          {article.effectiveDate && (
            <span>生效日期：{article.effectiveDate}</span>
          )}
          <span>更新于：{new Date(article.updatedAt).toLocaleDateString('zh-CN')}</span>
          {article.isVectorized && (
            <span className="text-green-600 flex items-center gap-1">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              已索引
            </span>
          )}
        </div>
      </div>

      {/* 内容区域 */}
      <div className="p-6">
        <KnowledgeViewer content={article.content} />

        {article.keywords && (
          <div className="mt-6 pt-4 border-t border-gray-100">
            <h4 className="text-sm font-medium text-gray-700 mb-2">关键词</h4>
            <div className="flex flex-wrap gap-2">
              {article.keywords.split(',').map((keyword) => (
                <span
                  key={keyword.trim()}
                  className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                >
                  {keyword.trim()}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 底部操作 */}
      {onClose && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm"
          >
            返回列表
          </button>
        </div>
      )}
    </div>
  );
}