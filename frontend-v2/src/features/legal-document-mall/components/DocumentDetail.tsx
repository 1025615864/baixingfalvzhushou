/**
 * 文书详情组件
 * 支持详情展示、预览、购买和收藏功能
 */

import { logger } from '@/shared/lib/logger';
import { useState, useCallback, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Eye,
  Heart,
  Star,
  Gift,
  Crown,
  Tag,
  ArrowLeft,
  Share2,
  UserCheck,
  AlertCircle,
  CheckCircle,
  Printer,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Maximize2,
  Minimize2,
  Sparkles,
  Shield,
  Download,
  Clock,
  HelpCircle,
  Copy,
} from 'lucide-react';

// RotateCw 的别名
const RotateCw = RotateCcw;
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { useAuthStore } from '@/features/auth/store/authStore';

import { useDocument, useDocumentPrice, useToggleFavorite, usePurchaseDocument } from '../hooks/useLegalDocuments';
import type { PriceCalculation, LegalDocumentDetail } from '../types';

// 会员等级颜色映射
const MEMBER_TIER_COLORS: Record<string, string> = {
  monthly: 'border-purple-200 bg-purple-50',
  annual: 'border-amber-200 bg-amber-50',
  lifetime: 'border-emerald-200 bg-emerald-50',
};

const MEMBER_TIER_NAMES: Record<string, string> = {
  monthly: '月度会员',
  annual: '年度会员',
  lifetime: '终身会员',
};

const MEMBER_TIER_TEXT_COLORS: Record<string, string> = {
  monthly: 'text-purple-600',
  annual: 'text-amber-600',
  lifetime: 'text-emerald-600',
};

interface DocumentDetailProps {
  documentId: number;
  onPurchase?: (document: LegalDocumentDetail) => void;
  onBack?: () => void;
  className?: string;
}

/**
 * 加载骨架屏
 */
