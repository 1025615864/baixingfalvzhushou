/**
 * 数据格式转换工具
 *
 * 用于统一前后端数据格式映射
 * - 蛇形转驼峰（后端 → 前端）
 * - 驼峰转蛇形（前端 → 后端）
 * - 企业数据格式映射（FR-004）
 * - AI 消息元数据映射（FR-005）
 * - 分页参数转换（FR-015）
 */

/**
 * 将蛇形命名（snake_case）转换为驼峰命名（camelCase）
 * @param str - 蛇形命名字符串
 * @returns 驼峰命名字符串
 */
export function snakeToCamel(str: string): string {
  return str.toLowerCase().replace(/_([a-z0-9])/g, (match: string, letter: string) => letter.toUpperCase());
}

/**
 * 将驼峰命名（camelCase）转换为蛇形命名（snake_case）
 * @param str - 驼峰命名字符串
 * @returns 蛇形命名字符串
 */
export function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, (letter: string) => `_${letter.toLowerCase()}`);
}

/**
 * 将对象的键从蛇形命名转换为驼峰命名（递归）
 * @param obj - 输入对象
 * @returns 转换后的对象
 */
export function snakeKeysToCamel<T>(obj: unknown): T {
  if (obj === null || typeof obj !== 'object') {
    return obj as T;
  }

  if (Array.isArray(obj)) {
    return obj.map(item => snakeKeysToCamel(item)) as T;
  }

  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
    const camelKey = snakeToCamel(key);
    if (typeof value === 'object' && value !== null) {
      result[camelKey] = snakeKeysToCamel(value);
    } else {
      result[camelKey] = value;
    }
  }
  return result as T;
}

/**
 * 将对象的键从驼峰命名转换为蛇形命名（递归）
 * @param obj - 输入对象
 * @returns 转换后的对象
 */
export function camelKeysToSnake<T>(obj: unknown): T {
  if (obj === null || typeof obj !== 'object') {
    return obj as T;
  }

  if (Array.isArray(obj)) {
    return obj.map(item => camelKeysToSnake(item)) as T;
  }

  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
    const snakeKey = camelToSnake(key);
    if (typeof value === 'object' && value !== null) {
      result[snakeKey] = camelKeysToSnake(value);
    } else {
      result[snakeKey] = value;
    }
  }
  return result as T;
}

// ============================================
// 企业数据格式映射（FR-004）
// ============================================

/**
 * 企业响应数据转换（蛇形 → 驼峰）
 * @param data - 后端返回的企业数据
 * @returns 转换后的前端数据
 */
export function convertEnterpriseResponse<T>(data: unknown): T {
  return snakeKeysToCamel<T>(data);
}

/**
 * 企业请求数据转换（驼峰 → 蛇形）
 * @param data - 前端提交的企业数据
 * @returns 转换后的后端数据
 */
export function convertEnterpriseRequest<T>(data: unknown): T {
  return camelKeysToSnake<T>(data);
}

// ============================================
// AI 消息元数据格式映射（FR-005）
// ============================================

/**
 * AI 消息元数据响应转换（蛇形 → 驼峰）
 * @param metadata - 后端返回的元数据
 * @returns 转换后的前端元数据
 */
export function convertMessageMetadata<T>(metadata: unknown): T {
  return snakeKeysToCamel<T>(metadata);
}

/**
 * AI 消息元数据请求转换（驼峰 → 蛇形）
 * @param metadata - 前端提交的元数据
 * @returns 转换后的后端元数据
 */
export function convertMessageMetadataReverse<T>(metadata: unknown): T {
  return camelKeysToSnake<T>(metadata);
}

// ============================================
// 分页参数转换（FR-015）
// ============================================

/**
 * 分页参数转换（分页参数转换）将前端分页参数转换为后端格式
 * 前端：page, pageSize, sortBy, sortOrder
 * 后端：page, page_size, sort_by, sort_order
 * 
 * @param params - 前端分页参数
 * @returns 转换后的后端参数
 */
export function convertPaginationParams(params: {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}): Record<string, string | number> {
  const result: Record<string, string | number> = {};
  
  if (params.page !== undefined) {
    result.page = params.page;
  }
  
  if (params.pageSize !== undefined) {
    result.page_size = params.pageSize;
  }
  
  if (params.sortBy !== undefined) {
    result.sort_by = camelToSnake(params.sortBy);
  }
  
  if (params.sortOrder !== undefined) {
    result.sort_order = params.sortOrder;
  }
  
  return result;
}

/**
 * 分页响应转换
 * 后端返回：page, page_size, total, items
 * 前端使用：page, pageSize, total, items
 * 
 * @param response - 后端分页响应
 * @returns 转换后的前端分页数据
 */
export function convertPaginationResponse<T>(response: {
  page?: number;
  page_size?: number;
  total?: number;
  items?: T[];
}): { page: number; pageSize: number; total: number; items: T[] } {
  return {
    page: response.page ?? 1,
    pageSize: response.page_size ?? 20,
    total: response.total ?? 0,
    items: response.items ?? [],
  };
}

// ============================================
// 日期格式转换
// ============================================

/**
 * ISO 日期字符串转本地日期
 * @param isoString - ISO 格式日期字符串
 * @returns 格式化后的本地日期字符串
 */
export function isoToLocalDate(isoString: string | null | undefined): string {
  if (!isoString) {
    return '';
  }
  const date = new Date(isoString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 格式化日期为 ISO 字符串
 * @param date - Date 对象
 * @returns ISO 格式字符串
 */
export function dateToIso(date: Date): string {
  return date.toISOString();
}

// ============================================
// 导出所有工具
// ============================================
export const transformers = {
  // 命名转换
  snakeToCamel,
  camelToSnake,
  snakeKeysToCamel,
  camelKeysToSnake,
  // 企业数据
  convertEnterpriseResponse,
  convertEnterpriseRequest,
  // AI 消息
  convertMessageMetadata,
  convertMessageMetadataReverse,
  // 分页参数
  convertPaginationParams,
  convertPaginationResponse,
  // 日期格式化
  isoToLocalDate,
  dateToIso,
};