/**
 * 文书购买流程组件
 * 支持支付方式选择、积分抵扣选项和订单确认
 */

import { useState, useCallback, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Gift,
  Crown,
  CheckCircle,
  AlertCircle,
  Coins,
  Shield,
  Loader2,
  Info,
  // Clock - unused
} from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { useAuthStore } from '@/features/auth/store/authStore';

import { useDocumentPrice, usePurchaseDocument } from '../hooks/useLegalDocuments';
import type { LegalDocument, LegalDocumentDetail, PurchaseResponse, PriceCalculation } from '../types';

// 支付方式类型
export type PaymentMethod = 'points' | 'free' | 'member_free';

// 购买步骤
type PurchaseStep = 'confirm' | 'payment' | 'processing' | 'success' | 'error';

// 会员等级配置
const MEMBER_TIERS = [
  { key: 'monthly', name: '月度会员', discount: 10 },
  { key: 'annual', name: '年度会员', discount: 20 },
  { key: 'lifetime', name: '终身会员', discount: 30 },
];

interface DocumentPurchaseFlowProps {
  document: LegalDocument | LegalDocumentDetail;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (result: PurchaseResponse) => void;
  onError?: (error: Error) => void;
  userPoints?: number;
  userMemberTier?: 'monthly' | 'annual' | 'lifetime' | null;
}

 
const _unusedInterfaceCheck = (props: DocumentPurchaseFlowProps) => props;

/**
 * 价格摘要组件
 */
function PriceSummary({
  document,
  priceCalculation,
  paymentMethod,
  userPoints,
  usePointsDeduction,
  pointsToUse,
}: {
  document: LegalDocument | LegalDocumentDetail;
  priceCalculation?: PriceCalculation;
  paymentMethod: PaymentMethod;
  userPoints?: number;
  usePointsDeduction?: boolean;
  pointsToUse?: number;
}) {
  // 计算价格详情
  const priceDetails = useMemo(() => {
    const basePrice = document.price;
    const originalPrice = (priceCalculation as { original_price?: number } | undefined)?.original_price ?? basePrice;
    const finalPrice = (priceCalculation as { price?: number } | undefined)?.price ?? basePrice;
    const discount = (priceCalculation as { discount?: number } | undefined)?.discount ?? 0;
    const tier = (priceCalculation as { tier?: string } | undefined)?.tier;

    // 积分抵扣金额（假设 100 积分 = 1 元）
    const deductionAmount = usePointsDeduction && pointsToUse ? Math.floor(pointsToUse / 100) : 0;
    const actualPrice = Math.max(0, finalPrice - deductionAmount);

    return {
      basePrice,
      originalPrice,
      finalPrice,
      discount,
      tier,
      deductionAmount,
      actualPrice,
      pointsToUse: pointsToUse || 0,
    };
  }, [document, priceCalculation, usePointsDeduction, pointsToUse]);

  // 免费文书
  if (document.is_free) {
    return (
      <div className="bg-green-50 rounded-lg p-4 text-center">
        <Gift className="w-8 h-8 text-green-500 mx-auto mb-2" />
        <div className="text-lg font-bold text-green-600">免费文书</div>
        <div className="text-sm text-green-600 mt-1">无需支付，直接获取</div>
      </div>
    );
  }

  // 会员免费
  if (paymentMethod === 'member_free') {
    return (
      <div className="bg-purple-50 rounded-lg p-4 text-center">
        <Crown className="w-8 h-8 text-purple-500 mx-auto mb-2" />
        <div className="text-lg font-bold text-purple-600">会员免费</div>
        <div className="text-sm text-purple-600 mt-1">您的会员等级可免费获取此文书</div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* 原价 */}
      {priceDetails.discount > 0 && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>原价</span>
          <span className="line-through">{priceDetails.originalPrice} 积分</span>
        </div>
      )}

      {/* 会员折扣 */}
      {priceDetails.tier && priceDetails.discount > 0 && (
        <div className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-1">
            <Crown className="w-4 h-4 text-purple-500" />
            {MEMBER_TIERS.find((t) => t.key === priceDetails.tier)?.name}折扣
          </span>
          <span className="text-green-600">-{priceDetails.discount}%</span>
        </div>
      )}

      {/* 折后价格 */}
      <div className="flex items-center justify-between text-sm">
        <span>应付积分</span>
        <span className="font-medium">{priceDetails.finalPrice} 积分</span>
      </div>

      {/* 积分抵扣 */}
      {usePointsDeduction && priceDetails.pointsToUse > 0 && (
        <div className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-1">
            <Coins className="w-4 h-4 text-amber-500" />
            积分抵扣
          </span>
          <span className="text-green-600">-{priceDetails.deductionAmount} 积分</span>
        </div>
      )}

      {/* 分隔线 */}
      <div className="border-t border-gray-200 my-2" />

      {/* 实付金额 */}
      <div className="flex items-center justify-between">
        <span className="font-medium text-gray-900">实付积分</span>
        <span className="text-xl font-bold text-orange-600">{priceDetails.actualPrice}</span>
      </div>

      {/* 余额提示 */}
      {userPoints !== undefined && (
        <div className={`text-xs ${userPoints >= priceDetails.actualPrice ? 'text-gray-500' : 'text-red-500'}`}>
          当前余额：{userPoints} 积分
          {userPoints < priceDetails.actualPrice && '（余额不足）'}
        </div>
      )}
    </div>
  );
}

