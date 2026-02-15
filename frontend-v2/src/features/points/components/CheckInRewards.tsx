/**
 * CheckInRewards - 签到奖励规则组件
 * 功能：展示7天连续签到奖励规则
 * 使用进度条或日历形式展示
 */

import { useMemo } from 'react';

interface CheckInRewardsProps {
  /** 连续签到天数 */
  continuousDays: number;
  /** 今日是否已签到 */
  hasCheckedInToday: boolean;
  /** 点击某天奖励 */
  onDayClick?: (day: number) => void;
  className?: string;
}

/**
 * 签到奖励配置
 */
interface DayReward {
  day: number;
  points: number;
  bonus?: string;
  icon: string;
  isMilestone: boolean;
}

/**
 * 7天签到奖励配置
 */
const WEEKLY_REWARDS: DayReward[] = [
  { day: 1, points: 10, icon: '☀️', isMilestone: false },
  { day: 2, points: 15, icon: '🌤️', isMilestone: false },
  { day: 3, points: 20, icon: '⛅', isMilestone: false },
  { day: 4, points: 25, icon: '🌥️', isMilestone: false },
  { day: 5, points: 30, icon: '☁️', isMilestone: false },
  { day: 6, points: 40, icon: '🌤️', isMilestone: false },
  { day: 7, points: 100, bonus: '神秘大奖', icon: '🎁', isMilestone: true },
];

/**
 * 签到奖励规则组件
 */
