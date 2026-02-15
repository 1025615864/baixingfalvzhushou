/**
 * WeChat（微信生态）API 层
 * 对接后端 /api/v1/wechat 端点
 */

import apiClient from "@/shared/lib/api/client";

import type {
  WechatBindInfo,
  WechatAccountType,
  OfficialAccountFollowState,
  MiniProgramLoginResult,
  WechatShareConfig,
  WechatShareType,
  UnifiedOrderResponse,
  GetWechatBindStatusResponse,
  BindWechatRequest,
  BindWechatResponse,
  UnbindWechatRequest,
  UnbindWechatResponse,
  GetOfficialAccountQrCodeResponse,
  MiniProgramLoginRequest,
  MiniProgramLoginResponse,
  GetShareConfigRequest,
  GetShareConfigResponse,
  WechatUnifiedOrderRequest,
  WechatUnifiedOrderResponse,
  QueryPayStatusResponse,
  GetJsApiConfigRequest,
  GetJsApiConfigResponse,
} from '../types';

// API 基础路径
const API_BASE = '/wechat';

/** API 错误响应 */
interface ApiErrorResponse {
  detail?: string;
  message?: string;
  code?: string;
}

/**
 * 安全获取 JSON 响应
 */
async function safeJson<T>(response: Response): Promise<T> {
  const data = await response.json() as T;
  return data;
}

/**
 * 获取 API 错误信息
 */
function getErrorMessage(error: unknown, defaultMsg: string): string {
  if (typeof error === 'object' && error !== null) {
    if ('detail' in error) {
      return (error as ApiErrorResponse).detail || defaultMsg;
    }
    if ('message' in error) {
      return (error as ApiErrorResponse).message || defaultMsg;
    }
  }
  return defaultMsg;
}

// ==================== 微信绑定状态 API ====================

/**
 * 获取微信绑定状态
 */
export async function apiGetWechatBindStatus(userId: number, accountType?: WechatAccountType): Promise<WechatBindInfo[]> {
  const searchParams = new URLSearchParams();
  searchParams.set('user_id', String(userId));
  if (accountType) searchParams.set('account_type', accountType);

  const response = await fetch(`${API_BASE}/bind-status?${searchParams.toString()}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取微信绑定状态失败' }));
    throw new Error(getErrorMessage(error, '获取微信绑定状态失败'));
  }

  const data = await safeJson<GetWechatBindStatusResponse>(response);
  return data.bindInfo;
}

/**
 * 绑定微信账号
 */
export async function apiBindWechat(request: BindWechatRequest): Promise<WechatBindInfo> {
  const response = await apiClient.post<BindWechatResponse>(`${API_BASE}/bind`, {
    user_id: request.userId,
    account_type: request.accountType,
    auth_code: request.authCode,
    state: request.state,
  });
  return response.data.bindInfo;
}

/**
 * 解绑微信账号
 */
export async function apiUnbindWechat(request: UnbindWechatRequest): Promise<boolean> {
  const response = await apiClient.delete<UnbindWechatResponse>(`${API_BASE}/unbind`, {
    data: {
      user_id: request.userId,
      account_type: request.accountType,
      bind_id: request.bindId,
    },
  });
  return response.data.success;
}

// ==================== 公众号 API ====================

/**
 * 获取公众号关注二维码
 */
export async function apiGetOfficialAccountQrCode(
  userId: number,
  scene?: string,
  expireSeconds?: number
): Promise<GetOfficialAccountQrCodeResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set('user_id', String(userId));
  if (scene) searchParams.set('scene', scene);
  if (expireSeconds) searchParams.set('expire_seconds', String(expireSeconds));

  const response = await fetch(`${API_BASE}/qr-code?${searchParams.toString()}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取公众号二维码失败' }));
    throw new Error(getErrorMessage(error, '获取公众号二维码失败'));
  }

  const data = await safeJson<GetOfficialAccountQrCodeResponse>(response);
  return data;
}

/**
 * 获取公众号关注状态
 */
