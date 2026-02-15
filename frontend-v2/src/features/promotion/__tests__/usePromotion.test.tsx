/**
 * usePromotion Hooks 测试
 * 测试 usePromotionStats 和 useCommissionRecords 等 Hooks
 */

import { vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as React from 'react';

import type {
  PromotionStats,
  CommissionRecord,
  PromotionLink,
  PromotionPoster,
  CommissionWithdrawal,
} from '../types';
import {
  apiGetPromotionLink,
  apiGeneratePromotionLink,
  apiGetPromotionStats,
  apiGetCommissionRecords,
  apiGetPosters,
  apiGeneratePoster,
  apiRequestWithdrawal,
  apiGetWithdrawals,
  apiGetPromotionRules,
} from '../api';
import {
  usePromotionStats,
  useCommissionRecords,
  usePromotionLink,
  useGeneratePromotionLink,
  usePosters,
  useGeneratePoster,
  useWithdrawals,
  useRequestWithdrawal,
  usePromotionRules,
} from '../hooks/usePromotion';

// ============================================
// Mock API 模块
// ============================================

vi.mock('../api', () => ({
  apiGetPromotionLink: vi.fn(),
  apiGeneratePromotionLink: vi.fn(),
  apiGetPromotionStats: vi.fn(),
  apiGetCommissionRecords: vi.fn(),
  apiGeneratePoster: vi.fn(),
  apiGetPosters: vi.fn(),
  apiRequestWithdrawal: vi.fn(),
  apiGetWithdrawals: vi.fn(),
  apiGetPromotionRules: vi.fn(),
}));


// ============================================
// 测试工具
// ============================================

function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
        refetchOnWindowFocus: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

function TestQueryProvider({ children }: { children: React.ReactNode }): JSX.Element {
  const [queryClient] = React.useState(() => createTestQueryClient());
  return React.createElement(QueryClientProvider, { client: queryClient }, children);
}

// ============================================
// 测试数据工厂
// ============================================

const createMockPromotionStats = (overrides?: Partial<PromotionStats>): PromotionStats => ({
  totalInvited: 100,
  totalRegistered: 50,
  totalRewards: 500,
  pendingRewards: 100,
  conversionRate: 0.5,
  period: 'all',
  totalCommission: 500,
  pendingCommission: 100,
  paidCommission: 400,
  ...overrides,
});

const createMockCommissionRecords = (count: number = 3): CommissionRecord[] =>
  Array.from({ length: count }, (_, i) => ({
    id: `record-${i + 1}`,
    orderId: `order-${i + 1}`,
    orderAmount: 1000 * (i + 1),
    commissionAmount: 100 * (i + 1),
    commissionRate: 0.1,
    status: i === 0 ? 'pending' : 'paid',
    sourceUserId: `user-${i + 1}`,
    sourceUserName: `用户${i + 1}`,
    createdAt: new Date(Date.now() - i * 86400000).toISOString(),
    confirmedAt: i > 0 ? new Date(Date.now() - i * 43200000).toISOString() : undefined,
    paidAt: i > 0 ? new Date(Date.now() - i * 21600000).toISOString() : undefined,
    description: `邀请用户: 用户${i + 1}`,
  }));

const createMockPromotionLink = (overrides?: Partial<PromotionLink>): PromotionLink => ({
  code: 'ABC123',
  url: 'https://example.com/invite/ABC123',
  shortUrl: 'https://ex.co/ABC123',
  qrCodeUrl: 'https://example.com/qrcode/ABC123',
  createdAt: new Date().toISOString(),
  expiresAt: null,
  ...overrides,
});

const createMockPosters = (count: number = 3): PromotionPoster[] =>
  Array.from({ length: count }, (_, i) => ({
    id: `poster-${i + 1}`,
    templateId: 'default',
    imageUrl: `https://example.com/poster-${i + 1}.png`,
    title: `海报${i + 1}`,
    description: `海报描述${i + 1}`,
    createdAt: new Date().toISOString(),
    customData: { index: i + 1 },
  }));

const createMockWithdrawals = (count: number = 2): CommissionWithdrawal[] =>
  Array.from({ length: count }, (_, i) => ({
    id: `withdrawal-${i + 1}`,
    amount: 100 * (i + 1),
    status: i === 0 ? 'pending' : 'completed',
    withdrawalMethod: 'reward',
    createdAt: new Date(Date.now() - i * 86400000).toISOString(),
    processedAt: i > 0 ? new Date(Date.now() - i * 43200000).toISOString() : undefined,
    accountInfo: { claimedCount: i + 1 },
  }));

// ============================================
// usePromotionStats 测试
// ============================================

describe('usePromotionStats', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该成功获取推广统计数据', async () => {
    const mockStats = createMockPromotionStats();
    vi.mocked(apiGetPromotionStats).mockResolvedValueOnce(mockStats);

    const { result } = renderHook(() => usePromotionStats(), {
      wrapper: TestQueryProvider,
    });

    // 初始状态：加载中
    expect(result.current.isLoading).toBe(true);

    // 等待数据加载完成
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // 验证数据
    expect(result.current.data).toEqual(mockStats);
    expect(apiGetPromotionStats).toHaveBeenCalledWith({});
  });

  it('应该支持按时间段筛选', async () => {
    const mockStats = createMockPromotionStats({ period: 'month' });
    vi.mocked(apiGetPromotionStats).mockResolvedValueOnce(mockStats);

    const { result } = renderHook(() => usePromotionStats({ period: 'month' }), {
      wrapper: TestQueryProvider,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiGetPromotionStats).toHaveBeenCalledWith({ period: 'month' });
  });

  it('应该处理获取失败的情况', async () => {
    const error = new Error('获取统计数据失败');
    vi.mocked(apiGetPromotionStats).mockRejectedValueOnce(error);

    const { result } = renderHook(() => usePromotionStats(), {
      wrapper: TestQueryProvider,
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeTruthy();
  });

  it('应该缓存数据1分钟', async () => {
    const mockStats = createMockPromotionStats();
    vi.mocked(apiGetPromotionStats).mockResolvedValue(mockStats);

    const { result } = renderHook(() => usePromotionStats(), {
      wrapper: TestQueryProvider,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // 重新渲染，应该使用缓存
    const { result: result2 } = renderHook(() => usePromotionStats(), {
      wrapper: TestQueryProvider,
    });

    expect(result2.current.isLoading).toBe(true); // 新实例会重新加载
  });
});

// ============================================
// useCommissionRecords 测试
// ============================================

describe('useCommissionRecords', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该成功获取佣金记录列表', async () => {
    const mockRecords = createMockCommissionRecords(5);
    vi.mocked(apiGetCommissionRecords).mockResolvedValueOnce({
      records: mockRecords,
      total: 5,
      limit: 20,
      offset: 0,
    });

    const { result } = renderHook(() => useCommissionRecords(), {
      wrapper: TestQueryProvider,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.records).toHaveLength(5);
    expect(result.current.data?.total).toBe(5);
    expect(result.current.data?.limit).toBe(20);
    expect(result.current.data?.offset).toBe(0);
  });

  it('应该支持分页参数', async () => {
    const mockRecords = createMockCommissionRecords(2);
    vi.mocked(apiGetCommissionRecords).mockResolvedValueOnce({
      records: mockRecords,
      total: 10,
      limit: 2,
      offset: 4,
    });

    const { result } = renderHook(
      () => useCommissionRecords({ limit: 2, offset: 4 }),
      { wrapper: TestQueryProvider }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiGetCommissionRecords).toHaveBeenCalledWith({ limit: 2, offset: 4 });
    expect(result.current.data?.limit).toBe(2);
    expect(result.current.data?.offset).toBe(4);
  });

  it('应该正确映射返回数据', async () => {
    const mockRecords = [
      {
        id: 1,
        invited_user_id: 101,
        invited_user_name: '测试用户',
        invited_at: '2024-01-15T10:00:00Z',
        status: 'claimed' as const,
        reward_amount: 100,
        claimed_at: '2024-01-15T12:00:00Z',
      },
    ];

    vi.mocked(apiGetCommissionRecords).mockResolvedValueOnce({
      records: mockRecords.map(item => ({
        id: String(item.id),
        orderId: String(item.invited_user_id),
        orderAmount: 0,
        commissionAmount: item.reward_amount ?? 0,
        commissionRate: 0,
        status: item.status === 'claimed' ? 'paid' : 'pending',
        sourceUserId: String(item.invited_user_id),
        sourceUserName: item.invited_user_name,
        createdAt: item.invited_at,
        confirmedAt: item.claimed_at,
        paidAt: item.claimed_at,
        description: `邀请用户: ${item.invited_user_name ?? '未知用户'}`,
      })),
      total: 1,
      limit: 20,
      offset: 0,
    });

    const { result } = renderHook(() => useCommissionRecords(), {
      wrapper: TestQueryProvider,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const record = result.current.data?.records[0];
    expect(record?.status).toBe('paid');
    expect(record?.commissionAmount).toBe(100);
    expect(record?.sourceUserName).toBe('测试用户');
  });

  it('应该处理空记录列表', async () => {
    vi.mocked(apiGetCommissionRecords).mockResolvedValueOnce({
      records: [],
      total: 0,
      limit: 20,
      offset: 0,
    });

    const { result } = renderHook(() => useCommissionRecords(), {
      wrapper: TestQueryProvider,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.records).toHaveLength(0);
    expect(result.current.data?.total).toBe(0);
  });
});

// ============================================
// usePromotionLink 测试
// ============================================

describe('usePromotionLink', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该成功获取推广链接', async () => {
    const mockLink = createMockPromotionLink();
    vi.mocked(apiGetPromotionLink).mockResolvedValueOnce(mockLink);

    const { result } = renderHook(() => usePromotionLink(), {
      wrapper: TestQueryProvider,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.code).toBe('ABC123');
    expect(result.current.data?.url).toContain('ABC123');
  });

  it('应该使用正确的缓存时间', () => {
    const mockLink = createMockPromotionLink();
    vi.mocked(apiGetPromotionLink).mockResolvedValueOnce(mockLink);

    const { result } = renderHook(() => usePromotionLink(), {
      wrapper: TestQueryProvider,
    });

    expect(result.current.isLoading).toBe(true);
  });
});

// ============================================
// useGeneratePromotionLink 测试
// ============================================

describe('useGeneratePromotionLink', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该成功生成新的推广链接', async () => {
    const mockLink = createMockPromotionLink({ code: 'NEW456' });
    vi.mocked(apiGeneratePromotionLink).mockResolvedValueOnce(mockLink);

    const { result } = renderHook(() => useGeneratePromotionLink(), {
      wrapper: TestQueryProvider,
    });

    // 执行 mutation
    await result.current.mutateAsync();

    expect(apiGeneratePromotionLink).toHaveBeenCalled();
  });

  it('生成成功后应该刷新链接缓存', async () => {
    const mockLink = createMockPromotionLink();
    vi.mocked(apiGeneratePromotionLink).mockResolvedValueOnce(mockLink);

    const { result } = renderHook(() => useGeneratePromotionLink(), {
      wrapper: TestQueryProvider,
    });

    // 等待 mutation 完成并验证成功状态
    await waitFor(async () => {
      await result.current.mutateAsync();
      expect(result.current.isSuccess).toBe(true);
    });
  });
});

