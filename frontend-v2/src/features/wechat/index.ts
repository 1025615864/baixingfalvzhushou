/**
 * 微信生态模块 - 微信登录、绑定、公众号关注等功能
 * 
 * @module features/wechat
 */

// ============================================
// 页面导出
// ============================================

export { WechatPage } from './pages/WechatPage';

// ============================================
// 组件导出
// ============================================

export { WechatBindCard } from './components/WechatBindCard';
export { WechatLoginButton } from './components/WechatLoginButton';
export { OfficialAccountQrCode } from './components/OfficialAccountQrCode';
export { WechatShareDialog } from './components/WechatShareDialog';

// ============================================
// Hooks导出
// ============================================

export {
  useWechatBindStatus,
  useOfficialAccountFollowStatus,
  useWechatPay,
  useWechatLogin,
  useWechatShare,
} from './hooks/useWechat';

// ============================================
// API导出
// ============================================

export {
  apiGetWechatBindStatus,
  apiBindWechat,
  apiUnbindWechat,
  apiGetOfficialAccountQrCode,
  apiGetOfficialAccountFollowStatus,
  apiMiniProgramLogin,
  apiRefreshMiniProgramSession,
  apiGetShareConfig,
  apiGetJsApiConfig,
  apiReportShareResult,
  apiUnifiedOrder,
  apiQueryPayStatus,
  apiClosePayOrder,
  apiHandleWechatCallback,
  apiWechatUserLogin,
} from './api';

// ============================================
// 类型导出
// ============================================

export type {
  WechatBindInfo,
  OfficialAccountFollowStatus,
  WechatPayConfig,
  WechatPayResult,
  MiniProgramLoginResult,
  WechatShareConfig,
  WechatAccountType,
} from './types';
