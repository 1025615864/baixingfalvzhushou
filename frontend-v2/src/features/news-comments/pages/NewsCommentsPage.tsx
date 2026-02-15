/**
 * 新闻评论页面
 */

import { useParams } from 'react-router-dom';

import { CommentPanel } from '../components/CommentPanel';

/**
 * 新闻评论页面
 */
export function NewsCommentsPage(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const newsId = id ? parseInt(id, 10) : 0;

  // 从 localStorage 获取当前用户 ID（实际项目中应从 auth context 获取）
  const currentUserId = (() => {
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        const user = JSON.parse(userStr) as { id?: number };
        return user.id ?? null;
      }
      return null;
    } catch {
      return null;
    }
  })();

  if (!newsId) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">无效的新闻ID</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">新闻评论</h1>
        <CommentPanel
          newsId={newsId}
          currentUserId={currentUserId}
          className="shadow-sm"
        />
      </div>
    </div>
  );
}

export default NewsCommentsPage;