/**
 * 统一持久化存储工具
 * 提供类型安全的本地存储操作，支持过期时间和多种存储后端
 */

// ==================== 类型定义 ====================

/** 持久化存储选项 */
export interface PersistenceOptions {
  /** 存储键名 */
  key: string;
  /** 存储类型：localStorage 或 sessionStorage */
  storage?: 'local' | 'session';
  /** 过期时间（毫秒） */
  expire?: number;
  /** 是否启用加密（简单混淆） */
  encrypt?: boolean;
}

/** 带过期时间的数据结构 */
interface ExpirableData<T> {
  /** 存储的值 */
  value: T;
  /** 过期时间戳（毫秒） */
  expireAt: number | null;
  /** 创建时间戳 */
  createdAt: number;
  /** 数据版本号 */
  version: number;
}

/** 存储统计信息 */
export interface StorageStats {
  /** 总使用大小（字节） */
  totalSize: number;
  /** 存储项数量 */
  itemCount: number;
  /** 最旧的项时间 */
  oldestItem: number | null;
}

// ==================== 常量定义 ====================

/** 当前数据版本 */
const CURRENT_VERSION = 1;

/** 默认存储前缀 */
const DEFAULT_PREFIX = 'baixing_';

/** 简单加密密钥（用于基本混淆，非安全加密） */
const OBFUSCATION_KEY = 0x5a;

// ==================== 工具函数 ====================

/**
 * 获取存储实例
 */
function getStorage(storageType: 'local' | 'session'): Storage | null {
  try {
    const storage = storageType === 'local' ? localStorage : sessionStorage;
    // 测试存储是否可用
    const testKey = '__storage_test__';
    storage.setItem(testKey, testKey);
    storage.removeItem(testKey);
    return storage;
  } catch {
     
    console.warn(`[Persistence] ${storageType}Storage 不可用`);
    return null;
  }
}

/**
 * 简单的 XOR 混淆（非加密，仅用于防止明文存储敏感信息）
 */
function obfuscate(str: string): string {
  const chars = str.split('');
  for (let i = 0; i < chars.length; i++) {
    chars[i] = String.fromCharCode(chars[i].charCodeAt(0) ^ OBFUSCATION_KEY);
  }
  return chars.join('');
}

/**
 * 反混淆
 */
function deobfuscate(str: string): string {
  // XOR 是对称操作
  return obfuscate(str);
}

/**
 * 计算字符串字节大小
 */
function getByteSize(str: string): number {
  return new Blob([str]).size;
}

// ==================== Persistence 类 ====================

/**
 * 持久化存储工具类
 * 提供统一的存储接口，支持过期时间、加密等功能
 */
export class Persistence {
  private static prefix = DEFAULT_PREFIX;
  private static defaultStorage: 'local' | 'session' = 'local';

  /**
   * 设置全局前缀
   */
  static setPrefix(prefix: string): void {
    Persistence.prefix = prefix;
  }

  /**
   * 设置默认存储类型
   */
  static setDefaultStorage(storage: 'local' | 'session'): void {
    Persistence.defaultStorage = storage;
  }

  /**
   * 生成完整的存储键名
   */
  private static getFullKey(key: string): string {
    return `${Persistence.prefix}${key}`;
  }

  /**
   * 存储数据
   * @param key 存储键名
   * @param value 要存储的值
   * @param options 存储选项
   */
  static set<T>(key: string, value: T, options?: Partial<PersistenceOptions>): void {
    const storageType = options?.storage ?? Persistence.defaultStorage;
    const storage = getStorage(storageType);
    if (!storage) return;

    const fullKey = Persistence.getFullKey(key);
    const now = Date.now();
    const expireAt = options?.expire ? now + options.expire : null;

    const data: ExpirableData<T> = {
      value,
      expireAt,
      createdAt: now,
      version: CURRENT_VERSION,
    };

    try {
      let serialized = JSON.stringify(data);

      // 如果需要加密
      if (options?.encrypt) {
        serialized = obfuscate(serialized);
      }

      storage.setItem(fullKey, serialized);
    } catch (error) {
      // 存储空间不足，尝试清理过期数据后重试
      if (error instanceof DOMException && error.name === 'QuotaExceededError') {
        Persistence.cleanExpired(storageType);
        try {
          let serialized = JSON.stringify(data);
          if (options?.encrypt) {
            serialized = obfuscate(serialized);
          }
          storage.setItem(fullKey, serialized);
        } catch {
          console.error(`[Persistence] 存储空间不足，无法保存: ${key}`);
        }
      } else {
        console.error(`[Persistence] 保存数据失败: ${key}`, error);
      }
    }
  }

