/**
 * System-Config（系统配置）API 层
 */

import apiClient from "@/shared/lib/api/client";

import type {
  ConfigValue,
  GetConfigListRequest,
  GetConfigListResponse,
  GetConfigDetailRequest,
  GetConfigDetailResponse,
  UpdateConfigRequest,
  UpdateConfigResponse,
  BatchUpdateConfigRequest,
  BatchUpdateConfigResponse,
  GetConfigHistoryRequest,
  GetConfigHistoryResponse,
  GetConfigGroupsResponse,
  ExportConfigResponse,
  ImportConfigRequest,
  ImportConfigResponse,
  GetConfigCacheResponse,
  ResetConfigRequest,
  ResetConfigResponse,
} from '../types';

// API 基础路径
const API_BASE = '/system/configs';

/** API 错误响应 */
interface ApiErrorResponse {
  detail?: string;
  message?: string;
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

/**
 * 转换值为 ConfigValue 类型
 */
function toConfigValue(value: unknown): ConfigValue {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return value;
  }
  if (Array.isArray(value)) {
    return value as string[] | number[];
  }
  if (typeof value === 'object') {
    return value as Record<string, unknown>;
  }
  return String(value);
}

/**
 * 获取配置列表
 */
export async function apiGetConfigList(
  params: GetConfigListRequest = {}
): Promise<GetConfigListResponse> {
  const searchParams = new URLSearchParams();
  if (params.group) searchParams.set('group', params.group);
  if (params.search) searchParams.set('search', params.search);
  if (params.editable !== undefined) searchParams.set('editable', String(params.editable));

  const url = `${API_BASE}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取配置列表失败' }));
    throw new Error(getErrorMessage(error, '获取配置列表失败'));
  }

  const data = await safeJson<{
    configs: Array<{
      id: string;
      key: string;
      value: unknown;
      default_value: unknown;
      description: string;
      type: string;
      options?: string[];
      group: string;
      is_editable: boolean;
      is_sensitive: boolean;
      updated_at: string;
      updated_by?: string;
    }>;
    groups: Array<{
      id: string;
      name: string;
      description: string;
      icon?: string;
      order: number;
      config_count: number;
    }>;
  }>(response);

  return {
    configs: data.configs.map((item) => ({
      id: item.id,
      key: item.key,
      value: toConfigValue(item.value),
      defaultValue: toConfigValue(item.default_value),
      description: item.description,
      type: item.type as 'string' | 'number' | 'boolean' | 'json' | 'array' | 'select',
      options: item.options,
      group: item.group,
      isEditable: item.is_editable,
      isSensitive: item.is_sensitive,
      updatedAt: item.updated_at,
      updatedBy: item.updated_by,
    })),
    groups: data.groups.map((item) => ({
      id: item.id,
      name: item.name,
      description: item.description,
      icon: item.icon,
      order: item.order,
      configCount: item.config_count,
    })),
  };
}

/**
 * 获取配置详情
 */
export async function apiGetConfigDetail(
  request: GetConfigDetailRequest
): Promise<GetConfigDetailResponse> {
  const response = await fetch(`${API_BASE}/${request.configId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取配置详情失败' }));
    throw new Error(getErrorMessage(error, '获取配置详情失败'));
  }

  const data = await safeJson<{
    config: {
      id: string;
      key: string;
      value: unknown;
      default_value: unknown;
      description: string;
      type: string;
      options?: string[];
      group: string;
      is_editable: boolean;
      is_sensitive: boolean;
      updated_at: string;
      updated_by?: string;
    };
  }>(response);

  return {
    config: {
      id: data.config.id,
      key: data.config.key,
      value: toConfigValue(data.config.value),
      defaultValue: toConfigValue(data.config.default_value),
      description: data.config.description,
      type: data.config.type as 'string' | 'number' | 'boolean' | 'json' | 'array' | 'select',
      options: data.config.options,
      group: data.config.group,
      isEditable: data.config.is_editable,
      isSensitive: data.config.is_sensitive,
      updatedAt: data.config.updated_at,
      updatedBy: data.config.updated_by,
    },
  };
}

/**
 * 更新配置
 */
