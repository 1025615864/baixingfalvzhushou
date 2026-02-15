/**
 * VerticalChannelPage（垂直频道页面）
 * 婚姻/劳动法律服务专属入口页面
 */

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { ChannelList } from '../components/ChannelList';
import { ChannelContent } from '../components/ChannelContent';
import { TopicList } from '../components/TopicList';
import {
  useVerticalChannels,
  useChannelNews,
  useChannelConsultationTypes,
  useChannelDocumentTypes,
  useChannelStats,
} from '../hooks/useVerticalChannel';
import type { VerticalChannelKey } from '../types';

/**
 * 频道详情页面
 */
function ChannelDetailPage({ channelKey }: { channelKey: VerticalChannelKey }): JSX.Element {
  const [currentPage] = useState(1);
  const navigate = useNavigate();

  // 获取频道数据
  const { data: newsData, isLoading: newsLoading } = useChannelNews(channelKey, currentPage, 20);
  const { data: consultationTypesData, isLoading: consultationLoading } = useChannelConsultationTypes(channelKey);
  const { data: documentTypesData, isLoading: documentLoading } = useChannelDocumentTypes(channelKey);
  const { data: statsData, isLoading: statsLoading } = useChannelStats(channelKey);

  // 频道标题映射
  const channelTitles: Record<VerticalChannelKey, { title: string; subtitle: string; color: string }> = {
    marriage: {
      title: '婚姻家庭',
      subtitle: '离婚纠纷、子女抚养、财产分割等婚姻家庭法律服务',
      color: 'from-pink-500 to-rose-600',
    },
    labor: {
      title: '劳动争议',
      subtitle: '劳动合同、工资福利、工伤赔偿等劳动法律服务',
      color: 'from-blue-500 to-indigo-600',
    },
  };

  const channelInfo = channelTitles[channelKey];

  const handleNewsClick = (newsId: number): void => {
    navigate(`/news/${newsId}`);
  };

  const handleConsultationClick = (typeKey: string): void => {
    navigate(`/consultation?type=${typeKey}&channel=${channelKey}`);
  };

  const handleDocumentClick = (typeKey: string): void => {
    navigate(`/document?template=${typeKey}&channel=${channelKey}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className={`bg-gradient-to-r ${channelInfo.color} text-white`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-center gap-2 mb-4">
            <button
              onClick={() => navigate('/vertical-channel')}
              className="text-white/80 hover:text-white flex items-center gap-1 text-sm transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              返回频道列表
            </button>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold mb-4">{channelInfo.title}</h1>
          <p className="text-lg text-white/90 max-w-2xl">{channelInfo.subtitle}</p>

          {/* 统计信息 */}
          {!statsLoading && statsData && (
            <div className="mt-6 flex flex-wrap gap-6">
              <div className="bg-white/20 backdrop-blur rounded-lg px-4 py-2">
                <span className="text-white/80 text-sm">相关资讯</span>
                <div className="text-2xl font-bold">{statsData.newsCount.toLocaleString()}+</div>
              </div>
              <div className="bg-white/20 backdrop-blur rounded-lg px-4 py-2">
                <span className="text-white/80 text-sm">咨询类型</span>
                <div className="text-2xl font-bold">{(consultationTypesData?.types.length || 0)}种</div>
              </div>
              <div className="bg-white/20 backdrop-blur rounded-lg px-4 py-2">
                <span className="text-white/80 text-sm">文书模板</span>
                <div className="text-2xl font-bold">{(documentTypesData?.types.length || 0)}种</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 左侧：新闻内容 */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                </svg>
                最新资讯
              </h2>
            </div>
            <ChannelContent
              news={newsData?.items || []}
              isLoading={newsLoading}
              onNewsClick={handleNewsClick}
            />
          </div>

          {/* 右侧：专题列表 */}
          <div>
            <TopicList
              consultationTypes={consultationTypesData?.types || []}
              documentTypes={documentTypesData?.types || []}
              isLoading={consultationLoading || documentLoading}
              onConsultationClick={handleConsultationClick}
              onDocumentClick={handleDocumentClick}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * 频道列表页面
 */
function ChannelListPage(): JSX.Element {
  const { data: channels, isLoading } = useVerticalChannels();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <h1 className="text-3xl md:text-4xl font-bold mb-4">垂直法律服务</h1>
          <p className="text-lg text-white/90 max-w-2xl">
            为婚姻家庭和劳动争议领域提供专业、精准的法律服务入口，让您快速找到所需的法律帮助
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">选择服务频道</h2>
          <p className="text-gray-500">根据您的需求选择对应的法律服务领域</p>
        </div>
        <ChannelList channels={channels || []} isLoading={isLoading} />
      </div>
    </div>
  );
}

/**
 * 垂直频道主页面
 */
export function VerticalChannelPage(): JSX.Element {
  const { channelKey } = useParams<{ channelKey?: string }>();

  // 如果有 channelKey，显示频道详情页；否则显示频道列表页
  if (channelKey) {
    // 验证 channelKey 是否有效
    const validKeys: VerticalChannelKey[] = ['marriage', 'labor'];
    if (!validKeys.includes(channelKey as VerticalChannelKey)) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <div className="text-6xl mb-4">😕</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">频道不存在</h1>
            <p className="text-gray-500 mb-6">您访问的垂直频道不存在或已下线</p>
            <a
              href="/vertical-channel"
              className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              返回频道列表
            </a>
          </div>
        </div>
      );
    }

    return <ChannelDetailPage channelKey={channelKey as VerticalChannelKey} />;
  }

  return <ChannelListPage />;
}