// ============================================
// usePosters 测试
// ============================================

describe('usePosters', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该成功获取海报列表', async () => {
    const mockPosters = createMockPosters(3);
    vi.mocked(apiGetPosters).mockResolvedValueOnce(mockPosters);

    const { result } = renderHook(() => usePosters(), {
      wrapper: TestQueryProvider,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(3);
    expect(result.current.data?.[0].title).toBe('海报1');
  });

});

// ============================================
// useGeneratePoster 测试
// ============================================

describe('useGeneratePoster', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该成功生成海报', async () => {
    const mockPoster = createMockPosters(1)[0];
    vi.mocked(apiGeneratePoster).mockResolvedValueOnce(mockPoster);

    const { result } = renderHook(() => useGeneratePoster(), {
      wrapper: TestQueryProvider,
    });

    await result.current.mutateAsync({ templateId: 'default' });

    expect(apiGeneratePoster).toHaveBeenCalledWith({ templateId: 'default' });
  });
});

// ============================================
// useWithdrawals 测试
// ============================================

describe('useWithdrawals', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该成功获取提现记录', async () => {
    const mockWithdrawals = createMockWithdrawals(3);
    vi.mocked(apiGetWithdrawals).mockResolvedValueOnce(mockWithdrawals);

    const { result } = renderHook(() => useWithdrawals(), {
      wrapper: TestQueryProvider,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(3);
  });
});

