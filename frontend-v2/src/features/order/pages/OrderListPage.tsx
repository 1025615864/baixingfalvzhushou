import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface Order {
  id: number;
  order_no: string;
  title: string;
  order_type: string;
  amount: number;
  actual_amount: number;
  status: string;
  created_at: string;
}

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending: { label: '待支付', color: 'bg-yellow-100 text-yellow-800' },
  paid: { label: '已支付', color: 'bg-green-100 text-green-800' },
  completed: { label: '已完成', color: 'bg-blue-100 text-blue-800' },
  cancelled: { label: '已取消', color: 'bg-gray-100 text-gray-600' },
};

const TABS = ['全部', '待支付', '已完成', '已取消'] as const;
const TAB_STATUS: Record<string, string> = { '全部': '', '待支付': 'pending', '已完成': 'completed', '已取消': 'cancelled' };

export function OrderListPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<string>(TABS[0]);
  const navigate = useNavigate();
  const userId = 1;

  useEffect(() => {
    fetchOrders();
  }, [activeTab]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const status = TAB_STATUS[activeTab];
      const url = status
        ? `/api/v1/orders?user_id=${userId}&status=${status}&page=1&page_size=50`
        : `/api/v1/orders?user_id=${userId}&page=1&page_size=50`;
      const res = await fetch(url);
      const data = await res.json();
      setOrders(data.items || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center min-h-[50vh] items-center"><div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" /></div>;
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-xl font-bold mb-4">我的订单</h1>

      <div className="flex gap-2 mb-4 overflow-x-auto">
        {TABS.map(t => (
          <button
            key={t}
            onClick={() => setActiveTab(t)}
            className={`px-4 py-1.5 rounded-full text-sm whitespace-nowrap transition-colors ${
              activeTab === t ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {orders.length === 0 ? (
        <div className="text-center py-16 text-gray-400">暂无订单</div>
      ) : (
        <div className="space-y-3">
          {orders.map(o => {
            const status = STATUS_MAP[o.status] || STATUS_MAP.pending;
            return (
              <div key={o.id} className="bg-white border rounded-lg p-4 hover:shadow transition-shadow cursor-pointer"
                onClick={() => navigate(`/orders/${o.id}`)}
              >
                <div className="flex items-start justify-between mb-2">
                  <p className="font-medium text-gray-900">{o.title}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${status.color}`}>{status.label}</span>
                </div>
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>{o.order_no}</span>
                  <span className="font-bold text-orange-600">¥{o.actual_amount || o.amount}</span>
                </div>
                <p className="text-xs text-gray-400 mt-1">{o.created_at}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}