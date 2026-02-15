/**
 * 支付系统模块 - 统一导出
 */

// 类型
export type * from './types';

// API
export { paymentApi } from './api';
export { default as paymentApiDefault } from './api';

// Hooks
export {
  useOrderList,
  useOrderDetail,
  useCreateOrder,
  usePayOrder,
  useCancelOrder,
  useBalance,
  useBalanceTransactions,
  usePricing,
  usePaymentPolling,
  usePaymentFlow,
  paymentQueryKeys,
} from './hooks/usePayment';

// 额外的Hooks
export {
  useWalletBalance,
  useTransactions,
} from './hooks/usePayments';

// 组件
export { OrderCard } from './components/OrderCard';
export { OrderList } from './components/OrderList';
export { PaymentMethodSelector } from './components/PaymentMethodSelector';
export { PaymentModal } from './components/PaymentModal';
export { PaymentQRCode } from './components/PaymentQRCode';
export { PaymentStatus } from './components/PaymentStatus';
export { PaymentHistory } from './components/PaymentHistory';

// 页面
export { OrdersPage } from './pages/OrdersPage';
export { PaymentResultPage } from './pages/PaymentResultPage';