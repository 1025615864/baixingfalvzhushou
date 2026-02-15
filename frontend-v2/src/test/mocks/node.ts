/**
 * MSW Node Setup
 * 用于 Node.js 测试环境的 API 模拟
 */

import { setupServer } from 'msw/node';

import { handlers } from './handlers';

export const server = setupServer(...handlers);
