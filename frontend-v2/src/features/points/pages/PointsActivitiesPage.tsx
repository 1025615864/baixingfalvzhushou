/**
 * PointsActivitiesPage - 积分活动页
 * 
 * 包含每日任务列表、新手任务列表、成就系统展示、积分排行榜入口
 */

import { useMemo } from 'react';
import { Link } from 'react-router-dom';

import { useDailyStats, usePointsRules, usePointsBalance, usePointsLeaderboard, useCheckIn } from '../hooks/usePoints';
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
 * 获取动作图标
 */
function getActionIcon(action: string): string {
  const iconMap: Record<string, string> = {
    sign_in: '📅',
    post_create: '📝',
    comment_create: '💬',
    like: '❤️',
    share: '📤',
    consultation_complete: '🤝',
    document_upload: '📄',
    profile_complete: '👤',
    invite_friend: '👥',
    exchange_product: '🎁',
    bonus: '🎉',
  };
  return iconMap[action] || '✨';
}

/**
 * 任务进度条组件
 */
function TaskProgressBar({ 
  current, 
  max, 
  color = 'blue' 
}: { 
  current: number; 
  max: number; 
  color?: 'blue' | 'green' | 'orange' | 'purple';
}): JSX.Element {
  const percentage = Math.min((current / max) * 100, 100);
  
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    orange: 'bg-orange-500',
    purple: 'bg-purple-500',
  };

  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>进度</span>
        <span>{current}/{max}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div 
          className={`h-full ${colorClasses[color]} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

/**
 * 每日任务卡片
 */
function DailyTasksCard(): JSX.Element {
  const { data: rules, isLoading: rulesLoading } = usePointsRules();
  const { data: dailyStats, isLoading: statsLoading } = useDailyStats();
  const { data: balance } = usePointsBalance();
  const checkInMutation = useCheckIn();
  const toast = useToast();

  const isLoading = rulesLoading || statsLoading;

  // 获取任务进度
  const getTaskProgress = (action: string): number => {
    if (!dailyStats) return 0;
    const stat = dailyStats.find(s => s.action === action);
    return stat?.count || 0;
  };

  // 处理签到
  const handleCheckIn = async (): Promise<void> => {
    try {
      const result = await checkInMutation.mutateAsync();
      toast.success(`签到成功！获得 ${result.pointsEarned} 积分`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '签到失败');
    }
  };

  // 检查今日是否已签到
  const hasCheckedInToday = useMemo(() => {
    if (!dailyStats) return false;
    const signInStat = dailyStats.find(stat => stat.action === 'sign_in');
    return (signInStat?.count || 0) > 0;
  }, [dailyStats]);

  // 获取每日任务（排除签到和兑换）
  const dailyTasks = rules?.filter(r => 
    r.action !== 'sign_in' && 
    r.action !== 'exchange_product' && 
    r.action !== 'bonus'
  ) || [];

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/4" />
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">📋 每日任务</h2>
        <span className="text-sm text-gray-500">
          今日已完成 {dailyTasks.filter(t => getTaskProgress(t.action) >= t.dailyLimit).length}/{dailyTasks.length}
        </span>
      </div>

      {/* 签到区域 */}
      <div className="mb-6 p-4 bg-gradient-to-r from-orange-500 to-yellow-500 rounded-xl text-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold mb-1">每日签到</h3>
            <p className="text-orange-100 text-sm">
              {hasCheckedInToday 
                ? '今日已签到，明天再来吧！' 
                : '签到即可领取积分奖励'}
            </p>
            {balance && balance.continuousDays > 0 && (
              <p className="text-orange-100 text-sm mt-1">
                已连续签到 {balance.continuousDays} 天
              </p>
            )}
          </div>
          <button
            onClick={() => void handleCheckIn()}
            disabled={hasCheckedInToday || checkInMutation.isPending}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              hasCheckedInToday
                ? 'bg-white/30 cursor-not-allowed'
                : 'bg-white text-orange-600 hover:bg-orange-50'
            }`}
          >
            {checkInMutation.isPending 
              ? '签到中...' 
              : hasCheckedInToday 
                ? '已签到' 
                : '立即签到'
            }
          </button>
        </div>
      </div>

      {/* 任务列表 */}
      <div className="space-y-3">
        {dailyTasks.map((rule) => {
          const progress = getTaskProgress(rule.action);
          const isCompleted = progress >= rule.dailyLimit;
          
          return (
            <div 
              key={rule.action}
              className={`flex items-center gap-4 p-4 rounded-xl border transition-all ${
                isCompleted 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-gray-50 border-gray-100 hover:border-gray-200'
              }`}
            >
              {/* 图标 */}
              <div className={`
                flex items-center justify-center w-12 h-12 text-2xl rounded-full
                ${isCompleted ? 'bg-green-100' : 'bg-white'}
              `}>
                {getActionIcon(rule.action)}
              </div>
              
              {/* 任务信息 */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-gray-900">
                    {getActionLabel(rule.action)}
                  </span>
                  <span className="text-xs px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full">
                    +{rule.points} 积分
                  </span>
                </div>
                <p className="text-sm text-gray-500 truncate">
                  {rule.description}
                </p>
                <div className="mt-2">
                  <TaskProgressBar 
                    current={progress} 
                    max={rule.dailyLimit} 
                    color={isCompleted ? 'green' : 'orange'}
                  />
                </div>
              </div>
              
              {/* 完成状态 */}
              {isCompleted && (
                <div className="flex items-center justify-center w-10 h-10 bg-green-500 rounded-full">
                  <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * 新手任务卡片
 */
function BeginnerTasksCard(): JSX.Element {
  const beginnerTasks = [
    { id: 'profile', title: '完善个人资料', icon: '👤', points: 50, completed: true },
    { id: 'first_post', title: '发布第一条帖子', icon: '📝', points: 30, completed: true },
    { id: 'first_like', title: '点赞一条内容', icon: '❤️', points: 10, completed: false },
    { id: 'first_share', title: '分享一次内容', icon: '📤', points: 20, completed: false },
    { id: 'first_consultation', title: '完成首次咨询', icon: '🤝', points: 100, completed: false },
  ];

  const completedCount = beginnerTasks.filter(t => t.completed).length;

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">🎯 新手任务</h2>
        <span className="text-sm text-gray-500">
          已完成 {completedCount}/{beginnerTasks.length}
        </span>
      </div>

      <div className="space-y-3">
        {beginnerTasks.map((task) => (
          <div 
            key={task.id}
            className={`flex items-center gap-4 p-4 rounded-xl border transition-all ${
              task.completed 
                ? 'bg-green-50 border-green-200' 
                : 'bg-white border-gray-200 hover:border-blue-300'
            }`}
          >
            <div className={`
              flex items-center justify-center w-12 h-12 text-2xl rounded-full
              ${task.completed ? 'bg-green-100' : 'bg-blue-50'}
            `}>
              {task.icon}
            </div>
            
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className={`font-medium ${task.completed ? 'text-gray-500 line-through' : 'text-gray-900'}`}>
                  {task.title}
                </span>
                <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                  +{task.points} 积分
                </span>
              </div>
            </div>
            
            {task.completed ? (
              <span className="text-green-600 text-sm font-medium">已完成</span>
            ) : (
              <button className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors">
                去完成
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * 成就卡片
 */
function AchievementsCard(): JSX.Element {
  const achievements = [
    { id: 'early_bird', title: '早起鸟', description: '连续7天签到', icon: '🌅', progress: 5, max: 7, unlocked: false },
    { id: 'social_butterfly', title: '社交达人', description: '发布10条帖子', icon: '🦋', progress: 10, max: 10, unlocked: true },
    { id: 'helper', title: '热心帮助', description: '回复20条评论', icon: '🤝', progress: 15, max: 20, unlocked: false },
    { id: 'knowledge_seeker', title: '求知者', description: '阅读50篇知识文章', icon: '📚', progress: 50, max: 50, unlocked: true },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">🏆 成就系统</h2>
        <span className="text-sm text-gray-500">
          已解锁 {achievements.filter(a => a.unlocked).length}/{achievements.length}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {achievements.map((achievement) => (
          <div 
            key={achievement.id}
            className={`p-4 rounded-xl border transition-all ${
              achievement.unlocked 
                ? 'bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-200' 
                : 'bg-gray-50 border-gray-200'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`
                text-3xl
                ${achievement.unlocked ? '' : 'grayscale opacity-50'}
              `}>
                {achievement.icon}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className={`font-semibold ${achievement.unlocked ? 'text-gray-900' : 'text-gray-500'}`}>
                  {achievement.title}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">{achievement.description}</p>
                
                {!achievement.unlocked && (
                  <div className="mt-2">
                    <TaskProgressBar 
                      current={achievement.progress} 
                      max={achievement.max}
                      color="purple"
                    />
                  </div>
                )}
                
                {achievement.unlocked && (
                  <span className="inline-block mt-2 text-xs px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full">
                    已解锁
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * 排行榜预览卡片
 */
function LeaderboardPreviewCard(): JSX.Element {
  const { data: leaderboard, isLoading } = usePointsLeaderboard(5);

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-6 bg-gray-200 rounded w-1/3" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  const topUsers = leaderboard || [];

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">🏅 积分排行</h2>
        <Link 
          to="/points/leaderboard"
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          查看全部 →
        </Link>
      </div>

      <div className="space-y-3">
        {topUsers.map((user, index) => (
          <div 
            key={user.userId}
            className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors"
          >
            {/* 排名 */}
            <div className={`
              w-8 h-8 flex items-center justify-center rounded-full font-bold text-sm
              ${index === 0 ? 'bg-yellow-100 text-yellow-700' :
                index === 1 ? 'bg-gray-100 text-gray-700' :
                index === 2 ? 'bg-orange-100 text-orange-700' :
                'bg-gray-50 text-gray-500'}
            `}>
              {index + 1}
            </div>
            
            {/* 头像占位 */}
            <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-medium">
              {user.username.charAt(0).toUpperCase()}
            </div>
            
            {/* 用户名 */}
            <div className="flex-1">
              <p className="font-medium text-gray-900 truncate">{user.username}</p>
            </div>
            
            {/* 积分 */}
            <div className="text-right">
              <p className="font-semibold text-orange-600">
                {user.totalPoints.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500">积分</p>
            </div>
          </div>
        ))}
      </div>

      {topUsers.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          暂无排行数据
        </div>
      )}
    </div>
  );
}

/**
 * 积分活动页
 */
export function PointsActivitiesPage(): JSX.Element {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* 页面标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">积分活动中心</h1>
          <p className="text-gray-500 mt-1">完成任务，赚取积分，兑换好礼</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧：任务区域 */}
          <div className="lg:col-span-2 space-y-6">
            <DailyTasksCard />
            <BeginnerTasksCard />
            <AchievementsCard />
          </div>

          {/* 右侧：排行榜 */}
          <div className="space-y-6">
            <LeaderboardPreviewCard />
            
            {/* 快速链接 */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">快速链接</h3>
              <div className="space-y-2">
                <Link 
                  to="/points/checkin"
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <span className="text-2xl">📅</span>
                  <div>
                    <p className="font-medium text-gray-900">每日签到</p>
                    <p className="text-sm text-gray-500">坚持签到获得奖励</p>
                  </div>
                </Link>
                <Link 
                  to="/points/mall"
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <span className="text-2xl">🛒</span>
                  <div>
                    <p className="font-medium text-gray-900">积分商城</p>
                    <p className="text-sm text-gray-500">兑换精美商品</p>
                  </div>
                </Link>
                <Link 
                  to="/points/rules"
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <span className="text-2xl">📖</span>
                  <div>
                    <p className="font-medium text-gray-900">积分规则</p>
                    <p className="text-sm text-gray-500">了解积分获取方式</p>
                  </div>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}