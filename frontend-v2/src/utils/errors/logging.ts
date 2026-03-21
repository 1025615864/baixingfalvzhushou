import type { ApiError } from './types';

interface ErrorLogConfig {
  enabled: boolean;
  reportToServer: boolean;
  logToConsole: boolean;
  reportUrl: string;
}

const DEFAULT_LOG_CONFIG: ErrorLogConfig = {
  enabled: true,
  reportToServer: false,
  logToConsole: true,
  reportUrl: '/api/logs/error',
};

export function logError(
  error: ApiError,
  context?: {
    component?: string;
    action?: string;
    userId?: string;
    extra?: Record<string, unknown>;
  }
): void {
  const errorLog = {
    ...error,
    timestamp: Date.now(),
    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
    url: typeof window !== 'undefined' ? window.location.href : 'unknown',
    context,
  };

  if (DEFAULT_LOG_CONFIG.logToConsole) {
    console.error('[Error Log]', JSON.stringify(errorLog, null, 2));
  }

  if (DEFAULT_LOG_CONFIG.reportToServer) {
    if (typeof navigator !== 'undefined' && 'sendBeacon' in navigator) {
      navigator.sendBeacon(DEFAULT_LOG_CONFIG.reportUrl, JSON.stringify(errorLog));
    }
  }
}

export async function reportErrors(errors: ApiError[]): Promise<void> {
  if (!DEFAULT_LOG_CONFIG.reportToServer || errors.length === 0) {
    return;
  }

  try {
    await fetch(DEFAULT_LOG_CONFIG.reportUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        errors: errors.map((err) => ({
          ...err,
          timestamp: err.timestamp || Date.now(),
        })),
        reportedAt: new Date().toISOString(),
      }),
    });
  } catch (reportError) {
    console.error('[Error Report Failed]', reportError);
  }
}