function DetailSkeleton() {
  return (
    <div className="animate-pulse">
      {/* 顶部返回 */}
      <div className="mb-6">
        <Skeleton className="h-6 w-24" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* 左侧内容 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 标题区域 */}
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-start gap-4 mb-4">
              <Skeleton className="w-20 h-20 rounded-lg" />
              <div className="flex-1">
                <Skeleton className="h-6 w-3/4 mb-2" />
                <Skeleton className="h-4 w-1/2" />
              </div>
            </div>
            <div className="flex gap-2 mb-4">
              <Skeleton className="h-6 w-16" />
              <Skeleton className="h-6 w-16" />
              <Skeleton className="h-6 w-16" />
            </div>
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-2/3" />
          </div>

          {/* 预览区域 */}
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <Skeleton className="h-6 w-32 mb-4" />
            <div className="bg-gray-100 rounded-lg h-96" />
          </div>
        </div>

        {/* 右侧信息 */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <Skeleton className="h-8 w-full mb-4" />
            <Skeleton className="h-10 w-full mb-2" />
            <Skeleton className="h-10 w-full" />
          </div>
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <Skeleton className="h-6 w-32 mb-4" />
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-4 w-full" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * 价格信息组件
 */
function PriceInfo({
  document,
  priceCalculation,
  isLoading,
}: {
  document: LegalDocumentDetail;
  priceCalculation?: PriceCalculation;
  isLoading?: boolean;
}) {
  if (isLoading) {
    return <Skeleton className="h-20 w-full" />;
  }

  // 免费文书
  if (document.is_free) {
    return (
      <div className="text-center py-4 bg-green-50 rounded-lg border border-green-200">
        <Gift className="w-8 h-8 text-green-500 mx-auto mb-2" />
        <div className="text-2xl font-bold text-green-600">免费</div>
        <div className="text-sm text-green-600">可直接下载使用</div>
      </div>
    );
  }

  // 已购买
  if (document.is_purchased) {
    return (
      <div className="text-center py-4 bg-blue-50 rounded-lg border border-blue-200">
        <CheckCircle className="w-8 h-8 text-blue-500 mx-auto mb-2" />
        <div className="text-lg font-bold text-blue-600">已购买</div>
        <div className="text-sm text-blue-600">可直接查看和下载</div>
      </div>
    );
  }

  // 显示价格信息
  const originalPrice = priceCalculation?.original_price ?? document.price;
  const finalPrice = priceCalculation?.price ?? document.price;
  const discount = priceCalculation?.discount ?? 0;
  const tier = priceCalculation?.tier;

  return (
    <div className="space-y-4">
      {/* 原价和折扣 */}
      <div className="text-center">
        {discount > 0 && (
          <div className="flex items-center justify-center gap-2 mb-1">
            <span className="text-sm text-gray-400 line-through">
              {originalPrice} 积分
            </span>
            <Badge variant="danger" className="text-xs">
              -{discount}%
            </Badge>
          </div>
        )}
        <div className="flex items-baseline justify-center gap-1">
          <span className="text-3xl font-bold text-orange-600">{finalPrice}</span>
          <span className="text-sm text-gray-500">积分</span>
        </div>
        {tier && (
          <div className="text-xs text-gray-500 mt-1">
            {MEMBER_TIER_NAMES[tier]}专享价
          </div>
        )}
      </div>

      {/* 会员价格列表 */}
      {document.member_prices && (
        <div className="space-y-2">
          {document.member_prices.monthly && (
            <div className={`flex items-center justify-between px-3 py-2 rounded-lg border ${MEMBER_TIER_COLORS.monthly}`}>
              <span className={`text-sm font-medium ${MEMBER_TIER_TEXT_COLORS.monthly}`}>
                <Crown className="w-4 h-4 inline mr-1" />
                {MEMBER_TIER_NAMES.monthly}
              </span>
              <span className={`font-bold ${MEMBER_TIER_TEXT_COLORS.monthly}`}>
                {document.member_prices.monthly} 积分
              </span>
            </div>
          )}
          {document.member_prices.annual && (
            <div className={`flex items-center justify-between px-3 py-2 rounded-lg border ${MEMBER_TIER_COLORS.annual}`}>
              <span className={`text-sm font-medium ${MEMBER_TIER_TEXT_COLORS.annual}`}>
                <Crown className="w-4 h-4 inline mr-1" />
                {MEMBER_TIER_NAMES.annual}
              </span>
              <span className={`font-bold ${MEMBER_TIER_TEXT_COLORS.annual}`}>
                {document.member_prices.annual} 积分
              </span>
            </div>
          )}
          {document.member_prices.lifetime && (
            <div className={`flex items-center justify-between px-3 py-2 rounded-lg border ${MEMBER_TIER_COLORS.lifetime}`}>
              <span className={`text-sm font-medium ${MEMBER_TIER_TEXT_COLORS.lifetime}`}>
                <Crown className="w-4 h-4 inline mr-1" />
                {MEMBER_TIER_NAMES.lifetime}
              </span>
              <span className={`font-bold ${MEMBER_TIER_TEXT_COLORS.lifetime}`}>
                {document.member_prices.lifetime} 积分
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * 文档预览组件
 */
function DocumentPreview({
  content,
  documentName,
  isPurchased,
}: {
  content?: string;
  documentName: string;
  isPurchased: boolean;
}) {
  const [scale, setScale] = useState(100);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleZoomIn = () => setScale((prev) => Math.min(prev + 10, 200));
  const handleZoomOut = () => setScale((prev) => Math.max(prev - 10, 50));
  const handleReset = () => setScale(100);

  // 模拟预览内容（未购买时只显示部分）
  const previewContent = useMemo(() => {
    if (!content) {
      return `
${documentName}

【文书说明】
本模板为专业法律文书，适用于相关法律事务处理。

【文书预览】
----------------------------------------------
（以下为文书内容预览）

一、当事人信息
甲方：____________________
乙方：____________________

二、协议内容
根据《中华人民共和国民法典》及相关法律法规的规定，甲乙双方在平等、自愿的基础上，就相关事宜达成如下协议：

1. ____________________
2. ____________________
3. ____________________

...更多内容需要购买后查看...

----------------------------------------------

【购买后可获得】
✓ 完整文书内容
✓ 无限次下载
✓ 一年内免费更新
${isPurchased ? '' : '✓ 专属客服支持'}
      `;
    }
    return content;
  }, [content, documentName, isPurchased]);

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      {/* 工具栏 */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100 bg-gray-50">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleZoomOut}
            title="缩小"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <span className="text-sm text-gray-600 min-w-[3rem] text-center">
            {scale}%
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleZoomIn}
            title="放大"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReset}
            title="重置"
          >
            <RotateCw className="w-4 h-4" />
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? '退出全屏' : '全屏'}
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>

      {/* 预览区域 */}
      <div
        className={`bg-gray-100 overflow-auto ${
          isFullscreen ? 'fixed inset-0 z-50' : 'h-96'
        }`}
      >
        <div
          className="bg-white mx-auto my-4 shadow-lg p-8 transition-transform"
          style={{
            width: `${scale}%`,
            minWidth: '320px',
            maxWidth: '800px',
          }}
        >
          {/* 未购买提示 */}
          {!isPurchased && (
            <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>此为预览版本，购买后可查看完整内容</span>
            </div>
          )}

          {/* 文档内容 */}
          <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans leading-relaxed">
            {previewContent}
          </pre>
        </div>
      </div>
    </div>
  );
}

/**
 * 文书详情主组件
 */
export default function DocumentDetail({
  documentId,
  onPurchase,
  onBack,
  className = '',
}: Omit<DocumentDetailProps, 'showPurchaseFlow'>) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const [isFavorited, setIsFavorited] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);

  // 获取文书详情
  const { data: document, isLoading, error } = useDocument(documentId);
  const { data: priceCalculation } = useDocumentPrice(documentId);

  // 收藏/取消收藏
  const favoriteMutation = useToggleFavorite();

  // 购买
  const purchaseMutation = usePurchaseDocument();

  // 初始化收藏状态
  useEffect(() => {
    if (document) {
      setIsFavorited(document.is_favorited || false);
    }
  }, [document]);

  // 返回
  const handleBack = useCallback(() => {
    if (onBack) {
      onBack();
    } else {
      navigate(-1);
    }
  }, [navigate, onBack]);

  // 收藏
  const handleFavorite = useCallback(async () => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    try {
      await favoriteMutation.mutateAsync({
        documentId,
        isFavorited,
      });
      setIsFavorited(!isFavorited);
    } catch (error) {
      logger.error('收藏操作失败', error);
    }
  }, [documentId, isAuthenticated, isFavorited, favoriteMutation, navigate]);

  // 购买
  const handlePurchase = useCallback(async () => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    if (!document) return;

    if (onPurchase) {
      onPurchase(document);
    } else {
      // 直接购买
      try {
        const paymentMethod = document.is_free ? 'free' : 'points';
        const result = await purchaseMutation.mutateAsync({
          documentId,
          paymentMethod,
        });

        if (result.success) {
          alert(`购买成功！订单号: ${result.order_no}`);
          navigate(`/legal-documents/${documentId}/content`);
        } else {
          alert(result.error || '购买失败');
        }
      } catch (error: unknown) {
        const message = error instanceof Error ? error.message : String(error);
        alert(message || '购买失败，请稍后重试');
      }
    }
  }, [document, documentId, isAuthenticated, onPurchase, purchaseMutation, navigate]);

  // 分享
  const handleShare = useCallback(() => {
    setShowShareModal(true);
  }, []);

  // 复制链接
  const handleCopyLink = useCallback(async () => {
    const url = window.location.href;
    try {
      await navigator.clipboard.writeText(url);
      alert('链接已复制到剪贴板');
    } catch {
      alert('复制失败，请手动复制');
    }
    setShowShareModal(false);
  }, []);

  // 打印
  const handlePrint = useCallback(() => {
    window.print();
  }, []);

  // 下载
  const handleDownload = useCallback(() => {
    if (!document?.is_purchased) {
      alert('请先购买文书');
      return;
    }
    // TODO: 实现下载功能
    alert('下载功能开发中...');
  }, [document]);

  // 处理分享
  const handleShareClick = useCallback(() => {
    void handleShare();
  }, [handleShare]);

  // 处理打印
  const handlePrintClick = useCallback(() => {
    void handlePrint();
  }, [handlePrint]);

  // 处理下载
  const handleDownloadClick = useCallback(() => {
    void handleDownload();
  }, [handleDownload]);

  if (isLoading) {
    return (
      <div className={className}>
        <DetailSkeleton />
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className={className}>
        <div className="text-center py-16">
          <AlertCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">文书不存在</h2>
          <p className="text-gray-500 mb-4">您访问的文书可能已删除或不存在</p>
          <Button onClick={handleBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* 顶部导航 */}
      <div className="flex items-center justify-between mb-6">
        <Button variant="ghost" onClick={handleBack} className="text-gray-600">
          <ArrowLeft className="w-4 h-4 mr-2" />
          返回列表
        </Button>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleShareClick}>
            <Share2 className="w-4 h-4 mr-2" />
            分享
          </Button>
          <Button variant="outline" size="sm" onClick={handlePrintClick}>
            <Printer className="w-4 h-4 mr-2" />
            打印
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* 左侧内容 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 标题区域 */}
          <Card className="p-6">
            <div className="flex items-start gap-4 mb-4">
              <div className="w-20 h-20 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                <FileText className="w-10 h-10 text-blue-500" />
              </div>
              <div className="flex-1">
                <h1 className="text-xl font-bold text-gray-900 mb-2">
                  {document.name}
                </h1>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span className="flex items-center gap-1">
                    <Eye className="w-4 h-4" />
                    {document.view_count.toLocaleString()} 浏览
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Download className="w-4 h-4" />
                    {document.download_count.toLocaleString()} 下载
                  </span>
                  {document.rating > 0 && (
                    <>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                        {document.rating.toFixed(1)}
                      </span>
                    </>
                  )}
                </div>
              </div>
              <button
                onClick={() => {
                  void handleFavorite();
                }}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                title={isFavorited ? '取消收藏' : '收藏'}
              >
                <Heart
                  className={`w-6 h-6 transition-colors ${
                    isFavorited
                      ? 'fill-red-500 text-red-500'
                      : 'text-gray-300 hover:text-gray-400'
                  }`}
                />
              </button>
            </div>

            {/* 标签 */}
            <div className="flex flex-wrap gap-2 mb-4">
              {document.is_featured && (
                <Badge className="bg-yellow-50 text-yellow-700 border-yellow-200">
                  <Star className="w-3 h-3 mr-1" />
                  精选推荐
                </Badge>
              )}
              {document.is_free && (
                <Badge className="bg-green-50 text-green-700 border-green-200">
                  <Gift className="w-3 h-3 mr-1" />
                  免费
                </Badge>
              )}
              {document.is_purchased && (
                <Badge className="bg-blue-50 text-blue-700 border-blue-200">
                  <UserCheck className="w-3 h-3 mr-1" />
                  已购买
                </Badge>
              )}
              {document.custom_service_available && (
                <Badge className="bg-purple-50 text-purple-700 border-purple-200">
                  <Sparkles className="w-3 h-3 mr-1" />
                  可定制
                </Badge>
              )}
            </div>

            {/* 描述 */}
            <p className="text-gray-600 leading-relaxed">
              {document.description || '暂无描述'}
            </p>

            {/* 分类标签 */}
            <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-gray-100">
              <Badge variant="default" className="text-gray-500">
                <Tag className="w-3 h-3 mr-1" />
                {document.category_name}
              </Badge>
              {document.tags?.map((tag) => (
                <Badge
                  key={tag}
                  variant="default"
                  className="text-gray-500 bg-gray-50"
                >
                  {tag}
                </Badge>
              ))}
            </div>
          </Card>

          {/* 预览区域 */}
          <div>
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              文书预览
            </h2>
            <DocumentPreview
              content={document.content}
              documentName={document.name}
              isPurchased={document.is_purchased || false}
            />
          </div>
        </div>

        {/* 右侧信息 */}
        <div className="space-y-6">
          {/* 购买卡片 */}
          <Card className="p-6 sticky top-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">购买信息</h3>

            {/* 价格 */}
            <PriceInfo
              document={document}
              priceCalculation={priceCalculation}
            />

            {/* 操作按钮 */}
            <div className="mt-6 space-y-3">
              {document.is_purchased ? (
                <>
                  <Button
                    className="w-full"
                    size="lg"
                    onClick={handleDownloadClick}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    下载文档
                  </Button>
                  <Button
                    variant="ghost"
                    className="w-full"
                    size="lg"
                    onClick={() => {
                      navigate(`/legal-documents/${documentId}/content`);
                    }}
                  >
                    查看完整内容
                  </Button>
                </>
              ) : (
                <Button
                  className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
                  size="lg"
                  onClick={() => {
                    void handlePurchase();
                  }}
                  disabled={purchaseMutation.isPending}
                >
                  {purchaseMutation.isPending && '处理中...'}
                  {!purchaseMutation.isPending && document.is_free && (
                    <>
                      <Gift className="w-4 h-4 mr-2" />
                      免费获取
                    </>
                  )}
                  {!purchaseMutation.isPending && !document.is_free && (
                    <>
                      <Crown className="w-4 h-4 mr-2" />
                      立即购买
                    </>
                  )}
                </Button>
              )}
            </div>

            {/* 定制服务 */}
            {document.custom_service_available && (
              <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
                <div className="flex items-center gap-2 text-purple-700 mb-2">
                  <Sparkles className="w-4 h-4" />
                  <span className="font-medium">专业定制服务</span>
                </div>
                <p className="text-sm text-purple-600 mb-3">
                  根据您的具体需求，由专业律师为您定制文书
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-lg font-bold text-purple-700">
                    {document.custom_service_price} 积分起
                  </span>
                  <Button size="sm" variant="outline" className="border-purple-300 text-purple-600">
                    咨询定制
                  </Button>
                </div>
              </div>
            )}
          </Card>

          {/* 服务保障 */}
          <Card className="p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">服务保障</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <Shield className="w-5 h-5 text-blue-500" />
                <span>专业律师审核</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span>内容准确合规</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <Clock className="w-5 h-5 text-amber-500" />
                <span>一年内免费更新</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <Download className="w-5 h-5 text-purple-500" />
                <span>无限次下载</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <HelpCircle className="w-5 h-5 text-teal-500" />
                <span>专属客服支持</span>
              </div>
            </div>
          </Card>

          {/* 购买须知 */}
          <Card className="p-6 bg-gray-50">
            <h3 className="text-sm font-bold text-gray-700 mb-3">购买须知</h3>
            <ul className="space-y-2 text-xs text-gray-500">
              <li>• 购买后可无限次下载文档</li>
              <li>• 文档支持 Word、PDF 格式导出</li>
              <li>• 虚拟商品，购买后不支持退款</li>
              <li>• 如有问题请联系客服</li>
            </ul>
          </Card>
        </div>
      </div>

      {/* 分享弹窗 */}
      <Modal
        isOpen={showShareModal}
        onClose={() => setShowShareModal(false)}
        title="分享文书"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            将此文书分享给您的朋友或同事
          </p>
          <div className="flex gap-2">
            <Input
              value={window.location.href}
              readOnly
              className="flex-1"
            />
            <Button onClick={() => {
              void handleCopyLink();
            }}>
              <Copy className="w-4 h-4 mr-2" />
              复制
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// 导出子组件
export { PriceInfo, DocumentPreview, DetailSkeleton };
export type { DocumentDetailProps };