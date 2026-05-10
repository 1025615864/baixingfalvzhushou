// ============================================
// 本地存储持久化工具
// ============================================

import { logger } from '../logger';

/**
 * 存储类型
 */
export type StorageType = 'localStorage' | 'sessionStorage';

/**
 * 存储选项
 */
interface StorageOptions<T> {
  /** 存储键名 */
  key: string;
  /** 默认值 */
  defaultValue: T;
  /** 存储类型 */
  storage?: StorageType;
  /** 序列化函数 */
  serialize?: (value: T) => string;
  /** 反序列化函数 */
  deserialize?: (value: string) => T;
  /** 过期时间（毫秒） */
  expire?: number;
}

/**
 * 存储项元数据
 */
interface StorageMetadata {
  timestamp: number;
  expire?: number;
}

/**
 * 带元数据的存储值
 */
interface StorageValue<T> {
  value: T;
  meta: StorageMetadata;
}

/**
 * 创建持久化存储
 */
export function createPersistence<T>(options: StorageOptions<T>) {
  const {
    key,
    defaultValue,
    storage = 'localStorage',
    serialize = JSON.stringify,
    deserialize = JSON.parse,
    expire,
  } = options;

  const storageEngine = typeof window !== 'undefined'
    ? window[storage]
    : undefined;

  /**
   * 获取完整键名（添加命名空间）
   */
  const getFullKey = (): string => `baixing:${key}`;

  /**
   * 获取存储值
   */
  const get = (): T => {
    if (!storageEngine) return defaultValue;

    try {
      const item = storageEngine.getItem(getFullKey());
      if (!item) return defaultValue;

      const parsed = deserialize(item) as StorageValue<T>;

      // 检查是否过期
      if (parsed.meta?.expire && Date.now() > parsed.meta.expire) {
        remove();
        return defaultValue;
      }

      return parsed.value;
    } catch {
      return defaultValue;
    }
  };

  /**
   * 设置存储值
   */
  const set = (value: T): void => {
    if (!storageEngine) return;

    try {
      const data: StorageValue<T> = {
        value,
        meta: {
          timestamp: Date.now(),
          expire: expire ? Date.now() + expire : undefined,
        },
      };
      storageEngine.setItem(getFullKey(), serialize(data));
    } catch (error) {
      logger.error('Storage set error:', error);
    }
  };

  /**
   * 移除存储值
   */
  const remove = (): void => {
    if (!storageEngine) return;
    storageEngine.removeItem(getFullKey());
  };

  /**
   * 检查是否存在
   */
  const exists = (): boolean => {
    if (!storageEngine) return false;
    return storageEngine.getItem(getFullKey()) !== null;
  };

  return {
    get,
    set,
    remove,
    exists,
  };
}

/**
 * 清除所有应用存储
 */
export function clearAllAppStorage(storage: StorageType = 'localStorage'): void {
  if (typeof window === 'undefined') return;

  const storageEngine = window[storage];
  const keysToRemove: string[] = [];

  for (let i = 0; i < storageEngine.length; i++) {
    const key = storageEngine.key(i);
    if (key?.startsWith('baixing:')) {
      keysToRemove.push(key);
    }
  }

  keysToRemove.forEach((key) => storageEngine.removeItem(key));
}