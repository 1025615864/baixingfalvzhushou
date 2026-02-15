/**
 * WeChat（微信生态）Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import type {
  WechatBindInfo,
  WechatAccountType,
  OfficialAccountFollowState,
  MiniProgramLoginResult,
  WechatShareConfig,
  WechatShareType,
  UnifiedOrderResponse,
  QueryPayStatusResponse,
  BindWechatRequest,
  UnbindWechatRequest,
  MiniProgramLoginRequest,
  WechatUnifiedOrderRequest,
} from '../types';
import {
  apiGetWechatBindStatus,
  apiBindWechat,
  apiUnbindWechat,
  apiGetOfficialAccountQrCode,
  apiGetOfficialAccountFollowStatus,
  apiMiniProgramLogin,
  apiGetShareConfig,
  apiReportShareResult,
  apiUnifiedOrder,
  apiQueryPayStatus,
  apiGetJsApiConfig,
} from '../api';

// ==================== Query Keys ====================

const WECHAT_QUERY_KEYS = {
  bindStatus: (userId: number, accountType?: WechatAccountType) => 
    ['wechat', 'bind-status', userId, accountType] as const,
  officialAccountQrCode: (userId: number) => 
    ['wechat', 'official-account', 'qr-code', userId] as const,
  officialAccountFollowStatus: (userId: number) => 
    ['wechat', 'official-account', 'follow-status', userId] as const,
  shareConfig: (url: string) => 
    ['wechat', 'share-config', url] as const,
  payStatus: (outTradeNo: string) => 
    ['wechat', 'pay-status', outTradeNo] as const,
  jsApiConfig: (url: string) => 
    ['wechat', 'jsapi-config', url] as const,
} as const;

// ==================== 微信绑定状态 Hooks ====================

/**
 * 使用微信绑定状态 Hook
 */
export function useWechatBindStatus(userId: number, accountType?: WechatAccountType) {
  return useQuery<WechatBindInfo[]>({
    queryKey: WECHAT_QUERY_KEYS.bindStatus(userId, accountType),
    queryFn: () => apiGetWechatBindStatus(userId, accountType),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    enabled: userId > 0,
  });
}

/**
 * 检查是否已绑定指定类型的微信账号
 */
export function useIsWechatBound(userId: number, accountType: WechatAccountType) {
  const { data: bindInfos, isLoading, error } = useWechatBindStatus(userId, accountType);
  
  const isBound = bindInfos?.some(info => 
    info.accountType === accountType && info.bindStatus === 'bound'
  ) ?? false;
  
  return { isBound, isLoading, error };
}

/**
 * 绑定微信账号 Hook
 */
export function useBindWechat() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: BindWechatRequest) => apiBindWechat(request),
    onSuccess: (_data, variables) => {
      // 绑定成功后刷新绑定状态
      void queryClient.invalidateQueries({ 
        queryKey: WECHAT_QUERY_KEYS.bindStatus(variables.userId, variables.accountType) 
      });
    },
  });
}

/**
 * 解绑微信账号 Hook
 */
export function useUnbindWechat() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: UnbindWechatRequest) => apiUnbindWechat(request),
    onSuccess: (_data, variables) => {
      // 解绑成功后刷新绑定状态
      void queryClient.invalidateQueries({ 
        queryKey: WECHAT_QUERY_KEYS.bindStatus(variables.userId, variables.accountType) 
      });
    },
  });
}

// ==================== 公众号 Hooks ====================

/**
 * 获取公众号二维码 Hook
 */
export function useOfficialAccountQrCode(userId: number) {
  return useQuery<{ qrCodeUrl: string; scene: string; expireAt: string }>({
    queryKey: WECHAT_QUERY_KEYS.officialAccountQrCode(userId),
    queryFn: async () => {
      const response = await apiGetOfficialAccountQrCode(userId, `follow_${userId}`, 2592000);
      return {
        qrCodeUrl: response.qrCodeUrl,
        scene: response.scene,
        expireAt: response.expireAt,
      };
    },
    staleTime: 30 * 60 * 1000, // 30分钟缓存
    enabled: userId > 0,
  });
}

