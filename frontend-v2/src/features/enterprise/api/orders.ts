import { apiClient } from '@/shared/lib/api/client';
import type {
  EnterpriseOrder,
  GetEnterpriseOrdersRequest,
  GetEnterpriseOrdersResponse,
} from '../types';
import type { BackendEnterpriseOrder } from './transforms';

const API_BASE = '/enterprise';

export async function apiGetEnterpriseOrders(
  accountId: number,
  params: GetEnterpriseOrdersRequest = {}
): Promise<GetEnterpriseOrdersResponse> {
  const response = await apiClient.get<{
    orders: BackendEnterpriseOrder[];
    total: number;
    total_amount: number;
  }>(`${API_BASE}/account/${accountId}/orders`, {
    params: {
      status: params.status,
      order_type: params.orderType,
      start_date: params.startDate,
      end_date: params.endDate,
      limit: params.limit,
      offset: params.offset,
    },
  });
  
  return {
    orders: response.data.orders.map(order => ({
      id: order.id,
      enterpriseId: order.enterprise_id,
      orderType: order.order_type as EnterpriseOrder['orderType'],
      status: order.status as EnterpriseOrder['status'],
      amount: order.amount,
      currency: order.currency,
      description: order.description,
      items: order.items.map(item => ({
        id: item.id,
        name: item.name,
        quantity: item.quantity,
        unitPrice: item.unit_price,
        totalPrice: item.total_price,
        description: item.description,
      })),
      createdAt: order.created_at,
      paidAt: order.paid_at,
      completedAt: order.completed_at,
      invoiceNo: order.invoice_no,
      paymentMethod: order.payment_method,
    })),
    total: response.data.total,
    totalAmount: response.data.total_amount,
  };
}
