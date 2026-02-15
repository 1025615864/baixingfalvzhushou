// ============================================
// EmptyState 组件测试
// ============================================

import { render, screen } from '@testing-library/react';

import { EmptyState, type EmptyIconType } from '../EmptyState';

describe('EmptyState', () => {
  describe('基础渲染', () => {
    it('应该正确渲染默认空状态', () => {
      render(<EmptyState data-testid="empty-state" />);
      
      const emptyState = screen.getByTestId('empty-state');
      expect(emptyState).toBeInTheDocument();
      
      // 默认标题
      expect(screen.getByText('暂无数据')).toBeInTheDocument();
    });

    it('应该渲染自定义标题和描述', () => {
      render(
        <EmptyState
          title="搜索无结果"
          description="请尝试其他关键词"
          data-testid="empty-state"
        />
      );
      
      expect(screen.getByText('搜索无结果')).toBeInTheDocument();
      expect(screen.getByText('请尝试其他关键词')).toBeInTheDocument();
    });

    it('应该支持不显示描述', () => {
      render(
        <EmptyState title="无数据" data-testid="empty-state" />
      );
      
      expect(screen.getByText('无数据')).toBeInTheDocument();
      // 描述不应存在
      const desc = screen.queryByRole('paragraph');
      expect(desc).not.toBeInTheDocument();
    });
  });

  describe('预设图标', () => {
    const iconTypes: EmptyIconType[] = [
      'default',
      'search',
      'box',
      'document',
      'message',
      'notification',
      'cart',
      'network',
      'error',
    ];

    iconTypes.forEach((iconType) => {
      it(`应该正确渲染 ${iconType} 图标`, () => {
        const { container } = render(
          <EmptyState icon={iconType} title={`${iconType} 图标`} />
        );
        
        // 检查 SVG 是否存在
        const svg = container.querySelector('svg');
        expect(svg).toBeInTheDocument();
      });
    });

    it('未知图标类型应使用默认图标', () => {
      const { container } = render(
        <EmptyState icon={'unknown' as EmptyIconType} title="未知图标" />
      );
      
      // 应该仍然渲染图标（使用默认值）
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('自定义图标', () => {
    it('应该渲染自定义图标', () => {
      const customIcon = <span data-testid="custom-icon">🔥</span>;
      
      render(
        <EmptyState
          icon="custom"
          customIcon={customIcon}
          title="自定义图标"
          data-testid="empty-state"
        />
      );
      
      expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
    });
  });

  describe('尺寸变体', () => {
    it('应该支持 sm 尺寸', () => {
      render(<EmptyState size="sm" data-testid="empty-state" />);
      
      const emptyState = screen.getByTestId('empty-state');
      expect(emptyState).toHaveClass('p-4');
      
      // 标题尺寸
      const title = screen.getByText('暂无数据');
      expect(title).toHaveClass('text-base');
    });

    it('应该支持 md 尺寸', () => {
      render(<EmptyState size="md" data-testid="empty-state" />);
      
      const emptyState = screen.getByTestId('empty-state');
      expect(emptyState).toHaveClass('p-8');
      
      const title = screen.getByText('暂无数据');
      expect(title).toHaveClass('text-lg');
    });

    it('应该支持 lg 尺寸', () => {
      render(<EmptyState size="lg" data-testid="empty-state" />);
      
      const emptyState = screen.getByTestId('empty-state');
      expect(emptyState).toHaveClass('p-12');
      
      const title = screen.getByText('暂无数据');
      expect(title).toHaveClass('text-xl');
    });
  });

  describe('紧凑模式', () => {
    it('应该支持紧凑模式', () => {
      render(<EmptyState compact data-testid="empty-state" />);
      
      const emptyState = screen.getByTestId('empty-state');
      expect(emptyState).toHaveClass('p-4');
    });

    it('紧凑模式下标题间距应减小', () => {
      render(<EmptyState compact title="紧凑" />);
      
      const title = screen.getByText('紧凑');
      expect(title).toHaveClass('mb-1');
    });
  });

  describe('操作按钮', () => {
    it('应该渲染操作按钮', () => {
      render(
        <EmptyState
          title="购物车为空"
          action={<button data-testid="action-btn">去购物</button>}
        />
      );
      
      expect(screen.getByTestId('action-btn')).toBeInTheDocument();
    });

    it('应该支持复杂的操作按钮', () => {
      render(
        <EmptyState
          title="网络错误"
          icon="network"
          action={
            <div>
              <button data-testid="retry-btn">重试</button>
              <button data-testid="contact-btn">联系客服</button>
            </div>
          }
        />
      );
      
      expect(screen.getByTestId('retry-btn')).toBeInTheDocument();
      expect(screen.getByTestId('contact-btn')).toBeInTheDocument();
    });
  });

  describe('自定义类名', () => {
    it('应该支持自定义类名', () => {
      render(<EmptyState className="custom-class" data-testid="empty-state" />);
      
      const emptyState = screen.getByTestId('empty-state');
      expect(emptyState).toHaveClass('custom-class');
    });
  });

  describe('暗色模式', () => {
    it('应该包含暗色模式样式类', () => {
      render(<EmptyState data-testid="empty-state" />);

      const emptyState = screen.getByTestId('empty-state');
      // 检查子元素中是否有暗色模式相关的类
      const darkElements = emptyState.querySelectorAll('[class*="dark:"]');
      expect(darkElements.length).toBeGreaterThan(0);
    });
  });
});