  /**
   * 获取数据
   * @param key 存储键名
   * @param options 可选配置
   * @returns 存储的值，如果不存在或已过期则返回 null
   */
  static get<T>(key: string, options?: Partial<PersistenceOptions>): T | null {
    const storageType = options?.storage ?? Persistence.defaultStorage;
    const storage = getStorage(storageType);
    if (!storage) return null;

    const fullKey = Persistence.getFullKey(key);

    try {
      let serialized = storage.getItem(fullKey);
      if (!serialized) return null;

      // 如果需要解密
      if (options?.encrypt) {
        serialized = deobfuscate(serialized);
      }

      const data: ExpirableData<T> = JSON.parse(serialized) as ExpirableData<T>;

      // 检查版本兼容性
      if (data.version !== CURRENT_VERSION) {
        Persistence.remove(key, options);
        return null;
      }

      // 检查是否过期
      if (data.expireAt && Date.now() > data.expireAt) {
        Persistence.remove(key, options);
        return null;
      }

      return data.value;
    } catch (error) {
      console.error(`[Persistence] 读取数据失败: ${key}`, error);
      return null;
    }
  }

  /**
   * 移除数据
   * @param key 存储键名
   * @param options 可选配置
   */
  static remove(key: string, options?: Partial<PersistenceOptions>): void {
    const storageType = options?.storage ?? Persistence.defaultStorage;
    const storage = getStorage(storageType);
    if (!storage) return;

    const fullKey = Persistence.getFullKey(key);
    storage.removeItem(fullKey);
  }

  /**
   * 检查键是否存在且未过期
   * @param key 存储键名
   * @param options 可选配置
   */
  static has(key: string, options?: Partial<PersistenceOptions>): boolean {
    return Persistence.get(key, options) !== null;
  }

  /**
   * 清除所有带有当前前缀的数据
   * @param storageType 存储类型
   */
  static clear(storageType?: 'local' | 'session'): void {
    const types: ('local' | 'session')[] = storageType 
      ? [storageType] 
      : ['local', 'session'];

    for (const type of types) {
      const storage = getStorage(type);
      if (!storage) continue;

      const keysToRemove: string[] = [];
      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        if (key?.startsWith(Persistence.prefix)) {
          keysToRemove.push(key);
        }
      }

      keysToRemove.forEach(key => storage.removeItem(key));
    }
  }

  /**
   * 清理所有过期数据
   * @param storageType 存储类型
   */
  static cleanExpired(storageType?: 'local' | 'session'): void {
    const types: ('local' | 'session')[] = storageType 
      ? [storageType] 
      : ['local', 'session'];

    for (const type of types) {
      const storage = getStorage(type);
      if (!storage) continue;

      const now = Date.now();
      const keysToRemove: string[] = [];

      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        if (!key?.startsWith(Persistence.prefix)) continue;

        try {
          const serialized = storage.getItem(key);
          if (!serialized) continue;

          // 尝试解析，忽略加密（清理时尝试两种方式）
          let data: ExpirableData<unknown> | null = null;
          try {
            data = JSON.parse(serialized) as ExpirableData<unknown>;
          } catch {
            try {
              data = JSON.parse(deobfuscate(serialized)) as ExpirableData<unknown>;
            } catch {
              continue;
            }
          }

          if (data?.expireAt && now > data.expireAt) {
            keysToRemove.push(key);
          }
        } catch {
          // 解析失败，跳过
        }
      }

      keysToRemove.forEach(key => storage.removeItem(key));
    }
  }

  /**
   * 获取存储统计信息
   * @param storageType 存储类型
   */
  static getStats(storageType?: 'local' | 'session'): StorageStats {
    const type = storageType ?? Persistence.defaultStorage;
    const storage = getStorage(type);
    
    if (!storage) {
      return { totalSize: 0, itemCount: 0, oldestItem: null };
    }

    let totalSize = 0;
    let itemCount = 0;
    let oldestItem: number | null = null;

    for (let i = 0; i < storage.length; i++) {
      const key = storage.key(i);
      if (!key?.startsWith(Persistence.prefix)) continue;

      const value = storage.getItem(key);
      if (value) {
        totalSize += getByteSize(key) + getByteSize(value);
        itemCount++;

        try {
          // 尝试解析创建时间
          let data: ExpirableData<unknown> | null = null;
          try {
            data = JSON.parse(value) as ExpirableData<unknown>;
          } catch {
            try {
              data = JSON.parse(deobfuscate(value)) as ExpirableData<unknown>;
            } catch {
              // 忽略
            }
          }
          if (data?.createdAt) {
            if (oldestItem === null || data.createdAt < oldestItem) {
              oldestItem = data.createdAt;
            }
          }
        } catch {
          // 忽略解析错误
        }
      }
    }

    return { totalSize, itemCount, oldestItem };
  }

  /**
   * 更新数据（合并更新）
   * @param key 存储键名
   * @param updates 要更新的部分数据
   * @param options 存储选项
   */
  static update<T extends Record<string, unknown>>(
    key: string,
    updates: Partial<T>,
    options?: Partial<PersistenceOptions>
  ): T | null {
    const existing = Persistence.get<T>(key, options);
    if (!existing) {
      Persistence.set(key, updates as T, options);
      return updates as T;
    }

    const updated = { ...existing, ...updates };
    Persistence.set(key, updated, options);
    return updated;
  }

  /**
   * 获取或创建数据
   * @param key 存储键名
   * @param defaultValue 默认值或工厂函数
   * @param options 存储选项
   */
  static getOrCreate<T>(
    key: string,
    defaultValue: T | (() => T),
    options?: Partial<PersistenceOptions>
  ): T {
    const existing = Persistence.get<T>(key, options);
    if (existing !== null) {
      return existing;
    }

    const value = typeof defaultValue === 'function' 
      ? (defaultValue as () => T)() 
      : defaultValue;
    Persistence.set(key, value, options);
    return value;
  }
}