/**
 * 支付方式选择组件
 */
function PaymentMethodSelector({
  document,
  priceCalculation,
  selectedMethod,
  onMethodChange,
  userMemberTier,
}: {
  document: LegalDocument | LegalDocumentDetail;
  priceCalculation?: PriceCalculation;
  selectedMethod: PaymentMethod;
  onMethodChange: (method: PaymentMethod) => void;
  userMemberTier?: 'monthly' | 'annual' | 'lifetime' | null;
}) {
  const methods: { key: PaymentMethod; icon: React.ElementType; label: string; description: string; available: boolean }[] = [
    {
      key: 'points',
      icon: Coins,
      label: '积分支付',
      description: `使用 ${priceCalculation?.price ?? document.price} 积分购买`,
      available: !document.is_free,
    },
    {
      key: 'free',
      icon: Gift,
      label: '免费获取',
      description: '此文书为免费资源',
      available: document.is_free,
    },
    {
      key: 'member_free',
      icon: Crown,
      label: '会员免费',
      description: '您的会员等级可免费获取',
      available: !!userMemberTier && priceCalculation?.payment_method === 'member_free',
    },
  ];

  const availableMethods = methods.filter((m) => m.available);

  // 如果只有一种可用方式，自动选中
  useEffect(() => {
    if (availableMethods.length === 1 && selectedMethod !== availableMethods[0].key) {
      onMethodChange(availableMethods[0].key);
    }
  }, [availableMethods, selectedMethod, onMethodChange]);

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-gray-700 mb-3">选择支付方式</h3>
      {availableMethods.map((method) => {
        const Icon = method.icon;
        const isSelected = selectedMethod === method.key;
        return (
          <button
            key={method.key}
            onClick={() => onMethodChange(method.key)}
            className={`w-full flex items-center gap-3 p-4 rounded-lg border-2 transition-all ${
              isSelected
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300 bg-white'
            }`}
          >
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center ${
                isSelected ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-500'
              }`}
            >
              <Icon className="w-5 h-5" />
            </div>
            <div className="flex-1 text-left">
              <div className="font-medium text-gray-900">{method.label}</div>
              <div className="text-sm text-gray-500">{method.description}</div>
            </div>
            <div
              className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                isSelected ? 'border-blue-500' : 'border-gray-300'
              }`}
            >
              {isSelected && <CheckCircle className="w-4 h-4 text-blue-500" />}
            </div>
          </button>
        );
      })}
    </div>
  );
}

/**
 * 积分抵扣组件
 */
