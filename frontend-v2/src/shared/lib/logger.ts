type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level: LogLevel;
  message: string;
  data?: unknown;
  timestamp: number;
}

const isDev = import.meta.env.DEV;

const logBuffer: LogEntry[] = [];
const MAX_BUFFER_SIZE = 100;

function createLogEntry(level: LogLevel, message: string, data?: unknown): LogEntry {
  return { level, message, data, timestamp: Date.now() };
}

function addToBuffer(entry: LogEntry): void {
  logBuffer.push(entry);
  if (logBuffer.length > MAX_BUFFER_SIZE) {
    logBuffer.shift();
  }
}

export const logger = {
  debug(message: string, data?: unknown): void {
    const entry = createLogEntry('debug', message, data);
    addToBuffer(entry);
    if (isDev) {
      console.debug(`[DEBUG] ${message}`, data ?? '');
    }
  },

  info(message: string, data?: unknown): void {
    const entry = createLogEntry('info', message, data);
    addToBuffer(entry);
    if (isDev) {
      console.info(`[INFO] ${message}`, data ?? '');
    }
  },

  warn(message: string, data?: unknown): void {
    const entry = createLogEntry('warn', message, data);
    addToBuffer(entry);
    console.warn(`[WARN] ${message}`, data ?? '');
  },

  error(message: string, data?: unknown): void {
    const entry = createLogEntry('error', message, data);
    addToBuffer(entry);
    console.error(`[ERROR] ${message}`, data ?? '');
  },

  getRecentLogs(count: number = 50): LogEntry[] {
    return logBuffer.slice(-count);
  },

  clearLogs(): void {
    logBuffer.length = 0;
  },
};

export type { LogLevel, LogEntry };
