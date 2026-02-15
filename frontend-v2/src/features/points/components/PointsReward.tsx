/**
 * PointsReward - 积分奖励展示组件
 * 功能：展示会员升级奖励、商品兑换选项
 * 包含奖励卡片列表
 */

import { useState } from 'react';

import type { PointsProduct } from '../types';

interface PointsRewardProps {
  className?: string;
  onExchange?: (product: PointsProduct) => void;
}

/**
 * 模拟奖励数据
 */
const MOCK_REWARDS: RewardItem[] = [
  {
    id: 'reward-1',
    type: 'membership',
    title: '青铜会员',
    description: '完成首次签到即可获得',
    points: 50,
    icon: '🥉',
    color: 'from-orange-400 to-amber-500',
    unlocked: true,
    claimed: false,
  },
  {
    id: 'reward-2',
    type: 'membership',
    title: '白银会员',
    description: '连续签到7天解锁',
    points: 100,
    icon: '🥈',
    color: 'from-gray-400 to-gray-500',
    unlocked: false,
    claimed: false,
    requirement: '还需签到3天',
  },
  {
    id: 'reward-3',
    type: 'membership',
    title: '黄金会员',
    description: '累计获得500积分',
    points: 200,
    icon: '🥇',
    color: 'from-yellow-400 to-amber-500',
    unlocked: false,
    claimed: false,
    requirement: '还需350积分',
  },
  {
    id: 'reward-4',
    type: 'membership',
    title: '钻石会员',
    description: '完成所有新手任务',
    points: 500,
    icon: '💎',
    color: 'from-blue-400 to-cyan-500',
    unlocked: false,
    claimed: false,
    requirement: '完成3个任务',
  },
];

interface RewardItem {
  id: string;
  type: 'membership' | 'product' | 'bonus';
  title: string;
  description: string;
  points: number;
  icon: string;
  color: string;
  unlocked: boolean;
  claimed: boolean;
  requirement?: string;
}

/**
 * 积分奖励展示组件
 */
