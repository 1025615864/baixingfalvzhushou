/**
 * WechatPage - 微信生态中心页面
 * 包含绑定管理、关注公众号、小程序入口等功能
 */

import { useState } from 'react';

import { WechatBindCard } from '../components/WechatBindCard';
import { WechatLoginButton } from '../components/WechatLoginButton';
import { OfficialAccountQrCode } from '../components/OfficialAccountQrCode';
import { WechatShareDialog } from '../components/WechatShareDialog';
import { useWechatBindStatus, useOfficialAccountFollowStatus, useWechatPay } from '../hooks/useWechat';

// ==================== 子组件 ====================

/**
 * 页面头部组件
 */
function PageHeader(): JSX.Element {
  return (
    <div className="mb-8">
      <h1 className="text-2xl font-bold text-gray-900">微信生态中心</h1>
      <p className="mt-2 text-sm text-gray-600">
        管理您的微信账号绑定、关注公众号、使用小程序等功能
      </p>
    </div>
  );
}

/**
 * 微信图标组件
 */
function WechatIcon(): JSX.Element {
  return (
    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
      <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 0 1 .598.082l1.584.926a.272.272 0 0 0 .14.047c.134 0 .24-.111.24-.247 0-.06-.023-.12-.038-.177l-.327-1.233a.582.582 0 0 1-.023-.156.49.49 0 0 1 .201-.398C23.024 18.48 24 16.82 24 14.98c0-3.21-2.931-5.837-6.656-6.088V8.89c-.135-.01-.269-.03-.407-.03zm-2.53 3.274c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.97-.982zm4.844 0c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.969-.982z"/>
    </svg>
  );
}

/**
 * 分享图标组件
 */
function ShareIcon(): JSX.Element {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
    </svg>
  );
}

/**
 * 支付图标组件
 */
function PayIcon(): JSX.Element {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  );
}

// ==================== 主页面组件 ====================

/**
 * 微信生态中心页面
 */
