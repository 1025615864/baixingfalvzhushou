/**
 * 搜索结果列表组件
 */

import React from 'react';

import type {
  SearchResults as SearchResultsType,
  SearchType,
  NewsSearchItem,
  PostSearchItem,
  LawyerSearchItem,
  LawFirmSearchItem,
  KnowledgeSearchItem,
} from '../types';

export interface SearchResultsProps {
  /** 搜索结果 */
  results: SearchResultsType;
  /** 当前筛选类型 */
  filterType: SearchType;
  /** 点击结果项的回调 */
  onItemClick?: (type: string, id: number) => void;
  /** 是否显示分类标题 */
  showCategoryTitle?: boolean;
}

/** 新闻结果项 */
const NewsItem: React.FC<{
  item: NewsSearchItem;
  onClick?: () => void;
}> = ({ item, onClick }) => (
  <div
    onClick={onClick}
    className="p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md 
               hover:border-blue-300 transition-all duration-200 cursor-pointer"
  >
    <div className="flex items-start gap-3">
      <span className="px-2 py-0.5 text-xs font-medium text-blue-600 bg-blue-50 rounded">
        资讯
      </span>
      <div className="flex-1">
        <h3 className="text-base font-medium text-gray-900 mb-1">{item.title}</h3>
        {item.snippet && (
          <p className="text-sm text-gray-600 line-clamp-2">{item.snippet}</p>
        )}
      </div>
    </div>
  </div>
);

/** 帖子结果项 */
const PostItem: React.FC<{
  item: PostSearchItem;
  onClick?: () => void;
}> = ({ item, onClick }) => (
  <div
    onClick={onClick}
    className="p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md 
               hover:border-blue-300 transition-all duration-200 cursor-pointer"
  >
    <div className="flex items-start gap-3">
      <span className="px-2 py-0.5 text-xs font-medium text-green-600 bg-green-50 rounded">
        帖子
      </span>
      <div className="flex-1">
        <h3 className="text-base font-medium text-gray-900 mb-1">{item.title}</h3>
        <p className="text-sm text-gray-600 line-clamp-2">{item.content}</p>
      </div>
    </div>
  </div>
);

/** 律师结果项 */
const LawyerItem: React.FC<{
  item: LawyerSearchItem;
  onClick?: () => void;
}> = ({ item, onClick }) => (
  <div
    onClick={onClick}
    className="p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md 
               hover:border-blue-300 transition-all duration-200 cursor-pointer"
  >
    <div className="flex items-center gap-4">
      <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
        <span className="text-lg font-medium text-blue-600">
          {item.name.charAt(0)}
        </span>
      </div>
      <div className="flex-1">
        <h3 className="text-base font-medium text-gray-900">{item.name}</h3>
        {item.specialties && (
          <p className="text-sm text-gray-600">{item.specialties}</p>
        )}
      </div>
      <span className="px-2 py-0.5 text-xs font-medium text-purple-600 bg-purple-50 rounded">
        律师
      </span>
    </div>
  </div>
);

/** 律所结果项 */
const LawFirmItem: React.FC<{
  item: LawFirmSearchItem;
  onClick?: () => void;
}> = ({ item, onClick }) => (
  <div
    onClick={onClick}
    className="p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md 
               hover:border-blue-300 transition-all duration-200 cursor-pointer"
  >
    <div className="flex items-start gap-3">
      <span className="px-2 py-0.5 text-xs font-medium text-orange-600 bg-orange-50 rounded">
        律所
      </span>
      <div className="flex-1">
        <h3 className="text-base font-medium text-gray-900">{item.name}</h3>
        {item.address && (
          <p className="text-sm text-gray-600 mt-1">{item.address}</p>
        )}
      </div>
    </div>
  </div>
);

/** 知识结果项 */
const KnowledgeItem: React.FC<{
  item: KnowledgeSearchItem;
  onClick?: () => void;
}> = ({ item, onClick }) => (
  <div
    onClick={onClick}
    className="p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md 
               hover:border-blue-300 transition-all duration-200 cursor-pointer"
  >
    <div className="flex items-start gap-3">
      <span className="px-2 py-0.5 text-xs font-medium text-teal-600 bg-teal-50 rounded">
        知识
      </span>
      <div className="flex-1">
        <h3 className="text-base font-medium text-gray-900">{item.title}</h3>
        {item.category && (
          <p className="text-sm text-gray-500 mt-1">分类：{item.category}</p>
        )}
      </div>
    </div>
  </div>
);

/**
 * 搜索结果组件
 */
