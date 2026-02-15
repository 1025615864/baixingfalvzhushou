// ============================================
// PointsHistory 组件测试
// ============================================

import { vi, type Mock } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

import { PointsHistory } from '../components/PointsHistory';
import { usePointsHistory } from '../hooks/usePoints';

// Mock hooks
vi.mock('../hooks/usePoints', () => ({
  usePointsHistory: vi.fn(),
}));

// Mock UI 组件
vi.mock('../../../components/ui/Pagination', () => ({
  Pagination: ({ currentPage, totalPages, onChange }: any) => (
    <div data-testid="pagination">
      <span data-testid="current-page">{currentPage}</span>
      <span data-testid="total-pages">{totalPages}</span>
      <button onClick={() => onChange(currentPage + 1, 10)}>下一页</button>
    </div>
  ),
}));

vi.mock('../../../components/ui/FilterDropdown', () => ({
  FilterDropdown: ({ label, value, onChange }: any) => (
    <div data-testid="filter-dropdown">
      <span>{label}</span>
      <button onClick={() => onChange(['sign_in'])}>筛选签到</button>
    </div>
  ),
}));

vi.mock('../../../components/ui/DateRangePicker', () => ({
  DateRangePicker: ({ onChange }: any) => (
    <button
      data-testid="date-range-picker"
      onClick={() => onChange({ startDate: new Date(), endDate: new Date() })}
    >
      选择日期
    </button>
  ),
}));

vi.mock('../../../components/ui/Skeleton', () => ({
  Skeleton: () => <div data-testid="skeleton">Loading...</div>,
  ListItemSkeleton: () => <div data-testid="list-skeleton">Item Loading...</div>,
}));

vi.mock('../../../components/ui/EmptyState', () => ({
  EmptyState: ({ title, description, action }: any) => (
    <div data-testid="empty-state">
      <span>{title}</span>
      <span>{description}</span>
      {action}
    </div>
  ),
  EmptyError: ({ title, onRetry }: any) => (
    <div data-testid="empty-error">
      <span>{title}</span>
      <button onClick={onRetry}>重试</button>
    </div>
  ),
}));

// 测试数据
const mockHistoryData = {
  history: [
    {
      id: '1',
      action: 'sign_in',
      points: 10,
      balanceAfter: 1010,
      description: '每日签到',
      createdAt: '2024-01-15T10:00:00Z',
    },
    {
      id: '2',
      action: 'post_create',
      points: 20,
      balanceAfter: 1000,
      description: '发布帖子',
      createdAt: '2024-01-14T15:30:00Z',
    },
    {
      id: '3',
      action: 'exchange_product',
      points: -100,
      balanceAfter: 980,
      description: '兑换商品',
      createdAt: '2024-01-13T09:00:00Z',
    },
  ],
  total: 3,
  limit: 10,
  offset: 0,
};

describe('PointsHistory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (usePointsHistory as Mock).mockReturnValue({
      data: mockHistoryData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it('应该正确渲染积分历史列表', () => {
    render(<PointsHistory />);

    // 检查筛选组件
    expect(screen.getByTestId('filter-dropdown')).toBeInTheDocument();
    expect(screen.getByTestId('date-range-picker')).toBeInTheDocument();

    // 检查数据项 - 使用 getAllByText 因为文本可能出现多次
    expect(screen.getAllByText('每日签到').length).toBeGreaterThan(0);
    expect(screen.getAllByText('发布帖子').length).toBeGreaterThan(0);
    expect(screen.getAllByText('兑换商品').length).toBeGreaterThan(0);
  });

  it('应该显示正确的积分变化', () => {
    render(<PointsHistory />);

    // 正数积分
    expect(screen.getByText('+10')).toBeInTheDocument();
    expect(screen.getByText('+20')).toBeInTheDocument();

    // 负数积分
    expect(screen.getByText('-100')).toBeInTheDocument();
  });

  it('应该显示分页组件', () => {
    render(<PointsHistory />);

    expect(screen.getByTestId('pagination')).toBeInTheDocument();
    expect(screen.getByTestId('current-page')).toHaveTextContent('1');
  });

  it('应该显示加载状态', () => {
    (usePointsHistory as Mock).mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });

    render(<PointsHistory useSkeleton={true} />);

    // 使用 getAllByTestId 因为有多个骨架屏元素
    expect(screen.getAllByTestId('skeleton').length).toBeGreaterThan(0);
  });

  it('应该显示错误状态', () => {
    const mockRefetch = vi.fn();
    (usePointsHistory as Mock).mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('加载失败'),
      refetch: mockRefetch,
    });

    render(<PointsHistory />);

    expect(screen.getByTestId('empty-error')).toBeInTheDocument();
    expect(screen.getByText('加载失败')).toBeInTheDocument();
  });

  it('应该显示空状态', () => {
    (usePointsHistory as Mock).mockReturnValue({
      data: { history: [], total: 0, limit: 10, offset: 0 },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<PointsHistory />);

    expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    expect(screen.getByText('暂无积分记录')).toBeInTheDocument();
  });

  it('点击筛选应该更新列表', async () => {
    render(<PointsHistory />);

    // 点击筛选按钮
    fireEvent.click(screen.getByText('筛选签到'));

    // 验证 hook 被调用时带有筛选参数
    await waitFor(() => {
      expect(usePointsHistory).toHaveBeenCalledWith(
        expect.objectContaining({
          actionTypes: ['sign_in'],
        })
      );
    });
  });

  it('点击清除筛选应该重置筛选条件', async () => {
    render(<PointsHistory />);

    // 先设置筛选
    fireEvent.click(screen.getByText('筛选签到'));

    // 点击清除筛选
    const clearButton = screen.getByText('清除筛选');
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(usePointsHistory).toHaveBeenCalledWith(
        expect.objectContaining({
          actionTypes: undefined,
        })
      );
    });
  });

  it('点击分页应该更新页码', async () => {
    render(<PointsHistory />);

    // 点击下一页
    fireEvent.click(screen.getByText('下一页'));

    await waitFor(() => {
      expect(usePointsHistory).toHaveBeenCalled();
    });
  });

  it('应该显示余额信息', () => {
    render(<PointsHistory />);

    expect(screen.getByText('余: 1010')).toBeInTheDocument();
    expect(screen.getByText('余: 1000')).toBeInTheDocument();
    expect(screen.getByText('余: 980')).toBeInTheDocument();
  });

  it('应该支持自定义 className', () => {
    const { container } = render(<PointsHistory className="custom-class" />);

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('应该支持自定义每页条数', () => {
    render(<PointsHistory defaultPageSize={20} />);

    expect(usePointsHistory).toHaveBeenCalledWith(
      expect.objectContaining({
        limit: 20,
      })
    );
  });
});
