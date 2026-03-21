/**
 * 法律文书商城类型定义
 */

// 分类
export interface LegalDocumentCategory {
  name: string;
  categories: {
    key: string;
    name: string;
  }[];
}

// 法律文书商品
export interface LegalDocument {
  id: number;
  name: string;
  description: string | null;
  category: string;
  category_name: string;
  price: number;
  is_free: boolean;
  is_featured: boolean;
  view_count: number;
  download_count: number;
  rating: number;
  tags: string[];
  custom_service_available: boolean;
  custom_service_price: number;
  member_prices: {
    monthly?: number;
    annual?: number;
    lifetime?: number;
  } | null;
  created_at: string | null;
  is_favorited?: boolean;
  is_purchased?: boolean;
}

// 法律文书详情
export interface LegalDocumentDetail extends LegalDocument {
  content?: string;
}

// 价格计算响应
export interface PriceCalculation {
  price: number;
  original_price: number;
  discount: number;
  is_free: boolean;
  payment_method: string;
  tier: string | null;
}

// 购买请求
export interface PurchaseRequest {
  payment_method: 'points' | 'free' | 'member_free';
}

// 购买响应
export interface PurchaseResponse {
  success: boolean;
  order_no?: string;
  document_id?: number;
  document_name?: string;
  points_spent?: number;
  payment_method?: string;
  error?: string;
  balance?: number;
  required?: number;
}

// 订单记录
export interface LegalDocumentOrder {
  order_no: string;
  document_id: number;
  document_name: string;
  document_category: string | null;
  points_spent: number;
  payment_method: string;
  completed_at: string | null;
}

// 列表查询参数
export interface LegalDocumentQueryParams {
  category?: string;
  keyword?: string;
  page?: number;
  page_size?: number;
  is_featured?: boolean;
  is_free?: boolean;
}

// 列表响应
export interface LegalDocumentListResponse {
  items: LegalDocument[];
  total: number;
  page: number;
  page_size: number;
}

// 订单列表响应
export interface LegalDocumentOrderListResponse {
  items: LegalDocumentOrder[];
  total: number;
  page: number;
  page_size: number;
}