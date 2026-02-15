/**
 * Recommendations 组件 - 推荐内容
 * 美化后的推荐内容展示组件
 */

import { Link } from 'react-router-dom';
import { Star, ChevronRight, Eye } from 'lucide-react';

import type { Recommendation } from '../types';

interface RecommendationsProps {
  recommendations: Recommendation[];
  isLoading?: boolean;
  title?: string;
}

// 类型标签样式映射
const typeLabelMap: Record<string, { label: string; className: string; icon: React.ReactNode }> = {
  lawyer: { 
    label: '律师', 
    className: 'bg-blue-50 text-blue-700 border-blue-100',
    icon: <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
  },
  article: { 
    label: '文章', 
    className: 'bg-green-50 text-green-700 border-green-100',
    icon: <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
  },
  consultation: { 
    label: '咨询', 
    className: 'bg-purple-50 text-purple-700 border-purple-100',
    icon: <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
  },
  knowledge: { 
    label: '知识', 
    className: 'bg-orange-50 text-orange-700 border-orange-100',
    icon: <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
  },
};

// 默认推荐内容
const defaultRecommendations: Recommendation[] = [
  {
    id: '1',
    title: '劳动合同到期不续签，员工能获得哪些补偿？',
    description: '详细解读劳动合同到期不续签的法律规定，包括经济补偿金的计算方式、特殊情况处理等',
    type: 'article',
    link: '/knowledge/1',
    tags: ['劳动法', '劳动合同', '经济补偿'],
    viewCount: 12580,
  },
  {
    id: '2',
    title: '张律师 - 劳动纠纷专家',
    description: '15年从业经验，成功处理劳动纠纷案件2000+，专业高效',
    type: 'lawyer',
    link: '/lawyer/1',
    rating: 4.9,
    tags: ['劳动法', '合同纠纷'],
  },
  {
    id: '3',
    title: '离婚财产分割的常见误区',
    description: '解析离婚财产分割中的常见误区，帮助您维护自身合法权益',
    type: 'knowledge',
    link: '/knowledge/2',
    tags: ['婚姻法', '财产分割'],
    viewCount: 8960,
  },
  {
    id: '4',
    title: '交通事故责任认定与赔偿指南',
    description: '全面解读交通事故责任认定标准及赔偿计算方法',
    type: 'article',
    link: '/knowledge/3',
    tags: ['交通事故', '责任认定', '赔偿计算'],
    viewCount: 15230,
  },
];

export function Recommendations({
  recommendations,
  isLoading = false,
  title = '为您推荐',
}: RecommendationsProps): JSX.Element {
  const displayRecommendations = recommendations.length > 0 ? recommendations : defaultRecommendations;

  if (isLoading) {
    return (
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="h-8 bg-slate-200 rounded-xl w-32 mb-8" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="bg-slate-50 rounded-2xl p-6 animate-pulse">
                <div className="h-5 bg-slate-200 rounded-lg w-16 mb-4" />
                <div className="h-6 bg-slate-200 rounded-lg w-full mb-3" />
                <div className="h-4 bg-slate-200 rounded w-3/4" />
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="py-16 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <span className="inline-block px-3 py-1 bg-primary-100 text-primary-700 text-sm font-medium rounded-full mb-3">
              精选内容
            </span>
            <h2 className="text-2xl md:text-3xl font-bold text-slate-900">{title}</h2>
          </div>
          <Link
            to="/recommendations"
            className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center gap-1 group"
          >
            查看更多
            <ChevronRight className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {displayRecommendations.map((item) => {
            const typeInfo = typeLabelMap[item.type] ?? { 
              label: '推荐', 
              className: 'bg-slate-50 text-slate-700 border-slate-100',
              icon: null
            };

            return (
              <Link
                key={item.id}
                to={item.link}
                className="group bg-white rounded-2xl p-6 border border-slate-100 shadow-soft hover:shadow-soft-lg hover:-translate-y-1 transition-all duration-300"
              >
                {/* 类型标签 */}
                <div className="flex items-center justify-between mb-4">
                  <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-lg border ${typeInfo.className}`}>
                    {typeInfo.icon}
                    {typeInfo.label}
                  </span>
                  {item.rating && (
                    <div className="flex items-center text-amber-400">
                      <Star className="w-4 h-4 fill-current" />
                      <span className="text-sm text-slate-600 ml-1 font-medium">{item.rating.toFixed(1)}</span>
                    </div>
                  )}
                </div>

                {/* 标题 */}
                <h3 className="text-lg font-semibold text-slate-900 mb-2 group-hover:text-primary-600 transition-colors line-clamp-2 leading-snug">
                  {item.title}
                </h3>

                {/* 描述 */}
                {item.description && (
                  <p className="text-sm text-slate-600 mb-4 line-clamp-2 leading-relaxed">{item.description}</p>
                )}

                {/* 标签 */}
                {item.tags && item.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {item.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded-lg"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                {/* 底部信息 */}
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100">
                  {item.viewCount !== undefined && (
                    <div className="flex items-center gap-1 text-xs text-slate-400">
                      <Eye className="w-3.5 h-3.5" />
                      {item.viewCount.toLocaleString()} 次浏览
                    </div>
                  )}
                  {item.authorName && (
                    <div className="flex items-center">
                      {item.authorAvatar ? (
                        <img
                          src={item.authorAvatar}
                          alt={item.authorName}
                          className="w-6 h-6 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center">
                          <span className="text-xs font-medium text-white">
                            {item.authorName.charAt(0)}
                          </span>
                        </div>
                      )}
                      <span className="text-xs text-slate-500 ml-2">{item.authorName}</span>
                    </div>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </section>
  );
}
