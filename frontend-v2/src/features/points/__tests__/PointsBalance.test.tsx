// ============================================
// PointsBalance 组件测试
// ============================================

import { vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import { PointsBalance } from '../components/PointsBalance';

describe('PointsBalance', () => {
  describe('默认变体 (default)', () => {
    it('应该正确渲染默认变体', () => {
      render(<PointsBalance balance={1000} data-testid="points-balance" />);
      
      const component = screen.getByTestId('points-balance');
      expect(component).toBeInTheDocument();
      expect(screen.getByText('我的积分')).toBeInTheDocument();
      expect(screen.getByText('1,000')).toBeInTheDocument();
    });

    it('应该显示自定义余额', () => {
      render(<PointsBalance balance={5000} data-testid="points-balance" />);
      
      expect(screen.getByText('5,000')).toBeInTheDocument();
    });

    it('应该支持加载状态', () => {
      render(<PointsBalance balance={0} isLoading data-testid="points-balance" />);
      
      const skeletons = document.querySelectorAll('.bg-gray-200');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('应该支持点击事件', () => {
      const handleClick = vi.fn();
      render(
        <PointsBalance 
          balance={1000} 
          onClick={handleClick} 
          data-testid="points-balance" 
        />
      );
      
      const component = screen.getByTestId('points-balance');
      fireEvent.click(component);
      
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('行内变体 (inline)', () => {
    it('应该正确渲染行内变体', () => {
      render(
        <PointsBalance 
          balance={2500} 
          variant="inline" 
          data-testid="points-balance" 
        />
      );
      
      expect(screen.getByTestId('points-balance')).toBeInTheDocument();
      expect(screen.getByText('2,500')).toBeInTheDocument();
    });

    it('行内变体应该使用行内样式', () => {
      render(<PointsBalance balance={1000} variant="inline" />);
      
      const container = document.querySelector('.inline-flex');
      expect(container).toBeInTheDocument();
    });
  });

  describe('紧凑变体 (compact)', () => {
    it('应该正确渲染紧凑变体', () => {
      render(
        <PointsBalance 
          balance={800} 
          variant="compact" 
          data-testid="points-balance" 
        />
      );
      
      expect(screen.getByTestId('points-balance')).toBeInTheDocument();
      expect(screen.getByText('800')).toBeInTheDocument();
    });
  });

  describe('详细变体 (detailed)', () => {
    it('应该正确渲染详细变体', () => {
      render(
        <PointsBalance 
          balance={5000} 
          variant="detailed" 
          data-testid="points-balance" 
        />
      );
      
      expect(screen.getByTestId('points-balance')).toBeInTheDocument();
      expect(screen.getByText('5,000')).toBeInTheDocument();
      expect(screen.getByText('当前可用余额')).toBeInTheDocument();
    });

    it('应该显示今日获得积分', () => {
      render(
        <PointsBalance 
          balance={5000} 
          variant="detailed" 
          todayEarned={150}
        />
      );
      
      expect(screen.getByText('+150')).toBeInTheDocument();
      expect(screen.getByText('今日获得')).toBeInTheDocument();
    });

    it('应该显示连续签到天数', () => {
      render(
        <PointsBalance 
          balance={5000} 
          variant="detailed" 
          continuousDays={7}
        />
      );
      
      expect(screen.getByText('7天')).toBeInTheDocument();
      expect(screen.getByText('连续签到')).toBeInTheDocument();
    });
  });

  describe('数字格式化', () => {
    it('应该正确格式化千分位数字', () => {
      // 测试 compact 变体，它不使用动画
      const { rerender } = render(<PointsBalance balance={1000} variant="compact" />);
      expect(screen.getByText('1,000')).toBeInTheDocument();

      rerender(<PointsBalance balance={1000000} variant="compact" />);
      expect(screen.getByText('1,000,000')).toBeInTheDocument();

      rerender(<PointsBalance balance={0} variant="compact" />);
      expect(screen.getByText('0')).toBeInTheDocument();
    });
  });
});