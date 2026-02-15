/**
 * DeviceListPage - 设备管理页面
 */

import { useNavigate } from 'react-router-dom';
import { DesktopOutlined, ArrowLeftOutlined } from '@ant-design/icons';

import { DeviceList } from '../components/DeviceList';

/**
 * 设备管理页面
 */
export function DeviceListPage(): JSX.Element {
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
              <DesktopOutlined className="text-2xl text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">设备管理</h1>
              <p className="text-sm text-gray-500 mt-1">
                管理已登录的设备，随时退出可疑设备
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* 安全提示 */}
          <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
            <h4 className="text-sm font-semibold text-amber-900 mb-1">安全提醒</h4>
            <p className="text-sm text-amber-700">
              如果您发现不认识的设备，请立即点击&ldquo;退出&rdquo;按钮将其登出，并建议修改密码。
              当前登录的设备会标记为&ldquo;当前设备&rdquo;。
            </p>
          </div>

          {/* 设备列表 */}
          <DeviceList />
        </div>
      </div>
    </div>
  );
}