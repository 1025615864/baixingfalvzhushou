// ============================================
// 工具函数单元测试
// ============================================

import { formatDate, truncateText, sleep, generateId } from './index';

describe('formatDate', () => {
  it('should format date string correctly', () => {
    const result = formatDate('2024-01-15');
    expect(result).toBe('2024-01-15');
  });

  it('should support custom format', () => {
    const result = formatDate('2024-06-20', 'YYYY年MM月DD日');
    expect(result).toBe('2024年06月20日');
  });
});

describe('truncateText', () => {
  it('should truncate long text', () => {
    const result = truncateText('这是一个很长的文本', 5);
    expect(result).toBe('这是一个很...');
  });

  it('should return short text as is', () => {
    const result = truncateText('短文本', 10);
    expect(result).toBe('短文本');
  });
});

describe('sleep', () => {
  it('should delay for specified time', async () => {
    const start = Date.now();
    await sleep(50);
    const elapsed = Date.now() - start;
    expect(elapsed).toBeGreaterThanOrEqual(45);
  });
});

describe('generateId', () => {
  it('should generate unique ID', () => {
    const id1 = generateId();
    const id2 = generateId();
    expect(id1).not.toBe(id2);
    expect(typeof id1).toBe('string');
    expect(id1.length).toBeGreaterThan(0);
  });
});