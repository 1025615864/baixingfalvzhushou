/**
 * FunnelAnalysisPage - 漏斗分析详情页
 * 
 * 展示详细的转化漏斗数据，支持自定义漏斗步骤分析
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';

import { FunnelChart } from '../components/FunnelChart';
import { useConversionFunnel, useFunnelAnalysis } from '../hooks/useAnalytics';
import { useToast } from '../../../components/ui/useToast';
import type { FunnelChartDataItem, FunnelStepRequest } from '../types';

/**
 * 日期范围选择器
 */
function DateRangeSelector({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
}: {
  startDate: string;
  endDate: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
}): JSX.Element {
  return (
    <div className="flex items-center gap-3">
      <input
        type="date"
        value={startDate}
        onChange={(e) => onStartDateChange(e.target.value)}
        className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      />
      <span className="text-gray-500">至</span>
      <input
        type="date"
        value={endDate}
        onChange={(e) => onEndDateChange(e.target.value)}
        className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      />
    </div>
  );
}

/**
 * 漏斗步骤卡片
 */
function FunnelStepCard({
  step,
  index,
  totalSteps,
}: {
  step: FunnelChartDataItem;
  index: number;
  totalSteps: number;
}): JSX.Element {
  const isLast = index === totalSteps - 1;
  
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center gap-4">
        <div 
          className="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-lg"
          style={{ backgroundColor: step.color || '#3b82f6' }}
        >
          {index + 1}
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 text-lg">{step.name}</h3>
          <p className="text-gray-500 text-sm">用户数: {step.value.toLocaleString()}</p>
        </div>
      </div>
      
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="p-3 bg-green-50 rounded-lg">
          <p className="text-sm text-gray-500 mb-1">转化率</p>
          <p className="text-xl font-bold text-green-600">{(step.conversionRate * 100).toFixed(2)}%</p>
        </div>
        <div className="p-3 bg-red-50 rounded-lg">
          <p className="text-sm text-gray-500 mb-1">流失率</p>
          <p className="text-xl font-bold text-red-600">{(step.dropRate * 100).toFixed(2)}%</p>
        </div>
      </div>
      
      {!isLast && (
        <div className="mt-4 flex items-center justify-center">
          <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      )}
    </div>
  );
}

/**
 * 总体转化统计
 */
