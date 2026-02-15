/**
 * CheckInPage - 签到页面
 *
 * 包含日历形式展示本月签到记录、连续签到奖励提示、今日签到按钮、积分规则说明
 */

import { useMemo } from 'react';
import { Link } from 'react-router-dom';

import { useCheckIn, useDailyStats, usePointsRules, usePointsBalance } from '../hooks/usePoints';
import { useToast } from '../../../components/ui/useToast';

/**
 * 获取动作显示文本
 */
function getActionLabel(action: string): string {
  const actionMap: Record<string, string> = {
    sign_in: '每日签到',
    post_create: '发布帖子',
    comment_create: '发表评论',
    like: '点赞互动',
    share: '分享内容',
    consultation_complete: '完成咨询',
    document_upload: '上传文档',
    profile_complete: '完善资料',
    invite_friend: '邀请好友',
    exchange_product: '兑换商品',
    bonus: '系统奖励',
  };
  return actionMap[action] || action;
}

/**
 * 签到奖励配置
 */
const REWARD_CONFIG = {
  base: 10,           // 基础签到积分
  continuous3: 15,    // 连续3天额外奖励
  continuous7: 30,    // 连续7天额外奖励
  continuous30: 100,  // 连续30天额外奖励
};

/**
 * 日历组件
 */