/**
 * 获取公众号关注状态 Hook
 */
export function useOfficialAccountFollowStatus(userId: number) {
  return useQuery<OfficialAccountFollowState>({
    queryKey: WECHAT_QUERY_KEYS.officialAccountFollowStatus(userId),
    queryFn: () => apiGetOfficialAccountFollowStatus(userId),
    staleTime: 2 * 60 * 1000, // 2分钟缓存
    enabled: userId > 0,
    refetchInterval: 30 * 1000, // 每30秒刷新一次
  });
}

// ==================== 小程序 Hooks ====================

/**
 * 使用微信登录 Hook
 */
export function useWechatLogin() {
  const _queryClient = useQueryClient();
  const [loginResult, setLoginResult] = useState<MiniProgramLoginResult | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const login = useCallback(async (request: MiniProgramLoginRequest): Promise<MiniProgramLoginResult> => {
    setIsLoggingIn(true);
    try {
      const result = await apiMiniProgramLogin(request);
      setLoginResult(result);
      return result;
    } finally {
      setIsLoggingIn(false);
    }
  }, []);

  return {
    login,
    loginResult,
    isLoggingIn,
  };
}

/**
 * 小程序静默登录 Hook
 */
export function useSilentLogin() {
  const { isLoggingIn } = useWechatLogin();

  const silentLogin = useCallback((): MiniProgramLoginResult | null => {
    // 尝试从本地存储获取登录态
    const sessionToken = localStorage.getItem('wechat_session_token');
    if (sessionToken) {
      // 检查登录态是否有效
      // 实际实现中应该调用后端验证接口
      return {
        success: true,
        sessionToken,
      };
    }
    return null;
  }, []);

  return {
    silentLogin,
    isLoggingIn,
  };
}

// ==================== 微信分享 Hooks ====================

/**
 * 使用微信分享配置 Hook
 */
export function useShareConfig(url: string) {
  return useQuery<WechatShareConfig>({
    queryKey: WECHAT_QUERY_KEYS.shareConfig(url),
    queryFn: () => apiGetShareConfig({ url }),
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    enabled: !!url,
  });
}

/**
 * 使用微信分享 Hook
 */
export function useWechatShare() {
  const [isSharing, setIsSharing] = useState(false);

  const share = useCallback((
    config: WechatShareConfig,
    shareType: WechatShareType
  ): boolean => {
    setIsSharing(true);
    try {
      // 调用微信JSSDK分享API
      // 实际实现中需要根据分享类型调用不同的API
      if (typeof window !== 'undefined') {
        const win = window as unknown as { wx?: { updateAppMessageShareData?: (data: Record<string, unknown>) => void } };
        if (win.wx?.updateAppMessageShareData) {
          win.wx.updateAppMessageShareData({
            title: config.title,
            desc: config.description,
            link: config.link,
            imgUrl: config.imgUrl,
            success: () => {
              void apiReportShareResult(shareType, true, config.link);
            },
          });
          return true;
        }
      }
      return false;
    } finally {
      setIsSharing(false);
    }
  }, []);

  return {
    share,
    isSharing,
  };
}

/**
 * 使用微信JSSDK配置 Hook
 */
export function useWechatJsApiConfig(jsApiList: string[] = []) {
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const initConfig = useCallback(async (url: string): Promise<boolean> => {
    try {
      const config = await apiGetJsApiConfig({ url, jsApiList });
      
      // 初始化微信JSSDK
      if (typeof window !== 'undefined') {
        const win = window as unknown as {
          wx?: {
            config?: (data: Record<string, unknown>) => void;
            ready?: (callback: () => void) => void;
            error?: (callback: (err: Error) => void) => void;
          }
        };
        
        if (win.wx?.config) {
          win.wx.config({
            debug: false,
            appId: config.appId,
            timestamp: config.timestamp,
            nonceStr: config.nonceStr,
            signature: config.signature,
            jsApiList: config.jsApiList.length > 0 ? config.jsApiList : jsApiList,
          });
          
          win.wx.ready?.(() => {
            setIsReady(true);
          });
          
          win.wx.error?.((err: Error) => {
            setError(err);
          });
          
          return true;
        }
      }
      return false;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('初始化微信JSSDK失败'));
      return false;
    }
  }, [jsApiList]);

  return {
    initConfig,
    isReady,
    error,
  };
}

