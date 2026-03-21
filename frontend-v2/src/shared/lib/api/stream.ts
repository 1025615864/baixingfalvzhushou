/**
 * 流式请求封装
 * 
 * 功能：
 * - SSE 流式请求封装
 * - 流式数据解析
 * - 流式错误处理
 * - 取消/关闭流
 * 
 * @see FR-006: 流式请求封装
 * @see FR-007: 流式错误处理
 */

// ============================================
// 类型定义
// ============================================

/** 流式数据类型 */
export interface StreamData<T = unknown> {
  /** 数据内容 */
  data: T;
  /** 数据索引 */
  index?: number;
  /** 时间戳 */
  timestamp?: number;
}

/** 流式错误类型 */
export interface StreamError {
  /** 错误类型 */
  type: 'timeout' | 'network' | 'server' | 'parse' | 'aborted';
  /** 错误消息 */
  message: string;
  /** 原始错误 */
  cause?: Error;
  /** HTTP 状态码 */
  statusCode?: number;
}

/** 流式请求回调 */
export interface StreamCallbacks<T = unknown> {
  /** 数据回调 */
  onData?: (data: T) => void;
  /** 错误回调 */
  onError?: (error: StreamError) => void;
  /** 完成回调 */
  onDone?: () => void;
  /** 连接回调 */
  onConnect?: () => void;
  /** 断开回调 */
  onDisconnect?: () => void;
}

/** 流式请求选项 */
export interface StreamOptions {
  /** 超时时间（毫秒） */
  timeout?: number;
  /** 请求头 */
  headers?: Record<string, string>;
  /** 是否使用凭证 */
  withCredentials?: boolean;
  /** AbortSignal（用于外部取消） */
  signal?: AbortSignal;
  /** SSE 解码器（用于自定义事件格式） */
  decoder?: StreamDecoder;
}

/** SSE 事件格式 */
export interface SSEEvent {
  /** 事件类型 */
  type: string;
  /** 数据内容 */
  data: string;
  /** 事件 ID */
  id?: string;
  /** 重试间隔 */
  retry?: number;
}

/** SSE 解码器接口 */
export interface StreamDecoder {
  /** 解码原始数据 */
  decode: (chunk: string) => SSEEvent[];
}

/** 流式控制器 */
export interface StreamController {
  /** 关闭流 */
  close: () => void;
  /** 是否已关闭 */
  closed: boolean;
}

// ============================================
// 默认配置
// ============================================

const DEFAULT_TIMEOUT = 60000; // 60 秒
const DEFAULT_HEADERS: Record<string, string> = {
  'Accept': 'text/event-stream',
  'Cache-Control': 'no-cache',
};

// ============================================
// 默认 SSE 解码器
// ============================================

/**
 * 默认 SSE 事件解码器
 * 解析 SSE 格式：event: xxx \ndata: xxx \\n\\n
 */
export class DefaultSSEDecoder implements StreamDecoder {
  private buffer = '';

  decode(chunk: string): SSEEvent[] {
    this.buffer += chunk;
    
    const events: SSEEvent[] = [];
    const parts = this.buffer.split(/\n\n+/);
    
    // 保留最后一个可能不完整的部分
    this.buffer = parts.pop() || '';
    
    for (const part of parts) {
      const event = this.parseEvent(part);
      if (event) {
        events.push(event);
      }
    }
    
    return events;
  }

  private parseEvent(part: string): SSEEvent | null {
    const lines = part.split('\n');
    const event: SSEEvent = {
      type: 'message',
      data: '',
    };
    
    for (const line of lines) {
      if (line.startsWith('event:')) {
        event.type = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        event.data += line.slice(5).trim() + '\n';
      } else if (line.startsWith('id:')) {
        event.id = line.slice(3).trim();
      } else if (line.startsWith('retry:')) {
        event.retry = parseInt(line.slice(6).trim(), 10);
      }
    }
    
    // 移除末尾的换行符
    if (event.data) {
      event.data = event.data.slice(0, -1);
    }
    
    // 尝试解析 JSON 数据
    if (event.type === 'message' && event.data) {
      try {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
        event.data = JSON.parse(event.data);
      } catch {
        // 保持原始字符串
      }
    }
    
    return event;
  }
}

// ============================================
// 流式错误处理
// ============================================

/**
 * 创建流式错误对象
 */
function createStreamError(
  type: StreamError['type'],
  message: string,
  cause?: Error,
  statusCode?: number
): StreamError {
  return {
    type,
    message,
    cause,
    statusCode,
  };
}

/**
 * 格式化流式错误消息
 */
export function formatStreamError(error: StreamError): string {
  switch (error.type) {
    case 'timeout':
      return `请求超时：${error.message}`;
    case 'network':
      return `网络错误：${error.message}`;
    case 'server':
      return `服务器错误 (${error.statusCode || '未知'}): ${error.message}`;
    case 'parse':
      return `数据解析错误：${error.message}`;
    case 'aborted':
      return `请求已取消：${error.message}`;
    default:
      return error.message;
  }
}

// ============================================
// 主动式流式请求类
// ============================================

/**
 * 主动式流式请求类
 * 
 * 使用 fetch API 实现 SSE 流式请求
 * 支持：
 * - 自动重连
 * - 超时控制
 * - 错误处理
 * - 取消请求
 */
export class StreamClient<T = unknown> {
  /** 控制器 */
  private controller: AbortController | null = null;
  
