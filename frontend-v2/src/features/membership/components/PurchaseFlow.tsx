/**
 * PurchaseFlow 会员购买流程组件
 * 实现完整的会员购买流程：选择等级 -> 确认订单 -> 支付
 * 
 * 会员等级体系：
 * - free: 免费用户
 * - monthly: 月度会员 ¥29/月
 * - annual: 年度会员 ¥299/年 (享8.6折)
 * - lifetime: 终身会员 ¥999 (一次购买终身权益)
 */

import { logger } from '@/shared/lib/logger';
import { useState, useCallback, useMemo } from 'react';
import {
  Crown,
  Shield,
  Check,
  Loader2,
  X,
  Sparkles,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

import { PaymentModal } from '@/features/payment/components/PaymentModal';
import type { Order } from '@/features/payment/types';

import type { MembershipTier, MembershipPricing, MembershipBenefits } from '../types';
import { useCreateMembershipOrder } from '../hooks/useMembership';

interface PurchaseFlowProps {
  isOpen: boolean;
  onClose: () => void;
  selectedTier?: MembershipTier;
  pricing: MembershipPricing[];
  benefits: MembershipBenefits[];
  currentTier?: MembershipTier;
  onSuccess?: () => void;
}

// 等级配置
const tierConfig: Record<MembershipTier, {
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
  gradient: string;
  description: string;
}> = {
  free: {
    label: '免费用户',
    color: 'text-slate-600',
    bgColor: 'bg-slate-100',
    borderColor: 'border-slate-300',
    gradient: 'from-slate-100 to-slate-200',
    description: '体验基础功能',
  },
  monthly: {
    label: '月度会员',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-300',
    gradient: 'from-blue-400 to-blue-600',
    description: '灵活按月订阅',
  },
  annual: {
    label: '年度会员',
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-300',
    gradient: 'from-purple-400 to-purple-600',
    description: '最受欢迎，节省更多',
  },
  lifetime: {
    label: '终身会员',
    color: 'text-amber-600',
    bgColor: 'bg-amber-100',
    borderColor: 'border-amber-300',
    gradient: 'from-amber-400 to-orange-500',
    description: '一次购买，终身权益',
  },
};

// 计费周期配置
const billingCycles = [
  { value: 'monthly' as const, label: '月付', discount: 0 },
  { value: 'annual' as const, label: '年付', discount: 14 },
  { value: 'lifetime' as const, label: '终身', discount: 50 },
];

// 购买步骤类型
type PurchaseStep = 'select' | 'confirm' | 'pay';

export function PurchaseFlow({
  isOpen,
  onClose,
  selectedTier: initialTier,
  pricing,
  benefits,
  onSuccess,
}: PurchaseFlowProps): JSX.Element {
  const [step, setStep] = useState<PurchaseStep>('select');
  const [selectedTier, setSelectedTier] = useState<MembershipTier>(initialTier || 'annual');
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual' | 'lifetime'>('annual');
  const [paymentMethod, setPaymentMethod] = useState<'alipay' | 'wechat'>('alipay');

  // 创建订单 mutation
  const createOrderMutation = useCreateMembershipOrder();

  // 获取当前选中等级的价格信息
  const currentPricing = useMemo(() => {
    return pricing.find((p) => p.tier === selectedTier);
  }, [pricing, selectedTier]);

  // 获取当前选中等级的权益信息
  const currentBenefits = useMemo(() => {
    return benefits.find((b) => b.tier === selectedTier);
  }, [benefits, selectedTier]);

  // 计算价格
  const priceInfo = useMemo(() => {
    if (!currentPricing) return { price: 0, originalPrice: 0, savings: 0 };

    let price = 0;
    let originalPrice = 0;

    switch (billingCycle) {
      case 'monthly':
        price = currentPricing.monthlyPrice;
        originalPrice = currentPricing.monthlyPrice;
        break;
      case 'annual':
        price = currentPricing.annualPrice;
        originalPrice = currentPricing.monthlyPrice * 12;
        break;
      case 'lifetime':
        price = currentPricing.lifetimePrice;
        originalPrice = currentPricing.monthlyPrice * 36; // 3年
        break;
    }

    return {
      price,
      originalPrice,
      savings: originalPrice - price,
    };
  }, [currentPricing, billingCycle]);

  // 用于支付弹窗的订单数据
  const [paymentOrder, setPaymentOrder] = useState<Order | null>(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  // 处理上一步
  const handleBack = useCallback(() => {
    if (step === 'confirm') {
      setStep('select');
    }
  }, [step]);

  // 创建订单
  const handleCreateOrder = useCallback(async () => {
    try {
      const result = await createOrderMutation.mutateAsync({
        tier: selectedTier,
        duration: billingCycle === 'lifetime' ? 'year' : billingCycle === 'monthly' ? 'month' : 'year',
        paymentMethod,
      });

      // 构造支付订单
      const order: Order = {
        id: Number(result.order.id),
        order_no: result.order.orderNo,
        order_type: 'vip',
        amount: result.order.amount,
        actual_amount: result.order.amount,
        status: 'pending',
        payment_method: null,
        title: `${tierConfig[selectedTier].label} - ${billingCycles.find(c => c.value === billingCycle)?.label}`,
        created_at: result.order.createdAt,
        paid_at: null,
      };

      setPaymentOrder(order);
      setShowPaymentModal(true);
    } catch {
      logger.error('创建订单失败');
    }
  }, [selectedTier, billingCycle, paymentMethod, createOrderMutation]);

  // 处理下一步
  const handleNext = useCallback(() => {
    if (step === 'select') {
      setStep('confirm');
    } else if (step === 'confirm') {
      void handleCreateOrder();
    }
  }, [step, handleCreateOrder]);

  // 支付成功回调
  const handlePaymentSuccess = useCallback(() => {
    setShowPaymentModal(false);
    onSuccess?.();
    onClose();
  }, [onSuccess, onClose]);

  // 关闭支付弹窗
  const handlePaymentModalClose = useCallback(() => {
    setShowPaymentModal(false);
    setPaymentOrder(null);
  }, []);

  if (!isOpen) return <></>;

  const config = tierConfig[selectedTier];

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
        <div className="relative w-full max-w-2xl mx-4 bg-white rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
          {/* 关闭按钮 */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 p-2 text-slate-400 hover:text-slate-600 transition-colors bg-white/80 rounded-full"
          >
            <X className="w-5 h-5" />
          </button>

          {/* 头部 */}
          <div className={`bg-gradient-to-r ${config.gradient} p-6`}>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-white/20 backdrop-blur-sm rounded-lg">
                <Crown className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-xl font-bold text-white">
                {step === 'select' ? '选择会员方案' : step === 'confirm' ? '确认订单' : '支付'}
              </h2>
            </div>
            <p className="text-white/80 text-sm">
              {step === 'select' && '选择最适合您的会员等级和计费方式'}
              {step === 'confirm' && '请确认您的订单信息'}
            </p>

            {/* 步骤指示器 */}
            <div className="flex items-center gap-2 mt-4">
              {(['select', 'confirm', 'pay'] as const).map((s, index) => (
                <div key={s} className="flex items-center">
                  <div
                    className={`
                      w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all
                      ${step === s || (step === 'pay' && index < 2) || (step === 'confirm' && index < 1)
                        ? 'bg-white text-purple-600'
                        : 'bg-white/20 text-white'
                      }
                    `}
                  >
                    {index + 1}
                  </div>
                  {index < 2 && (
                    <div className={`w-12 h-0.5 ${index < (step === 'select' ? 0 : step === 'confirm' ? 1 : 2) ? 'bg-white' : 'bg-white/20'}`} />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* 内容区域 */}
          <div className="p-6">
            {/* 选择方案步骤 */}
            {step === 'select' && (
              <div className="space-y-6">
                {/* 等级选择 */}
                <div>
                  <h3 className="text-sm font-medium text-slate-700 mb-3">选择会员等级</h3>
                  <div className="grid grid-cols-3 gap-3">
                    {(['monthly', 'annual', 'lifetime'] as const).map((tier) => {
                      const tierConf = tierConfig[tier];
                      const isPopular = tier === 'annual';
                      
                      return (
                        <button
                          key={tier}
                          onClick={() => setSelectedTier(tier)}
                          className={`
                            relative p-4 rounded-xl border-2 text-left transition-all
                            ${selectedTier === tier
                              ? `${tierConf.bgColor} ${tierConf.borderColor || 'border-current'}`
                              : 'border-slate-200 hover:border-slate-300'
                            }
                          `}
                        >
                          {isPopular && (
                            <span className="absolute -top-2 left-1/2 -translate-x-1/2 px-2 py-0.5 text-xs font-medium bg-purple-500 text-white rounded-full">
                              推荐
                            </span>
                          )}
                          <h4 className={`font-semibold ${tierConf.color}`}>{tierConf.label}</h4>
                          <p className="text-xs text-slate-500 mt-1">{tierConf.description}</p>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* 计费周期选择 */}
                <div>
                  <h3 className="text-sm font-medium text-slate-700 mb-3">选择计费周期</h3>
                  <div className="grid grid-cols-3 gap-3">
                    {billingCycles.map((cycle) => {
                      const price = cycle.value === 'monthly'
                        ? currentPricing?.monthlyPrice
                        : cycle.value === 'annual'
                        ? currentPricing?.annualPrice
                        : currentPricing?.lifetimePrice;

                      return (
                        <button
                          key={cycle.value}
                          onClick={() => setBillingCycle(cycle.value)}
                          className={`
                            relative p-4 rounded-xl border-2 text-center transition-all
                            ${billingCycle === cycle.value
                              ? 'border-purple-500 bg-purple-50'
                              : 'border-slate-200 hover:border-slate-300'
                            }
                          `}
                        >
                          {cycle.discount > 0 && (
                            <span className="absolute -top-2 left-1/2 -translate-x-1/2 px-2 py-0.5 text-xs font-medium bg-red-500 text-white rounded-full">
                              省{cycle.discount}%
                            </span>
                          )}
                          <p className="font-semibold text-slate-900">{cycle.label}</p>
                          <p className="text-lg font-bold text-purple-600">¥{price}</p>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* 支付方式选择 */}
                <div>
                  <h3 className="text-sm font-medium text-slate-700 mb-3">选择支付方式</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => setPaymentMethod('alipay')}
                      className={`
                        flex items-center gap-3 p-4 rounded-xl border-2 transition-all
                        ${paymentMethod === 'alipay'
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-slate-200 hover:border-slate-300'
                        }
                      `}
                    >
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <span className="text-blue-600 font-bold text-lg">支</span>
                      </div>
                      <span className="font-medium text-slate-700">支付宝</span>
                      {paymentMethod === 'alipay' && <Check className="w-5 h-5 text-blue-500 ml-auto" />}
                    </button>
                    <button
                      onClick={() => setPaymentMethod('wechat')}
                      className={`
                        flex items-center gap-3 p-4 rounded-xl border-2 transition-all
                        ${paymentMethod === 'wechat'
                          ? 'border-green-500 bg-green-50'
                          : 'border-slate-200 hover:border-slate-300'
                        }
                      `}
                    >
                      <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                        <span className="text-green-600 font-bold text-lg">微</span>
                      </div>
                      <span className="font-medium text-slate-700">微信支付</span>
                      {paymentMethod === 'wechat' && <Check className="w-5 h-5 text-green-500 ml-auto" />}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* 确认订单步骤 */}
            {step === 'confirm' && (
              <div className="space-y-6">
                {/* 订单摘要 */}
                <div className="bg-slate-50 rounded-xl p-6">
                  <h3 className="text-sm font-medium text-slate-700 mb-4">订单摘要</h3>
                  
                  <div className="flex items-center gap-4 mb-6">
                    <div className={`p-4 rounded-xl bg-gradient-to-r ${config.gradient}`}>
                      <Crown className="w-8 h-8 text-white" />
                    </div>
                    <div className="flex-1">
                      <h4 className="text-lg font-bold text-slate-900">{config.label}</h4>
                      <p className="text-sm text-slate-500">
                        {billingCycles.find(c => c.value === billingCycle)?.label}
                      </p>
                    </div>
                  </div>

                  <div className="space-y-3 border-t border-slate-200 pt-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500">原价</span>
                      <span className="text-slate-500 line-through">¥{priceInfo.originalPrice}</span>
                    </div>
                    {priceInfo.savings > 0 && (
                      <div className="flex justify-between text-sm">
                        <span className="text-green-600">优惠</span>
                        <span className="text-green-600">-¥{priceInfo.savings}</span>
                      </div>
                    )}
                    <div className="flex justify-between text-lg font-bold border-t border-slate-200 pt-3">
                      <span className="text-slate-900">应付金额</span>
                      <span className="text-purple-600">¥{priceInfo.price}</span>
                    </div>
                  </div>
                </div>

                {/* 权益预览 */}
                <div className="bg-purple-50 rounded-xl p-6">
                  <h3 className="text-sm font-medium text-purple-700 mb-3 flex items-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    开通后可享受以下权益
                  </h3>
                  <ul className="grid grid-cols-2 gap-2">
                    {currentBenefits && (
                      <>
                        <li className="flex items-center gap-2 text-sm text-slate-600">
                          <Check className="w-4 h-4 text-green-500" />
                          每日 {currentBenefits.unlimitedAiChat ? '无限' : currentBenefits.dailyAiChatLimit} 次 AI 对话
                        </li>
                        <li className="flex items-center gap-2 text-sm text-slate-600">
                          <Check className="w-4 h-4 text-green-500" />
                          {currentBenefits.prioritySupport ? '优先客服支持' : '标准客服'}
                        </li>
                        {currentBenefits.videoConsultationDiscount > 0 && (
                          <li className="flex items-center gap-2 text-sm text-slate-600">
                            <Check className="w-4 h-4 text-green-500" />
                            视频咨询 {currentBenefits.videoConsultationDiscount * 10} 折
                          </li>
                        )}
                        {currentBenefits.pointsMultiplier > 1 && (
                          <li className="flex items-center gap-2 text-sm text-slate-600">
                            <Check className="w-4 h-4 text-green-500" />
                            积分 {currentBenefits.pointsMultiplier}x 返还
                          </li>
                        )}
                      </>
                    )}
                  </ul>
                </div>

                {/* 安全提示 */}
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <Shield className="w-4 h-4" />
                  <span>支付安全由支付宝/微信支付保障</span>
                </div>
              </div>
            )}
          </div>

          {/* 底部操作区 */}
          <div className="p-6 border-t border-slate-200 bg-slate-50">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                {step === 'confirm' && (
                  <button
                    onClick={handleBack}
                    className="px-4 py-2 text-slate-600 hover:text-slate-800 transition-colors flex items-center gap-1"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    返回修改
                  </button>
                )}
              </div>
              
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-sm text-slate-500">应付金额</p>
                  <p className="text-2xl font-bold text-purple-600">¥{priceInfo.price}</p>
                </div>
                <button
                  onClick={handleNext}
                  disabled={createOrderMutation.isPending}
                  className={`
                    px-8 py-3 rounded-xl font-semibold text-white transition-all flex items-center gap-2
                    bg-gradient-to-r ${config.gradient}
                    hover:opacity-90 disabled:opacity-50
                  `}
                >
                  {createOrderMutation.isPending ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      处理中...
                    </>
                  ) : (
                    <>
                      {step === 'select' ? '下一步' : '立即支付'}
                      <ChevronRight className="w-5 h-5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 支付弹窗 */}
      {paymentOrder && (
        <PaymentModal
          order={paymentOrder}
          isOpen={showPaymentModal}
          onClose={handlePaymentModalClose}
          onSuccess={handlePaymentSuccess}
        />
      )}
    </>
  );
}

export default PurchaseFlow;