export function CheckInRewards({
  continuousDays,
  hasCheckedInToday,
  onDayClick,
  className = '',
}: CheckInRewardsProps): JSX.Element {
  // 计算进度
  const currentDayInWeek = useMemo(() => {
    const day = continuousDays % 7;
    return day === 0 ? 7 : day;
  }, [continuousDays]);

  // 本周进度
  const weeklyProgress = useMemo(() => {
    if (continuousDays < 7) {
      return hasCheckedInToday ? currentDayInWeek : currentDayInWeek - 1;
    }
    return hasCheckedInToday ? 7 : 6;
  }, [continuousDays, hasCheckedInToday, currentDayInWeek]);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 标题和说明 */}
      <div className="text-center">
        <h3 className="text-lg font-bold text-gray-900">连续签到奖励</h3>
        <p className="text-sm text-gray-500 mt-1">
          连续签到7天可获得额外大奖
        </p>
      </div>

      {/* 进度条形式 */}
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm text-gray-600">本周进度</span>
          <span className="text-sm font-medium text-blue-600">
            {weeklyProgress}/7 天
          </span>
        </div>
        
        {/* 进度条 */}
        <div className="h-3 bg-gray-100 rounded-full overflow-hidden mb-4">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500"
            style={{ width: `${(weeklyProgress / 7) * 100}%` }}
          />
        </div>

        {/* 里程碑标记 */}
        <div className="flex justify-between px-1">
          {WEEKLY_REWARDS.map((reward) => (
            <div
              key={reward.day}
              className={`flex flex-col items-center cursor-pointer transition-transform hover:scale-110 ${
                reward.day <= weeklyProgress ? 'opacity-100' : 'opacity-40'
              }`}
              onClick={() => onDayClick?.(reward.day)}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm mb-1 ${
                  reward.day <= weeklyProgress
                    ? reward.isMilestone
                      ? 'bg-gradient-to-br from-yellow-400 to-orange-500 text-white shadow-lg'
                      : 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-400'
                }`}
              >
                {reward.isMilestone ? '🎁' : reward.day}
              </div>
              <span className="text-xs text-gray-500">+{reward.points}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 日历形式展示 */}
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <h4 className="font-medium text-gray-900 mb-4">每日奖励详情</h4>
        
        <div className="grid grid-cols-7 gap-2">
          {WEEKLY_REWARDS.map((reward) => {
            const isCompleted = reward.day <= weeklyProgress;
            const isToday = reward.day === currentDayInWeek && !hasCheckedInToday;

            return (
              <div
                key={reward.day}
                onClick={() => onDayClick?.(reward.day)}
                className={`
                  relative aspect-square rounded-xl p-2 flex flex-col items-center justify-center
                  cursor-pointer transition-all duration-200
                  ${isCompleted 
                    ? 'bg-gradient-to-br from-blue-50 to-purple-50 border-2 border-blue-200' 
                    : isToday
                    ? 'bg-amber-50 border-2 border-amber-400 ring-2 ring-amber-200 animate-pulse'
                    : 'bg-gray-50 border border-gray-100 hover:bg-gray-100'
                  }
                `}
              >
                {/* 日期 */}
                <span className={`
                  text-xs font-medium mb-1
                  ${isCompleted ? 'text-blue-600' : isToday ? 'text-amber-600' : 'text-gray-400'}
                `}>
                  {reward.day}天
                </span>
                
                {/* 图标 */}
                <span className="text-xl mb-1">{reward.icon}</span>
                
                {/* 积分 */}
                <span className={`
                  text-xs font-bold
                  ${isCompleted ? 'text-blue-600' : isToday ? 'text-amber-600' : 'text-gray-400'}
                `}>
                  +{reward.points}
                </span>

                {/* 今日标记 */}
                {isToday && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                    <span className="w-2 h-2 bg-white rounded-full animate-ping" />
                  </span>
                )}

                {/* 完成标记 */}
                {isCompleted && (
                  <span className="absolute top-1 right-1">
                    <svg className="w-3 h-3 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </span>
                )}

                {/* 里程碑标记 */}
                {reward.isMilestone && (
                  <span className="absolute -bottom-1 left-1/2 transform -translate-x-1/2">
                    <span className="px-1.5 py-0.5 bg-yellow-400 text-yellow-900 text-[8px] font-bold rounded-full">
                      大奖
                    </span>
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 统计信息 */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl p-4 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-blue-100 text-sm">累计连续签到</p>
            <p className="text-2xl font-bold">{continuousDays} 天</p>
          </div>
          <div className="text-right">
            <p className="text-blue-100 text-sm">本周预计获得</p>
            <p className="text-2xl font-bold">
              +{WEEKLY_REWARDS.slice(0, 7).reduce((sum, r) => sum + r.points, 0)} 积分
            </p>
          </div>
        </div>
        
        {hasCheckedInToday ? (
          <p className="mt-3 text-sm text-blue-100 text-center">
            今日已签到，明天继续加油！
          </p>
        ) : (
          <p className="mt-3 text-sm text-amber-200 text-center font-medium">
            今日还未签到，记得来领积分哦！
          </p>
        )}
      </div>

      {/* 奖励说明 */}
      <div className="bg-amber-50 rounded-lg p-4 text-sm text-amber-800">
        <h5 className="font-medium mb-2 flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          签到规则
        </h5>
        <ul className="space-y-1 text-amber-700">
          <li>• 每日签到可获得对应积分奖励</li>
          <li>• 连续签到7天可获得额外100积分大奖</li>
          <li>• 断签后将从第1天重新开始计算</li>
          <li>• 签到积分实时到账，可用于兑换商品</li>
        </ul>
      </div>
    </div>
  );
}

/**
 * 简化版签到奖励组件（用于嵌入其他页面）
 */
interface CheckInRewardsCompactProps {
  continuousDays: number;
  hasCheckedInToday: boolean;
  className?: string;
}

export function CheckInRewardsCompact({
  continuousDays,
  hasCheckedInToday: _hasCheckedInToday,
  className = '',
}: CheckInRewardsCompactProps): JSX.Element {
  const currentDay = (continuousDays % 7) || 7;
  const todayReward = WEEKLY_REWARDS[currentDay - 1];

  return (
    <div className={`bg-white rounded-lg p-4 shadow-sm ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{todayReward.icon}</span>
          <div>
            <p className="text-sm font-medium text-gray-900">今日签到奖励</p>
            <p className="text-xs text-gray-500">
              已连续签到 {continuousDays} 天
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xl font-bold text-amber-500">+{todayReward.points}</p>
          <p className="text-xs text-gray-400">积分</p>
        </div>
      </div>
      
      {/* 本周进度条 */}
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-amber-400 to-orange-500 rounded-full"
          style={{ width: `${(currentDay / 7) * 100}%` }}
        />
      </div>
      <div className="flex justify-between mt-1 text-[10px] text-gray-400">
        <span>周一</span>
        <span>周日大奖</span>
      </div>
    </div>
  );
}