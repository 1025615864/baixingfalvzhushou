import { useState } from 'react';
import { Search, MapPin, Star, Briefcase, GraduationCap, MessageSquare, ChevronRight, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { useLawyers } from '@/features/lawyer/hooks/useLawyers';

type LawyerSpecialty = 'all' | 'labor' | 'contract' | 'marriage' | 'property' | 'criminal' | 'traffic' | 'intellectual' | 'inheritance' | 'corporate';

interface SpecialtyOption {
  value: LawyerSpecialty;
  label: string;
}

const specialties: SpecialtyOption[] = [
  { value: 'all', label: '全部专业' },
  { value: 'labor', label: '劳动法' },
  { value: 'contract', label: '合同法' },
  { value: 'marriage', label: '婚姻法' },
  { value: 'property', label: '房产法' },
  { value: 'criminal', label: '刑事辩护' },
  { value: 'traffic', label: '交通事故' },
  { value: 'intellectual', label: '知识产权' },
  { value: 'inheritance', label: '继承法' },
  { value: 'corporate', label: '公司法' },
];

const specialtyLabelMap: Record<string, string> = {
  labor: '劳动法',
  contract: '合同法',
  marriage: '婚姻法',
  property: '房产法',
  criminal: '刑事辩护',
  traffic: '交通事故',
  intellectual: '知识产权',
  inheritance: '继承法',
  corporate: '公司法',
};

export function LawyerPage(): JSX.Element {
  const [selectedSpecialty, setSelectedSpecialty] = useState<LawyerSpecialty>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('recommended');
  const [showFilters, setShowFilters] = useState(false);

  const { data, isLoading, error } = useLawyers({
    specialty: selectedSpecialty === 'all' ? undefined : selectedSpecialty,
    searchQuery: searchQuery || undefined,
  });

  const lawyers = data?.lawyers ?? [];

  const sortedLawyers = [...lawyers].sort((a, b) => {
    switch (sortBy) {
      case 'rating':
        return b.rating - a.rating;
      case 'experience':
        return (b.experienceYears ?? 0) - (a.experienceYears ?? 0);
      case 'price':
        return (a.consultationFee ?? 0) - (b.consultationFee ?? 0);
      default:
        return b.rating - a.rating;
    }
  });

  return (
    <div className="min-h-screen bg-slate-50 pt-16">
      <div className="bg-gradient-primary py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
              找律师
            </h1>
            <p className="text-lg text-white/70 max-w-2xl mx-auto">
              专业律师在线解答，为您提供权威法律意见，一对一贴心服务
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-2xl shadow-soft p-6 mb-6">
          <div className="relative mb-6">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="搜索律师姓名、律所、专业领域..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition-all"
            />
          </div>

          <div className="flex flex-wrap gap-2 mb-4">
            {specialties.map((spec) => (
              <button
                key={spec.value}
                onClick={() => setSelectedSpecialty(spec.value)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  selectedSpecialty === spec.value
                    ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/25'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {spec.label}
              </button>
            ))}
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 text-sm text-slate-600 hover:text-primary-600 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /></svg>
              高级筛选
              <ChevronRight className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-90' : ''}`} />
            </button>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500">排序：</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="text-sm border-0 bg-transparent text-slate-700 font-medium focus:ring-0 cursor-pointer"
              >
                <option value="recommended">综合推荐</option>
                <option value="rating">评分最高</option>
                <option value="experience">经验最丰富</option>
                <option value="price">价格最低</option>
              </select>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4 text-sm text-slate-600">
            <span>共找到 <span className="font-semibold text-slate-900">{sortedLawyers.length}</span> 位律师</span>
            {selectedSpecialty !== 'all' && (
              <span className="px-2 py-1 bg-primary-50 text-primary-700 rounded-lg text-xs">
                {specialties.find(s => s.value === selectedSpecialty)?.label}
              </span>
            )}
          </div>
        </div>

        {isLoading && (
          <div className="text-center py-16">
            <Loader2 className="w-10 h-10 text-primary-500 animate-spin mx-auto mb-4" />
            <p className="text-slate-500">正在加载律师列表...</p>
          </div>
        )}

        {error && !isLoading && (
          <div className="text-center py-16">
            <div className="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-10 h-10 text-red-400" />
            </div>
            <h3 className="text-lg font-medium text-slate-900 mb-2">加载失败</h3>
            <p className="text-slate-500 mb-4">{error.message || '请稍后重试'}</p>
            <Button variant="outline" onClick={() => window.location.reload()}>重新加载</Button>
          </div>
        )}

        {!isLoading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sortedLawyers.map((lawyer) => (
              <Card key={lawyer.id} variant="hover" className="group">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4 mb-4">
                    <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center text-white text-xl font-bold shadow-lg">
                      {(lawyer.name || '?').charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-lg font-semibold text-slate-900">{lawyer.name}</h3>
                        {lawyer.isVerified && (
                          <span className="px-2 py-0.5 bg-accent-100 text-accent-700 text-xs font-medium rounded-full">
                            已认证
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-slate-500">{lawyer.title || '执业律师'}</p>
                      <p className="text-sm text-slate-400 truncate">{lawyer.firmName || ''}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 mb-4 text-sm">
                    <div className="flex items-center gap-1">
                      <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                      <span className="font-semibold text-slate-900">{lawyer.rating?.toFixed(1) ?? '-'}</span>
                      <span className="text-slate-400">({lawyer.reviewCount ?? 0})</span>
                    </div>
                    <div className="flex items-center gap-1 text-slate-600">
                      <Briefcase className="w-4 h-4" />
                      <span>{lawyer.experienceYears ?? 0}年经验</span>
                    </div>
                    <div className="flex items-center gap-1 text-slate-600">
                      <GraduationCap className="w-4 h-4" />
                      <span>{lawyer.caseCount ?? 0}案例</span>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-4">
                    {String(lawyer.specialties ?? '').split(',').filter(Boolean).map((spec: string) => (
                      <span
                        key={spec}
                        className="px-2.5 py-1 bg-slate-100 text-slate-600 text-xs rounded-lg"
                      >
                        {specialtyLabelMap[spec] || spec}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                    <div className="flex items-center gap-1 text-sm text-slate-500">
                      <MapPin className="w-4 h-4" />
                      {lawyer.introduction ? lawyer.introduction.slice(0, 20) + '...' : ''}
                    </div>
                    <div className="text-lg font-bold text-primary-600">
                      {lawyer.consultationFee ? `¥${lawyer.consultationFee}/小时` : '面议'}
                    </div>
                  </div>

                  <div className="flex gap-3 mt-4">
                    <Button variant="outline" size="sm" fullWidth>
                      查看详情
                    </Button>
                    <Button variant="primary" size="sm" fullWidth leftIcon={<MessageSquare className="w-4 h-4" />}>
                      立即咨询
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {!isLoading && !error && sortedLawyers.length === 0 && (
          <div className="text-center py-16">
            <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-10 h-10 text-slate-400" />
            </div>
            <h3 className="text-lg font-medium text-slate-900 mb-2">未找到符合条件的律师</h3>
            <p className="text-slate-500">请尝试调整筛选条件或搜索关键词</p>
          </div>
        )}
      </div>
    </div>
  );
}