function CalendarView({
  continuousDays,
  hasCheckedInToday,
  onCheckIn,
  isCheckingIn,
}: {
  continuousDays: number;
  hasCheckedInToday: boolean;
  onCheckIn: () => void;
  isCheckingIn: boolean;
}): JSX.Element {
  const today = new Date();
  const currentYear = today.getFullYear();
  const currentMonth = today.getMonth();
  const currentDate = today.getDate();

  // 获取当月天数
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  
  // 获取当月第一天是星期几
  const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay();

  // 生成日历数据
  const calendarDays = useMemo(() => {
    const days: Array<{ date: number; isToday: boolean; isSigned: boolean }> = [];
    
    // 填充月初空白
    for (let i = 0; i < firstDayOfMonth; i++) {
      days.push({ date: 0, isToday: false, isSigned: false });
    }
    
    // 填充日期
    for (let i = 1; i <= daysInMonth; i++) {
      const isToday = i === currentDate;
      // 模拟签到记录（前 continuousDays 天都签到，今天根据 hasCheckedInToday 判断）
      const isSigned = isToday 
        ? hasCheckedInToday 
        : i < currentDate && (currentDate - i) <= continuousDays;
      
      days.push({ date: i, isToday, isSigned });
    }
    
    return days;
  }, [daysInMonth, firstDayOfMonth, currentDate, continuousDays, hasCheckedInToday]);

  // 获取本月签到次数
  const signedCount = calendarDays.filter(d => d.isSigned).length;

  // 星期标题
  const weekDays = ['日', '一', '二', '三', '四', '五', '六'];

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      {/* 日历头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            {currentYear}年{currentMonth + 1}月
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            本月已签到 <span className="text-orange-600 font-semibold">{signedCount}</span> 天
          </p>
        </div>
        <button
          onClick={onCheckIn}
          disabled={hasCheckedInToday || isCheckingIn}
          className={`px-6 py-2.5 rounded-lg font-medium transition-all ${
            hasCheckedInToday
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-orange-500 to-yellow-500 text-white hover:from-orange-600 hover:to-yellow-600 shadow-lg shadow-orange-200'
          }`}
        >
          {isCheckingIn 
            ? '签到中...' 
            : hasCheckedInToday 
              ? '今日已签到' 
              : '立即签到'
          }
        </button>
      </div>

      {/* 星期标题 */}
      <div className="grid grid-cols-7 gap-2 mb-2">
        {weekDays.map(day => (
          <div key={day} className="text-center text-sm font-medium text-gray-500 py-2">
            {day}
          </div>
        ))}
      </div>

      {/* 日期网格 */}
      <div className="grid grid-cols-7 gap-2">
        {calendarDays.map((day, index) => (
          <div
            key={index}
            className={`
              aspect-square flex flex-col items-center justify-center rounded-lg text-sm
              ${day.date === 0 
                ? 'invisible' 
                : day.isToday
                  ? 'bg-orange-100 border-2 border-orange-400 text-orange-700'
                  : day.isSigned
                    ? 'bg-green-50 text-green-700'
                    : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
              }
            `}
          >
            {day.date > 0 && (
              <>
                <span className="font-medium">{day.date}</span>
                {day.isSigned && (
                  <svg className="w-4 h-4 mt-0.5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * 连续签到奖励卡片
 */
function ContinuousRewardCard({ continuousDays }: { continuousDays: number }): JSX.Element {
  const milestones = [
    { days: 3, reward: REWARD_CONFIG.continuous3, achieved: continuousDays >= 3 },
    { days: 7, reward: REWARD_CONFIG.continuous7, achieved: continuousDays >= 7 },
    { days: 30, reward: REWARD_CONFIG.continuous30, achieved: continuousDays >= 30 },
  ];

  return (
    <div className="bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl shadow-lg p-6 text-white">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <span className="text-2xl">🎁</span>
        连续签到奖励
      </h3>
      
      <div className="space-y-4">
        {milestones.map((milestone) => (
          <div 
            key={milestone.days}
            className={`flex items-center justify-between p-3 rounded-lg ${
              milestone.achieved ? 'bg-white/20' : 'bg-white/10'
            }`}
          >
            <div className="flex items-center gap-3">
              <div className={`
                w-8 h-8 rounded-full flex items-center justify-center
                ${milestone.achieved ? 'bg-green-400 text-white' : 'bg-white/30 text-white/70'}
              `}>
                {milestone.achieved ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <span className="text-sm font-bold">{milestone.days}</span>
                )}
              </div>
              <span className={milestone.achieved ? 'font-medium' : 'text-white/70'}>
                连续{milestone.days}天
              </span>
            </div>
            <span className={`font-semibold ${milestone.achieved ? 'text-yellow-200' : 'text-white/70'}`}>
              +{milestone.reward} 积分
            </span>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-white/10 rounded-lg">
        <p className="text-sm text-white/80">
          当前连续签到 <span className="text-yellow-200 font-bold text-lg">{continuousDays}</span> 天
          {continuousDays < 30 && (
            <span className="ml-1">
              ，再签到 <span className="text-yellow-200 font-bold">
                {(milestones.find(m => !m.achieved)?.days || 30) - continuousDays}
              </span> 天可获得额外奖励
            </span>
          )}
        </p>
      </div>
    </div>
  );
}

/**
 * 积分规则说明
 */
function RulesSection(): JSX.Element {
  const { data: rules, isLoading } = usePointsRules();

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-1/4" />
          <div className="h-3 bg-gray-200 rounded w-full" />
          <div className="h-3 bg-gray-200 rounded w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">积分获取规则</h3>
        <Link 
          to="/points/rules"
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          查看全部 →
        </Link>
      </div>
      
      <div className="space-y-3">
        {rules?.slice(0, 5).map((rule) => (
          <div key={rule.action} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-orange-400 rounded-full" />
              <span className="text-gray-700">{getActionLabel(rule.action)}</span>
            </div>
            <span className="text-orange-600 font-medium">+{rule.points} 积分</span>
          </div>
        ))}
      </div>

      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <h4 className="text-sm font-medium text-blue-900 mb-2">💡 小贴士</h4>
        <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
          <li>每日签到可获得基础积分</li>
          <li>连续签到可获得额外奖励</li>
          <li>完成日常任务赚取更多积分</li>
          <li>积分可用于兑换商品或服务</li>
        </ul>
      </div>
    </div>
  );
}

/**
 * 签到页面
 */
export function CheckInPage(): JSX.Element {
  const { data: balance, isLoading: balanceLoading } = usePointsBalance();
  const { data: dailyStats, isLoading: statsLoading } = useDailyStats();
  const checkInMutation = useCheckIn();
  const toast = useToast();

  // 检查今日是否已签到
  const hasCheckedInToday = useMemo(() => {
    if (!dailyStats) return false;
    const signInStat = dailyStats.find(stat => stat.action === 'sign_in');
    return (signInStat?.count || 0) > 0;
  }, [dailyStats]);

  const handleCheckIn = async (): Promise<void> => {
    try {
      const result = await checkInMutation.mutateAsync();
      toast.success(`签到成功！获得 ${result.pointsEarned} 积分，连续签到 ${result.continuousDays} 天`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '签到失败，请重试');
    }
  };

  if (balanceLoading || statsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-6xl mx-auto px-4">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 rounded w-1/4" />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 h-96 bg-gray-200 rounded-xl" />
              <div className="h-96 bg-gray-200 rounded-xl" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">每日签到</h1>
          <p className="text-gray-500 mt-1">坚持签到，赚取积分奖励</p>
        </div>

        {/* 积分余额快速预览 */}
        <div className="mb-6 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-xl shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white/80 text-sm mb-1">我的积分</p>
              <p className="text-4xl font-bold">{balance?.balance.toLocaleString() || '0'}</p>
            </div>
            <div className="text-right">
              <p className="text-white/80 text-sm mb-1">连续签到</p>
              <p className="text-3xl font-bold">{balance?.continuousDays || 0} <span className="text-lg">天</span></p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧：日历 */}
          <div className="lg:col-span-2">
            <CalendarView
              continuousDays={balance?.continuousDays || 0}
              hasCheckedInToday={hasCheckedInToday}
              onCheckIn={() => void handleCheckIn()}
              isCheckingIn={checkInMutation.isPending}
            />
          </div>

          {/* 右侧：奖励和规则 */}
          <div className="space-y-6">
            <ContinuousRewardCard continuousDays={balance?.continuousDays || 0} />
            <RulesSection />
          </div>
        </div>

        {/* 导航链接 */}
        <div className="mt-8 flex flex-wrap gap-4 justify-center">
          <Link
            to="/points/activities"
            className="px-6 py-3 bg-white rounded-lg shadow-sm text-gray-700 hover:text-blue-600 hover:shadow-md transition-all"
          >
            查看更多任务 →
          </Link>
          <Link
            to="/points/history"
            className="px-6 py-3 bg-white rounded-lg shadow-sm text-gray-700 hover:text-blue-600 hover:shadow-md transition-all"
          >
            积分明细 →
          </Link>
        </div>
      </div>
    </div>
  );
}