/**
 * LoginAuditPage - 登录审计日志页面
 */

import { useNavigate } from 'react-router-dom';
import { AuditOutlined, ArrowLeftOutlined } from '@ant-design/icons';

import { LoginAuditTable } from '../components/LoginAuditTable';

/**
 * 登录审计日志页面
 */
export function LoginAuditPage(): JSX.Element {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 页面头部 */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center">
            <button
              onClick={() => navigate('/security')}
              className="mr-4 p-2 text-gray-500 hover:text-gray-700 transition-colors"
              aria-label="返回安全中心"
            >
              <ArrowLeftOutlined className="text-xl" />
            </button>
            <div className="p-3 bg-blue-100 rounded-full mr-4">
              <AuditOutlined className="text-2xl text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">登录审计日志</h1>
              <p className="text-sm text-gray-500 mt-1">
                查看账号的登录历史记录，发现异常登录行为
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* 安全提示 */}
          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-blue-900 mb-1">安全提示</h4>
            <p className="text-sm text-blue-700">
              定期检查登录记录，如果发现可疑的登录活动，请立即修改密码并启用双重验证。
            </p>
          </div>

          {/* 登录审计表格 */}
          <LoginAuditTable pageSize={10} />
        </div>
      </div>
    </div>
  );
}