function OverallStats({
  totalUsers,
  overallConversion,
}: {
  totalUsers: number;
  overallConversion: number;
}): JSX.Element {
  return (
    <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg p-6 text-white">
      <div className="grid grid-cols-2 gap-6">
        <div>
          <p className="text-white/70 text-sm mb-1">初始用户数</p>
          <p className="text-3xl font-bold">{totalUsers.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-white/70 text-sm mb-1">总体转化率</p>
          <p className="text-3xl font-bold">{(overallConversion * 100).toFixed(2)}%</p>
        </div>
      </div>
    </div>
  );
}

/**
 * 自定义漏斗表单
 */
function CustomFunnelForm({
  onAnalyze,
  isLoading,
}: {
  onAnalyze: (steps: FunnelStepRequest[]) => void;
  isLoading: boolean;
}): JSX.Element {
  const [steps, setSteps] = useState<FunnelStepRequest[]>([
    { name: '访问首页', action: 'page_view' },
    { name: '浏览商品', action: 'click' },
    { name: '加入购物车', action: 'submit' },
    { name: '完成购买', action: 'purchase' },
  ]);

  const addStep = (): void => {
    setSteps([...steps, { name: '', action: 'page_view' }]);
  };

  const removeStep = (index: number): void => {
    setSteps(steps.filter((_, i) => i !== index));
  };

  const updateStep = (index: number, field: keyof FunnelStepRequest, value: string): void => {
    const newSteps = [...steps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setSteps(newSteps);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">自定义漏斗分析</h3>
      
      <div className="space-y-3">
        {steps.map((step, index) => (
          <div key={index} className="flex items-center gap-3">
            <span className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-sm font-medium text-gray-600">
              {index + 1}
            </span>
            <input
              type="text"
              value={step.name}
              onChange={(e) => updateStep(index, 'name', e.target.value)}
              placeholder="步骤名称"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
            <select
              value={step.action}
              onChange={(e) => updateStep(index, 'action', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="page_view">页面浏览</option>
              <option value="click">点击</option>
              <option value="submit">提交</option>
              <option value="search">搜索</option>
              <option value="purchase">购买</option>
              <option value="register">注册</option>
              <option value="login">登录</option>
            </select>
            <button
              onClick={() => removeStep(index)}
              disabled={steps.length <= 2}
              className="p-2 text-red-500 hover:bg-red-50 rounded-lg disabled:opacity-30"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        ))}
      </div>

      <div className="flex gap-3 mt-4">
        <button
          onClick={addStep}
          className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
        >
          添加步骤
        </button>
        <button
          onClick={() => onAnalyze(steps)}
          disabled={isLoading || steps.some(s => !s.name)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? '分析中...' : '开始分析'}
        </button>
      </div>
    </div>
  );
}

/**
 * 漏斗分析页面
 */
export function FunnelAnalysisPage(): JSX.Element {
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 30);
    return date.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);
  
  const { data: funnelData, isLoading } = useConversionFunnel(startDate, endDate);
  const funnelAnalysisMutation = useFunnelAnalysis();
  const toast = useToast();

  // 格式化漏斗图数据
  const funnelChartData: FunnelChartDataItem[] = useMemo(() => {
    if (!funnelData?.steps) return [];
    
    return funnelData.steps.map((step, index) => ({
      name: step.name,
      value: step.count,
      conversionRate: step.conversionRate,
      dropRate: step.dropRate,
      color: step.color || `hsl(${210 + index * 30}, 70%, ${50 + index * 5}%)`,
    }));
  }, [funnelData]);

  // 处理自定义漏斗分析
  const handleCustomAnalyze = async (steps: FunnelStepRequest[]): Promise<void> => {
    try {
      await funnelAnalysisMutation.mutateAsync({
        startDate,
        endDate,
        funnelSteps: steps,
      });
      toast.success('漏斗分析完成');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '分析失败');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* 页面标题 */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">漏斗分析</h1>
            <p className="text-gray-500 mt-1">深入了解用户转化路径和流失情况</p>
          </div>
          <Link
            to="/analytics"
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            ← 返回概览
          </Link>
        </div>

        {/* 日期范围选择 */}
        <div className="mb-6 bg-white rounded-xl shadow-sm p-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <DateRangeSelector
              startDate={startDate}
              endDate={endDate}
              onStartDateChange={setStartDate}
              onEndDateChange={setEndDate}
            />
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm text-gray-700"
            >
              重置筛选
            </button>
          </div>
        </div>

        {/* 总体统计 */}
        {funnelData && (
          <div className="mb-6">
            <OverallStats
              totalUsers={funnelData.totalUsers}
              overallConversion={funnelData.overallConversion}
            />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧：漏斗图表 */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">转化漏斗图</h2>
              <FunnelChart
                data={funnelChartData}
                title=""
                loading={isLoading}
              />
            </div>

            {/* 自定义漏斗分析 */}
            <CustomFunnelForm
              onAnalyze={(steps) => void handleCustomAnalyze(steps)}
              isLoading={funnelAnalysisMutation.isPending}
            />
          </div>

          {/* 右侧：步骤详情 */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">步骤详情</h2>
            {isLoading ? (
              <div className="space-y-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-40 bg-gray-100 rounded-xl animate-pulse" />
                ))}
              </div>
            ) : funnelChartData.length > 0 ? (
              funnelChartData.map((step, index) => (
                <FunnelStepCard
                  key={index}
                  step={step}
                  index={index}
                  totalSteps={funnelChartData.length}
                />
              ))
            ) : (
              <div className="text-center py-12 text-gray-500 bg-white rounded-xl">
                暂无漏斗数据
              </div>
            )}
          </div>
        </div>

        {/* 分析建议 */}
        <div className="mt-8 bg-blue-50 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">💡 优化建议</h3>
          <ul className="space-y-2 text-blue-700">
            <li>• 关注流失率较高的环节，针对性优化用户体验</li>
            <li>• 对比不同时间段的漏斗数据，识别趋势变化</li>
            <li>• 使用A/B测试验证优化方案的效果</li>
            <li>• 定期分析自定义漏斗，深入了解用户行为路径</li>
          </ul>
        </div>
      </div>
    </div>
  );
}