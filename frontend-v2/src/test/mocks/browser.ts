/**
 * MSW Browser Setup
 * 用于浏览器环境的 API 模拟
 */

import { setupWorker } from 'msw/browser';

import { handlers } from './handlers';

export const worker = setupWorker(...handlers);
