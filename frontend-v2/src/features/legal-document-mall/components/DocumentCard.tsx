/**
 * 文书卡片组件
 * 显示单个文书信息，支持收藏状态和会员折扣显示
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Eye,
  Heart,
  Star,
  Gift,
  Crown,
  Tag,
  ChevronRight,
  Sparkles,
  UserCheck,
  Download,
  // Clock - unused
} from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useAuthStore } from '@/features/auth/store/authStore';

import type { LegalDocument } from '../types';

// 会员等级颜色映射
const MEMBER_TIER_COLORS: Record<string, string> = {
  monthly: 'text-purple-600 bg-purple-50 border-purple-200',
  annual: 'text-amber-600 bg-amber-50 border-amber-200',
  lifetime: 'text-emerald-600 bg-emerald-50 border-emerald-200',
};

// 会员等级名称映射
const MEMBER_TIER_NAMES: Record<string, string> = {
  monthly: '月度会员',
  annual: '年度会员',
  lifetime: '终身会员',
};

interface DocumentCardProps {
  document: LegalDocument;
  onPurchase?: (document: LegalDocument) => void;
  onToggleFavorite?: (document: LegalDocument) => void;
  onClick?: (document: LegalDocument) => void;
  showMemberPrice?: boolean;
  compact?: boolean;
  className?: string;
}

/**
 * 价格显示组件
 */
