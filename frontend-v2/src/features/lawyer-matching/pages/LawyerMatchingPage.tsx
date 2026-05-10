/**
 * LawyerMatchingPage 页面 - 律师匹配页面
 */

import { useState, useCallback } from 'react';

import { useLawyerRecommendations, useLawyerSearch } from '../hooks/useLawyerMatching';
import { LawyerRecommendation } from '../components/LawyerRecommendation';
import { LawyerBookingModal } from '../components/LawyerBookingModal';
import { LawyerOnlineStatus } from '../components/LawyerOnlineStatus';
import type { LegalDomain, MatchingCriteria } from '../types';

const LEGAL_DOMAINS: { value: LegalDomain; label: string }[] = [
  { value: 'civil', label: '民事纠纷' },
  { value: 'criminal', label: '刑事辩护' },
  { value: 'commercial', label: '商事法律' },
  { value: 'labor', label: '劳动纠纷' },
  { value: 'family', label: '婚姻家事' },
  { value: 'property', label: '房产纠纷' },
  { value: 'intellectual', label: '知识产权' },
  { value: 'administrative', label: '行政诉讼' },
  { value: 'contract', label: '合同纠纷' },
  { value: 'tort', label: '侵权纠纷' },
];

export function LawyerMatchingPage(): JSX.Element {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedDomains, setSelectedDomains] = useState<LegalDomain[]>([]);
  const [activeTab, setActiveTab] = useState<'recommend' | 'search'>('recommend');
  const [bookingLawyerId, setBookingLawyerId] = useState<string | null>(null);
  const [bookingLawyerName, setBookingLawyerName] = useState<string>('');
  const [showBookingModal, setShowBookingModal] = useState<boolean>(false);

  const criteria: MatchingCriteria = {
    domains: selectedDomains,
  };

  const { data: recommendations, isLoading: isRecommendationsLoading } = useLawyerRecommendations(
    searchQuery,
    criteria,
    10
  );

  const { data: searchResults, isLoading: isSearchLoading } = useLawyerSearch({
    query: searchQuery,
    filters: {
      domains: criteria.domains,
      minRating: criteria.minRating,
      maxPrice: criteria.maxPrice,
    },
    limit: 20,
  });

  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    // 搜索由 React Query 自动处理
  }, []);

  const handleDomainToggle = useCallback((domain: LegalDomain) => {
    setSelectedDomains((prev) =>
      prev.includes(domain) ? prev.filter((d) => d !== domain) : [...prev, domain]
    );
  }, []);

  const handleSelectLawyer = useCallback((lawyerId: string) => {
    // 导航到律师详情页，暂时显示 alert
    alert(`查看律师详情: ${lawyerId}`);
  }, []);

  const handleBookLawyer = useCallback((lawyerId: string, lawyerName: string) => {
    setBookingLawyerId(lawyerId);
    setBookingLawyerName(lawyerName);
    setShowBookingModal(true);
  }, []);

  const handleCloseBookingModal = useCallback(() => {
    setShowBookingModal(false);
    setBookingLawyerId(null);
    setBookingLawyerName('');
  }, []);

  const handleBookingSuccess = useCallback(() => {
    alert('预约成功！');
  }, []);

  const isLoading = isRecommendationsLoading || isSearchLoading;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 页面头部 */}
      <div className="bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold text-gray-900">律师匹配</h1>
          <p className="mt-1 text-sm text-gray-500">
            根据您的需求智能推荐最合适的律师
          </p>
        </div>
      </div>

      {/* 搜索和筛选区域 */}
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* 搜索框 */}
        <form onSubmit={handleSearch} className="mb-6">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="描述您的法律问题，例如：劳动合同纠纷、房产继承..."
              className="w-full rounded-lg border border-gray-300 py-4 pl-12 pr-4 text-base shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <svg
              className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <button
              type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              搜索
            </button>
          </div>
        </form>

        {/* 法律领域筛选 */}
        <div className="mb-6">
          <h3 className="mb-3 text-sm font-medium text-gray-700">选择法律领域：</h3>
          <div className="flex flex-wrap gap-2">
            {LEGAL_DOMAINS.map((domain) => (
              <button
                key={domain.value}
                type="button"
                onClick={() => handleDomainToggle(domain.value)}
                className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                  selectedDomains.includes(domain.value)
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                }`}
              >
                {domain.label}
              </button>
            ))}
          </div>
          {selectedDomains.length > 0 && (
            <button
              type="button"
              onClick={() => setSelectedDomains([])}
              className="mt-3 text-sm text-blue-600 hover:text-blue-800"
            >
              清除筛选
            </button>
          )}
        </div>

        {/* 标签切换 */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex gap-8">
            <button
              type="button"
              onClick={() => setActiveTab('recommend')}
              className={`border-b-2 pb-4 text-sm font-medium transition-colors ${
                activeTab === 'recommend'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              }`}
            >
              智能推荐
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('search')}
              className={`border-b-2 pb-4 text-sm font-medium transition-colors ${
                activeTab === 'search'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              }`}
            >
              全部律师
            </button>
          </nav>
        </div>

        {/* 内容区域 */}
        <div className="relative">
          {/* 加载状态 */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
              <span className="ml-3 text-gray-600">正在匹配最适合的律师...</span>
            </div>
          )}

          {/* 智能推荐列表 */}
          {activeTab === 'recommend' && !isLoading && (
            <div>
              {recommendations && recommendations.length > 0 ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {recommendations.map((recommendation, index) => (
                    <div key={recommendation.lawyerId} className="relative">
                      <LawyerRecommendation
                        recommendation={recommendation}
                        onSelect={handleSelectLawyer}
                        onBook={(id) =>
                          handleBookLawyer(id, recommendation.lawyerName)
                        }
                        rank={index < 3 ? index + 1 : undefined}
                      />
                      <div className="absolute right-2 top-2">
                        <LawyerOnlineStatus
                          lawyerId={recommendation.lawyerId}
                          size="sm"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-lg bg-white py-12 text-center shadow-sm">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <h3 className="mt-4 text-lg font-medium text-gray-900">
                    暂无推荐结果
                  </h3>
                  <p className="mt-2 text-sm text-gray-500">
                    请尝试修改搜索词或选择其他法律领域
                  </p>
                </div>
              )}
            </div>
          )}

          {/* 全部律师列表 */}
          {activeTab === 'search' && !isLoading && searchResults && (
            <div>
              {searchResults.lawyers.length > 0 ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {searchResults.lawyers.map((lawyer) => (
                    <div
                      key={lawyer.id}
                      className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
                      role="button"
                      tabIndex={0}
                      onClick={() => handleSelectLawyer(lawyer.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          handleSelectLawyer(lawyer.id);
                        }
                      }}
                    >
                      <div className="mb-3 flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 text-lg font-bold text-blue-600">
                            {lawyer.name.charAt(0)}
                          </div>
                          <div>
                            <h3 className="font-semibold text-gray-900">{lawyer.name}</h3>
                            <p className="text-sm text-gray-500">
                              {lawyer.title || '执业律师'}
                            </p>
                          </div>
                        </div>
                        <LawyerOnlineStatus lawyerId={lawyer.id} size="md" />
                      </div>

                      <p className="mb-2 text-sm text-gray-600 line-clamp-2">
                        {lawyer.specialties.join('、')}
                      </p>

                      <div className="mb-3 flex items-center gap-4 text-sm">
                        <span className="text-yellow-500">★ {lawyer.rating.toFixed(1)}</span>
                        <span className="text-gray-500">{lawyer.completedCount} 单</span>
                        {lawyer.firmName && (
                          <span className="text-gray-500">{lawyer.firmName}</span>
                        )}
                      </div>

                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectLawyer(lawyer.id);
                          }}
                          className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                        >
                          查看详情
                        </button>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleBookLawyer(lawyer.id, lawyer.name);
                          }}
                          className="flex-1 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
                        >
                          立即预约
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-lg bg-white py-12 text-center shadow-sm">
                  <h3 className="text-lg font-medium text-gray-900">
                    未找到符合条件的律师
                  </h3>
                  <p className="mt-2 text-sm text-gray-500">
                    请尝试调整筛选条件或搜索词
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 预约弹窗 */}
      {bookingLawyerId && (
        <LawyerBookingModal
          lawyerId={bookingLawyerId}
          lawyerName={bookingLawyerName}
          isOpen={showBookingModal}
          onClose={handleCloseBookingModal}
          onSuccess={handleBookingSuccess}
        />
      )}
    </div>
  );
}