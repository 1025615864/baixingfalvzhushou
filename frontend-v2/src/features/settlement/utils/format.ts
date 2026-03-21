/**
 * Settlement 模块工具函数
 */

/**
 * 格式化货币
 */
export function formatCurrency(value: number): string {
  return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * 格式化日期
 */
export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('zh-CN');
}

/**
 * 格式化日期时间
 */
export function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString('zh-CN');
}