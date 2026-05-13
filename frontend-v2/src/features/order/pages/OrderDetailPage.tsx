import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

interface Order {
  id: number;
  order_no: string;
  title: string;
  order_type: string;
  amount: number;
  discount_amount: number;
  actual_amount: number;
  status: string;
  description: string;
  created_at: string;
}

const STATUS_FLOW = ['pending', 'paid', 'completed'];

export function OrderDetailPage() {
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const { orderNo } = useParams<{ orderNo: string }>();
  const navigate = useNavigate();

  useEffect(() => {
    fetchOrder();
  }, [orderNo]);

  const fetchOrder = async () => {
    try {
      const res = await fetch(`/api/v1/orders/${orderNo}`);
      if (!res.ok) throw new Error('not found');
      setOrder(await res.json());
    } catch {
      setOrder(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="flex justify-center min-h-[50vh] items-center"><div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" /></div>;
  if (!order) return <div className="text-center py-16 text-gray-400">订单不存在</div>;

  const statusIndex = STATUS_FLOW.indexOf(order.status);

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <button onClick={() => navigate(-1)} className="text-blue-600 text-sm mb-4 hover:underline">&larr; 返回</button>
      <div className="bg-white border rounded-lg p-6">
        <h1 className="text-xl font-bold mb-1">{order.title}</h1>
        <p className="text-sm text-gray-400 mb-4">订单号: {order.order_no}</p>

        <div className="flex items-center gap-2 mb-6">
          {STATUS_FLOW.map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <span className={`w-3 h-3 rounded-full ${i <= statusIndex ? 'bg-blue-500' : 'bg-gray-300'}`} />
              <span className={`text-xs ${i <= statusIndex ? 'text-blue-600' : 'text-gray-400'}`}>
                {s === 'pending' ? '待支付' : s === 'paid' ? '已支付' : '已完成'}
              </span>
              {i < STATUS_FLOW.length - 1 && <div className={`w-8 h-px ${i < statusIndex ? 'bg-blue-500' : 'bg-gray-300'}`} />}
            </div>
          ))}
        </div>

        <div className="border-t pt-4 space-y-3">
          <div className="flex justify-between text-sm"><span className="text-gray-500">订单金额</span><span>¥{order.amount}</span></div>
          <div className="flex justify-between text-sm"><span className="text-gray-500">优惠金额</span><span className="text-green-600">-¥{order.discount_amount || 0}</span></div>
          <div className="flex justify-between font-bold text-lg border-t pt-3"><span>实付金额</span><span className="text-orange-600">¥{order.actual_amount || order.amount}</span></div>
        </div>

        {order.description && <p className="text-sm text-gray-500 mt-4">{order.description}</p>}
        <p className="text-xs text-gray-400 mt-4">创建时间: {order.created_at}</p>
      </div>
    </div>
  );
}