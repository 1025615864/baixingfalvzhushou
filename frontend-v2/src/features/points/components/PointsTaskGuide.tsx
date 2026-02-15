/**
 * PointsTaskGuide - 任务引导组件
 */

import { useCheckIn, useDailyStats, usePointsRules } from '../hooks/usePoints';
import type { DailyStat, PointsRule } from '../types';

interface PointsTaskGuideProps {
  className?: string;
}

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
 * 任务引导组件
 */
export function PointsTaskGuide({ className = '' }: PointsTaskGuideProps): JSX.Element {
  const { data: dailyStats, isLoading: statsLoading } = useDailyStats();
  const { data: rules, isLoading: rulesLoading } = usePointsRules();
  const checkInMutation = useCheckIn();

  const isLoading = statsLoading || rulesLoading;

  // 合并统计数据和规则
  const getTaskProgress = (rule: PointsRule): number => {
    if (!dailyStats) return 0;
    const stat = dailyStats.find((s: DailyStat) => s.action === rule.action);
    return stat?.count || 0;
  };

  const handleCheckIn = async () => {
    try {
      await checkInMutation.mutateAsync();
      alert('签到成功！');
    } catch (err) {
      alert(err instanceof Error ? err.message : '签到失败');
    }
  };

  if (isLoading) {
    return (
      <div className={`space-y-3 ${className}`}>
        {Array.from({ length: 5 }).map((_, index) => (
          <div key={index} className="flex items-center gap-4 p-4 bg-white rounded-lg border animate-pulse">
            <div className="w-10 h-10 bg-gray-200 rounded-full" />
            <div className="flex-1 space-y-2">
              <div className="w-32 h-4 bg-gray-200 rounded" />
              <div className="w-24 h-3 bg-gray-200 rounded" />
            </div>
            <div className="w-16 h-8 bg-gray-200 rounded" />
          </div>
        ))}
      </div>
    );
  }

  // 找到签到规则
  const signInRule = rules?.find(r => r.action === 'sign_in');

  // 检查今日是否已签到
  const hasCheckedIn = signInRule 
    ? getTaskProgress(signInRule) >= signInRule.dailyLimit 
    : false;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 签到区域 */}
      <div className="p-6 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-xl text-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold mb-1">每日签到</h3>
            <p className="text-yellow-100 text-sm">
              {hasCheckedIn 
                ? '今日已签到，明天再来吧！' 
                : '签到即可领取积分奖励'}
            </p>
          </div>
          <button
            onClick={() => void handleCheckIn()}
            disabled={hasCheckedIn || checkInMutation.isPending}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              hasCheckedIn
                ? 'bg-white/30 cursor-not-allowed'
                : 'bg-white text-orange-600 hover:bg-yellow-50'
            }`}
          >
            {checkInMutation.isPending 
              ? '签到中...' 
              : hasCheckedIn 
              ? '已签到' 
              : '立即签到'
            }
          </button>
        </div>
        {signInRule && (
          <div className="mt-4 text-sm text-yellow-100">
            每次签到 +{signInRule.points} 积分
          </div>
        )}
      </div>

      {/* 任务列表 */}
      <div className="space-y-3">
        <h4 className="font-medium text-gray-900">今日任务</h4>
        
        {!rules || rules.length === 0 ? (
          <div className="p-4 text-center text-gray-500 bg-gray-50 rounded-lg">
            暂无任务数据
          </div>
        ) : (
          <div className="space-y-2">
            {rules
              .filter((rule: PointsRule) => rule.action !== 'sign_in' && rule.action !== 'exchange_product' && rule.action !== 'bonus')
              .map((rule: PointsRule) => {
                const progress = getTaskProgress(rule);
                const isCompleted = progress >= rule.dailyLimit;
                
                return (
                  <div 
                    key={rule.action}
                    className={`flex items-center gap-4 p-4 rounded-lg border transition-colors ${
                      isCompleted ? 'bg-green-50 border-green-200' : 'bg-white'
                    }`}
                  >
                    {/* 图标 */}
                    <div className="flex items-center justify-center w-10 h-10 text-2xl bg-gray-100 rounded-full">
                      {getActionIcon(rule.action)}
                    </div>
                    
                    {/* 任务信息 */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">
                          {getActionLabel(rule.action)}
                        </span>
                        <span className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full">
                          +{rule.points} 积分
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 mt-0.5">
                        {rule.description}
                      </p>
                    </div>
                    
                    {/* 进度 */}
                    <div className="flex items-center gap-2">
                      <div className="text-sm text-gray-600">
                        {progress}/{rule.dailyLimit}
                      </div>
                      {isCompleted && (
                        <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                  </div>
                );
              })}
          </div>
        )}
      </div>
    </div>
  );
}