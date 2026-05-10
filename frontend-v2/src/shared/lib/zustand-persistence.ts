/**
 * Zustand 持久化配置
 * 提供统一的 Zustand Store 持久化中间件配置
 */

import { logger } from './logger';

import { StateCreator } from 'zustand';
import { persist, createJSONStorage, PersistOptions } from 'zustand/middleware';

import { EXPIRE_TIMES } from './persistence';

// ==================== 类型定义 ====================

/** 存储类型 */
export type StorageType = 'local' | 'session';

/** 持久化配置选项 */
export interface ZustandPersistenceOptions<T> {
  /** 存储 key（必需） */
  key: string;
  /** 存储类型 */
  storage?: StorageType;
  /** 是否启用版本控制 */
  version?: number;
  /** 迁移函数 */
  migrate?: (persistedState: unknown, version: number) => T;
  /** 部分持久化（只持久化指定字段） */
  partialize?: (state: T) => Partial<T>;
  /** 是否压缩存储（减少 key 数量） */
  compressed?: boolean;
  /** 过期时间（毫秒），0 表示永不过期 */
  expireTime?: number;
  /** 序列化函数 */
  serialize?: (state: T) => string;
  /** 反序列化函数 */
  deserialize?: (str: string) => T;
  /** 是否在 hydration 完成前跳过渲染 */
  skipHydration?: boolean;
  /** 存储变更回调 */
  onRehydrateStorage?: (state: T | undefined) => void;
  /** 合并策略 */
  mergeStrategy?: 'merge' | 'overwrite';
}

/** 带元数据的存储状态 */
interface StorageMetadata {
  /** 数据版本 */
  _version: number;
  /** 存储时间戳 */
  _timestamp: number;
  /** 过期时间戳（可选） */
  _expireAt?: number;
}

/** Store 配置项 */
export interface StoreConfig {
  /** 存储 key 前缀 */
  keyPrefix?: string;
  /** 默认存储类型 */
  defaultStorage?: StorageType;
  /** 默认版本号 */
  defaultVersion?: number;
  /** 是否启用调试 */
  debug?: boolean;
  /** 是否全局启用压缩 */
  enableCompression?: boolean;
}

// ==================== 默认配置 ====================

/** 默认存储 key 前缀 */
const DEFAULT_KEY_PREFIX = 'baixing_';

/** 全局配置 */
let globalConfig: StoreConfig = {
  keyPrefix: DEFAULT_KEY_PREFIX,
  defaultStorage: 'local',
  defaultVersion: 1,
  debug: false,
  enableCompression: false,
};

// ==================== 工具函数 ====================

/**
 * 设置全局配置
 */
export function configureZustandPersistence(config: Partial<StoreConfig>): void {
  globalConfig = { ...globalConfig, ...config };
}

/**
 * 获取当前全局配置
 */
export function getZustandPersistenceConfig(): StoreConfig {
  return { ...globalConfig };
}

/**
 * 创建带前缀的存储 key
 */
function createStorageKey(key: string): string {
  return `${globalConfig.keyPrefix}${key}`;
}

/**
 * 获取存储实例
 */
function getStorage(type: StorageType) {
  return type === 'local' ? localStorage : sessionStorage;
}

/**
 * 检查存储是否过期
 */
function isExpired(data: StorageMetadata | null): boolean {
  if (!data?._expireAt) return false;
  return Date.now() > data._expireAt;
}

/**
 * 深度合并对象
 */
function deepMerge<T>(target: T, source: Partial<T>): T {
  if (typeof target !== 'object' || target === null) {
    return source as T;
  }
  if (typeof source !== 'object' || source === null) {
    return target;
  }

  const result = { ...(target as Record<string, unknown>) } as Record<string, unknown>;
  const targetRecord = target as Record<string, unknown>;
  const sourceRecord = source as Record<string, unknown>;

  for (const key of Object.keys(sourceRecord)) {
    const sourceValue = sourceRecord[key];
    const targetValue = targetRecord[key];

    if (
      typeof sourceValue === 'object' &&
      sourceValue !== null &&
      typeof targetValue === 'object' &&
      targetValue !== null
    ) {
      result[key] = deepMerge(targetValue, sourceValue as Record<string, unknown>);
    } else {
      result[key] = sourceValue;
    }
  }

  return result as T;
}

// ==================== 创建持久化中间件工厂 ====================

/**
 * 创建带过期时间检查的存储
 */
