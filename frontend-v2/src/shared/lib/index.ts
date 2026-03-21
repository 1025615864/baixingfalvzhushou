/**
 * 共享工具库统一导出
 * 提供便捷的模块访问入口
 */

// ==================== 持久化工具 ====================

// 核心持久化工具
export {
  Persistence,
  localPersistence,
  sessionPersistence,
  EXPIRE_TIMES,
  type PersistenceOptions,
  type StorageStats,
} from './persistence';

// 用户偏好设置持久化
export {
  preferencesPersistence,
  createPreferencesHook,
  selectTheme,
  selectLanguage,
  selectFontSize,
  selectSidebarCollapsed,
  selectNotificationEnabled,
  selectAnimationEnabled,
  selectPageSize,
  selectShowOnboarding,
  FONT_SIZE_MAP,
  PAGE_SIZE_OPTIONS,
  type UserPreferences,
  type ThemeMode,
  type Language,
  type FontSize,
} from './preferences';

// 表单持久化
export {
  useFormPersistence,
  useFormField,
  useMultiFormPersistence,
  clearFormData,
  clearAllFormData,
  getSavedFormKeys,
  hasSavedFormData,
  type FormPersistenceOptions,
  type FormPersistenceReturn,
} from './form-persistence';

// Zustand 持久化配置
export {
  createPersistConfig,
  createPersistedStore,
  configureZustandPersistence,
  getZustandPersistenceConfig,
  clearStore,
  clearAllStores,
  clearExpiredStores,
  getStoreKeys,
  getStoreSize,
  getTotalStoreSize,
  AUTH_PERSIST_CONFIG,
  MEMBERSHIP_PERSIST_CONFIG,
  PREFERENCES_PERSIST_CONFIG,
  VIDEO_CONSULTATION_PERSIST_CONFIG,
  CART_PERSIST_CONFIG,
  DRAFT_PERSIST_CONFIG,
  type StorageType,
  type ZustandPersistenceOptions,
  type StoreConfig,
} from './zustand-persistence';

// ==================== API 工具 ====================

export {
  apiClient,
  apiClientInstance,
  api,
  unwrapResponse,
  unwrapPaginatedResponse,
  ApiErrorClass,
  type ApiError,
} from './api/client';

// ==================== 安全工具 ====================

export {
  getToken,
  setToken,
  removeToken,
  getRefreshToken,
  setRefreshToken,
  clearAuthStorage,
} from './security/tokenStorage';