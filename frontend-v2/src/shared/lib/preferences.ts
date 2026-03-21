/**
 * 用户偏好设置持久化
 * 提供统一的用户偏好设置管理，支持响应式更新
 */

import { Persistence, EXPIRE_TIMES } from './persistence';

// ==================== 类型定义 ====================

/** 主题模式 */
export type ThemeMode = 'light' | 'dark' | 'system';

/** 语言设置 */
export type Language = 'zh-CN' | 'en-US';

/** 字体大小 */
export type FontSize = 'small' | 'medium' | 'large';

/** 用户偏好设置 */
export interface UserPreferences {
  /** 主题模式 */
  theme: ThemeMode;
  /** 语言设置 */
  language: Language;
  /** 字体大小 */
  fontSize: FontSize;
  /** 侧边栏是否折叠 */
  sidebarCollapsed: boolean;
  /** 是否启用通知 */
  notificationEnabled: boolean;
  /** 是否启用声音 */
  soundEnabled: boolean;
  /** 是否启用动画 */
  animationEnabled: boolean;
  /** 自动保存间隔（毫秒，0 表示禁用） */
  autoSaveInterval: number;
  /** 每页显示数量 */
  pageSize: number;
  /** 首页仪表盘布局 */
  dashboardLayout: 'grid' | 'list';
  /** 是否显示新手引导 */
  showOnboarding: boolean;
  /** 最后访问时间 */
  lastVisitAt: string | null;
}

/** 偏好设置变更回调 */
type PreferenceChangeCallback = <K extends keyof UserPreferences>(
  key: K,
  newValue: UserPreferences[K],
  oldValue: UserPreferences[K]
) => void;

// ==================== 常量定义 ====================

/** 存储键名 */
const PREFERENCES_KEY = 'user_preferences';

/** 默认偏好设置 */
const DEFAULT_PREFERENCES: UserPreferences = {
  theme: 'system',
  language: 'zh-CN',
  fontSize: 'medium',
  sidebarCollapsed: false,
  notificationEnabled: true,
  soundEnabled: true,
  animationEnabled: true,
  autoSaveInterval: 30000, // 30 秒
  pageSize: 10,
  dashboardLayout: 'grid',
  showOnboarding: true,
  lastVisitAt: null,
};

/** 字体大小映射（像素） */
export const FONT_SIZE_MAP: Record<FontSize, string> = {
  small: '14px',
  medium: '16px',
  large: '18px',
};

/** 分页大小选项 */
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100] as const;

// ==================== 偏好设置持久化类 ====================

/**
 * 用户偏好设置持久化管理
 */
class PreferencesManager {
  private cache: UserPreferences | null = null;
  private listeners: Set<PreferenceChangeCallback> = new Set();
  private initialized = false;

  /**
   * 初始化偏好设置
   * 从存储加载并合并默认值
   */
  private initialize(): void {
    if (this.initialized) return;

    const stored = Persistence.get<UserPreferences>(PREFERENCES_KEY);
    if (stored) {
      // 合并默认值（处理新增的偏好字段）
      this.cache = { ...DEFAULT_PREFERENCES, ...stored };
    } else {
      this.cache = { ...DEFAULT_PREFERENCES };
    }

    // 更新最后访问时间
    this.cache.lastVisitAt = new Date().toISOString();
    this.save();

    this.initialized = true;
  }

  /**
   * 保存偏好设置到存储
   */
  private save(): void {
    if (this.cache) {
      Persistence.set(PREFERENCES_KEY, this.cache, {
        // 偏好设置长期有效（30天）
        expire: EXPIRE_TIMES.MONTH,
      });
    }
  }

  /**
   * 触发变更回调
   */
  private notify<K extends keyof UserPreferences>(
    key: K,
    newValue: UserPreferences[K],
    oldValue: UserPreferences[K]
  ): void {
    this.listeners.forEach(callback => {
      try {
        callback(key, newValue, oldValue);
      } catch (error) {
        console.error(`[Preferences] 回调执行错误: ${key}`, error);
      }
    });
  }

  /**
   * 获取所有偏好设置
   */
  getPreferences(): UserPreferences {
    this.initialize();
    return { ...this.cache! };
  }

  /**
   * 获取单个偏好设置
   */
  getPreference<K extends keyof UserPreferences>(key: K): UserPreferences[K] {
    this.initialize();
    return this.cache![key];
  }

  /**
   * 更新偏好设置
   * @param prefs 要更新的偏好设置（部分）
   */
  setPreferences(prefs: Partial<UserPreferences>): void {
    this.initialize();

    const oldValues = { ...this.cache! };
    this.cache = { ...this.cache!, ...prefs };
    this.save();

    // 触发变更回调
    for (const key of Object.keys(prefs) as Array<keyof UserPreferences>) {
      if (oldValues[key] !== prefs[key]) {
        this.notify(key, prefs[key] as UserPreferences[typeof key], oldValues[key]);
      }
    }
  }