function PointsDeduction({
  userPoints,
  maxDeduction,
  pointsToUse,
  onPointsChange,
  enabled,
  onEnabledChange,
}: {
  userPoints: number;
  maxDeduction: number;
  pointsToUse: number;
  onPointsChange: (points: number) => void;
  enabled: boolean;
  onEnabledChange: (enabled: boolean) => void;
}) {
  const handleUseAll = useCallback(() => {
    onPointsChange(Math.min(userPoints, maxDeduction));
  }, [userPoints, maxDeduction, onPointsChange]);

  if (userPoints <= 0) {
    return null;
  }

  return (
    <div className="bg-amber-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Coins className="w-5 h-5 text-amber-500" />
          <span className="font-medium text-gray-900">积分抵扣</span>
        </div>
        <button
          onClick={() => onEnabledChange(!enabled)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            enabled ? 'bg-blue-600' : 'bg-gray-200'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              enabled ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      {enabled && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Info className="w-4 h-4" />
            <span>可使用 {Math.min(userPoints, maxDeduction)} 积分抵扣</span>
          </div>

          <div className="flex items-center gap-2">
            <Input
              type="number"
              min={0}
              max={Math.min(userPoints, maxDeduction)}
              value={pointsToUse}
              onChange={(e) => onPointsChange(Math.min(Number(e.target.value), maxDeduction))}
              className="flex-1"
              placeholder="输入积分数量"
            />
            <Button variant="outline" size="sm" onClick={handleUseAll}>
              全部使用
            </Button>
          </div>

          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>当前积分：{userPoints}</span>
            <span>最大可抵扣：{maxDeduction}</span>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * 购买确认组件
 */
function ConfirmStep({
  document,
  priceCalculation,
  paymentMethod,
  userPoints,
  userMemberTier,
  onConfirm,
  isProcessing,
}: {
  document: LegalDocument | LegalDocumentDetail;
  priceCalculation?: PriceCalculation;
  paymentMethod: PaymentMethod;
  userPoints?: number;
  userMemberTier?: 'monthly' | 'annual' | 'lifetime' | null;
  onConfirm: () => void;
  isProcessing: boolean;
}) {
  const [usePointsDeduction, setUsePointsDeduction] = useState(false);
  const [pointsToUse, setPointsToUse] = useState(0);

  // 检查是否可以购买
  const canPurchase = useMemo(() => {
    if (document.is_free || paymentMethod === 'member_free') return true;
    const price = priceCalculation?.price ?? document.price;
    const deduction = usePointsDeduction ? Math.floor(pointsToUse / 100) : 0;
    const actualPrice = Math.max(0, price - deduction);
    if (userPoints === undefined) return true; // 未知余额时不阻止
    return userPoints >= actualPrice;
  }, [document, paymentMethod, priceCalculation, userPoints, usePointsDeduction, pointsToUse]);

  return (
    <div className="space-y-6">
      {/* 文书信息 */}
      <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
        <div className="w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
          <FileText className="w-8 h-8 text-blue-500" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 line-clamp-2">{document.name}</h3>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="default" className="text-xs">
              {document.category_name}
            </Badge>
            {document.is_featured && (
              <Badge className="text-xs bg-yellow-50 text-yellow-700">精选</Badge>
            )}
          </div>
        </div>
      </div>

      {/* 支付方式选择 */}
      <PaymentMethodSelector
        document={document}
        priceCalculation={priceCalculation}
        selectedMethod={paymentMethod}
        onMethodChange={() => {}}
        userMemberTier={userMemberTier}
      />

      {/* 积分抵扣（仅积分支付时显示） */}
      {paymentMethod === 'points' && userPoints !== undefined && userPoints > 0 && (
        <PointsDeduction
          userPoints={userPoints}
          maxDeduction={(priceCalculation?.price ?? document.price) * 100}
          pointsToUse={pointsToUse}
          onPointsChange={setPointsToUse}
          enabled={usePointsDeduction}
          onEnabledChange={setUsePointsDeduction}
        />
      )}

      {/* 价格摘要 */}
      <Card className="p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">价格详情</h3>
        <PriceSummary
          document={document}
          priceCalculation={priceCalculation}
          paymentMethod={paymentMethod}
          userPoints={userPoints}
          usePointsDeduction={usePointsDeduction}
          pointsToUse={pointsToUse}
        />
      </Card>

      {/* 购买须知 */}
      <div className="text-xs text-gray-500 space-y-1">
        <p>• 虚拟商品，购买后不支持退款</p>
        <p>• 购买后可无限次下载文档</p>
        <p>• 文档支持 Word、PDF 格式导出</p>
      </div>

      {/* 确认按钮 */}
      <Button
        className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
        size="lg"
        onClick={onConfirm}
        disabled={!canPurchase || isProcessing}
      >
        {isProcessing ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            处理中...
          </>
        ) : (
          <>
            <Shield className="w-4 h-4 mr-2" />
            确认购买
          </>
        )}
      </Button>
    </div>
  );
}

/**
 * 处理中组件
 */
function ProcessingStep() {
  return (
    <div className="text-center py-8">
      <Loader2 className="w-16 h-16 text-blue-500 mx-auto mb-4 animate-spin" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">正在处理订单</h3>
      <p className="text-sm text-gray-500">请稍候，正在为您处理订单...</p>
    </div>
  );
}

/**
 * 成功组件
 */
function SuccessStep({
  result,
  onClose,
  onViewDocument,
}: {
  result: PurchaseResponse;
  onClose: () => void;
  onViewDocument: () => void;
}) {
  return (
    <div className="text-center py-8">
      <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <CheckCircle className="w-10 h-10 text-green-500" />
      </div>
      <h3 className="text-xl font-bold text-gray-900 mb-2">购买成功！</h3>
      <p className="text-gray-600 mb-6">您已成功获取该法律文书</p>

      {/* 订单信息 */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">订单号</span>
            <span className="font-medium">{result.order_no}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">文书名称</span>
            <span className="font-medium">{result.document_name}</span>
          </div>
          {result.points_spent !== undefined && result.points_spent > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-500">消费积分</span>
              <span className="font-medium text-orange-600">{result.points_spent}</span>
            </div>
          )}
          {result.balance !== undefined && (
            <div className="flex justify-between">
              <span className="text-gray-500">剩余积分</span>
              <span className="font-medium">{result.balance}</span>
            </div>
          )}
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-3">
        <Button variant="ghost" className="flex-1" onClick={onClose}>
          继续浏览
        </Button>
        <Button className="flex-1" onClick={onViewDocument}>
          查看文书
        </Button>
      </div>
    </div>
  );
}

/**
 * 错误组件
 */
function ErrorStep({
  error,
  onRetry,
  onClose,
}: {
  error: string;
  onRetry: () => void;
  onClose: () => void;
}) {
  return (
    <div className="text-center py-8">
      <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <AlertCircle className="w-10 h-10 text-red-500" />
      </div>
      <h3 className="text-xl font-bold text-gray-900 mb-2">购买失败</h3>
      <p className="text-gray-600 mb-6">{error}</p>

      {/* 操作按钮 */}
      <div className="flex gap-3">
        <Button variant="outline" className="flex-1" onClick={onClose}>
          取消
        </Button>
        <Button className="flex-1" onClick={onRetry}>
          重试
        </Button>
      </div>
    </div>
  );
}

/**
 * 文书购买流程主组件
 */
export default function DocumentPurchaseFlow({
  document,
  isOpen,
  onClose,
  onSuccess,
  onError,
  userPoints = 0,
}: DocumentPurchaseFlowProps) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const [currentStep, setCurrentStep] = useState<PurchaseStep>('confirm');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('points');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [purchaseResult, setPurchaseResult] = useState<PurchaseResponse | null>(null);

  // 获取价格计算
  const { data: priceCalculation } = useDocumentPrice(document.id);

  // 购买 mutation
  const purchaseMutation = usePurchaseDocument();

  // 初始化支付方式
  useEffect(() => {
    if (document.is_free) {
      setPaymentMethod('free');
    } else if (priceCalculation?.payment_method === 'member_free') {
      setPaymentMethod('member_free');
    } else {
      setPaymentMethod('points');
    }
  }, [document, priceCalculation]);

  // 处理购买
  const handlePurchase = useCallback(async () => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    setCurrentStep('processing');
    setErrorMessage('');

    try {
      const result = await purchaseMutation.mutateAsync({
        documentId: document.id,
        paymentMethod,
      });

      if (result.success) {
        setPurchaseResult(result);
        setCurrentStep('success');
        onSuccess?.(result);
      } else {
        setErrorMessage(result.error || '购买失败，请稍后重试');
        setCurrentStep('error');
        onError?.(new Error(result.error || '购买失败'));
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '购买失败，请稍后重试';
      setErrorMessage(message);
      setCurrentStep('error');
      onError?.(error instanceof Error ? error : new Error(String(error)));
    }
  }, [document, paymentMethod, isAuthenticated, purchaseMutation, navigate, onSuccess, onError]);

  // 重试
  const handleRetry = useCallback(() => {
    setCurrentStep('confirm');
    setErrorMessage('');
  }, []);

  // 查看文书
  const handleViewDocument = useCallback(() => {
    onClose();
    navigate(`/legal-documents/${document.id}/content`);
  }, [document, navigate, onClose]);

  // 关闭时重置状态
  const handleClose = useCallback(() => {
    setCurrentStep('confirm');
    setErrorMessage('');
    setPurchaseResult(null);
    onClose();
  }, [onClose]);

  const renderStepContent = () => {
    switch (currentStep) {
      case 'confirm':
        return (
          <ConfirmStep
            document={document}
            priceCalculation={priceCalculation}
            paymentMethod={paymentMethod}
            userPoints={userPoints}
            userMemberTier={undefined}
            onConfirm={() => {
              void handlePurchase();
            }}
            isProcessing={false}
          />
        );
      case 'processing':
        return <ProcessingStep />;
      case 'success':
        return (
          <SuccessStep
            result={purchaseResult!}
            onClose={handleClose}
            onViewDocument={handleViewDocument}
          />
        );
      case 'error':
        return (
          <ErrorStep
            error={errorMessage}
            onRetry={handleRetry}
            onClose={handleClose}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={
        currentStep === 'success' ? '购买成功' :
        currentStep === 'error' ? '购买失败' :
        '确认订单'
      }
      size="md"
    >
      <div className="min-h-[400px]">
        {renderStepContent()}
      </div>
    </Modal>
  );
}

// 导出子组件
export {
  PriceSummary,
  PaymentMethodSelector,
  PointsDeduction,
  ConfirmStep,
  ProcessingStep,
  SuccessStep,
  ErrorStep,
};
export type { DocumentPurchaseFlowProps };