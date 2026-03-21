/**
 * Token 管理器 - 单例模式
 *
 * 功能：
 * - Token 刷新并发控制（防止并发刷新）
 * - 等待队列（并发请求时共享刷新结果）
 * - 多标签页同步（使用 localStorage 事件）
 *
 * @see FR-009: Token 刷新并发控制
 */

import axios from 'axios';

import {
  setToken,
  getRefreshToken,
  setRefreshToken,
} from '../security/tokenStorage';

// ============================================
// 类型定义
// ============================================

/** Token 刷新结果 */
export interface TokenRefreshResult {
  success: boolean;
  accessToken?: string;
  refreshToken?: string;
  error?: Error;
}

/** Token 刷新任务 */
export interface RefreshTask {
  /** 解决函数 */
  resolve: (result: TokenRefreshResult) => void;
  /** 拒绝函数 */
  reject: (error: Error) => void;
}

/** Token 管理器接口 */
export interface ITokenManager {
  /** 刷新 Token（带并发控制） */
  refreshToken(): Promise<TokenRefreshResult>;
  /** 检查是否有刷新锁 */
  hasRefreshLock(): boolean;
  /** 清除刷新锁 */
  clearRefreshLock(): void;
  /** 获取等待队列长度 */
  getQueueLength(): number;
}

// ============================================
// 常量定义
// ============================================

/** localStorage 键名 */
const STORAGE_KEYS = {
  /** 刷新锁标记 */
  REFRESH_LOCK: 'token_refresh_lock',
  /** 刷新完成事件 */
  REFRESH_COMPLETE: 'token_refresh_complete',
} as const;

/** 刷新锁过期时间（毫秒） */
const REFRESH_LOCK_EXPIRY_MS = 30000; // 30 秒超时

// ============================================
// Token 管理器实现
// ============================================

export class TokenManager implements ITokenManager {
  /** 单例实例 */
  private static instance: TokenManager | null = null;

  /** 等待队列 */
  private refreshQueue: RefreshTask[] = [];

  /** 当前刷新 Promise（如果有） */
  private currentRefreshPromise: Promise<TokenRefreshResult> | null = null;

  /** 刷新锁检查计时器 */
  private lockCheckTimer: ReturnType<typeof setInterval> | null = null;

  /** 初始化标记 */
  private isInitialized = false;

  /** 刷新 token URL */
  private refreshUrl: string;

  /** storage 事件监听器引用 */
  private readonly storageEventListener: (event: StorageEvent) => void;

  private constructor(options?: {
    refreshUrl?: string;
  }) {
    this.refreshUrl = options?.refreshUrl || `${import.meta.env.VITE_API_BASE_URL || '/api'}/user/auth/refresh`;
    this.storageEventListener = this.handleStorageEvent.bind(this);
  }

  /**
   * 获取单例实例
   */
  static getInstance(options?: {
    refreshUrl?: string;
  }): TokenManager {
    if (!TokenManager.instance) {
      TokenManager.instance = new TokenManager(options);
    }
    return TokenManager.instance;
  }

  /**
   * 初始化（启动锁检查）
   */
  init(): void {
    if (this.isInitialized) {
      return;
    }

    this.isInitialized = true;
    
    // 启动定期检查过期锁
    this.lockCheckTimer = setInterval(() => {
      this.checkExpiredLock();
    }, 1000);

    // 监听其他标签页的刷新完成事件
    window.addEventListener('storage', this.storageEventListener);
  }

  /**
   * 销毁（清理资源）
   */
  destroy(): void {
    if (this.lockCheckTimer) {
      clearInterval(this.lockCheckTimer);
      this.lockCheckTimer = null;
    }

    window.removeEventListener('storage', this.storageEventListener);
    
    // 清除所有等待的请求
    this.refreshQueue.forEach(task => {
      task.reject(new Error('TokenManager destroyed'));
    });
    this.refreshQueue = [];
  }

  /**
   * 刷新 Token（带并发控制）
   * 
   * 流程：
   * 1. 检查是否有刷新锁（其他标签页正在刷新）
   * 2. 如果有锁，加入等待队列
   * 3. 如果没有锁，获取锁并执行刷新
   * 4. 刷新完成后释放锁并通知所有等待者
   */
  async refreshToken(): Promise<TokenRefreshResult> {
    // 检查是否有其他标签页正在刷新
    if (this.hasRefreshLock()) {
      // 等待其他标签页刷新完成
      return this.waitForRefresh();
    }

    // 检查是否已有刷新在进行中（当前标签页）
    if (this.currentRefreshPromise) {
      return this.addToQueue();
    }

    // 获取锁并开始刷新
    this.acquireRefreshLock();
    this.currentRefreshPromise = this.performRefresh();
    
    try {
      const result = await this.currentRefreshPromise;
      return result;
    } finally {
      // 刷新完成后清理
      this.currentRefreshPromise = null;
      this.releaseRefreshLock();
    }
  }

  /**
   * 检查是否有刷新锁
   */
  hasRefreshLock(): boolean {
    if (this.currentRefreshPromise) {
      // 当前标签页正在刷新
      return true;
    }

    try {
      const lockData = localStorage.getItem(STORAGE_KEYS.REFRESH_LOCK);
      if (!lockData) {
        return false;
      }

      const { timestamp } = JSON.parse(lockData) as { timestamp: number };
      const now = Date.now();
      
      // 检查锁是否过期
      if (now - timestamp > REFRESH_LOCK_EXPIRY_MS) {
        // 锁已过期，清除它
        this.clearRefreshLock();
        return false;
      }

      return true;
    } catch {
      return false;
    }
  }

