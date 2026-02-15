/**
 * ForumAssistantPage - 论坛助手页面
 */

import { useState } from 'react';

import { SmartReply } from '../components/SmartReply';
import { ContentRecommendation } from '../components/ContentRecommendation';
import { useAssistantConfig, useTrendingTopics, useRelatedExperts } from '../hooks/useForumAssistant';

type TabType = 'smart-reply' | 'recommendations' | 'trending' | 'experts';

interface TabItem {
  id: TabType;
  label: string;
  icon: JSX.Element;
  description: string;
}

const tabs: TabItem[] = [
  {
    id: 'smart-reply',
    label: '智能回复',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    description: 'AI 智能生成回复建议',
  },
  {
    id: 'recommendations',
    label: '内容推荐',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
    ),
    description: '个性化内容推荐',
  },
  {
    id: 'trending',
    label: '热门话题',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    ),
    description: '发现社区热门讨论',
  },
  {
    id: 'experts',
    label: '专家推荐',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    description: '推荐相关领域专家',
  },
];

// 示例帖子 ID，实际项目中应该从路由参数获取
const MOCK_POST_ID = 'demo-post-123';
const MOCK_POST_TITLE = '如何处理劳动合同纠纷？';

/**
 * 论坛助手页面
 */
export function ForumAssistantPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabType>('smart-reply');
  const [demoPostId, setDemoPostId] = useState<string>(MOCK_POST_ID);
  const [replySuccess, setReplySuccess] = useState<boolean>(false);

  const { data: config } = useAssistantConfig();
  const { data: trendingData } = useTrendingTopics();
  const { data: expertsData } = useRelatedExperts();

  /**
   * 处理回复采纳成功
   */
  const handleReplyAdopted = (): void => {
    setReplySuccess(true);
    setTimeout(() => setReplySuccess(false), 3000);
  };

  /**
   * 渲染标签页内容
   */
  const renderTabContent = (): JSX.Element => {
    switch (activeTab) {
      case 'smart-reply':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 左侧：演示输入 */}
            <div className="lg:col-span-1 space-y-4">
              <div className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">演示设置</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      帖子 ID
                    </label>
                    <input
                      type="text"
                      value={demoPostId}
                      onChange={(e) => setDemoPostId(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                      placeholder="输入帖子 ID"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      帖子标题
                    </label>
                    <input
                      type="text"
                      value={MOCK_POST_TITLE}
                      readOnly
                      className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600"
                    />
                  </div>
                  {replySuccess && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-sm text-green-600 flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        回复已采纳成功！
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* 助手配置 */}
              {config && (
                <div className="bg-white rounded-xl shadow-sm p-6">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">助手配置</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">自动建议</span>
                      <span className={config.autoSuggest ? 'text-green-600' : 'text-gray-400'}>
                        {config.autoSuggest ? '开启' : '关闭'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">建议数量</span>
                      <span className="text-gray-900">{config.suggestionCount} 条</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">最低置信度</span>
                      <span className="text-gray-900">{(config.minConfidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 右侧：智能回复组件 */}
            <div className="lg:col-span-2">
              <SmartReply
                postId={demoPostId}
                postTitle={MOCK_POST_TITLE}
                onReplyAdopted={handleReplyAdopted}
              />
            </div>
          </div>
        );

      case 'recommendations':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <ContentRecommendation limit={10} />
            </div>
            <div className="space-y-6">
              {/* 推荐说明 */}
              <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl shadow-sm p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">个性化推荐</h3>
                <p className="text-sm text-gray-600 mb-4">
                  根据您的阅读历史和兴趣偏好，为您推荐最相关的内容。
                </p>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    智能分析您的兴趣
                  </li>
                  <li className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    实时更新推荐内容
                  </li>
                  <li className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    支持反馈优化推荐
                  </li>
                </ul>
              </div>
            </div>
          </div>
        );

      case 'trending':
        return (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">热门话题</h3>
              <span className="text-sm text-gray-500">实时更新</span>
            </div>
            {trendingData?.topics ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {trendingData.topics.map((topic, index) => (
                  <div
                    key={topic.id}
                    className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all cursor-pointer group"
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`
                        w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
                        ${index < 3 ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'}
                      `}>
                        {index + 1}
                      </span>
                      <h4 className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                        {topic.name}
                      </h4>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500 ml-11">
                      <span className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        {topic.hotScore.toFixed(0)} 热度
                      </span>
                      <span className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                        </svg>
                        {topic.postCount} 帖子
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                <p>暂无热门话题数据</p>
              </div>
            )}
          </div>
        );

      case 'experts':
        return (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">推荐专家</h3>
              <span className="text-sm text-gray-500">基于您的关注领域</span>
            </div>
            {expertsData?.experts ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {expertsData.experts.map((expert) => (
                  <div
                    key={expert.id}
                    className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all cursor-pointer group"
                  >
                    <div className="flex items-start gap-3">
                      {expert.avatar ? (
                        <img
                          src={expert.avatar}
                          alt={expert.name}
                          className="w-12 h-12 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-lg">
                          {expert.name.charAt(0)}
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors truncate">
                          {expert.name}
                        </h4>
                        <p className="text-sm text-gray-500">{expert.title}</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {expert.specialty.slice(0, 2).map((spec) => (
                            <span
                              key={spec}
                              className="text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded"
                            >
                              {spec}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100 text-sm text-gray-500">
                      <span>{expert.followerCount} 关注</span>
                      <span>{expert.replyCount} 回复</span>
                      <span className="text-green-600">{(expert.satisfactionRate * 100).toFixed(0)}% 满意</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <p>暂无专家推荐数据</p>
              </div>
            )}
          </div>
        );

      default:
        return <></>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      {/* 页面头部 */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">论坛助手</h1>
            <p className="mt-2 text-sm text-gray-600">
              AI 驱动的智能回复和内容推荐，提升您的论坛体验
            </p>
          </div>
          {config && (
            <div className="flex items-center gap-2 text-sm">
              <span className={`w-2 h-2 rounded-full ${config.enabled ? 'bg-green-500' : 'bg-gray-400'}`} />
              <span className="text-gray-600">
                {config.enabled ? '助手已启用' : '助手已禁用'}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* 标签页导航 */}
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-wrap gap-2 mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-white text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* 当前标签描述 */}
        <div className="mb-6">
          <p className="text-sm text-gray-500">
            {tabs.find((t) => t.id === activeTab)?.description}
          </p>
        </div>

        {/* 内容区域 */}
        <div className="min-h-[500px]">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
}