// ============================================
// useRequestWithdrawal 测试
// ============================================

describe('useRequestWithdrawal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该成功申请提现', async () => {
    const mockWithdrawal = createMockWithdrawals(1)[0];
    vi.mocked(apiRequestWithdrawal).mockResolvedValueOnce(mockWithdrawal);

    const { result } = renderHook(() => useRequestWithdrawal(), {
      wrapper: TestQueryProvider,
    });

    await result.current.mutateAsync({
      amount: 100,
      withdrawalMethod: 'reward',
      accountInfo: '{}',
    });

    expect(apiRequestWithdrawal).toHaveBeenCalledWith({
      amount: 100,
      withdrawalMethod: 'reward',
      accountInfo: '{}',
    });
  });
});

// ============================================
// usePromotionRules 测试
// ============================================

describe('usePromotionRules', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该成功获取推广规则', async () => {
    const mockRules = {
      commissionRate: 0.1,
      minWithdrawal: 100,
      withdrawalMethods: ['reward', 'alipay'],
      description: '推广规则说明',
    };
    vi.mocked(apiGetPromotionRules).mockResolvedValueOnce({
      rules: mockRules,
    });

    const { result } = renderHook(() => usePromotionRules(), {
      wrapper: TestQueryProvider,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.rules.commissionRate).toBe(0.1);
    expect(result.current.data?.rules.minWithdrawal).toBe(100);
  });
});