  /**
   * 清除刷新锁
   */
  clearRefreshLock(): void {
    localStorage.removeItem(STORAGE_KEYS.REFRESH_LOCK);
  }

  /**
   * 获取等待队列长度
   */
  getQueueLength(): number {
    return this.refreshQueue.length;
  }

  /**
   * 获取刷新锁
   */
  private acquireRefreshLock(): void {
    const lockData = {
      timestamp: Date.now(),
      tabId: this.getTabId(),
    };
    localStorage.setItem(STORAGE_KEYS.REFRESH_LOCK, JSON.stringify(lockData));
  }

  /**
   * 释放刷新锁
   */
  private releaseRefreshLock(): void {
    this.clearRefreshLock();

    // 广播刷新完成事件
    this.broadcastRefreshComplete();
  }

  /**
   * 执行实际的 Token 刷新请求
   */
  private async performRefresh(): Promise<TokenRefreshResult> {
    try {
      const refreshToken = getRefreshToken();
      
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      // 使用 axios 直接请求（避免使用拦截器导致循环）
      const response = await axios.post<{
        code: number;
        message: string;
        data: {
          access_token: string;
          refresh_token: string;
        };
      }>(this.refreshUrl, { refresh_token: refreshToken });

      const { access_token, refresh_token } = response.data.data;

      // 更新存储的 token
      setToken(access_token);
      setRefreshToken(refresh_token);

      return {
        success: true,
        accessToken: access_token,
        refreshToken: refresh_token,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error : new Error('Token refresh failed'),
      };
    }
  }

  /**
   * 等待其他标签页刷新完成
   */
  private waitForRefresh(): Promise<TokenRefreshResult> {
    return new Promise((resolve, reject) => {
      // 添加到等待队列
      this.refreshQueue.push({ resolve, reject });

      // 设置超时（防止永久等待）
      setTimeout(() => {
        const index = this.refreshQueue.findIndex(task => task.resolve === resolve);
        if (index !== -1) {
          this.refreshQueue.splice(index, 1);
          reject(new Error('Token refresh timeout'));
        }
      }, REFRESH_LOCK_EXPIRY_MS);
    });
  }

  /**
   * 加入当前标签页的等待队列
   */
  private addToQueue(): Promise<TokenRefreshResult> {
    return new Promise((resolve, reject) => {
      this.refreshQueue.push({ resolve, reject });
    });
  }

  /**
   * 广播刷新完成事件
   */
  private broadcastRefreshComplete(): void {
    // 通知所有等待的请求
    this.refreshQueue.forEach(task => {
      task.resolve({ success: true });
    });
    this.refreshQueue = [];

    // 触发 storage 事件（通知其他标签页）
    try {
      localStorage.setItem(STORAGE_KEYS.REFRESH_COMPLETE, JSON.stringify({
        timestamp: Date.now(),
        tabId: this.getTabId(),
      }));
      // 立即清除，触发 storage 事件
      localStorage.removeItem(STORAGE_KEYS.REFRESH_COMPLETE);
    } catch {
      // 静默处理
    }
  }

  /**
   * 处理 storage 事件（来自其他标签页）
   */
  private handleStorageEvent(event: StorageEvent): void {
    if (event.key === STORAGE_KEYS.REFRESH_COMPLETE && event.newValue) {
      try {
        // 通知当前等待队列
        this.refreshQueue.forEach(task => {
          task.resolve({ success: true });
        });
        this.refreshQueue = [];
      } catch {
        // 忽略解析错误
      }
    }
  }

  /**
   * 检查过期的锁
   */
  private checkExpiredLock(): void {
    try {
      const lockData = localStorage.getItem(STORAGE_KEYS.REFRESH_LOCK);
      if (!lockData) {
        return;
      }

      const { timestamp } = JSON.parse(lockData) as { timestamp: number };
      const now = Date.now();

      if (now - timestamp > REFRESH_LOCK_EXPIRY_MS) {
        // 锁已过期，清除它并通知等待队列
        this.clearRefreshLock();
        
        // 通知等待者重试
        this.refreshQueue.forEach(task => {
          task.resolve({ success: false, error: new Error('Refresh lock expired') });
        });
        this.refreshQueue = [];
      }
    } catch {
      // 忽略解析错误
    }
  }

  /**
   * 获取当前标签页 ID
   */
  private getTabId(): string {
    // 使用 sessionStorage 生成唯一 tab ID
    let tabId = sessionStorage.getItem('__tab_id');
    if (!tabId) {
      tabId = `tab-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      sessionStorage.setItem('__tab_id', tabId);
    }
    return tabId;
  }
}

// ============================================
// 导出单例
// ============================================

/** Token 管理器单例实例 */
export const tokenManager = TokenManager.getInstance();

/** 初始化和导出辅助函数 */
export function initTokenManager(options?: {
  refreshUrl?: string;
}): void {
  const manager = TokenManager.getInstance(options);
  manager.init();
}

export function getTokenManager(): ITokenManager {
  const manager = TokenManager.getInstance();
  manager.init();
  return manager;
}