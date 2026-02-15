/**
 * System-Config（系统配置）类型定义
 */

// ==================== 核心类型 ====================

/** 配置值类型 */
export type ConfigValue = string | number | boolean | string[] | number[] | Record<string, unknown> | null;

/** 配置项类型 */
export interface ConfigItem {
  id: string;
  key: string;
  value: ConfigValue;
  defaultValue: ConfigValue;
  description: string;
  type: 'string' | 'number' | 'boolean' | 'json' | 'array' | 'select';
  options?: string[];
  group: string;
  isEditable: boolean;
  isSensitive: boolean;
  updatedAt: string;
  updatedBy?: string;
}

/** 配置分组类型 */
export interface ConfigGroup {
  id: string;
  name: string;
  description: string;
  icon?: string;
  order: number;
  configCount: number;
}

/** 配置历史类型 */
export interface ConfigHistory {
  id: string;
  configId: string;
  configKey: string;
  oldValue: ConfigValue;
  newValue: ConfigValue;
  updatedBy: string;
  updatedByName?: string;
  updatedAt: string;
  changeReason?: string;
}

/** 配置变更记录 */
export interface ConfigChange {
  configId: string;
  key: string;
  oldValue: ConfigValue;
  newValue: ConfigValue;
}

// ==================== API 请求/响应类型 ====================

/** 获取配置列表请求 */
export interface GetConfigListRequest {
  group?: string;
  search?: string;
  editable?: boolean;
}

/** 获取配置列表响应 */
export interface GetConfigListResponse {
  configs: ConfigItem[];
  groups: ConfigGroup[];
}

/** 获取配置详情请求 */
export interface GetConfigDetailRequest {
  configId: string;
}

/** 获取配置详情响应 */
export interface GetConfigDetailResponse {
  config: ConfigItem;
}

/** 更新配置请求 */
export interface UpdateConfigRequest {
  configId: string;
  value: ConfigValue;
  reason?: string;
}

/** 更新配置响应 */
export interface UpdateConfigResponse {
  config: ConfigItem;
  history: ConfigHistory;
}

/** 批量更新配置请求 */
export interface BatchUpdateConfigRequest {
  changes: Array<{
    configId: string;
    value: ConfigValue;
    reason?: string;
  }>;
}

/** 批量更新配置响应 */
export interface BatchUpdateConfigResponse {
  updated: ConfigItem[];
  histories: ConfigHistory[];
}

/** 获取配置历史请求 */
export interface GetConfigHistoryRequest {
  configId?: string;
  group?: string;
  limit?: number;
  offset?: number;
  startDate?: string;
  endDate?: string;
}

/** 获取配置历史响应 */
export interface GetConfigHistoryResponse {
  histories: ConfigHistory[];
  total: number;
}

/** 获取配置分组列表响应 */
export interface GetConfigGroupsResponse {
  groups: ConfigGroup[];
}

/** 重置配置请求 */
export interface ResetConfigRequest {
  configId: string;
  reason?: string;
}

/** 重置配置响应 */
export interface ResetConfigResponse {
  config: ConfigItem;
  history: ConfigHistory;
}

/** 导出配置响应 */
export interface ExportConfigResponse {
  exportData: string;
  filename: string;
}

/** 导入配置请求 */
export interface ImportConfigRequest {
  importData: string;
  overwrite?: boolean;
}

/** 导入配置响应 */
export interface ImportConfigResponse {
  imported: number;
  updated: number;
  skipped: number;
  errors: string[];
}

/** 配置验证结果 */
export interface ConfigValidationResult {
  valid: boolean;
  errors: Array<{
    configId: string;
    key: string;
    message: string;
  }>;
}

/** 配置缓存信息 */
export interface ConfigCacheInfo {
  cached: boolean;
  cachedAt?: string;
  expiresAt?: string;
  version: string;
}

/** 获取配置缓存信息响应 */
export interface GetConfigCacheResponse {
  cache: ConfigCacheInfo;
}