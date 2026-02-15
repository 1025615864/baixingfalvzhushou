import { Link } from 'react-router-dom';

export function NotFoundPage(): JSX.Element {
  return (
    <div className="text-center py-20">
      <h1 className="text-6xl font-bold text-gray-300 mb-4">404</h1>
      <h2 className="text-2xl font-semibold text-gray-700 mb-4">
        页面未找到
      </h2>
      <p className="text-gray-600 mb-8">
        抱歉，您访问的页面不存在或已被移除
      </p>
      <Link
        to="/"
        className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition-colors"
      >
        返回首页
      </Link>
    </div>
  );
}