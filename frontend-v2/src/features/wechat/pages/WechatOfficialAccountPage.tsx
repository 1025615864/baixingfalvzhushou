/**
 * WechatOfficialAccountPage - 微信公众号关注页面
 * 展示公众号二维码和关注引导
 */

import { useState } from 'react';

import { OfficialAccountQrCode } from '../components/OfficialAccountQrCode';
import { useOfficialAccountFollowStatus } from '../hooks/useWechat';

/**
 * 微信图标
 */
function WechatIcon(): JSX.Element {
  return (
    <svg className="w-8 h-8 text-green-500" viewBox="0 0 24 24" fill="currentColor">
      <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 0 1 .598.082l1.584.926a.272.272 0 0 0 .14.047c.134 0 .24-.111.24-.247 0-.06-.023-.12-.038-.177l-.327-1.233a.582.582 0 0 1-.023-.156.49.49 0 0 1 .201-.398C23.024 18.48 24 16.82 24 14.98c0-3.21-2.931-5.837-6.656-6.088V8.89c-.135-.01-.269-.03-.407-.03zm-2.53 3.274c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.97-.982zm4.844 0c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.969-.982z"/>
    </svg>
  );
}

/**
 * 公众号关注页面
 */
export function WechatOfficialAccountPage(): JSX.Element {
  // 模拟当前用户ID
  const currentUserId = 1;
  const [refreshKey, setRefreshKey] = useState(0);

  const { data: followStatus, isLoading } = useOfficialAccountFollowStatus(currentUserId);

  /**
   * 处理扫码成功
   */
  const handleScanSuccess = (): void => {
    // 刷新关注状态
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        {/* 页面头部 */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
            <WechatIcon />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">关注微信公众号</h1>
          <p className="mt-2 text-gray-600">
            扫码关注公众号，获取最新资讯和服务提醒
          </p>
        </div>

        {/* 二维码卡片 */}
        <div className="bg-white rounded-lg shadow-sm p-8 mb-6">
          <div className="flex justify-center">
            <OfficialAccountQrCode
              userId={currentUserId}
              key={refreshKey}
              size="large"
              showRefresh={true}
              onScanSuccess={handleScanSuccess}
              title="扫码关注"
              description="使用微信扫一扫，关注我们的公众号"
            />
          </div>
        </div>

        {/* 关注状态 */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">关注状态</h2>
          
          {isLoading ? (
            <div className="flex items-center justify-center py-4">
              <div className="w-6 h-6 border-2 border-gray-300 border-t-green-500 rounded-full animate-spin" />
              <span className="ml-2 text-gray-600">加载中...</span>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded-full mr-3 ${followStatus?.followStatus === 'followed' ? 'bg-green-500' : 'bg-gray-400'}`} />
                  <div>
                    <p className="font-medium text-gray-900">
                      {followStatus?.followStatus === 'followed' ? '已关注' : '未关注'}
                    </p>
                    <p className="text-sm text-gray-500">
                      {followStatus?.followStatus === 'followed'
                        ? '您已成功关注我们的公众号'
                        : '您尚未关注公众号，请扫码关注'}
                    </p>
                  </div>
                </div>
              </div>

              {followStatus?.followedAt && (
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">关注时间</p>
                    <p className="text-sm text-gray-500">
                      {new Date(String(followStatus.followedAt)).toLocaleString('zh-CN')}
                    </p>
                  </div>
                </div>
              )}

              {/* 关注后的权益 */}
              {followStatus?.followStatus === 'followed' && (
                <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <h3 className="text-green-800 font-medium mb-2">关注成功！您已获得以下权益：</h3>
                  <ul className="space-y-2 text-sm text-green-700">
                    <li className="flex items-center">
                      <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      实时接收订单状态通知
                    </li>
                    <li className="flex items-center">
                      <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      获取最新法律资讯和活动信息
                    </li>
                    <li className="flex items-center">
                      <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      快捷访问法律咨询和文档服务
                    </li>
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 返回按钮 */}
        <div className="mt-6 text-center">
          <button
            onClick={() => window.history.back()}
            className="text-gray-600 hover:text-gray-800 font-medium"
          >
            ← 返回上一页
          </button>
        </div>
      </div>
    </div>
  );
}