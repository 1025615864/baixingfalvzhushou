/**
 * WeChat（微信生态）类型定义
 */

// ==================== 核心类型 ====================

/** 微信账号类型 */
export type WechatAccountType = 'official' | 'mini_program';

/** 微信绑定状态 */
export type WechatBindStatus = 'bound' | 'unbound' | 'pending';

/** 公众号关注状态 */
export type OfficialAccountFollowStatus = 'followed' | 'unfollowed' | 'unknown';

// ==================== 微信用户绑定信息 ====================

/** 微信用户信息 */
export interface WechatUserInfo {
  /** 微信OpenID */
  openid: string;
  /** 微信UnionID（可选） */
  unionid?: string;
  /** 用户昵称 */
  nickname?: string;
  /** 用户头像URL */
  avatarUrl?: string;
  /** 性别：1-男，2-女，0-未知 */
  gender?: 0 | 1 | 2;
  /** 国家 */
  country?: string;
  /** 省份 */
  province?: string;
  /** 城市 */
  city?: string;
}

/** 微信用户绑定信息 */
export interface WechatBindInfo {
  /** 绑定ID */
  id: string;
  /** 用户ID */
  userId: number;
  /** 微信账号类型 */
  accountType: WechatAccountType;
  /** 绑定状态 */
  bindStatus: WechatBindStatus;
  /** 微信用户信息 */
  wechatInfo?: WechatUserInfo;
  /** 绑定时间 */
  boundAt?: string;
  /** 最后更新时间 */
  updatedAt: string;
}

// ==================== 公众号关注状态 ====================

/** 公众号信息 */
export interface OfficialAccountInfo {
  /** 公众号ID */
  id: string;
  /** 公众号名称 */
  name: string;
  /** 公众号简介 */
  description?: string;
  /** 公众号头像 */
  avatarUrl?: string;
  /** 二维码URL */
  qrCodeUrl?: string;
}

/** 公众号关注状态 */
export interface OfficialAccountFollowState {
  /** 公众号信息 */
  account: OfficialAccountInfo;
  /** 关注状态 */
  followStatus: OfficialAccountFollowStatus;
  /** 关注时间 */
  followedAt?: string;
  /** 是否需要显示二维码 */
  showQrCode: boolean;
}

// ==================== 小程序登录凭证 ====================

/** 小程序登录凭证 */
export interface MiniProgramLoginCode {
  /** 临时登录凭证 */
  code: string;
  /** 过期时间（秒） */
  expiresIn: number;
  /** 获取时间 */
  obtainedAt: string;
}

/** 小程序登录结果 */
export interface MiniProgramLoginResult {
  /** 登录是否成功 */
  success: boolean;
  /** 会话令牌 */
  sessionToken?: string;
  /** 用户信息 */
  userInfo?: WechatUserInfo;
  /** 错误信息 */
  errorMessage?: string;
}

// ==================== 微信分享配置 ====================

/** 微信分享类型 */
export type WechatShareType = 'timeline' | 'session' | 'qq' | 'weibo';

/** 微信分享配置 */
export interface WechatShareConfig {
  /** 分享标题 */
  title: string;
  /** 分享描述 */
  description?: string;
  /** 分享链接 */
  link: string;
  /** 分享图片URL */
  imgUrl?: string;
  /** 分享类型 */
  type?: WechatShareType;
  /** 配置签名 */
  signature?: WechatJsSdkSignature;
}

/** JSSDK签名信息 */
export interface WechatJsSdkSignature {
  /** 应用ID */
  appId: string;
  /** 时间戳 */
  timestamp: number;
  /** 随机字符串 */
  nonceStr: string;
  /** 签名 */
  signature: string;
}

/** 分享结果 */
export interface WechatShareResult {
  /** 分享是否成功 */
  success: boolean;
  /** 分享类型 */
  shareType: WechatShareType;
  /** 分享时间 */
  sharedAt?: string;
}

// ==================== 微信支付配置 ====================

/** 微信支付类型 */
export type WechatPayType = 'jsapi' | 'native' | 'app' | 'h5';

/** 微信支付配置 */
export interface WechatPayConfig {
  /** 应用ID */
  appId: string;
  /** 时间戳 */
  timeStamp: string;
  /** 随机字符串 */
  nonceStr: string;
  /** 订单详情扩展字符串 */
  package: string;
  /** 签名方式 */
  signType: 'RSA' | 'MD5';
  /** 签名 */
  paySign: string;
}

/** 统一下单请求 */
export interface UnifiedOrderRequest {
  /** 订单描述 */
  body: string;
  /** 订单总金额（分） */
  totalFee: number;
  /** 商户订单号 */
  outTradeNo: string;
  /** 商品ID */
  productId?: string;
  /** 附加数据 */
  attach?: string;
  /** 终端IP */
  spbillCreateIp?: string;
  /** 支付类型 */
  tradeType: WechatPayType;
  /** 用户标识（JSAPI支付必填） */
  openid?: string;
  /** 通知地址 */
  notifyUrl?: string;
}