  /**
   * 设置单个偏好
   */
  setPreference<K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ): void {
    this.initialize();

    const oldValue = this.cache![key];
    if (oldValue !== value) {
      this.cache![key] = value;
      this.save();
      this.notify(key, value, oldValue);
    }
  }

  /**
   * 重置偏好设置为默认值
   */
  resetPreferences(): void {
    this.cache = { ...DEFAULT_PREFERENCES };
    this.save();

    // 触发所有字段的变更回调
    for (const key of Object.keys(DEFAULT_PREFERENCES) as Array<keyof UserPreferences>) {
      this.notify(key, DEFAULT_PREFERENCES[key], this.cache[key]);
    }
  }

  /**
   * 重置单个偏好设置
   */
  resetPreference<K extends keyof UserPreferences>(key: K): void {
    this.setPreference(key, DEFAULT_PREFERENCES[key]);
  }

  /**
   * 监听偏好设置变更
   * @param callback 变更回调函数
   * @returns 取消监听的函数
   */
  onChange(callback: PreferenceChangeCallback): () => void {
    this.listeners.add(callback);
    return () => {
      this.listeners.delete(callback);
    };
  }

  /**
   * 导出偏好设置（用于备份）
   */
  export(): string {
    this.initialize();
    return JSON.stringify(this.cache, null, 2);
  }

  /**
   * 导入偏好设置（用于恢复）
   * @param json JSON 字符串
   */
  import(json: string): boolean {
    try {
      const parsed = JSON.parse(json) as Partial<UserPreferences>;
      // 验证导入的数据
      const validKeys = Object.keys(DEFAULT_PREFERENCES) as Array<keyof UserPreferences>;
      const filtered = {} as Partial<UserPreferences>;
      const assignPreference = <K extends keyof UserPreferences>(
        key: K,
        value: UserPreferences[K]
      ) => {
        filtered[key] = value;
      };

      for (const prefKey of validKeys) {
        const value = parsed[prefKey];
        if (value !== undefined) {
          assignPreference(prefKey, value as UserPreferences[typeof prefKey]);
        }
      }

      this.setPreferences(filtered);
      return true;
    } catch (error) {
      console.error('[Preferences] 导入失败:', error);
      return false;
    }
  }

  /**
   * 应用主题到 DOM
   */
  applyTheme(): void {
    const theme = this.getPreference('theme');
    const root = document.documentElement;

    if (theme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.classList.toggle('dark', prefersDark);
    } else {
      root.classList.toggle('dark', theme === 'dark');
    }
  }

  /**
   * 应用字体大小到 DOM
   */
  applyFontSize(): void {
    const fontSize = this.getPreference('fontSize');
    const root = document.documentElement;
    root.style.fontSize = FONT_SIZE_MAP[fontSize];
  }

  /**
   * 应用所有视觉偏好
   */
  applyVisualPreferences(): void {
    this.applyTheme();
    this.applyFontSize();
  }
}

// ==================== 单例导出 ====================

const preferencesManager = new PreferencesManager();

/** 偏好设置持久化 API */
export const preferencesPersistence = {
  /** 获取所有偏好设置 */
  getPreferences: () => preferencesManager.getPreferences(),

  /** 获取单个偏好设置 */
  getPreference: <K extends keyof UserPreferences>(key: K) =>
    preferencesManager.getPreference(key),

  /** 更新偏好设置 */
  setPreferences: (prefs: Partial<UserPreferences>) =>
    preferencesManager.setPreferences(prefs),

  /** 设置单个偏好 */
  setPreference: <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => preferencesManager.setPreference(key, value),

  /** 重置所有偏好设置 */
  resetPreferences: () => preferencesManager.resetPreferences(),

  /** 重置单个偏好设置 */
  resetPreference: <K extends keyof UserPreferences>(key: K) =>
    preferencesManager.resetPreference(key),

  /** 监听偏好设置变更 */
  onChange: (callback: PreferenceChangeCallback) =>
    preferencesManager.onChange(callback),

  /** 导出偏好设置 */
  export: () => preferencesManager.export(),

  /** 导入偏好设置 */
  import: (json: string) => preferencesManager.import(json),

  /** 应用主题 */
  applyTheme: () => preferencesManager.applyTheme(),

  /** 应用字体大小 */
  applyFontSize: () => preferencesManager.applyFontSize(),

  /** 应用所有视觉偏好 */
  applyVisualPreferences: () => preferencesManager.applyVisualPreferences(),
};

// ==================== Hooks ====================

/**
 * 创建响应式的偏好设置 Hook
 * 用于 React 组件中获取和监听偏好设置变更
 */
export function createPreferencesHook(): {
  usePreferences: () => UserPreferences;
  usePreference: <K extends keyof UserPreferences>(key: K) => UserPreferences[K];
} {
  // 这里返回一个简单的接口，实际使用时可以结合 React 的 useState 和 useEffect
  // 例如在组件中：
  // const [theme, setTheme] = useState(() => preferencesPersistence.getPreference('theme'));
  return {
    usePreferences: () => preferencesManager.getPreferences(),
    usePreference: <K extends keyof UserPreferences>(key: K) =>
      preferencesManager.getPreference(key),
  };
}

// ==================== 便捷选择器 ====================

/** 主题选择器 */
export const selectTheme = () => preferencesManager.getPreference('theme');

/** 语言选择器 */
export const selectLanguage = () => preferencesManager.getPreference('language');

/** 字体大小选择器 */
export const selectFontSize = () => preferencesManager.getPreference('fontSize');

/** 侧边栏折叠状态选择器 */
export const selectSidebarCollapsed = () =>
  preferencesManager.getPreference('sidebarCollapsed');

/** 通知启用状态选择器 */
export const selectNotificationEnabled = () =>
  preferencesManager.getPreference('notificationEnabled');

/** 动画启用状态选择器 */
export const selectAnimationEnabled = () =>
  preferencesManager.getPreference('animationEnabled');

/** 分页大小选择器 */
export const selectPageSize = () => preferencesManager.getPreference('pageSize');

/** 新手引导状态选择器 */
export const selectShowOnboarding = () =>
  preferencesManager.getPreference('showOnboarding');

export default preferencesPersistence;