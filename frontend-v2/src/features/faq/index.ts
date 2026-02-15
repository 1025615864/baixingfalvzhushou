/**
 * FAQ 模块 - 入口文件
 */

// 类型导出
export * from './types';

// API导出
export * from './api';

// Hooks导出
export * from './hooks/useFAQ';

// 组件导出
export { FAQList } from './components/FAQList';
export { FAQDetail } from './components/FAQDetail';
export { FAQSearch } from './components/FAQSearch';
export { FAQForm } from './components/FAQForm';

// 页面导出
export { FAQPage } from './pages/FAQPage';
export { FAQAdminPage } from './pages/FAQAdminPage';