export async function apiUpdateConfig(
  request: UpdateConfigRequest
): Promise<UpdateConfigResponse> {
  const response = await apiClient.put<{
    config: {
      id: string;
      key: string;
      value: unknown;
      default_value: unknown;
      description: string;
      type: string;
      options?: string[];
      group: string;
      is_editable: boolean;
      is_sensitive: boolean;
      updated_at: string;
      updated_by?: string;
    };
    history: {
      id: string;
      config_id: string;
      config_key: string;
      old_value: unknown;
      new_value: unknown;
      updated_by: string;
      updated_by_name?: string;
      updated_at: string;
      change_reason?: string;
    };
  }>(`${API_BASE}/${request.configId}`, {
    value: request.value,
    reason: request.reason,
  });

  const data = response.data;

  return {
    config: {
      id: data.config.id,
      key: data.config.key,
      value: toConfigValue(data.config.value),
      defaultValue: toConfigValue(data.config.default_value),
      description: data.config.description,
      type: data.config.type as 'string' | 'number' | 'boolean' | 'json' | 'array' | 'select',
      options: data.config.options,
      group: data.config.group,
      isEditable: data.config.is_editable,
      isSensitive: data.config.is_sensitive,
      updatedAt: data.config.updated_at,
      updatedBy: data.config.updated_by,
    },
    history: {
      id: data.history.id,
      configId: data.history.config_id,
      configKey: data.history.config_key,
      oldValue: toConfigValue(data.history.old_value),
      newValue: toConfigValue(data.history.new_value),
      updatedBy: data.history.updated_by,
      updatedByName: data.history.updated_by_name,
      updatedAt: data.history.updated_at,
      changeReason: data.history.change_reason,
    },
  };
}

/**
 * 批量更新配置
 */
export async function apiBatchUpdateConfig(
  request: BatchUpdateConfigRequest
): Promise<BatchUpdateConfigResponse> {
  const response = await apiClient.put<{
    updated: Array<{
      id: string;
      key: string;
      value: unknown;
      default_value: unknown;
      description: string;
      type: string;
      options?: string[];
      group: string;
      is_editable: boolean;
      is_sensitive: boolean;
      updated_at: string;
      updated_by?: string;
    }>;
    histories: Array<{
      id: string;
      config_id: string;
      config_key: string;
      old_value: unknown;
      new_value: unknown;
      updated_by: string;
      updated_by_name?: string;
      updated_at: string;
      change_reason?: string;
    }>;
  }>(`${API_BASE}/batch`, {
    changes: request.changes.map((change) => ({
      config_id: change.configId,
      value: change.value,
      reason: change.reason,
    })),
  });

  const data = response.data;

  return {
    updated: data.updated.map((item) => ({
      id: item.id,
      key: item.key,
      value: toConfigValue(item.value),
      defaultValue: toConfigValue(item.default_value),
      description: item.description,
      type: item.type as 'string' | 'number' | 'boolean' | 'json' | 'array' | 'select',
      options: item.options,
      group: item.group,
      isEditable: item.is_editable,
      isSensitive: item.is_sensitive,
      updatedAt: item.updated_at,
      updatedBy: item.updated_by,
    })),
    histories: data.histories.map((item) => ({
      id: item.id,
      configId: item.config_id,
      configKey: item.config_key,
      oldValue: toConfigValue(item.old_value),
      newValue: toConfigValue(item.new_value),
      updatedBy: item.updated_by,
      updatedByName: item.updated_by_name,
      updatedAt: item.updated_at,
      changeReason: item.change_reason,
    })),
  };
}

/**
 * 获取配置历史
 */