function createExpirableStorage<T>(
  storage: Storage,
  options: ZustandPersistenceOptions<T>
) {
  const { expireTime = 0 } = options;

  return {
    getItem: (key: string): string | null => {
      try {
        const item = storage.getItem(key);
        if (!item) return null;

        const parsed = JSON.parse(item) as StorageMetadata & { state?: unknown };
        
        // 检查是否过期
        if (isExpired(parsed)) {
          storage.removeItem(key);
          return null;
        }

        // 返回状态部分
        return JSON.stringify(parsed.state ?? parsed);
      } catch {
        // 解析失败，返回原始数据
        return storage.getItem(key);
      }
    },
    setItem: (key: string, value: string): void => {
      try {
        const metadata: StorageMetadata & { state: unknown } = {
          _version: options.version ?? globalConfig.defaultVersion ?? 1,
          _timestamp: Date.now(),
          state: JSON.parse(value),
        };

        // 设置过期时间
        if (expireTime > 0) {
          metadata._expireAt = Date.now() + expireTime;
        }

        storage.setItem(key, JSON.stringify(metadata));
      } catch {
        // 存储失败，使用原始方式
        storage.setItem(key, value);
      }
    },
    removeItem: (key: string): void => {
      storage.removeItem(key);
    },
  };
}

/**
 * 创建状态迁移函数
 */
function createMigrateFunction<T>(
  migrate?: (persistedState: unknown, version: number) => T,
  targetVersion: number = globalConfig.defaultVersion ?? 1
) {
  return (persistedState: unknown, version: number): T => {
    if (migrate) {
      return migrate(persistedState, version);
    }

    // 默认迁移策略：版本一致则直接返回
    if (version === targetVersion) {
      return persistedState as T;
    }

    // 版本不匹配时返回空对象（让 store 使用默认值）
    if (globalConfig.debug) {
      logger.warn(
        `版本不匹配: 期望 ${targetVersion}，实际 ${version}`
      );
    }
    return {} as T;
  };
}

/**
 * 创建合并函数
 */
function createMergeFunction<T>(strategy: 'merge' | 'overwrite' = 'merge') {
  return (persistedState: unknown, currentState: T): T => {
    if (!persistedState || typeof persistedState !== 'object') {
      return currentState;
    }

    if (strategy === 'overwrite') {
      return persistedState as T;
    }

    return deepMerge(currentState, persistedState as Partial<T>);
  };
}

// ==================== 主要导出函数 ====================

/**
 * 创建持久化配置选项
 * 用于 Zustand 的 persist 中间件
 * 
 * @example
 * ```tsx
 * import { create } from 'zustand';
 * import { createPersistConfig } from '@/shared/lib/zustand-persistence';
 * 
 * interface MyStore {
 *   count: number;
 *   increment: () => void;
 * }
 * 
 * export const useMyStore = create<MyStore>()(
 *   persist(
 *     (set) => ({
 *       count: 0,
 *       increment: () => set((s) => ({ count: s.count + 1 })),
 *     }),
 *     createPersistConfig<MyStore>('my-store', {
 *       partialize: (state) => ({ count: state.count }),
 *       expireTime: 24 * 60 * 60 * 1000, // 24 小时
 *     })
 *   )
 * );
 * ```
 */
export function createPersistConfig<T extends object>(
  key: string,
  options: Omit<ZustandPersistenceOptions<T>, 'key'> = {}
): PersistOptions<T, Partial<T>> {
  const {
    storage = globalConfig.defaultStorage ?? 'local',
    version = globalConfig.defaultVersion ?? 1,
    migrate,
    partialize,
    expireTime = 0,
    onRehydrateStorage,
  } = options;

  const storageKey = createStorageKey(key);
  const baseStorage = getStorage(storage);

  // 创建带过期检查的存储
  const customStorage = expireTime > 0
    ? createExpirableStorage<T>(baseStorage, { key, ...options, expireTime })
    : baseStorage;

  const config: PersistOptions<T, Partial<T>> = {
    name: storageKey,
    storage: createJSONStorage(() => customStorage),
    version,
    migrate: createMigrateFunction(migrate, version),
    partialize,
    onRehydrateStorage,
    merge: createMergeFunction(options.mergeStrategy),
  };

  return config;
}

/**
 * 持久化 Store 工厂函数
 * 简化持久化 Store 的创建
 * 
 * @example
 * ```tsx
 * interface AuthState {
 *   token: string | null;
 *   setToken: (token: string) => void;
 * }
 * 
 * export const useAuthStore = createPersistedStore<AuthState>(
 *   'auth',
 *   (set) => ({
 *     token: null,
 *     setToken: (token) => set({ token }),
 *   }),
 *   {
 *     partialize: (state) => ({ token: state.token }),
 *     storage: 'session',
 *   }
 * );
 * ```
 */
export function createPersistedStore<T extends object>(
  key: string,
  stateCreator: StateCreator<T, [], []>,
  options: Omit<ZustandPersistenceOptions<T>, 'key'> = {}
) {
  const persistConfig = createPersistConfig<T>(key, options);
  
  return persist(stateCreator, persistConfig);
}

// ==================== 存储管理工具 ====================

/**
 * 清除指定 Store 的持久化数据
 */
export function clearStore(key: string, storage: StorageType = 'local'): void {
  const storageKey = createStorageKey(key);
  getStorage(storage).removeItem(storageKey);
}

