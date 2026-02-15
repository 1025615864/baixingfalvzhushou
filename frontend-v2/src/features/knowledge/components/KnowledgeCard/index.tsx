/**
 * 知识卡片组件
 * 展示法律知识条目的概要信息
 */

import type { KnowledgeArticle } from '../../types';

interface KnowledgeCardProps {
  item: KnowledgeArticle;
  onClick?: (id: string) => void;
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
 * 知识卡片组件
 */
export function KnowledgeCard({ item, onClick }: KnowledgeCardProps): JSX.Element {
  const handleClick = (): void => {
    onClick?.(item.id);
  };

  return (
    <article
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 cursor-pointer hover:shadow-md transition-shadow"
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e): void => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleClick();
        }
      }}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          {/* 类型和分类标签 */}
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2 py-0.5 bg-primary-50 text-primary-700 text-xs font-medium rounded">
              {knowledgeTypeLabels[item.knowledgeType] || item.knowledgeType}
            </span>
            <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
              {item.category}
            </span>
            {item.articleNumber && (
              <span className="px-2 py-0.5 bg-amber-50 text-amber-700 text-xs rounded">
                {item.articleNumber}
              </span>
            )}
          </div>

          {/* 标题 */}
          <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2 hover:text-primary-600">
            {item.title}
          </h3>

          {/* 摘要 */}
          {item.summary && (
            <p className="text-sm text-gray-600 line-clamp-2 mb-3">
              {item.summary}
            </p>
          )}

          {/* 关键词 */}
          {item.keywords && (
            <div className="flex flex-wrap gap-2 mb-3">
              {item.keywords.split(',').slice(0, 5).map((keyword) => (
                <span
                  key={keyword.trim()}
                  className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                >
                  {keyword.trim()}
                </span>
              ))}
            </div>
          )}

          {/* 元信息 */}
          <div className="flex items-center gap-4 text-xs text-gray-400">
            {item.source && <span>来源：{item.source}</span>}
            {item.effectiveDate && <span>生效：{item.effectiveDate}</span>}
            <time dateTime={item.updatedAt}>
              更新于 {new Date(item.updatedAt).toLocaleDateString('zh-CN')}
            </time>
            {item.isVectorized && (
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
      </div>
    </article>
  );
}
