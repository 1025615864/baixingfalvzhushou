/**
 * SecurityLevel - 安全等级展示组件
 */

import {
  SafetyCertificateOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  SafetyOutlined,
  LockOutlined,
  EyeOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';

import type { SecurityCheckItem, SecurityLevelAssessment } from '../types';
import { useSecurityLevel, useTwoFactorStatus } from '../hooks/useSecurity';

interface SecurityLevelProps {
  onCheckItemClick?: (item: SecurityCheckItem) => void;
}

const levelConfig: Record<SecurityLevelAssessment['level'], { 
  label: string; 
  color: string; 
  bgColor: string;
  icon: React.ReactNode;
}> = {
  high: {
    label: '高',
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    icon: <SafetyOutlined className="text-3xl text-green-600" />,
  },
  medium: {
    label: '中',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    icon: <WarningOutlined className="text-3xl text-yellow-600" />,
  },
  low: {
    label: '低',
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    icon: <CloseCircleOutlined className="text-3xl text-red-600" />,
  },
};

/**
 * 安全等级展示组件
 */
export function SecurityLevel({ onCheckItemClick }: SecurityLevelProps): JSX.Element {
  const { data: assessment, isLoading: isLoadingLevel, error: levelError, refetch: refetchLevel } = useSecurityLevel();
  const { data: twoFactorStatus } = useTwoFactorStatus();

  const handleRefresh = (): void => {
    void refetchLevel();
  };

  // 计算安全检查通过的数量
  const passedChecks = assessment?.checks.filter(c => c.passed).length || 0;
  const totalChecks = assessment?.checks.length || 0;

  // 获取建议的安全检查项
  const failedChecks = assessment?.checks.filter(c => !c.passed) || [];

  if (isLoadingLevel) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="h-32 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (levelError || !assessment) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center text-red-600">
          <CloseCircleOutlined className="mr-2" />
          <span>加载安全等级失败</span>
        </div>
      </div>
    );
  }

  const levelInfo = levelConfig[assessment.level];

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* 安全等级概览 */}
      <div className={`p-6 ${levelInfo.bgColor}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">安全等级评估</h3>
          <button
            onClick={handleRefresh}
            className="p-2 text-gray-500 hover:text-gray-700 transition-colors rounded-full hover:bg-white/50"
          >
            <ReloadOutlined />
          </button>
        </div>

        <div className="flex items-center">
          <div className="p-4 bg-white rounded-full shadow-sm mr-6">
            {levelInfo.icon}
          </div>
          <div>
            <div className="flex items-baseline">
              <span className="text-4xl font-bold text-gray-900">{assessment.score}</span>
              <span className="text-lg text-gray-500 ml-1">/ 100</span>
            </div>
            <div className="mt-1">
              <span className={`text-lg font-medium ${levelInfo.color}`}>
                安全等级: {levelInfo.label}
              </span>
            </div>
            <div className="mt-2 text-sm text-gray-600">
              {passedChecks}/{totalChecks} 项安全检查通过
            </div>
          </div>
        </div>

        {/* 进度条 */}
        <div className="mt-6">
          <div className="w-full bg-white rounded-full h-2.5">
            <div
              className={`h-2.5 rounded-full transition-all duration-500 ${
                assessment.score >= 80 ? 'bg-green-500' : 
                assessment.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${assessment.score}%` }}
            />
          </div>
        </div>
      </div>

      {/* 快速安全概览 */}
      <div className="p-4 border-b border-gray-200">
        <h4 className="text-sm font-medium text-gray-700 mb-3">安全状态概览</h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="flex items-center p-3 bg-gray-50 rounded-lg">
            <div className={`p-2 rounded-full mr-3 ${twoFactorStatus?.enabled ? 'bg-green-100' : 'bg-gray-200'}`}>
              <SafetyCertificateOutlined className={twoFactorStatus?.enabled ? 'text-green-600' : 'text-gray-400'} />
            </div>
            <div>
              <div className="text-xs text-gray-500">双重验证</div>
              <div className={`text-sm font-medium ${twoFactorStatus?.enabled ? 'text-green-600' : 'text-gray-500'}`}>
                {twoFactorStatus?.enabled ? '已启用' : '未启用'}
              </div>
            </div>
          </div>

          <div className="flex items-center p-3 bg-gray-50 rounded-lg">
            <div className="p-2 rounded-full mr-3 bg-green-100">
              <EyeOutlined className="text-green-600" />
            </div>
            <div>
              <div className="text-xs text-gray-500">登录通知</div>
              <div className="text-sm font-medium text-green-600">
                已开启
              </div>
            </div>
          </div>

          <div className="flex items-center p-3 bg-gray-50 rounded-lg">
            <div className="p-2 rounded-full mr-3 bg-blue-100">
              <ClockCircleOutlined className="text-blue-600" />
            </div>
            <div>
              <div className="text-xs text-gray-500">会话超时</div>
              <div className="text-sm font-medium text-gray-900">
                30 分钟
              </div>
            </div>
          </div>

          <div className="flex items-center p-3 bg-gray-50 rounded-lg">
            <div className="p-2 rounded-full mr-3 bg-purple-100">
              <LockOutlined className="text-purple-600" />
            </div>
            <div>
              <div className="text-xs text-gray-500">密码修改</div>
              <div className="text-sm font-medium text-gray-900">
                请查看账户设置
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 安全检查项 */}
      {failedChecks.length > 0 && (
        <div className="p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            待改进的安全项 ({failedChecks.length})
          </h4>
          <div className="space-y-2">
            {failedChecks.slice(0, 3).map((check) => (
              <button
                key={check.id}
                onClick={() => onCheckItemClick?.(check)}
                className="w-full text-left p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start">
                  <WarningOutlined className="text-orange-500 mr-3 mt-0.5" />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900">{check.name}</div>
                    <div className="text-xs text-gray-500 mt-1">{check.description}</div>
                    {check.recommendation && (
                      <div className="text-xs text-blue-600 mt-1">
                        建议: {check.recommendation}
                      </div>
                    )}
                  </div>
                  <div className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600">
                    {check.severity === 'high' ? '高危' : check.severity === 'medium' ? '中危' : '低危'}
                  </div>
                </div>
              </button>
            ))}
            {failedChecks.length > 3 && (
              <div className="text-center text-sm text-gray-500 py-2">
                还有 {failedChecks.length - 3} 项待改进...
              </div>
            )}
          </div>
        </div>
      )}

      {failedChecks.length === 0 && (
        <div className="p-4 text-center">
          <CheckCircleOutlined className="text-2xl text-green-500 mb-2" />
          <div className="text-sm text-gray-600">恭喜！所有安全检查项均已通过</div>
        </div>
      )}
    </div>
  );
}