/**
 * 清除所有持久化的 Store 数据
 */
export function clearAllStores(storage?: StorageType): void {
  const types: StorageType[] = storage ? [storage] : ['local', 'session'];

  for (const type of types) {
    const storageObj = getStorage(type);
    const keysToRemove: string[] = [];
    const prefix = globalConfig.keyPrefix ?? DEFAULT_KEY_PREFIX;

    for (let i = 0; i < storageObj.length; i++) {
      const key = storageObj.key(i);
      if (key?.startsWith(prefix)) {
        keysToRemove.push(key);
      }
    }

    keysToRemove.forEach((key) => storageObj.removeItem(key));
  }
}

/**
 * 清除过期的持久化数据
 */
export function clearExpiredStores(storage?: StorageType): void {
  const types: StorageType[] = storage ? [storage] : ['local', 'session'];

  for (const type of types) {
    const storageObj = getStorage(type);
    const now = Date.now();
    const keysToRemove: string[] = [];
    const prefix = globalConfig.keyPrefix ?? DEFAULT_KEY_PREFIX;

    for (let i = 0; i < storageObj.length; i++) {
      const key = storageObj.key(i);
      if (!key?.startsWith(prefix)) continue;

      try {
        const item = storageObj.getItem(key);
        if (!item) continue;

        const parsed = JSON.parse(item) as StorageMetadata;
        if (parsed._expireAt && now > parsed._expireAt) {
          keysToRemove.push(key);
        }
      } catch {
        // 解析失败，跳过
      }
    }

    keysToRemove.forEach((key) => storageObj.removeItem(key));
  }
}

/**
 * 获取所有持久化 Store 的 key
 */
export function getStoreKeys(storage?: StorageType): string[] {
  const types: StorageType[] = storage ? [storage] : ['local', 'session'];
  const keys: string[] = [];
  const prefix = globalConfig.keyPrefix ?? DEFAULT_KEY_PREFIX;

  for (const type of types) {
    const storageObj = getStorage(type);
    for (let i = 0; i < storageObj.length; i++) {
      const key = storageObj.key(i);
      if (key?.startsWith(prefix)) {
        // 移除前缀
        keys.push(key.slice(prefix.length));
      }
    }
  }

  return keys;
}

/**
 * 获取持久化 Store 的大小
 */
export function getStoreSize(key: string, storage: StorageType = 'local'): number {
  const storageKey = createStorageKey(key);
  const item = getStorage(storage).getItem(storageKey);
  return item ? new Blob([item]).size : 0;
}

/**
 * 获取所有持久化数据的总大小
 */
export function getTotalStoreSize(storage?: StorageType): number {
  const types: StorageType[] = storage ? [storage] : ['local', 'session'];
  let totalSize = 0;
  const prefix = globalConfig.keyPrefix ?? DEFAULT_KEY_PREFIX;

  for (const type of types) {
    const storageObj = getStorage(type);
    for (let i = 0; i < storageObj.length; i++) {
      const key = storageObj.key(i);
      if (key?.startsWith(prefix)) {
        const item = storageObj.getItem(key);
        if (item) {
          totalSize += new Blob([key + item]).size;
        }
      }
    }
  }

  return totalSize;
}

// ==================== 预定义配置 ====================

/** 认证 Store 持久化配置 */
export const AUTH_PERSIST_CONFIG = {
  key: 'auth-storage',
  storage: 'local' as StorageType,
  version: 1,
  expireTime: EXPIRE_TIMES.WEEK,
};

/** 会员 Store 持久化配置 */
export const MEMBERSHIP_PERSIST_CONFIG = {
  key: 'membership-storage',
  storage: 'local' as StorageType,
  version: 1,
  expireTime: EXPIRE_TIMES.DAY,
};

/** 偏好设置 Store 持久化配置 */
export const PREFERENCES_PERSIST_CONFIG = {
  key: 'preferences-storage',
  storage: 'local' as StorageType,
  version: 1,
  expireTime: EXPIRE_TIMES.MONTH,
};

/** 视频咨询 Store 持久化配置（会话级别） */
export const VIDEO_CONSULTATION_PERSIST_CONFIG = {
  key: 'video-consultation-storage',
  storage: 'session' as StorageType,
  version: 1,
  expireTime: 0, // 永不过期（会话级别）
};

/** 购物车 Store 持久化配置 */
export const CART_PERSIST_CONFIG = {
  key: 'cart-storage',
  storage: 'local' as StorageType,
  version: 1,
  expireTime: EXPIRE_TIMES.WEEK,
};

/** 草稿 Store 持久化配置 */
export const DRAFT_PERSIST_CONFIG = {
  key: 'draft-storage',
  storage: 'local' as StorageType,
  version: 1,
  expireTime: EXPIRE_TIMES.DAY,
};

// ==================== 预定义过期时间 ====================

export { EXPIRE_TIMES };

export default createPersistConfig;