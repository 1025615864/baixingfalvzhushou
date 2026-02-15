/**
 * useDailyCheckin - 每日签到逻辑 Hook
 */

import { useState, useCallback, useEffect } from 'react';

import { useCheckIn, useDailyStats, usePointsBalance, usePointsRules } from './usePoints';

interface UseDailyCheckinOptions {
  /** 签到成功回调 */
  onSuccess?: (points: number, continuousDays: number) => void;
  /** 签到失败回调 */
  onError?: (error: Error) => void;
  /** 是否自动刷新数据 */
  autoRefresh?: boolean;
}

interface UseDailyCheckinReturn {
  /** 是否已签到 */
  hasCheckedIn: boolean;
  /** 连续签到天数 */
  continuousDays: number;
  /** 当前积分余额 */
  balance: number;
  /** 今日可获得的积分 */
  todayPoints: number;
  /** 是否正在签到中 */
  isCheckingIn: boolean;
  /** 是否正在加载 */
  isLoading: boolean;
  /** 执行签到 */
  checkIn: () => Promise<void>;
  /** 刷新数据 */
  refresh: () => void;
  /** 签到结果 */
  lastCheckInResult: {
    points: number;
    totalPoints: number;
    continuousDays: number;
  } | null;
}

/**
 * 每日签到逻辑 Hook
 */
export function useDailyCheckin(options: UseDailyCheckinOptions = {}): UseDailyCheckinReturn {
  const { onSuccess, onError, autoRefresh = true } = options;

  const [lastCheckInResult, setLastCheckInResult] = useState<UseDailyCheckinReturn['lastCheckInResult']>(null);

  // 获取必要的数据
  const { data: balanceData, isLoading: balanceLoading, refetch: refetchBalance } = usePointsBalance();
  const { data: dailyStats, isLoading: statsLoading, refetch: refetchStats } = useDailyStats();
  const { data: rules, isLoading: rulesLoading } = usePointsRules();
  const checkInMutation = useCheckIn();

  // 计算今日是否已签到
  const hasCheckedIn = dailyStats?.some(stat => stat.action === 'sign_in' && stat.count > 0) ?? false;

  // 连续签到天数
  const continuousDays = balanceData?.continuousDays ?? 0;

  // 当前积分余额
  const balance = balanceData?.balance ?? 0;

  // 查找签到规则获取今日积分
  const signInRule = rules?.find(rule => rule.action === 'sign_in');
  const todayPoints = signInRule?.points ?? 10;

  /**
   * 执行签到
   */
  const checkIn = useCallback(async () => {
    if (hasCheckedIn || checkInMutation.isPending) {
      return;
    }

    try {
      const result = await checkInMutation.mutateAsync();
      
      setLastCheckInResult({
        points: result.pointsEarned,
        totalPoints: result.totalPoints,
        continuousDays: result.continuousDays,
      });

      onSuccess?.(result.pointsEarned, result.continuousDays);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('签到失败');
      onError?.(error);
      throw error;
    }
  }, [hasCheckedIn, checkInMutation, onSuccess, onError]);

  /**
   * 刷新数据
   */
  const refresh = useCallback(() => {
    void refetchBalance();
    void refetchStats();
  }, [refetchBalance, refetchStats]);

  // 自动刷新 - 修复内存泄漏问题
  useEffect(() => {
    if (!autoRefresh) return;
    
    // 立即刷新一次
    refresh();
    
    // 设置定时刷新（每60秒）
    const interval = setInterval(() => {
      refresh();
    }, 60000);
    
    // 清理函数：组件卸载时清除定时器
    return () => {
      clearInterval(interval);
    };
  }, [autoRefresh, refresh]);

  const isLoading = balanceLoading || statsLoading || rulesLoading;
  const isCheckingIn = checkInMutation.isPending;

  return {
    hasCheckedIn,
    continuousDays,
    balance,
    todayPoints,
    isCheckingIn,
    isLoading,
    checkIn,
    refresh,
    lastCheckInResult,
  };
}

/**
 * 使用本地存储记住签到状态（用于优化体验）
 */
export function useCheckInStorage(): {
  getLastCheckInDate: () => string | null;
  setLastCheckInDate: (date: string) => void;
  isCheckedInToday: () => boolean;
} {
  const STORAGE_KEY = 'last_check_in_date';

  const getLastCheckInDate = useCallback((): string | null => {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch {
      return null;
    }
  }, []);

  const setLastCheckInDate = useCallback((date: string): void => {
    try {
      localStorage.setItem(STORAGE_KEY, date);
    } catch {
      // 忽略存储错误
    }
  }, []);

  const isCheckedInToday = useCallback((): boolean => {
    const lastDate = getLastCheckInDate();
    if (!lastDate) return false;
    
    const today = new Date().toISOString().split('T')[0];
    return lastDate === today;
  }, [getLastCheckInDate]);

  return {
    getLastCheckInDate,
    setLastCheckInDate,
    isCheckedInToday,
  };
}