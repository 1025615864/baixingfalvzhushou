// ============================================
// Skeleton 组件测试
// ============================================

import { render, screen } from '@testing-library/react';

import {
  Skeleton,
  TextSkeleton,
  CardSkeleton,
  ListItemSkeleton,
  StatCardSkeleton,
  TableSkeleton,
} from '../Skeleton';

describe('Skeleton', () => {
  describe('基础 Skeleton 组件', () => {
    it('应该正确渲染基础骨架屏', () => {
      render(<Skeleton data-testid="skeleton" />);
      
      const skeleton = screen.getByTestId('skeleton');
      expect(skeleton).toBeInTheDocument();
      expect(skeleton).toHaveClass('bg-gray-200');
      expect(skeleton).toHaveClass('rounded-md');
      expect(skeleton).toHaveClass('animate-pulse');
    });

    it('应该支持自定义宽度和高度（数字）', () => {
      render(<Skeleton data-testid="skeleton" width={200} height={24} />);
      
      const skeleton = screen.getByTestId('skeleton');
      expect(skeleton).toHaveStyle({
        width: '200px',
        height: '24px',
      });
    });

    it('应该支持自定义宽度和高度（字符串）', () => {
      render(<Skeleton data-testid="skeleton" width="100%" height="3rem" />);
      
      const skeleton = screen.getByTestId('skeleton');
      expect(skeleton).toHaveStyle({
        width: '100%',
        height: '3rem',
      });
    });

    it('应该支持不同的圆角变体', () => {
      const { rerender } = render(<Skeleton data-testid="skeleton" rounded="none" />);
      expect(screen.getByTestId('skeleton')).toHaveClass('rounded-none');

      rerender(<Skeleton data-testid="skeleton" rounded="sm" />);
      expect(screen.getByTestId('skeleton')).toHaveClass('rounded-sm');

      rerender(<Skeleton data-testid="skeleton" rounded="lg" />);
      expect(screen.getByTestId('skeleton')).toHaveClass('rounded-lg');

      rerender(<Skeleton data-testid="skeleton" rounded="xl" />);
      expect(screen.getByTestId('skeleton')).toHaveClass('rounded-xl');

      rerender(<Skeleton data-testid="skeleton" rounded="full" />);
      expect(screen.getByTestId('skeleton')).toHaveClass('rounded-full');
    });

    it('应该支持禁用动画', () => {
      render(<Skeleton data-testid="skeleton" animate={false} />);
      
      const skeleton = screen.getByTestId('skeleton');
      expect(skeleton).not.toHaveClass('animate-pulse');
    });

    it('应该支持自定义类名', () => {
      render(<Skeleton data-testid="skeleton" className="custom-class" />);
      
      const skeleton = screen.getByTestId('skeleton');
      expect(skeleton).toHaveClass('custom-class');
    });

    it('应该支持子元素', () => {
      render(
        <Skeleton data-testid="skeleton">
          <div data-testid="child">子元素</div>
        </Skeleton>
      );
      
      expect(screen.getByTestId('child')).toBeInTheDocument();
    });
  });

  describe('TextSkeleton 变体', () => {
    it('应该正确渲染单行文本骨架', () => {
      render(<TextSkeleton data-testid="text-skeleton" />);
      
      const container = screen.getByTestId('text-skeleton');
      expect(container).toBeInTheDocument();
      
      // 检查是否有骨架元素
      const skeletons = container.querySelectorAll('.bg-gray-200');
      expect(skeletons.length).toBe(1);
    });

    it('应该支持多行文本', () => {
      render(<TextSkeleton data-testid="text-skeleton" lines={3} />);
      
      const container = screen.getByTestId('text-skeleton');
      const skeletons = container.querySelectorAll('.bg-gray-200');
      expect(skeletons.length).toBe(3);
    });

    it('应该支持自定义最后一行宽度', () => {
      render(<TextSkeleton lines={2} lastLineWidth="60%" />);
      
      // 应该正常渲染，不报错
      expect(document.querySelector('.space-y-2')).toBeInTheDocument();
    });

    it('应该支持自定义类名', () => {
      render(<TextSkeleton data-testid="text-skeleton" className="custom-class" />);
      
      const container = screen.getByTestId('text-skeleton');
      expect(container).toHaveClass('custom-class');
    });
  });

  describe('CardSkeleton 变体', () => {
    it('应该正确渲染卡片骨架（带图片）', () => {
      render(<CardSkeleton data-testid="card-skeleton" />);
      
      const card = screen.getByTestId('card-skeleton');
      expect(card).toBeInTheDocument();
      expect(card).toHaveClass('bg-white');
      expect(card).toHaveClass('rounded-lg');
    });

    it('应该支持无图片模式', () => {
      render(<CardSkeleton hasImage={false} />);
      
      // 检查是否没有图片骨架
      const images = document.querySelectorAll('[class*="h-40"]');
      expect(images.length).toBe(0);
    });

    it('应该支持自定义行数', () => {
      render(<CardSkeleton lines={4} />);
      
      // 应该正常渲染，包含文本骨架
      expect(document.querySelector('.space-y-2')).toBeInTheDocument();
    });

    it('应该支持自定义类名', () => {
      render(<CardSkeleton data-testid="card-skeleton" className="custom-class" />);
      
      const card = screen.getByTestId('card-skeleton');
      expect(card).toHaveClass('custom-class');
    });
  });

  describe('ListItemSkeleton 变体', () => {
    it('应该正确渲染列表项骨架（带头像）', () => {
      render(<ListItemSkeleton data-testid="list-item" />);
      
      const item = screen.getByTestId('list-item');
      expect(item).toBeInTheDocument();
      expect(item).toHaveClass('flex');
      expect(item).toHaveClass('items-center');
    });

    it('应该支持无头像模式', () => {
      render(<ListItemSkeleton avatar={false} />);
      
      // 检查是否没有圆形骨架（头像）
      const avatars = document.querySelectorAll('.rounded-full');
      // 只有一个文本骨架可能有圆角
      expect(avatars.length).toBeLessThanOrEqual(1);
    });

    it('应该支持自定义行数', () => {
      render(<ListItemSkeleton lines={3} />);
      
      // 应该正常渲染
      const item = document.querySelector('.flex');
      expect(item).toBeInTheDocument();
    });

    it('应该支持自定义类名', () => {
      render(<ListItemSkeleton data-testid="list-item" className="custom-class" />);
      
      const item = screen.getByTestId('list-item');
      expect(item).toHaveClass('custom-class');
    });
  });

  describe('StatCardSkeleton 变体', () => {
    it('应该正确渲染统计卡片骨架', () => {
      render(<StatCardSkeleton data-testid="stat-skeleton" />);
      
      const container = screen.getByTestId('stat-skeleton');
      expect(container).toBeInTheDocument();
      expect(container).toHaveClass('grid');
    });

    it('应该支持自定义卡片数量', () => {
      render(<StatCardSkeleton count={6} />);
      
      const cards = document.querySelectorAll('.bg-gray-50');
      expect(cards.length).toBe(6);
    });

    it('应该支持自定义类名', () => {
      render(<StatCardSkeleton data-testid="stat-skeleton" className="custom-class" />);
      
      const container = screen.getByTestId('stat-skeleton');
      expect(container).toHaveClass('custom-class');
    });
  });

  describe('TableSkeleton 变体', () => {
    it('应该正确渲染表格骨架', () => {
      render(<TableSkeleton data-testid="table-skeleton" />);
      
      const table = screen.getByTestId('table-skeleton');
      expect(table).toBeInTheDocument();
    });

    it('应该支持自定义行数和列数', () => {
      render(<TableSkeleton rows={3} columns={5} />);
      
      // 表头 + 3行 = 4行
      const rows = document.querySelectorAll('.flex');
      expect(rows.length).toBeGreaterThanOrEqual(3);
    });

    it('应该支持自定义类名', () => {
      render(<TableSkeleton data-testid="table-skeleton" className="custom-class" />);
      
      const table = screen.getByTestId('table-skeleton');
      expect(table).toHaveClass('custom-class');
    });
  });
});