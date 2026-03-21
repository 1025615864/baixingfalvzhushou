/**
 * AI配置管理类型定义
 */

// ==================== AI提供商类型 ====================

/** AI提供商信息 */
export interface AIProvider {
  id: string;
  name: string;
  models: string[];
}

// ==================== AI配置相关类型 ====================

/** 健康状态 */
export type HealthStatus = 'unknown' | 'healthy' | 'degraded' | 'unhealthy';

/** AI模型配置列表项 */
export interface AIModelConfigItem {
  id: number;
  name: string;
  provider: string;
  model_id: string;
  base_url: string | null;
  enabled: boolean;
  weight: number;
  priority: number;
  is_primary: boolean;
  max_tokens: number | null;
  temperature: number | null;
  api_key_configured: boolean;
  call_count: number;
  error_count: number;
  last_used_at: string | null;
  health_status: HealthStatus;
  last_health_check: string | null;
  health_check_message: string | null;
  created_at: string;
  updated_at: string;
}

/** AI模型配置统计 */
export interface AIModelConfigStats {
  total: number;
  enabled: number;
  healthy: number;
  degraded: number;
  unhealthy: number;
  unknown: number;
  total_calls: number;
  total_errors: number;
}

/** AI模型配置列表响应 */
export interface AIModelConfigListResponse {
  items: AIModelConfigItem[];
  total: number;
}

/** 创建AI模型配置请求 */
export interface CreateAIModelConfigRequest {
  name: string;
  provider?: string;
  model_id: string;
  api_key?: string;
  base_url?: string;
  enabled?: boolean;
  weight?: number;
  priority?: number;
  is_primary?: boolean;
  max_tokens?: number;
  temperature?: number;
}

/** 更新AI模型配置请求 */
export interface UpdateAIModelConfigRequest {
  name?: string;
  provider?: string;
  model_id?: string;
  api_key?: string;
  base_url?: string;
  enabled?: boolean;
  weight?: number;
  priority?: number;
  is_primary?: boolean;
  max_tokens?: number;
  temperature?: number;
}

/** 批量操作请求 */
export interface BatchOperationRequest {
  ids: number[];
  action: 'enable' | 'disable' | 'delete';
}

/** 批量操作响应 */
export interface BatchOperationResponse {
  success: number;
  failed: number;
  message: string;
}

/** 测试配置响应 */
export interface TestConfigResponse {
  status: 'success' | 'failed';
  message: string;
  model_id: string;
  provider: string;
  latency_ms: number;
  health_status: HealthStatus;
}

/** 健康检查响应 */
export interface HealthCheckResponse {
  success: boolean;
  health_status: HealthStatus;
  health_check_message: string | null;
  latency_ms: number;
  checked_at: string | null;
}

/** 单个配置统计响应 */
export interface ConfigStatsResponse {
  id: number;
  name: string;
  provider: string;
  model_id: string;
  call_count: number;
  error_count: number;
  error_rate: number;
  last_used_at: string | null;
  health_status: HealthStatus;
  last_health_check: string | null;
  health_check_message: string | null;
}

// ==================== 组件Props类型 ====================

/** AI配置表格Props */
export interface AIConfigTableProps {
  configs: AIModelConfigItem[];
  loading: boolean;
  onEdit: (config: AIModelConfigItem) => void;
  onDelete: (configId: number) => void;
  onToggleEnabled: (configId: number, currentStatus: boolean) => void;
  onTest: (configId: number) => void;
  onHealthCheck: (configId: number) => void;
  testingIds: Set<number>;
  healthCheckingIds: Set<number>;
}

/** AI配置表单Props */
export interface AIConfigFormProps {
  visible: boolean;
  config: AIModelConfigItem | null;
  providers: AIProvider[];
  onCancel: () => void;
  onConfirm: (data: CreateAIModelConfigRequest | UpdateAIModelConfigRequest) => void;
  loading: boolean;
}

/** AI配置统计卡片Props */
export interface AIConfigStatsCardProps {
  stats: AIModelConfigStats | null;
  loading: boolean;
}