export function WechatPage(): JSX.Element {
  // 模拟当前用户ID，实际应从认证上下文中获取
  const currentUserId = 1;
  
  const [activeTab, setActiveTab] = useState<'bind' | 'follow' | 'tools'>('bind');
  const [isShareDialogOpen, setIsShareDialogOpen] = useState(false);
  const [shareUrl, setShareUrl] = useState(typeof window !== 'undefined' ? window.location.href : '');
  
  // 使用Hooks获取数据
  const { data: bindInfos, isLoading: isBindLoading } = useWechatBindStatus(currentUserId);
  const { data: followStatus, isLoading: isFollowLoading } = useOfficialAccountFollowStatus(currentUserId);
  const { pay, isPaying, payResult } = useWechatPay();

  // 获取特定类型的绑定信息
  const officialBindInfo = bindInfos?.find(info => info.accountType === 'official') || null;
  const miniProgramBindInfo = bindInfos?.find(info => info.accountType === 'mini_program') || null;

  /**
   * 处理分享
   */
  const handleShare = (): void => {
    setShareUrl(typeof window !== 'undefined' ? window.location.href : '');
    setIsShareDialogOpen(true);
  };

  /**
   * 处理支付测试
   */
  const handlePayTest = async (): Promise<void> => {
    // 创建测试订单
    await pay({
      userId: currentUserId,
      body: '测试商品',
      totalFee: 1, // 0.01元
      outTradeNo: `TEST_${Date.now()}`,
      tradeType: 'jsapi',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <PageHeader />

        {/* 快捷操作栏 */}
        <div className="mb-6 flex flex-wrap gap-3">
          <button
            onClick={handleShare}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <ShareIcon />
            <span>分享页面</span>
          </button>
          
          <button
            onClick={() => void handlePayTest()}
            disabled={isPaying}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <PayIcon />
            <span>{isPaying ? '支付中...' : '测试支付'}</span>
          </button>
        </div>

        {/* 标签导航 */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('bind')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${activeTab === 'bind'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              账号绑定
            </button>
            <button
              onClick={() => setActiveTab('follow')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${activeTab === 'follow'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              关注公众号
            </button>
            <button
              onClick={() => setActiveTab('tools')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${activeTab === 'tools'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              工具箱
            </button>
          </nav>
        </div>

        {/* 标签内容 */}
        <div className="space-y-6">
          {/* 账号绑定标签 */}
          {activeTab === 'bind' && (
            <div className="space-y-4">
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <WechatIcon />
                  <span className="ml-2">微信账号绑定</span>
                </h2>
                <p className="text-sm text-gray-600 mb-6">
                  绑定微信账号后，您可以使用微信登录、接收消息通知等功能
                </p>
                
                <div className="grid gap-4 md:grid-cols-1">
                  <WechatBindCard
                    userId={currentUserId}
                    bindInfo={officialBindInfo}
                    accountType="official"
                    isLoading={isBindLoading}
                  />
                  <WechatBindCard
                    userId={currentUserId}
                    bindInfo={miniProgramBindInfo}
                    accountType="mini_program"
                    isLoading={isBindLoading}
                  />
                </div>
              </div>

              {/* 登录按钮演示 */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">快捷登录</h2>
                <div className="flex flex-wrap gap-4">
                  <WechatLoginButton
                    loginType="official"
                    onLoginSuccess={(token, openid) => {
                      alert(`登录成功！Token: ${token}, OpenID: ${openid}`);
                    }}
                    onLoginFailure={(error) => {
                      alert(`登录失败: ${error.message}`);
                    }}
                  />
                  <WechatLoginButton
                    loginType="mini_program"
                    variant="outline"
                  />
                </div>
              </div>
            </div>
          )}

          {/* 关注公众号标签 */}
          {activeTab === 'follow' && (
            <div className="space-y-4">
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">关注公众号</h2>
                <p className="text-sm text-gray-600 mb-6">
                  关注我们的微信公众号，获取最新资讯和服务提醒
                </p>
                
                <div className="flex justify-center">
                  <OfficialAccountQrCode
                    userId={currentUserId}
                    size="large"
                    showRefresh={true}
                    onScanSuccess={() => {
                      alert('扫码成功！');
                    }}
                    title="扫码关注公众号"
                    description="使用微信扫一扫，关注我们获取更多服务"
                  />
                </div>
              </div>

              {/* 关注状态展示 */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">关注状态</h2>
                {isFollowLoading ? (
                  <div className="animate-pulse space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                  </div>
                ) : followStatus ? (
                  <div className="space-y-2">
                    <p className="text-sm">
                      <span className="text-gray-500">公众号：</span>
                      <span className="font-medium">{followStatus.account.name}</span>
                    </p>
                    <p className="text-sm">
                      <span className="text-gray-500">关注状态：</span>
                      <span className={`
                        inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                        ${followStatus.followStatus === 'followed' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                        }
                      `}>
                        {followStatus.followStatus === 'followed' ? '已关注' : '未关注'}
                      </span>
                    </p>
                    {followStatus.followedAt && (
                      <p className="text-sm">
                        <span className="text-gray-500">关注时间：</span>
                        <span>{new Date(followStatus.followedAt).toLocaleString('zh-CN')}</span>
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">暂无关注状态信息</p>
                )}
              </div>
            </div>
          )}

          {/* 工具箱标签 */}
          {activeTab === 'tools' && (
            <div className="space-y-4">
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">微信工具箱</h2>
                
                <div className="grid gap-4 md:grid-cols-2">
                  {/* 分享工具 */}
                  <div className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center text-green-600">
                        <ShareIcon />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">微信分享</h3>
                        <p className="text-xs text-gray-500">分享到朋友圈、好友</p>
                      </div>
                    </div>
                    <button
                      onClick={handleShare}
                      className="w-full mt-2 px-4 py-2 text-sm font-medium text-green-600 border border-green-600 rounded-md hover:bg-green-50 transition-colors"
                    >
                      立即分享
                    </button>
                  </div>

                  {/* 支付工具 */}
                  <div className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600">
                        <PayIcon />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">微信支付</h3>
                        <p className="text-xs text-gray-500">快捷支付测试</p>
                      </div>
                    </div>
                    <button
                      onClick={() => void handlePayTest()}
                      disabled={isPaying}
                      className="w-full mt-2 px-4 py-2 text-sm font-medium text-blue-600 border border-blue-600 rounded-md hover:bg-blue-50 transition-colors disabled:opacity-50"
                    >
                      {isPaying ? '支付中...' : '测试支付'}
                    </button>
                  </div>

                  {/* 小程序入口 */}
                  <div className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center text-purple-600">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">小程序</h3>
                        <p className="text-xs text-gray-500">打开微信小程序</p>
                      </div>
                    </div>
                    <button
                      className="w-full mt-2 px-4 py-2 text-sm font-medium text-purple-600 border border-purple-600 rounded-md hover:bg-purple-50 transition-colors"
                      onClick={() => alert('请使用微信扫描小程序码')}
                    >
                      打开小程序
                    </button>
                  </div>

                  {/* 更多工具 */}
                  <div className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-gray-600">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">更多</h3>
                        <p className="text-xs text-gray-500">敬请期待</p>
                      </div>
                    </div>
                    <button
                      disabled
                      className="w-full mt-2 px-4 py-2 text-sm font-medium text-gray-400 border border-gray-300 rounded-md cursor-not-allowed"
                    >
                      即将上线
                    </button>
                  </div>
                </div>
              </div>

              {/* 支付结果展示 */}
              {payResult && (
                <div className="bg-white rounded-lg shadow-sm p-6">
                  <h2 className="text-lg font-medium text-gray-900 mb-4">支付结果</h2>
                  <div className="space-y-2">
                    <p className="text-sm">
                      <span className="text-gray-500">支付状态：</span>
                      <span className={`
                        inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                        ${payResult.tradeState === 'SUCCESS' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                        }
                      `}>
                        {payResult.tradeState === 'SUCCESS' ? '支付成功' : payResult.tradeState}
                      </span>
                    </p>
                    {payResult.orderInfo && (
                      <>
                        <p className="text-sm">
                          <span className="text-gray-500">订单描述：</span>
                          <span>{payResult.orderInfo.body}</span>
                        </p>
                        <p className="text-sm">
                          <span className="text-gray-500">支付金额：</span>
                          <span>¥{(payResult.orderInfo.totalFee / 100).toFixed(2)}</span>
                        </p>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 分享弹窗 */}
        <WechatShareDialog
          url={shareUrl}
          isOpen={isShareDialogOpen}
          onClose={() => setIsShareDialogOpen(false)}
          onShareSuccess={(type) => {
            alert(`分享到 ${type} 成功！`);
          }}
        />
      </div>
    </div>
  );
}