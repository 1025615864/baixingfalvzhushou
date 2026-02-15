// ============================================
// CheckInButton 组件测试
// ============================================

import { vi, type Mock } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

import { CheckInButton, CheckInButtonCompact } from '../components/CheckInButton';
import { useCheckIn } from '../hooks/usePoints';

vi.mock('../hooks/usePoints', () => ({
  useCheckIn: vi.fn(),
}));

vi.mock('../components/CheckInSuccessAnimation', () => ({
  CheckInSuccessAnimation: ({ isAnimating }: { isAnimating: boolean }) => (
    isAnimating ? <div data-testid="success-animation">Animation</div> : null
  ),
}));

const mockCheckInResult = {
  success: true,
  pointsEarned: 10,
  continuousDays: 6,
  totalPoints: 1010,
};

describe('CheckInButton', () => {
  const mockMutateAsync = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useCheckIn as Mock).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isSuccess: false,
      isError: false,
    });
  });

  it('应该正确渲染签到按钮', () => {
    render(<CheckInButton data-testid="checkin-button" />);
    expect(screen.getByTestId('checkin-button')).toBeInTheDocument();
    expect(screen.getByText('签到')).toBeInTheDocument();
  });

  it('应该显示连续签到天数', () => {
    render(<CheckInButton continuousDays={5} />);
    expect(screen.getByText('5天')).toBeInTheDocument();
  });

  it('点击签到按钮应该触发签到', async () => {
    mockMutateAsync.mockResolvedValueOnce(mockCheckInResult);
    render(<CheckInButton data-testid="checkin-button" />);
    fireEvent.click(screen.getByTestId('checkin-button'));
    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledTimes(1);
    });
  });

  it('签到成功应该调用 onCheckInSuccess 回调', async () => {
    const onCheckInSuccess = vi.fn();
    mockMutateAsync.mockResolvedValueOnce(mockCheckInResult);
    render(<CheckInButton onCheckInSuccess={onCheckInSuccess} />);
    fireEvent.click(screen.getByText('签到'));
    await waitFor(() => {
      expect(onCheckInSuccess).toHaveBeenCalledWith(10, 6);
    });
  });

  it('已经签到应该显示已签到状态', () => {
    render(<CheckInButton hasCheckedIn={true} continuousDays={3} />);
    expect(screen.getByText('已签到')).toBeInTheDocument();
  });
});

describe('CheckInButtonCompact', () => {
  const mockMutateAsync = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useCheckIn as Mock).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    });
  });

  it('应该正确渲染紧凑版按钮', () => {
    render(<CheckInButtonCompact data-testid="checkin-compact" />);
    expect(screen.getByTestId('checkin-compact')).toBeInTheDocument();
  });

  it('已经签到应该显示绿色状态', () => {
    render(<CheckInButtonCompact hasCheckedIn={true} />);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-green-100');
  });
});