// ==================== 微信支付 Hooks ====================

/**
 * 使用微信支付 Hook
 */
export function useWechatPay() {
  const [payResult, setPayResult] = useState<QueryPayStatusResponse | null>(null);
  const [isPaying, setIsPaying] = useState(false);

  // 创建支付订单
  const createOrder = useCallback(async (request: WechatUnifiedOrderRequest): Promise<UnifiedOrderResponse | null> => {
    setIsPaying(true);
    try {
      const result = await apiUnifiedOrder(request);
      return result;
    } catch (error) {
      console.error('创建支付订单失败:', error);
      return null;
    } finally {
      setIsPaying(false);
    }
  }, []);

  // 调起微信支付
  const requestPayment = useCallback(async (payConfig: UnifiedOrderResponse['payConfig']): Promise<boolean> => {
    return new Promise((resolve) => {
      if (typeof window !== 'undefined') {
        const win = window as unknown as { wx?: { chooseWXPay?: (data: Record<string, unknown>) => void } };
        if (win.wx?.chooseWXPay) {
          win.wx.chooseWXPay({
            timestamp: payConfig.timeStamp,
            nonceStr: payConfig.nonceStr,
            package: payConfig.package,
            signType: payConfig.signType,
            paySign: payConfig.paySign,
            success: () => {
              resolve(true);
            },
            fail: () => {
              resolve(false);
            },
          });
        } else {
          // 非微信环境，模拟支付成功
          setTimeout(() => resolve(true), 1000);
        }
      } else {
        // 非浏览器环境，直接失败
        resolve(false);
      }
    });
  }, []);

  // 查询支付状态
  const queryPayStatus = useCallback(async (outTradeNo: string): Promise<QueryPayStatusResponse | null> => {
    try {
      const result = await apiQueryPayStatus(outTradeNo);
      setPayResult(result);
      return result;
    } catch (error) {
      console.error('查询支付状态失败:', error);
      return null;
    }
  }, []);

  // 完整的支付流程
  const pay = useCallback(async (request: WechatUnifiedOrderRequest): Promise<boolean> => {
    // 1. 创建订单
    const orderResult = await createOrder(request);
    if (!orderResult) return false;

    // 2. 调起支付
    const paySuccess = await requestPayment(orderResult.payConfig);
    if (!paySuccess) return false;

    // 3. 查询支付状态
    const status = await queryPayStatus(orderResult.orderNo);

    return status?.tradeState === 'SUCCESS';
  }, [createOrder, requestPayment, queryPayStatus]);

  return {
    pay,
    createOrder,
    requestPayment,
    queryPayStatus,
    payResult,
    isPaying,
  };
}

/**
 * 使用支付状态轮询 Hook
 */
export function usePayStatusPolling(outTradeNo: string, enabled = false) {
  return useQuery<QueryPayStatusResponse>({
    queryKey: WECHAT_QUERY_KEYS.payStatus(outTradeNo),
    queryFn: () => apiQueryPayStatus(outTradeNo),
    staleTime: 0,
    enabled: enabled && !!outTradeNo,
    refetchInterval: (query) => {
      const status = query.state.data?.tradeState;
      // 如果支付成功或失败，停止轮询
      if (status === 'SUCCESS' || status === 'CLOSED' || status === 'PAYERROR') {
        return false;
      }
      // 每3秒轮询一次
      return 3000;
    },
    refetchIntervalInBackground: true,
  });
}