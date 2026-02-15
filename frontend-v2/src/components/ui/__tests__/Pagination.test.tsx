// ============================================
// Pagination 组件测试
// ============================================

import { vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import { Pagination } from '../Pagination';

describe('Pagination', () => {
  const mockOnChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('基础渲染', () => {
    it('应该正确渲染分页组件', () => {
      render(<Pagination total={100} data-testid="pagination" />);
      
      const pagination = screen.getByTestId('pagination');
      expect(pagination).toBeInTheDocument();
    });

    it('当总条目数小于等于0时不应渲染', () => {
      const { container } = render(<Pagination total={0} />);
      
      expect(container.firstChild).toBeNull();
    });

    it('应该显示总条目数', () => {
      render(<Pagination total={100} showTotal />);

      // 检查 "共" 文本是否存在
      expect(screen.getByText(/共/)).toBeInTheDocument();
      // 检查 "100 条" 文本是否存在（使用更具体的匹配）
      expect(screen.getByText(/100\s*条/)).toBeInTheDocument();
    });
  });

  describe('页码按钮', () => {
    it('应该渲染首页和末页按钮', () => {
      render(<Pagination total={100} />);
      
      // 检查导航按钮是否存在（使用 title 属性）
      expect(screen.getByTitle('首页')).toBeInTheDocument();
      expect(screen.getByTitle('末页')).toBeInTheDocument();
      expect(screen.getByTitle('上一页')).toBeInTheDocument();
      expect(screen.getByTitle('下一页')).toBeInTheDocument();
    });

    it('第一页时首页和上一页应该禁用', () => {
      render(<Pagination total={100} />);
      
      const firstBtn = screen.getByTitle('首页');
      const prevBtn = screen.getByTitle('上一页');
      
      expect(firstBtn).toBeDisabled();
      expect(prevBtn).toBeDisabled();
    });

    it('最后一页时末页和下一页应该禁用', () => {
      render(<Pagination total={100} initialPage={5} initialPageSize={20} />);
      
      const lastBtn = screen.getByTitle('末页');
      const nextBtn = screen.getByTitle('下一页');
      
      expect(lastBtn).toBeDisabled();
      expect(nextBtn).toBeDisabled();
    });

    it('应该渲染页码数字按钮', () => {
      render(<Pagination total={100} />);
      
      // 应该显示页码按钮
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  describe('分页操作', () => {
    it('点击下一页应该触发 onChange', () => {
      render(<Pagination total={100} onChange={mockOnChange} />);
      
      const nextBtn = screen.getByTitle('下一页');
      fireEvent.click(nextBtn);
      
      expect(mockOnChange).toHaveBeenCalledWith(2, 20);
    });

    it('点击上一页应该触发 onChange', () => {
      render(<Pagination total={100} initialPage={2} onChange={mockOnChange} />);
      
      const prevBtn = screen.getByTitle('上一页');
      fireEvent.click(prevBtn);
      
      expect(mockOnChange).toHaveBeenCalledWith(1, 20);
    });

    it('点击首页应该触发 onChange', () => {
      render(<Pagination total={100} initialPage={3} onChange={mockOnChange} />);
      
      const firstBtn = screen.getByTitle('首页');
      fireEvent.click(firstBtn);
      
      expect(mockOnChange).toHaveBeenCalledWith(1, 20);
    });

    it('点击末页应该触发 onChange', () => {
      render(<Pagination total={100} onChange={mockOnChange} />);
      
      const lastBtn = screen.getByTitle('末页');
      fireEvent.click(lastBtn);
      
      expect(mockOnChange).toHaveBeenCalledWith(5, 20);
    });

    it('点击页码数字应该触发 onChange', () => {
      render(<Pagination total={100} onChange={mockOnChange} />);
      
      // 找到页码为 2 的按钮
      const page2Btn = screen.getByRole('button', { name: '2' });
      fireEvent.click(page2Btn);
      
      expect(mockOnChange).toHaveBeenCalledWith(2, 20);
    });
  });

  describe('每页条数选择', () => {
    it('应该显示每页条数选择器', () => {
      render(<Pagination total={100} showPageSize />);
      
      const select = screen.getByRole('combobox');
      expect(select).toBeInTheDocument();
    });

    it('选择每页条数应该触发 onChange', () => {
      render(<Pagination total={100} showPageSize onChange={mockOnChange} />);
      
      const select = screen.getByRole('combobox');
      fireEvent.change(select, { target: { value: '50' } });
      
      expect(mockOnChange).toHaveBeenCalledWith(1, 50);
    });

    it('不应该显示每页条数选择器（当 showPageSize 为 false）', () => {
      render(<Pagination total={100} showPageSize={false} />);
      
      const select = screen.queryByRole('combobox');
      expect(select).not.toBeInTheDocument();
    });
  });

  describe('快速跳转', () => {
    it('应该显示快速跳转输入框', () => {
      render(<Pagination total={100} showQuickJumper />);
      
      const input = screen.getByPlaceholderText(/页/);
      expect(input).toBeInTheDocument();
    });

    it('快速跳转应该触发 onChange', () => {
      render(<Pagination total={100} showQuickJumper onChange={mockOnChange} />);
      
      const input = screen.getByPlaceholderText(/页/);
      fireEvent.change(input, { target: { value: '3' } });
      
      // 按 Enter 或点击跳转按钮
      const jumpBtn = screen.getByRole('button', { name: /跳转/ });
      fireEvent.click(jumpBtn);
      
      expect(mockOnChange).toHaveBeenCalledWith(3, 20);
    });

    it('不应该显示快速跳转（当 showQuickJumper 为 false）', () => {
      render(<Pagination total={100} showQuickJumper={false} />);
      
      const input = screen.queryByPlaceholderText(/页/);
      expect(input).not.toBeInTheDocument();
    });
  });

  describe('简洁模式', () => {
    it('应该渲染简洁模式', () => {
      render(<Pagination total={100} simple data-testid="pagination" />);
      
      const pagination = screen.getByTestId('pagination');
      expect(pagination).toBeInTheDocument();
    });

    it('简洁模式应该显示当前页/总页数', () => {
      render(<Pagination total={100} initialPage={2} initialPageSize={20} simple />);
      
      expect(screen.getByText('2 / 5')).toBeInTheDocument();
    });

    it('简洁模式应该有上一页和下一页按钮', () => {
      render(<Pagination total={100} simple />);
      
      expect(screen.getByTitle('上一页')).toBeInTheDocument();
      expect(screen.getByTitle('下一页')).toBeInTheDocument();
    });

    it('简洁模式不应该显示总条目数、每页条数选择和快速跳转', () => {
      render(<Pagination total={100} simple />);
      
      expect(screen.queryByText(/共/)).not.toBeInTheDocument();
      expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
      expect(screen.queryByPlaceholderText(/页/)).not.toBeInTheDocument();
    });
  });

  describe('自定义配置', () => {
    it('应该支持自定义每页条数选项', () => {
      render(
        <Pagination
          total={100}
          showPageSize
          pageSizeOptions={[5, 10, 15]}
        />
      );
      
      const select = screen.getByRole('combobox');
      expect(select).toBeInTheDocument();
    });

    it('应该支持自定义初始页码', () => {
      render(<Pagination total={100} initialPage={3} simple />);
      
      expect(screen.getByText('3 / 5')).toBeInTheDocument();
    });

    it('应该支持自定义初始每页条数', () => {
      render(
        <Pagination
          total={100}
          initialPageSize={10}
          simple
        />
      );
      
      expect(screen.getByText(/\/ 10/)).toBeInTheDocument();
    });

    it('应该支持自定义类名', () => {
      render(<Pagination total={100} className="custom-class" data-testid="pagination" />);
      
      const pagination = screen.getByTestId('pagination');
      expect(pagination).toHaveClass('custom-class');
    });
  });

  describe('边界情况', () => {
    it('总条目数为0时不应该渲染', () => {
      const { container } = render(<Pagination total={0} />);
      expect(container.firstChild).toBeNull();
    });

    it('负数总条目数不应该渲染', () => {
      const { container } = render(<Pagination total={-1} />);
      expect(container.firstChild).toBeNull();
    });

    it('超大页码应该正确处理', () => {
      render(<Pagination total={1000} initialPage={50} initialPageSize={20} simple />);
      
      expect(screen.getByText('50 / 50')).toBeInTheDocument();
    });
  });
});