export function PointsReward({
  className = '',
  onExchange,
}: PointsRewardProps): JSX.Element {
  const [activeTab, setActiveTab] = useState<'membership' | 'products'>('membership');
  const [claimingId, setClaimingId] = useState<string | null>(null);

  /**
   * 处理领取奖励
   */
  const handleClaim = async (reward: RewardItem) => {
    if (!reward.unlocked || reward.claimed) return;
    
    setClaimingId(reward.id);
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000));
    setClaimingId(null);
    
    // 显示成功提示
    alert(`成功领取 ${reward.title} 奖励！获得 ${reward.points} 积分`);
  };

  /**
   * 处理兑换商品
   */
  const handleExchangeProduct = (product: PointsProduct) => {
    onExchange?.(product);
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 标签切换 */}
      <div className="flex gap-2 p-1 bg-gray-100 rounded-lg">
        <button
          onClick={() => setActiveTab('membership')}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'membership'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          会员升级
        </button>
        <button
          onClick={() => setActiveTab('products')}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'products'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          商品兑换
        </button>
      </div>

      {/* 会员升级内容 */}
      {activeTab === 'membership' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {MOCK_REWARDS.map((reward) => (
            <div
              key={reward.id}
              className={`relative overflow-hidden rounded-xl p-5 transition-all ${
                reward.unlocked
                  ? 'bg-white shadow-md hover:shadow-lg'
                  : 'bg-gray-50 opacity-75'
              }`}
            >
              {/* 背景渐变装饰 */}
              <div
                className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${reward.color} opacity-10 rounded-bl-full`}
              />
              
              <div className="relative flex items-start gap-4">
                {/* 图标 */}
                <div
                  className={`flex-shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br ${reward.color} flex items-center justify-center text-3xl shadow-lg`}
                >
                  {reward.icon}
                </div>
                
                {/* 内容 */}
                <div className="flex-1 min-w-0">
                  <h4 className="font-bold text-gray-900">{reward.title}</h4>
                  <p className="text-sm text-gray-500 mt-1">{reward.description}</p>
                  
                  {/* 积分奖励 */}
                  <div className="flex items-center gap-1 mt-2 text-amber-600 font-medium">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M10 2l2.5 5.5L18 8l-4 3.5L15 17l-5-3-5 3 1-5.5L2 8l5.5-.5L10 2z" />
                    </svg>
                    <span>+{reward.points} 积分</span>
                  </div>

                  {/* 状态标签 */}
                  {!reward.unlocked && reward.requirement && (
                    <span className="inline-block mt-2 text-xs px-2 py-1 bg-gray-200 text-gray-600 rounded-full">
                      {reward.requirement}
                    </span>
                  )}
                  
                  {reward.unlocked && !reward.claimed && (
                    <button
                      onClick={() => void handleClaim(reward)}
                      disabled={claimingId === reward.id}
                      className="mt-3 w-full py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white text-sm font-medium rounded-lg hover:from-blue-600 hover:to-blue-700 transition-colors disabled:opacity-50"
                    >
                      {claimingId === reward.id ? '领取中...' : '立即领取'}
                    </button>
                  )}
                  
                  {reward.claimed && (
                    <span className="inline-flex items-center gap-1 mt-3 text-sm text-green-600">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      已领取
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 商品兑换内容 */}
      {activeTab === 'products' && (
        <PointsProductGrid onExchange={handleExchangeProduct} />
      )}
    </div>
  );
}

/**
 * 积分商品网格组件
 */
interface PointsProductGridProps {
  products?: PointsProduct[];
  onExchange?: (product: PointsProduct) => void;
  loading?: boolean;
}

function PointsProductGrid({
  products,
  onExchange,
  loading = false,
}: PointsProductGridProps): JSX.Element {
  // 模拟商品数据
  const mockProducts: PointsProduct[] = products || [
    {
      id: 'prod-1',
      name: '10元话费充值',
      description: '三网通用，即时到账',
      pointsRequired: 1000,
      productType: 'virtual',
      stock: 999,
      status: 'active',
      imageUrl: '💳',
    },
    {
      id: 'prod-2',
      name: '腾讯视频月卡',
      description: '畅享海量影视资源',
      pointsRequired: 2000,
      productType: 'virtual',
      stock: 500,
      status: 'active',
      imageUrl: '🎬',
    },
    {
      id: 'prod-3',
      name: '星巴克咖啡券',
      description: '全国门店通用',
      pointsRequired: 3000,
      productType: 'virtual',
      stock: 200,
      status: 'active',
      imageUrl: '☕',
    },
    {
      id: 'prod-4',
      name: '法律咨询优惠券',
      description: '抵扣50元咨询费用',
      pointsRequired: 500,
      productType: 'coupon',
      stock: 1000,
      status: 'active',
      imageUrl: '📋',
    },
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-xl p-4 animate-pulse">
            <div className="w-full h-32 bg-gray-200 rounded-lg mb-4" />
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
            <div className="h-3 bg-gray-200 rounded w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {mockProducts.map((product) => (
        <div
          key={product.id}
          className="bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow"
        >
          {/* 商品图片/图标 */}
          <div className="aspect-square bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg flex items-center justify-center text-5xl mb-3">
            {product.imageUrl || '🎁'}
          </div>
          
          {/* 商品信息 */}
          <h4 className="font-medium text-gray-900 text-sm line-clamp-1">{product.name}</h4>
          <p className="text-xs text-gray-500 mt-1 line-clamp-1">{product.description}</p>
          
          {/* 积分和兑换按钮 */}
          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-1 text-amber-600 font-bold">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 2l2.5 5.5L18 8l-4 3.5L15 17l-5-3-5 3 1-5.5L2 8l5.5-.5L10 2z" />
              </svg>
              <span className="text-sm">{product.pointsRequired}</span>
            </div>
            
            <button
              onClick={() => onExchange?.(product)}
              disabled={product.stock <= 0}
              className="px-3 py-1.5 bg-blue-500 text-white text-xs font-medium rounded-lg hover:bg-blue-600 transition-colors disabled:bg-gray-300"
            >
              {product.stock > 0 ? '兑换' : '缺货'}
            </button>
          </div>
          
          {/* 库存提示 */}
          {product.stock < 50 && product.stock > 0 && (
            <p className="text-xs text-orange-500 mt-2">仅剩 {product.stock} 件</p>
          )}
        </div>
      ))}
    </div>
  );
}

/**
 * 奖励进度条组件
 */
interface RewardProgressProps {
  currentPoints: number;
  targetPoints: number;
  level: string;
  nextLevel?: string;
  className?: string;
}

export function RewardProgress({
  currentPoints,
  targetPoints,
  level,
  nextLevel,
  className = '',
}: RewardProgressProps): JSX.Element {
  const progress = Math.min((currentPoints / targetPoints) * 100, 100);
  
  return (
    <div className={`bg-white rounded-xl p-5 shadow-sm ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="font-bold text-gray-900">当前等级：{level}</h4>
          {nextLevel && (
            <p className="text-sm text-gray-500">
              距离 {nextLevel} 还需 {Math.max(0, targetPoints - currentPoints)} 积分
            </p>
          )}
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold text-blue-600">{currentPoints}</span>
          <span className="text-gray-400"> / {targetPoints}</span>
        </div>
      </div>
      
      {/* 进度条 */}
      <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
      
      {/* 里程碑标记 */}
      <div className="flex justify-between mt-2 text-xs text-gray-400">
        <span>0</span>
        <span>{Math.round(targetPoints * 0.25)}</span>
        <span>{Math.round(targetPoints * 0.5)}</span>
        <span>{Math.round(targetPoints * 0.75)}</span>
        <span>{targetPoints}</span>
      </div>
    </div>
  );
}