// ============================================
// 论坛列表页面
// ============================================

import { useState } from 'react';

import { usePostList, useHotPosts } from '../../features/forum/hooks/useForum';
import { PostCard } from '../../features/forum/components/PostCard';
import type { PostCategory } from '../../features/forum/types';

const categories: { value: PostCategory | ''; label: string }[] = [
  { value: '', label: '全部' },
  { value: 'legal', label: '法律咨询' },
  { value: 'consultation', label: '问题求助' },
  { value: 'experience', label: '经验分享' },
  { value: 'discussion', label: '话题讨论' },
  { value: 'help', label: '求助问答' },
];

export function ForumListPage() {
  const [selectedCategory, setSelectedCategory] = useState<PostCategory | ''>('');
  const [searchKeyword, setSearchKeyword] = useState('');
  
  const { data: posts, isLoading } = usePostList({
    category: selectedCategory || undefined,
    keyword: searchKeyword,
  });
  
  const { data: hotPosts } = useHotPosts(5);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* 头部 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">法律论坛</h1>
          <p className="text-gray-600">交流法律问题，分享维权经验</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* 左侧：帖子列表 */}
          <div className="lg:col-span-3 space-y-6">
            {/* 筛选栏 */}
            <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <div className="flex flex-wrap items-center gap-2">
                {categories.map((cat) => (
                  <button
                    key={cat.value}
                    onClick={() => { setSelectedCategory(cat.value); }}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                      selectedCategory === cat.value
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>
              
              {/* 搜索框 */}
              <div className="mt-4 flex gap-2">
                <input
                  type="text"
                  placeholder="搜索帖子..."
                  value={searchKeyword}
                  onChange={(e) => { setSearchKeyword(e.target.value); }}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  搜索
                </button>
              </div>
            </div>

            {/* 帖子列表 */}
            {isLoading ? (
              <div className="text-center py-12 text-gray-500">加载中...</div>
            ) : posts?.items.length === 0 ? (
              <div className="text-center py-12 text-gray-500">暂无帖子</div>
            ) : (
              <div className="space-y-4">
                {posts?.items.map((post) => (
                  <PostCard key={post.id} post={post} />
                ))}
              </div>
            )}
          </div>

          {/* 右侧：侧边栏 */}
          <div className="space-y-6">
            {/* 发布按钮 */}
            <button className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              发布帖子
            </button>

            {/* 热门帖子 */}
            <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.534-.398-2.654A1 1 0 005.05 6.05 6.981 6.981 0 003 11a7 7 0 1011.95-4.95c-.592-.591-.98-.985-1.348-1.467-.363-.476-.724-1.063-1.207-2.03zM12.12 15.12A3 3 0 017 13s.879.5 2.5.5c0-1 .5-4 1.25-4.5.5 1 .786 1.293 1.371 1.879A2.99 2.99 0 0113 13a2.99 2.99 0 01-.879 2.121z" clipRule="evenodd" />
                </svg>
                热门帖子
              </h3>
              <div className="space-y-3">
                {hotPosts?.items.map((post, index) => (
                  <div
                    key={post.id}
                    className="flex gap-3 cursor-pointer group"
                  >
                    <span className={`flex-shrink-0 w-6 h-6 flex items-center justify-center rounded text-sm font-medium ${
                      index < 3 ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {index + 1}
                    </span>
                    <p className="text-sm text-gray-700 line-clamp-2 group-hover:text-blue-600 transition-colors">
                      {post.title}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* 社区规则 */}
            <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-gray-900 mb-3">社区规则</h3>
              <ul className="text-sm text-gray-600 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-blue-600">1.</span>
                  禁止发布违法违规内容
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600">2.</span>
                  尊重他人，文明交流
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600">3.</span>
                  保护个人隐私信息
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600">4.</span>
                  禁止发布虚假信息
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}