export async function apiGetConfigHistory(
  params: GetConfigHistoryRequest = {}
): Promise<GetConfigHistoryResponse> {
  const searchParams = new URLSearchParams();
  if (params.configId) searchParams.set('config_id', params.configId);
  if (params.group) searchParams.set('group', params.group);
  if (params.limit) searchParams.set('limit', String(params.limit));
  if (params.offset) searchParams.set('offset', String(params.offset));
  if (params.startDate) searchParams.set('start_date', params.startDate);
  if (params.endDate) searchParams.set('end_date', params.endDate);

  const url = `${API_BASE}/history${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取配置历史失败' }));
    throw new Error(getErrorMessage(error, '获取配置历史失败'));
  }

  const data = await safeJson<{
    histories: Array<{
      id: string;
      config_id: string;
      config_key: string;
      old_value: unknown;
      new_value: unknown;
      updated_by: string;
      updated_by_name?: string;
      updated_at: string;
      change_reason?: string;
    }>;
    total: number;
  }>(response);

  return {
    histories: data.histories.map((item) => ({
      id: item.id,
      configId: item.config_id,
      configKey: item.config_key,
      oldValue: toConfigValue(item.old_value),
      newValue: toConfigValue(item.new_value),
      updatedBy: item.updated_by,
      updatedByName: item.updated_by_name,
      updatedAt: item.updated_at,
      changeReason: item.change_reason,
    })),
    total: data.total,
  };
}

/**
 * 获取配置分组列表
 */
export async function apiGetConfigGroups(): Promise<GetConfigGroupsResponse> {
  const response = await fetch(`${API_BASE}/groups`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取配置分组失败' }));
    throw new Error(getErrorMessage(error, '获取配置分组失败'));
  }

  const data = await safeJson<{
    groups: Array<{
      id: string;
      name: string;
      description: string;
      icon?: string;
      order: number;
      config_count: number;
    }>;
  }>(response);

  return {
    groups: data.groups.map((item) => ({
      id: item.id,
      name: item.name,
      description: item.description,
      icon: item.icon,
      order: item.order,
      configCount: item.config_count,
    })),
  };
}

/**
 * 导出配置
 */
export async function apiExportConfig(): Promise<ExportConfigResponse> {
  const response = await apiClient.get<ExportConfigResponse>(`${API_BASE}/export`);
  return response.data;
}

/**
 * 重置配置为默认值
 */
export async function apiResetConfig(
  request: ResetConfigRequest
): Promise<ResetConfigResponse> {
  const response = await apiClient.post<{
    config: {
      id: string;
      key: string;
      value: unknown;
      default_value: unknown;
      description: string;
      type: string;
      options?: string[];
      group: string;
      is_editable: boolean;
      is_sensitive: boolean;
      updated_at: string;
      updated_by?: string;
    };
    history: {
      id: string;
      config_id: string;
      config_key: string;
      old_value: unknown;
      new_value: unknown;
      updated_by: string;
      updated_at: string;
    };
  }>(`${API_BASE}/${request.configId}/reset`, {
    reason: request.reason,
  });

  const data = response.data;

  return {
    config: {
      id: data.config.id,
      key: data.config.key,
      value: toConfigValue(data.config.value),
      defaultValue: toConfigValue(data.config.default_value),
      description: data.config.description,
      type: data.config.type as 'string' | 'number' | 'boolean' | 'json' | 'array' | 'select',
      options: data.config.options,
      group: data.config.group,
      isEditable: data.config.is_editable,
      isSensitive: data.config.is_sensitive,
      updatedAt: data.config.updated_at,
      updatedBy: data.config.updated_by,
    },
    history: {
      id: data.history.id,
      configId: data.history.config_id,
      configKey: data.history.config_key,
      oldValue: toConfigValue(data.history.old_value),
      newValue: toConfigValue(data.history.new_value),
      updatedBy: data.history.updated_by,
      updatedAt: data.history.updated_at,
    },
  };
}

/**
 * 导入配置
 */
export async function apiImportConfig(
  request: ImportConfigRequest
): Promise<ImportConfigResponse> {
  const response = await apiClient.post<ImportConfigResponse>(`${API_BASE}/import`, {
    import_data: request.importData,
    overwrite: request.overwrite,
  });
  return response.data;
}

/**
 * 刷新配置缓存
 */
export async function apiRefreshConfigCache(): Promise<GetConfigCacheResponse> {
  const response = await apiClient.post<GetConfigCacheResponse>(`${API_BASE}/cache/refresh`);
  return response.data;
}

/**
 * 获取配置缓存信息
 */
export async function apiGetConfigCache(): Promise<GetConfigCacheResponse> {
  const response = await fetch(`${API_BASE}/cache`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await safeJson<ApiErrorResponse>(response).catch(() => ({ detail: '获取配置缓存信息失败' }));
    throw new Error(getErrorMessage(error, '获取配置缓存信息失败'));
  }

  const data = await safeJson<GetConfigCacheResponse>(response);
  return data;
}
