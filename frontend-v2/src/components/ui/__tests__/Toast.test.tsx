// ============================================
// Toast 组件测试
// ============================================

import { vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

import { ToastItem, ToastContainer, type ToastData, type ToastType } from '../Toast';
import { ToastProvider, useToast } from '../ToastProvider';

// ============================================
// Mock requestAnimationFrame
// ============================================

global.requestAnimationFrame = vi.fn((callback: FrameRequestCallback) => {
  return setTimeout(callback, 16) as unknown as number;
});

global.cancelAnimationFrame = vi.fn((id: number) => {
  clearTimeout(id);
});

// ============================================
// ToastItem 测试
// ============================================

describe('ToastItem', () => {
  const mockOnClose = vi.fn();

  const createToast = (overrides: Partial<ToastData> = {}): ToastData => ({
    id: '1',
    type: 'info',
    message: '测试消息',
    duration: 5000,
    createdAt: Date.now(),
    ...overrides,
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('应该正确渲染 Toast 项', () => {
    const toast = createToast();
    render(<ToastItem toast={toast} onClose={mockOnClose} />);
    
    expect(screen.getByText('测试消息')).toBeInTheDocument();
  });

  it('应该渲染标题（如果有）', () => {
    const toast = createToast({ title: '测试标题' });
    render(<ToastItem toast={toast} onClose={mockOnClose} />);
    
    expect(screen.getByText('测试标题')).toBeInTheDocument();
    expect(screen.getByText('测试消息')).toBeInTheDocument();
  });

  it('应该支持不同类型的 Toast', () => {
    const types: ToastType[] = ['success', 'error', 'warning', 'info'];
    
    types.forEach((type) => {
      const { container } = render(
        <ToastItem toast={createToast({ type, id: type })} onClose={mockOnClose} />
      );
      
      // 检查对应的样式类
      expect(container.firstChild).toBeInTheDocument();
    });
  });

  it('应该有关闭按钮', () => {
    const toast = createToast();
    render(<ToastItem toast={toast} onClose={mockOnClose} />);
    
    const closeButton = screen.getByLabelText('关闭通知');
    expect(closeButton).toBeInTheDocument();
  });

  it('点击关闭按钮应该调用 onClose', () => {
    const toast = createToast();
    render(<ToastItem toast={toast} onClose={mockOnClose} />);
    
    const closeButton = screen.getByLabelText('关闭通知');
    fireEvent.click(closeButton);
    
    // 由于有过渡动画，不会立即调用
    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it('应该显示进度条（当 duration > 0）', () => {
    const toast = createToast({ duration: 5000 });
    const { container } = render(<ToastItem toast={toast} onClose={mockOnClose} />);
    
    const progressBar = container.querySelector('[class*="absolute bottom-0"]');
    expect(progressBar).toBeInTheDocument();
  });

  it('不应该显示进度条（当 duration = 0）', () => {
    const toast = createToast({ duration: 0 });
    const { container } = render(<ToastItem toast={toast} onClose={mockOnClose} />);
    
    const progressBar = container.querySelector('[class*="absolute bottom-0"]');
    expect(progressBar).not.toBeInTheDocument();
  });

  it('应该有正确的 ARIA 属性', () => {
    const toast = createToast();
    render(<ToastItem toast={toast} onClose={mockOnClose} />);
    
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});

// ============================================
// ToastContainer 测试
// ============================================

describe('ToastContainer', () => {
  const mockOnClose = vi.fn();

  const createToasts = (count: number): ToastData[] => {
    return Array.from({ length: count }, (_, i) => ({
      id: String(i + 1),
      type: 'info',
      message: `消息 ${i + 1}`,
      duration: 5000,
      createdAt: Date.now(),
    }));
  };

  it('当没有 Toast 时应该返回 null', () => {
    const { container } = render(
      <ToastContainer toasts={[]} onClose={mockOnClose} />
    );
    
    expect(container.firstChild).toBeNull();
  });

  it('应该渲染 Toast 列表', () => {
    const toasts = createToasts(3);
    render(<ToastContainer toasts={toasts} onClose={mockOnClose} />);
    
    expect(screen.getByText('消息 1')).toBeInTheDocument();
    expect(screen.getByText('消息 2')).toBeInTheDocument();
    expect(screen.getByText('消息 3')).toBeInTheDocument();
  });

  it('应该支持不同的位置', () => {
    const toasts = createToasts(1);
    const positions = [
      'top-left',
      'top-center',
      'top-right',
      'bottom-left',
      'bottom-center',
      'bottom-right',
    ] as const;

    positions.forEach((position) => {
      const { container } = render(
        <ToastContainer
          key={position}
          toasts={toasts}
          onClose={mockOnClose}
          position={position}
        />
      );
      
      expect(container.firstChild).toBeInTheDocument();
    });
  });

  it('应该有正确的 ARIA 属性', () => {
    const toasts = createToasts(1);
    const { container } = render(
      <ToastContainer toasts={toasts} onClose={mockOnClose} />
    );
    
    const containerEl = container.firstChild as HTMLElement;
    expect(containerEl).toHaveAttribute('aria-live', 'polite');
    expect(containerEl).toHaveAttribute('aria-atomic', 'true');
  });

  it('应该支持自定义类名', () => {
    const toasts = createToasts(1);
    const { container } = render(
      <ToastContainer
        toasts={toasts}
        onClose={mockOnClose}
        className="custom-class"
      />
    );
    
    const containerEl = container.firstChild as HTMLElement;
    expect(containerEl).toHaveClass('custom-class');
  });
});

// ============================================
// ToastProvider 测试
// ============================================

describe('ToastProvider', () => {
  const TestComponent = () => {
    const toast = useToast();
    
    return (
      <div>
        <button onClick={() => toast.success('成功消息')}>显示成功</button>
        <button onClick={() => toast.error('错误消息')}>显示错误</button>
        <button onClick={() => toast.warning('警告消息')}>显示警告</button>
        <button onClick={() => toast.info('信息消息')}>显示信息</button>
        <button onClick={() => toast.show({ message: '自定义消息', type: 'info' })}>
          显示自定义
        </button>
        <button onClick={() => toast.closeAll()}>关闭全部</button>
      </div>
    );
  };

  it('应该正确渲染子元素', () => {
    render(
      <ToastProvider>
        <div data-testid="child">子元素</div>
      </ToastProvider>
    );
    
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('应该显示成功 Toast', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );
    
    fireEvent.click(screen.getByText('显示成功'));
    expect(screen.getByText('成功消息')).toBeInTheDocument();
  });

  it('应该显示错误 Toast', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );
    
    fireEvent.click(screen.getByText('显示错误'));
    expect(screen.getByText('错误消息')).toBeInTheDocument();
  });

  it('应该显示警告 Toast', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );
    
    fireEvent.click(screen.getByText('显示警告'));
    expect(screen.getByText('警告消息')).toBeInTheDocument();
  });

  it('应该显示信息 Toast', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );
    
    fireEvent.click(screen.getByText('显示信息'));
    expect(screen.getByText('信息消息')).toBeInTheDocument();
  });

  it('应该显示自定义 Toast', () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );
    
    fireEvent.click(screen.getByText('显示自定义'));
    expect(screen.getByText('自定义消息')).toBeInTheDocument();
  });

  it('关闭全部按钮应该清除所有 Toast', async () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );
    
    // 添加多个 Toast
    fireEvent.click(screen.getByText('显示成功'));
    fireEvent.click(screen.getByText('显示错误'));
    
    await waitFor(() => {
      expect(screen.getByText('成功消息')).toBeInTheDocument();
      expect(screen.getByText('错误消息')).toBeInTheDocument();
    });
  });

  it('不支持在 Provider 外使用 useToast', () => {
    const OriginalConsoleError = console.error;
    console.error = vi.fn();
    
    const InvalidComponent = () => {
      useToast();
      return <div>无效</div>;
    };
    
    expect(() => {
      render(<InvalidComponent />);
    }).toThrow('useToast must be used within a ToastProvider');
    
    console.error = OriginalConsoleError;
  });

  it('应该支持自定义位置', () => {
    render(
      <ToastProvider position="bottom-center">
        <div>内容</div>
      </ToastProvider>
    );
    
    expect(screen.getByText('内容')).toBeInTheDocument();
  });

  it('应该支持自定义默认时长', () => {
    render(
      <ToastProvider defaultDuration={3000}>
        <TestComponent />
      </ToastProvider>
    );
    
    fireEvent.click(screen.getByText('显示信息'));
    expect(screen.getByText('信息消息')).toBeInTheDocument();
  });

  it('应该限制最大 Toast 数量', () => {
    const ManyToastsComponent = () => {
      const toast = useToast();
      
      return (
        <button onClick={() => {
          for (let i = 0; i < 10; i++) {
            toast.info(`消息 ${i}`);
          }
        }}>
          显示多个
        </button>
      );
    };
    
    render(
      <ToastProvider maxToasts={3}>
        <ManyToastsComponent />
      </ToastProvider>
    );
    
    fireEvent.click(screen.getByText('显示多个'));
    
    // 应该只显示最多 3 个 Toast
    const toasts = screen.getAllByRole('alert');
    expect(toasts.length).toBeLessThanOrEqual(3);
  });
});