function PriceDisplay({
  document,
  showMemberPrice,
}: {
  document: LegalDocument;
  showMemberPrice?: boolean;
}) {
  // 免费文书
  if (document.is_free) {
    return (
      <div className="flex items-center gap-1">
        <Gift className="w-4 h-4 text-green-500" />
        <span className="text-lg font-bold text-green-600">免费</span>
      </div>
    );
  }

  // 会员价格显示
  const memberPrices = document.member_prices;
  const hasMemberPrice = memberPrices && (memberPrices.monthly || memberPrices.annual || memberPrices.lifetime);

  return (
    <div className="flex flex-col gap-1">
      {/* 原价 */}
      <div className="flex items-baseline gap-1">
        <span className="text-lg font-bold text-orange-600">{document.price}</span>
        <span className="text-xs text-gray-500">积分</span>
      </div>

      {/* 会员折扣价 */}
      {showMemberPrice && hasMemberPrice && (
        <div className="flex flex-wrap gap-1">
          {memberPrices.monthly && (
            <Badge
              variant="default"
              className={`text-xs ${MEMBER_TIER_COLORS.monthly}`}
            >
              <Crown className="w-3 h-3 mr-1" />
              {MEMBER_TIER_NAMES.monthly}: {memberPrices.monthly}积分
            </Badge>
          )}
          {memberPrices.annual && (
            <Badge
              variant="default"
              className={`text-xs ${MEMBER_TIER_COLORS.annual}`}
            >
              <Crown className="w-3 h-3 mr-1" />
              {MEMBER_TIER_NAMES.annual}: {memberPrices.annual}积分
            </Badge>
          )}
          {memberPrices.lifetime && (
            <Badge
              variant="default"
              className={`text-xs ${MEMBER_TIER_COLORS.lifetime}`}
            >
              <Crown className="w-3 h-3 mr-1" />
              {MEMBER_TIER_NAMES.lifetime}: {memberPrices.lifetime}积分
            </Badge>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * 文书卡片主组件
 */
export default function DocumentCard({
  document,
  onPurchase,
  onToggleFavorite,
  onClick,
  showMemberPrice = true,
  compact = false,
  className = '',
}: DocumentCardProps) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const [isFavorited, setIsFavorited] = useState(document.is_favorited || false);
  const [isHovered, setIsHovered] = useState(false);

  // 处理卡片点击
  const handleClick = useCallback(() => {
    if (onClick) {
      onClick(document);
    } else {
      navigate(`/legal-documents/${document.id}`);
    }
  }, [document, onClick, navigate]);

  // 处理收藏
  const handleFavorite = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (!isAuthenticated) {
        navigate('/login');
        return;
      }
      const newState = !isFavorited;
      setIsFavorited(newState);
      onToggleFavorite?.({ ...document, is_favorited: newState } as LegalDocument);
    },
    [document, isAuthenticated, isFavorited, navigate, onToggleFavorite]
  );

  // 处理购买
  const handlePurchase = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (!isAuthenticated) {
        navigate('/login');
        return;
      }
      onPurchase?.(document);
    },
    [document, isAuthenticated, navigate, onPurchase]
  );

  // 紧凑模式
  if (compact) {
    return (
      <Card
        className={`p-3 hover:shadow-md transition-all duration-200 cursor-pointer ${className}`}
        onClick={handleClick}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0 p-2 bg-blue-50 rounded-lg">
            <FileText className="w-5 h-5 text-blue-600" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-medium text-gray-900 truncate">
                {document.name}
              </h3>
              {document.is_featured && (
                <Star className="w-3 h-3 text-yellow-500 flex-shrink-0" />
              )}
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
              <span>{document.category_name}</span>
              {document.is_free ? (
                <Badge variant="success" className="text-green-600 text-xs">
                  免费
                </Badge>
              ) : (
                <span className="text-orange-600">{document.price}积分</span>
              )}
            </div>
          </div>
          <ChevronRight className={`w-4 h-4 text-gray-400 transition-transform ${isHovered ? 'translate-x-1' : ''}`} />
        </div>
      </Card>
    );
  }

  return (
    <Card
      className={`p-4 hover:shadow-lg transition-all duration-300 cursor-pointer group ${className}`}
      onClick={handleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* 顶部标签栏 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          {/* 推荐标签 */}
          {document.is_featured && (
            <Badge variant="warning" className="text-xs bg-yellow-50 text-yellow-700 border-yellow-200">
              <Star className="w-3 h-3 mr-1" />
              精选推荐
            </Badge>
          )}
          {/* 免费标签 */}
          {document.is_free && (
            <Badge variant="success" className="text-xs text-green-600 border-green-200">
              <Gift className="w-3 h-3 mr-1" />
              免费
            </Badge>
          )}
          {/* 已购买标签 */}
          {document.is_purchased && (
            <Badge variant="primary" className="text-xs text-blue-600 border-blue-200">
              <UserCheck className="w-3 h-3 mr-1" />
              已购买
            </Badge>
          )}
          {/* 定制服务标签 */}
          {document.custom_service_available && (
            <Badge variant="default" className="text-xs text-purple-600 border-purple-200">
              <Sparkles className="w-3 h-3 mr-1" />
              可定制
            </Badge>
          )}
        </div>

        {/* 收藏按钮 */}
        <button
          onClick={handleFavorite}
          className="p-1.5 hover:bg-gray-100 rounded-full transition-colors"
          title={isFavorited ? '取消收藏' : '收藏'}
        >
          <Heart
            className={`w-5 h-5 transition-colors ${
              isFavorited
                ? 'fill-red-500 text-red-500'
                : 'text-gray-300 group-hover:text-gray-400'
            }`}
          />
        </button>
      </div>

      {/* 文书名称 */}
      <h3 className="font-medium text-gray-900 line-clamp-2 mb-2 group-hover:text-blue-600 transition-colors">
        {document.name}
      </h3>

      {/* 文书描述 */}
      <p className="text-sm text-gray-500 line-clamp-2 mb-3">
        {document.description || '暂无描述'}
      </p>

      {/* 标签 */}
      {document.tags && document.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {document.tags.slice(0, 3).map((tag, index) => (
            <Badge
              key={index}
              variant="default"
              className="text-xs text-gray-500 bg-gray-50"
            >
              <Tag className="w-2.5 h-2.5 mr-1" />
              {tag}
            </Badge>
          ))}
          {document.tags.length > 3 && (
            <Badge variant="default" className="text-xs text-gray-400">
              +{document.tags.length - 3}
            </Badge>
          )}
        </div>
      )}

      {/* 统计信息 */}
      <div className="flex items-center gap-4 text-xs text-gray-400 mb-4">
        <span className="flex items-center gap-1">
          <Eye className="w-3.5 h-3.5" />
          {document.view_count.toLocaleString()} 浏览
        </span>
        <span className="flex items-center gap-1">
          <Download className="w-3.5 h-3.5" />
          {document.download_count.toLocaleString()} 下载
        </span>
        {document.rating > 0 && (
          <span className="flex items-center gap-1">
            <Star className="w-3.5 h-3.5 text-yellow-400 fill-yellow-400" />
            {document.rating.toFixed(1)}
          </span>
        )}
      </div>

      {/* 价格和购买区域 */}
      <div className="flex items-end justify-between pt-3 border-t border-gray-100">
        <PriceDisplay document={document} showMemberPrice={showMemberPrice} />

        <div className="flex items-center gap-2">
          {document.is_purchased ? (
            <Button size="sm" variant="ghost" className="text-blue-600 border-blue-200">
              查看文档
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={handlePurchase}
              className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
            >
              {document.is_free ? '立即获取' : '立即购买'}
            </Button>
          )}
        </div>
      </div>

      {/* 定制服务价格提示 */}
      {document.custom_service_available && document.custom_service_price > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-purple-500" />
              专业定制服务
            </span>
            <span className="text-purple-600 font-medium">
              {document.custom_service_price} 积分起
            </span>
          </div>
        </div>
      )}
    </Card>
  );
}

// 导出子组件
export { PriceDisplay };
export type { DocumentCardProps };