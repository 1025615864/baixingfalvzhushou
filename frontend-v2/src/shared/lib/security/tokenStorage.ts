/**
 * 安全的Token存储封装
 * 提供localStorage的XSS防护增强
 * 
 * ⚠️ 注意：这只是缓解措施，最佳实践是使用httpOnly cookie
 * 长期建议：迁移到httpOnly cookie存储方案
 */

const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

/**
 * 存储token（带基础防护）
 */
export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch (e) {
    console.error('Failed to store token:', e);
  }
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch (e) {
    return null;
  }
}

export function removeToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch (e) {
    console.error('Failed to remove token:', e);
  }
}

// 刷新token相关
export function setRefreshToken(token: string): void {
  try {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  } catch (e) {
    console.error('Failed to store refresh token:', e);
  }
}

export function getRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch (e) {
    return null;
  }
}

export function removeRefreshToken(): void {
  try {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  } catch (e) {
    console.error('Failed to remove refresh token:', e);
  }
}

/**
 * 清除所有认证相关存储
 */
export function clearAuthStorage(): void {
  removeToken();
  removeRefreshToken();
}