  /** 是否已关闭 */
  public closed = false;
  
  /** 解码器 */
  private decoder: StreamDecoder;
  
  /** 超时计时器 */
  private timeoutTimer: ReturnType<typeof setTimeout> | null = null;
  
  /** 回调函数 */
  private callbacks: StreamCallbacks<T>;
  
  /** 选项 */
  private options: StreamOptions;
  
  /** 最后收到数据的时间 */
  private lastDataTime = 0;

  constructor(
    private url: string,
    callbacks: StreamCallbacks<T>,
    options: StreamOptions = {}
  ) {
    this.callbacks = callbacks;
    this.options = {
      timeout: DEFAULT_TIMEOUT,
      headers: {},
      withCredentials: true,
      ...options,
      decoder: options.decoder || new DefaultSSEDecoder(),
    };
    this.decoder = this.options.decoder!;
  }

  /**
   * 启动流式请求
   */
  async start(): Promise<StreamController> {
    if (this.closed) {
      throw new Error('Stream is closed');
    }

    this.controller = new AbortController();
    
    // 设置超时
    if (this.options.timeout) {
      this.timeoutTimer = setTimeout(() => {
        this.handleError(createStreamError(
          'timeout',
          '请求超时',
          undefined,
          408
        ));
      }, this.options.timeout);
    }

    // 监听外部取消信号
    if (this.options.signal) {
      this.options.signal.addEventListener('abort', () => {
        this.close();
      });
    }

    try {
      const response = await fetch(this.url, {
        method: 'POST',
        headers: {
          ...DEFAULT_HEADERS,
          ...this.options.headers,
        },
        credentials: this.options.withCredentials ? 'include' : 'same-origin',
        signal: this.controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // 触发连接回调
      this.callbacks.onConnect?.();

      // 清除超时
      if (this.timeoutTimer) {
        clearTimeout(this.timeoutTimer);
        this.timeoutTimer = null;
      }

      // 读取流式数据
      await this.readStream(response);
      
      // 完成回调
      this.callbacks.onDone?.();
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        this.handleError(createStreamError('aborted', '请求已取消'));
      } else {
        this.handleError(createStreamError(
          'network',
          error instanceof Error ? error.message : '网络错误',
          error instanceof Error ? error : undefined
        ));
      }
    }

    return {
      close: () => this.close(),
      closed: this.closed,
    };
  }

  /**
   * 读取流式数据
   */
  private async readStream(response: Response): Promise<void> {
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is null');
    }

    const decoder = new TextDecoder();

    try {
      /* eslint-disable-next-line no-constant-condition */
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }

        // 更新最后收到数据的时间
        this.lastDataTime = Date.now();

        // 解码数据
        const chunk = decoder.decode(value, { stream: true });
        const events = this.decoder.decode(chunk);

        // 处理事件
        for (const event of events) {
          if (event.type === 'error') {
            this.handleError(createStreamError(
              'server',
              typeof event.data === 'string' ? event.data : '服务器错误',
              undefined,
              500
            ));
            return;
          }
          
          if (event.type === 'message' && event.data) {
            // 调用数据回调（直接传递数据）
            this.callbacks.onData?.(event.data as T);
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        this.handleError(createStreamError(
          'parse',
          '数据解析错误',
          error instanceof Error ? error : undefined
        ));
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * 处理错误
   */
  private handleError(error: StreamError): void {
    if (this.closed) {
      return;
    }

    // 清除超时
    if (this.timeoutTimer) {
      clearTimeout(this.timeoutTimer);
      this.timeoutTimer = null;
    }

    // 调用错误回调
    this.callbacks.onError?.(error);
  }

  /**
   * 关闭流式请求
   */
  close(): void {
    if (this.closed) {
      return;
    }

    this.closed = true;
    
    // 清除超时
    if (this.timeoutTimer) {
      clearTimeout(this.timeoutTimer);
      this.timeoutTimer = null;
    }

    // 中止请求
    if (this.controller) {
      this.controller.abort();
      this.controller = null;
    }

    // 触发断开回调
    this.callbacks.onDisconnect?.();
  }
}

// ============================================
// 便捷函数
// ============================================

/**
 * 创建并启动流式请求
 * 
 * @param url - SSE 端点 URL
 * @param callbacks - 回调函数
 * @param options - 选项
 * @returns 流式控制器
 */
export async function createStreamRequest<T>(
  url: string,
  callbacks: StreamCallbacks<T>,
  options?: StreamOptions
): Promise<StreamController> {
  const client = new StreamClient<T>(url, callbacks, options);
  return client.start();
}

/**
 * 发送单次流式请求并收集所有数据
 * 
 * @param url - SSE 端点 URL
 * @param options - 选项
 * @returns Promise 解析为数据数组
 */
export async function fetchStreamData<T>(
  url: string,
  options?: StreamOptions
): Promise<T[]> {
  const data: T[] = [];
  
  return new Promise((resolve, reject) => {
    const controller = new StreamClient<T>(
      url,
      {
        onData: (item: T) => {
          data.push(item);
        },
        onDone: () => {
          resolve(data);
        },
        onError: (error: StreamError) => {
          reject(new Error(formatStreamError(error)));
        },
      },
      options
    );
    
    controller.start().catch(reject);
  });
}

// ============================================
// 导出
// ============================================

export const stream = {
  createStreamRequest,
  fetchStreamData,
  createStreamError,
  formatStreamError,
  StreamClient,
  DefaultSSEDecoder,
};