// ==================== 便捷导出 ====================

/** localStorage 便捷方法 */
export const localPersistence = {
  set: <T>(key: string, value: T, options?: Omit<Partial<PersistenceOptions>, 'storage'>) =>
    Persistence.set(key, value, { ...options, storage: 'local' }),
  get: <T>(key: string, options?: Omit<Partial<PersistenceOptions>, 'storage'>) =>
    Persistence.get<T>(key, { ...options, storage: 'local' }),
  remove: (key: string) =>
    Persistence.remove(key, { storage: 'local' }),
  has: (key: string) =>
    Persistence.has(key, { storage: 'local' }),
};

/** sessionStorage 便捷方法 */
export const sessionPersistence = {
  set: <T>(key: string, value: T, options?: Omit<Partial<PersistenceOptions>, 'storage'>) =>
    Persistence.set(key, value, { ...options, storage: 'session' }),
  get: <T>(key: string, options?: Omit<Partial<PersistenceOptions>, 'storage'>) =>
    Persistence.get<T>(key, { ...options, storage: 'session' }),
  remove: (key: string) =>
    Persistence.remove(key, { storage: 'session' }),
  has: (key: string) =>
    Persistence.has(key, { storage: 'session' }),
};

/** 预定义的过期时间常量 */
export const EXPIRE_TIMES = {
  /** 1 分钟 */
  MINUTE: 60 * 1000,
  /** 5 分钟 */
  MINUTES_5: 5 * 60 * 1000,
  /** 15 分钟 */
  MINUTES_15: 15 * 60 * 1000,
  /** 30 分钟 */
  MINUTES_30: 30 * 60 * 1000,
  /** 1 小时 */
  HOUR: 60 * 60 * 1000,
  /** 2 小时 */
  HOURS_2: 2 * 60 * 60 * 1000,
  /** 6 小时 */
  HOURS_6: 6 * 60 * 60 * 1000,
  /** 12 小时 */
  HOURS_12: 12 * 60 * 60 * 1000,
  /** 1 天 */
  DAY: 24 * 60 * 60 * 1000,
  /** 7 天 */
  WEEK: 7 * 24 * 60 * 60 * 1000,
  /** 30 天 */
  MONTH: 30 * 24 * 60 * 60 * 1000,
} as const;

export default Persistence;