/** 统一下单响应 */
export interface UnifiedOrderResponse {
  /** 预支付交易会话标识 */
  prepayId: string;
  /** 支付配置 */
  payConfig: WechatPayConfig;
  /** 订单号 */
  orderNo: string;
  /** 二维码链接（NATIVE支付） */
  codeUrl?: string;
  /** 支付跳转链接（H5支付） */
  mwebUrl?: string;
}

/** 支付结果 */
export interface WechatPayResult {
  /** 支付是否成功 */
  success: boolean;
  /** 微信支付订单号 */
  transactionId?: string;
  /** 商户订单号 */
  outTradeNo: string;
  /** 支付完成时间 */
  timeEnd?: string;
  /** 错误代码 */
  errCode?: string;
  /** 错误描述 */
  errCodeDes?: string;
}

// ==================== API 请求/响应类型 ====================

/** 获取微信绑定状态请求 */
export interface GetWechatBindStatusRequest {
  userId: number;
  accountType?: WechatAccountType;
}

/** 获取微信绑定状态响应 */
export interface GetWechatBindStatusResponse {
  bindInfo: WechatBindInfo[];
}

/** 绑定微信账号请求 */
export interface BindWechatRequest {
  userId: number;
  accountType: WechatAccountType;
  /** 微信授权码 */
  authCode: string;
  /** 状态校验参数 */
  state?: string;
}

/** 绑定微信账号响应 */
export interface BindWechatResponse {
  success: boolean;
  bindInfo: WechatBindInfo;
}

/** 解绑微信账号请求 */
export interface UnbindWechatRequest {
  userId: number;
  accountType: WechatAccountType;
  bindId: string;
}

/** 解绑微信账号响应 */
export interface UnbindWechatResponse {
  success: boolean;
  message: string;
}

/** 获取公众号关注二维码请求 */
export interface GetOfficialAccountQrCodeRequest {
  userId: number;
  /** 场景值 */
  scene?: string;
  /** 过期时间（秒，最大2592000即30天） */
  expireSeconds?: number;
}

/** 获取公众号关注二维码响应 */
export interface GetOfficialAccountQrCodeResponse {
  /** 二维码URL */
  qrCodeUrl: string;
  /** 场景值 */
  scene: string;
  /** 过期时间 */
  expireAt: string;
  /** ticket */
  ticket: string;
}

/** 小程序登录请求 */
export interface MiniProgramLoginRequest {
  /** 临时登录凭证 */
  code: string;
  /** 加密数据（可选，用于获取用户信息） */
  encryptedData?: string;
  /** 加密算法初始向量 */
  iv?: string;
}

/** 小程序登录响应 */
export interface MiniProgramLoginResponse {
  success: boolean;
  sessionToken: string;
  openid: string;
  unionid?: string;
  userInfo?: WechatUserInfo;
}

/** 获取微信分享配置请求 */
export interface GetShareConfigRequest {
  /** 当前页面URL */
  url: string;
  /** 分享类型列表 */
  shareTypes?: WechatShareType[];
}

/** 获取微信分享配置响应 */
export interface GetShareConfigResponse {
  config: WechatShareConfig;
}

/** 微信支付统一下单请求 */
export interface WechatUnifiedOrderRequest extends UnifiedOrderRequest {
  userId: number;
}

/** 微信支付统一下单响应 */
export interface WechatUnifiedOrderResponse extends UnifiedOrderResponse {
  /** 订单创建时间 */
  createdAt: string;
}

/** 查询支付状态请求 */
export interface QueryPayStatusRequest {
  outTradeNo: string;
}

/** 查询支付状态响应 */
export interface QueryPayStatusResponse {
  /** 支付状态：SUCCESS-支付成功，REFUND-转入退款，NOTPAY-未支付，CLOSED-已关闭，REVOKED-已撤销，USERPAYING-用户支付中，PAYERROR-支付失败 */
  tradeState: 'SUCCESS' | 'REFUND' | 'NOTPAY' | 'CLOSED' | 'REVOKED' | 'USERPAYING' | 'PAYERROR';
  /** 支付结果 */
  payResult?: WechatPayResult;
  /** 订单信息 */
  orderInfo?: {
    body: string;
    totalFee: number;
    outTradeNo: string;
    timeEnd?: string;
  };
}

/** 微信JSAPI配置请求 */
export interface GetJsApiConfigRequest {
  /** 当前页面URL */
  url: string;
  /** 需要使用的JSAPI列表 */
  jsApiList?: string[];
}

/** 微信JSAPI配置响应 */
export interface GetJsApiConfigResponse {
  appId: string;
  timestamp: number;
  nonceStr: string;
  signature: string;
  jsApiList: string[];
}