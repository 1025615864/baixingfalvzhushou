/**
 * KnowledgeStats 组件 - 知识库统计面板
 */

import type { KnowledgeStats, KnowledgeType } from '../types';
import { KnowledgeTypeLabels } from '../types';

interface KnowledgeStatsProps {
  stats: KnowledgeStats | undefined;
  isLoading?: boolean;
}

interface StatCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
}

function StatCard({ title, value, icon, color, subtitle }: StatCardProps): JSX.Element {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${color}`}>
          {icon}
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
        </div>
      </div>
    </div>
  );
}

interface TypeDistributionProps {
  byType: Record<KnowledgeType, number>;
}

function TypeDistribution({ byType }: TypeDistributionProps): JSX.Element {
  const total = Object.values(byType).reduce((sum, count) => sum + count, 0);

  const colors: Record<KnowledgeType, string> = {
    law: 'bg-blue-500',
    case: 'bg-green-500',
    regulation: 'bg-purple-500',
    interpretation: 'bg-orange-500',
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">知识类型分布</h3>
      
      <div className="space-y-4">
        {(Object.keys(KnowledgeTypeLabels) as KnowledgeType[]).map((type) => {
          const count = byType[type] || 0;
          const percentage = total > 0 ? Math.round((count / total) * 100) : 0;

          return (
            <div key={type}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">
                  {KnowledgeTypeLabels[type]}
                </span>
                <span className="text-sm text-gray-500">
                  {count} 篇 ({percentage}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`${colors[type]} h-2 rounded-full transition-all duration-500`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface CategoryDistributionProps {
  byCategory: Record<string, number>;
}

function CategoryDistribution({ byCategory }: CategoryDistributionProps): JSX.Element {
  const sortedCategories = Object.entries(byCategory)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10); // 只显示前10个

  if (sortedCategories.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">分类分布</h3>
        <p className="text-gray-500 text-center py-8">暂无分类数据</p>
      </div>
    );
  }

  const maxCount = Math.max(...sortedCategories.map(([, count]) => count));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        分类分布
        <span className="text-sm font-normal text-gray-500 ml-2">
          (Top {sortedCategories.length})
        </span>
      </h3>
      
      <div className="space-y-3">
        {sortedCategories.map(([category, count]) => {
          const percentage = maxCount > 0 ? Math.round((count / maxCount) * 100) : 0;

          return (
            <div key={category} className="flex items-center">
              <span className="w-24 text-sm text-gray-600 truncate" title={category}>
                {category}
              </span>
              <div className="flex-1 mx-3">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
              <span className="w-12 text-sm text-gray-500 text-right">
                {count}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function KnowledgeStatsComponent({
  stats,
  isLoading = false,
}: KnowledgeStatsProps): JSX.Element {
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
              <div className="flex items-center">
                <div className="h-12 w-12 bg-gray-200 rounded-lg"></div>
                <div className="ml-4 space-y-2">
                  <div className="h-4 w-20 bg-gray-200 rounded"></div>
                  <div className="h-6 w-12 bg-gray-200 rounded"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <p className="text-gray-500">暂无统计数据</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="总文章数"
          value={stats.totalArticles}
          icon={
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
          color="bg-blue-100"
          subtitle="知识库文章总数"
        />
        
        <StatCard
          title="分类数"
          value={stats.totalCategories}
          icon={
            <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
          }
          color="bg-purple-100"
          subtitle="知识分类数量"
        />
        
        <StatCard
          title="已向量化"
          value={stats.vectorizedCount}
          icon={
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          }
          color="bg-green-100"
          subtitle={`占比 ${stats.totalArticles > 0 ? Math.round((stats.vectorizedCount / stats.totalArticles) * 100) : 0}%`}
        />
        
        <StatCard
          title="近期新增"
          value={stats.recentAdditions}
          icon={
            <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          }
          color="bg-orange-100"
          subtitle="最近7天新增"
        />
      </div>

      {/* 分布图表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TypeDistribution byType={stats.byType} />
        <CategoryDistribution byCategory={stats.byCategory} />
      </div>

      {/* 提示信息 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-blue-500 mt-0.5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="text-sm text-blue-700">
            <p className="font-medium mb-1">知识库管理提示</p>
            <ul className="list-disc list-inside space-y-1 text-blue-600">
              <li>向量化后的文章可以被 AI 助手引用和检索</li>
              <li>定期整理分类有助于提高知识检索效率</li>
              <li>建议为每篇文章添加关键词以便更好地被搜索到</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}