export const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  filterType,
  onItemClick,
  showCategoryTitle = true,
}) => {
  const hasResults =
    results.news.length > 0 ||
    results.posts.length > 0 ||
    results.lawyers.length > 0 ||
    results.lawfirms.length > 0 ||
    results.knowledge.length > 0;

  if (!hasResults) {
    return null;
  }

  const handleItemClick = (type: string, id: number) => {
    onItemClick?.(type, id);
  };

  // 根据筛选类型渲染对应结果
  const renderResults = () => {
    switch (filterType) {
      case 'news':
        return results.news.length > 0 ? (
          <div className="space-y-3">
            {showCategoryTitle && (
              <h2 className="text-lg font-semibold text-gray-900 px-4">
                资讯 ({results.news.length})
              </h2>
            )}
            {results.news.map((item) => (
              <NewsItem
                key={`news-${item.id}`}
                item={item}
                onClick={() => handleItemClick('news', item.id)}
              />
            ))}
          </div>
        ) : null;

      case 'post':
        return results.posts.length > 0 ? (
          <div className="space-y-3">
            {showCategoryTitle && (
              <h2 className="text-lg font-semibold text-gray-900 px-4">
                帖子 ({results.posts.length})
              </h2>
            )}
            {results.posts.map((item) => (
              <PostItem
                key={`post-${item.id}`}
                item={item}
                onClick={() => handleItemClick('post', item.id)}
              />
            ))}
          </div>
        ) : null;

      case 'lawyer':
        return results.lawyers.length > 0 ? (
          <div className="space-y-3">
            {showCategoryTitle && (
              <h2 className="text-lg font-semibold text-gray-900 px-4">
                律师 ({results.lawyers.length})
              </h2>
            )}
            {results.lawyers.map((item) => (
              <LawyerItem
                key={`lawyer-${item.id}`}
                item={item}
                onClick={() => handleItemClick('lawyer', item.id)}
              />
            ))}
          </div>
        ) : null;

      case 'lawfirm':
        return results.lawfirms.length > 0 ? (
          <div className="space-y-3">
            {showCategoryTitle && (
              <h2 className="text-lg font-semibold text-gray-900 px-4">
                律所 ({results.lawfirms.length})
              </h2>
            )}
            {results.lawfirms.map((item) => (
              <LawFirmItem
                key={`lawfirm-${item.id}`}
                item={item}
                onClick={() => handleItemClick('lawfirm', item.id)}
              />
            ))}
          </div>
        ) : null;

      case 'knowledge':
        return results.knowledge.length > 0 ? (
          <div className="space-y-3">
            {showCategoryTitle && (
              <h2 className="text-lg font-semibold text-gray-900 px-4">
                法律知识 ({results.knowledge.length})
              </h2>
            )}
            {results.knowledge.map((item) => (
              <KnowledgeItem
                key={`knowledge-${item.id}`}
                item={item}
                onClick={() => handleItemClick('knowledge', item.id)}
              />
            ))}
          </div>
        ) : null;

      case 'all':
      default:
        return (
          <div className="space-y-6">
            {results.news.length > 0 && (
              <div className="space-y-3">
                {showCategoryTitle && (
                  <h2 className="text-lg font-semibold text-gray-900 px-4">
                    资讯 ({results.news.length})
                  </h2>
                )}
                {results.news.map((item) => (
                  <NewsItem
                    key={`news-${item.id}`}
                    item={item}
                    onClick={() => handleItemClick('news', item.id)}
                  />
                ))}
              </div>
            )}

            {results.posts.length > 0 && (
              <div className="space-y-3">
                {showCategoryTitle && (
                  <h2 className="text-lg font-semibold text-gray-900 px-4">
                    帖子 ({results.posts.length})
                  </h2>
                )}
                {results.posts.map((item) => (
                  <PostItem
                    key={`post-${item.id}`}
                    item={item}
                    onClick={() => handleItemClick('post', item.id)}
                  />
                ))}
              </div>
            )}

            {results.lawyers.length > 0 && (
              <div className="space-y-3">
                {showCategoryTitle && (
                  <h2 className="text-lg font-semibold text-gray-900 px-4">
                    律师 ({results.lawyers.length})
                  </h2>
                )}
                {results.lawyers.map((item) => (
                  <LawyerItem
                    key={`lawyer-${item.id}`}
                    item={item}
                    onClick={() => handleItemClick('lawyer', item.id)}
                  />
                ))}
              </div>
            )}

            {results.lawfirms.length > 0 && (
              <div className="space-y-3">
                {showCategoryTitle && (
                  <h2 className="text-lg font-semibold text-gray-900 px-4">
                    律所 ({results.lawfirms.length})
                  </h2>
                )}
                {results.lawfirms.map((item) => (
                  <LawFirmItem
                    key={`lawfirm-${item.id}`}
                    item={item}
                    onClick={() => handleItemClick('lawfirm', item.id)}
                  />
                ))}
              </div>
            )}

            {results.knowledge.length > 0 && (
              <div className="space-y-3">
                {showCategoryTitle && (
                  <h2 className="text-lg font-semibold text-gray-900 px-4">
                    法律知识 ({results.knowledge.length})
                  </h2>
                )}
                {results.knowledge.map((item) => (
                  <KnowledgeItem
                    key={`knowledge-${item.id}`}
                    item={item}
                    onClick={() => handleItemClick('knowledge', item.id)}
                  />
                ))}
              </div>
            )}
          </div>
        );
    }
  };

  return <div className="py-4">{renderResults()}</div>;
};

export default SearchResults;