export async function apiGetOfficialAccountFollowStatus(userId: number): Promise<OfficialAccountFollowState> {
  const response = await fetch(`${API_BASE}/follow-status?user_id=${userId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取关注状态失败' }));
    throw new Error(getErrorMessage(error, '获取关注状态失败'));
  }

  const data = await safeJson<{ follow_status: OfficialAccountFollowState }>(response);
  return data.follow_status;
}

// ==================== 小程序 API ====================

/**
 * 小程序登录
 */
export async function apiMiniProgramLogin(request: MiniProgramLoginRequest): Promise<MiniProgramLoginResult> {
  const response = await apiClient.post<MiniProgramLoginResponse>(`${API_BASE}/mini-program/login`, {
    code: request.code,
    encrypted_data: request.encryptedData,
    iv: request.iv,
  });
  return {
    success: response.data.success,
    sessionToken: response.data.sessionToken,
    userInfo: response.data.userInfo,
    errorMessage: response.data.success ? undefined : '登录失败',
  };
}

/**
 * 刷新小程序登录状态
 */
export async function apiRefreshMiniProgramSession(refreshToken: string): Promise<MiniProgramLoginResult> {
  const response = await apiClient.post<MiniProgramLoginResponse>(`${API_BASE}/mini-program/refresh`, {
    refresh_token: refreshToken,
  });
  return {
    success: response.data.success,
    sessionToken: response.data.sessionToken,
    userInfo: response.data.userInfo,
    errorMessage: response.data.success ? undefined : '刷新失败',
  };
}

// ==================== 微信分享 API ====================

/**
 * 获取微信分享配置
 */
export async function apiGetShareConfig(request: GetShareConfigRequest): Promise<WechatShareConfig> {
  const response = await fetch(`${API_BASE}/share-config`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      url: request.url,
      share_types: request.shareTypes,
    }),
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取分享配置失败' }));
    throw new Error(getErrorMessage(error, '获取分享配置失败'));
  }

  const data = await safeJson<GetShareConfigResponse>(response);
  return data.config;
}

/**
 * 获取微信JSSDK配置
 */
export async function apiGetJsApiConfig(request: GetJsApiConfigRequest): Promise<GetJsApiConfigResponse> {
  const response = await apiClient.post<GetJsApiConfigResponse>(`${API_BASE}/jsapi-config`, {
    url: request.url,
    js_api_list: request.jsApiList,
  });
  return response.data;
}

/**
 * 上报分享结果
 */
export async function apiReportShareResult(
  shareType: WechatShareType,
  success: boolean,
  url: string
): Promise<void> {
  await apiClient.post(`${API_BASE}/share-report`, {
    share_type: shareType,
    success,
    url,
    shared_at: new Date().toISOString(),
  });
}

// ==================== 微信支付 API ====================

/**
 * 微信支付统一下单
 */
export async function apiUnifiedOrder(request: WechatUnifiedOrderRequest): Promise<UnifiedOrderResponse> {
  const response = await apiClient.post<WechatUnifiedOrderResponse>(`${API_BASE}/pay/unified-order`, {
    user_id: request.userId,
    body: request.body,
    total_fee: request.totalFee,
    out_trade_no: request.outTradeNo,
    product_id: request.productId,
    attach: request.attach,
    spbill_create_ip: request.spbillCreateIp,
    trade_type: request.tradeType,
    openid: request.openid,
    notify_url: request.notifyUrl,
  });
  return {
    prepayId: response.data.prepayId,
    payConfig: response.data.payConfig,
    orderNo: response.data.orderNo,
    codeUrl: response.data.codeUrl,
    mwebUrl: response.data.mwebUrl,
  };
}

/**
 * 查询支付状态
 */
export async function apiQueryPayStatus(outTradeNo: string): Promise<QueryPayStatusResponse> {
  const response = await fetch(`${API_BASE}/pay/status?out_trade_no=${outTradeNo}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '查询支付状态失败' }));
    throw new Error(getErrorMessage(error, '查询支付状态失败'));
  }

  const data = await safeJson<QueryPayStatusResponse>(response);
  return data;
}

/**
 * 关闭支付订单
 */
export async function apiClosePayOrder(outTradeNo: string): Promise<boolean> {
  const response = await apiClient.post<{ success: boolean }>(`${API_BASE}/pay/close`, {
    out_trade_no: outTradeNo,
  });
  return response.data.success;
}

// ==================== 微信登录回调 API ====================

/**
 * 微信登录回调处理响应
 */
interface WechatCallbackResponse {
  success: boolean;
  openid?: string;
  session_key?: string;
  access_token?: string;
  refresh_token?: string;
  expires_in?: number;
  errorMessage?: string;
}

/**
 * 处理微信登录回调
 */
export async function apiHandleWechatCallback(code: string, state: string): Promise<WechatCallbackResponse> {
  const response = await apiClient.post<WechatCallbackResponse>(
    `${API_BASE}/auth/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`
  );
  return response.data;
}

/**
 * 微信用户登录（兼容接口）
 */
export async function apiWechatUserLogin(code: string, state: string): Promise<WechatCallbackResponse> {
  const response = await apiClient.post<WechatCallbackResponse>(
    `${API_BASE}/user/login?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`
  );
  return response.data;
}