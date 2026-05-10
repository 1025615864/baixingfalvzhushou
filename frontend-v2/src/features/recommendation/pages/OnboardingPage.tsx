/**
 * OnboardingPage - 新用户引导问卷页面
 * 收集用户兴趣信息，构建个性化推荐画像
 */

import { logger } from '@/shared/lib/logger';
import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ChevronLeft,
  ChevronRight,
  Check,
  Sparkles,
  Target,
  Heart,
  BookOpen,
  Users,
} from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/Loading';

import type { OnboardingAnswers } from '../types';
import { useOnboardingPageData, useCompleteOnboarding } from '../hooks/useRecommendation';


// 问题选项类型
interface QuestionOption {
  value: string;
  label: string;
}

// 问题类型
type QuestionType = 'single' | 'multiple' | 'text' | 'slider';

// 问题数据类型
interface QuestionData {
  id: string;
  type: QuestionType;
  question: string;
  options?: QuestionOption[];
  required?: boolean;
}

// 步骤配置
const STEPS = [
  { id: 'welcome', title: '欢迎使用', icon: Sparkles },
  { id: 'interests', title: '兴趣领域', icon: Heart },
  { id: 'goals', title: '使用目标', icon: Target },
  { id: 'frequency', title: '使用频率', icon: BookOpen },
  { id: 'complete', title: '完成设置', icon: Check },
];

export function OnboardingPage(): JSX.Element {
  const navigate = useNavigate();
  const { survey, shouldShowOnboarding, isLoading } = useOnboardingPageData();
  const completeOnboarding = useCompleteOnboarding();

  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<OnboardingAnswers>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 转换问题数据格式
  const normalizedSurvey: QuestionData[] = survey.map((q) => ({
    id: String(q.id ?? ''),
    type: String(q.type ?? 'text') as QuestionType,
    question: String(q.question ?? ''),
    options: Array.isArray(q.options)
      ? q.options.map((opt) => ({
          value: String(opt.value ?? ''),
          label: String(opt.label ?? ''),
        }))
      : undefined,
    required: Boolean(q.required),
  }));

  // 如果不需要引导，跳转到推荐页
  useEffect(() => {
    if (!isLoading && shouldShowOnboarding === false) {
      navigate('/recommendation', { replace: true });
    }
  }, [isLoading, shouldShowOnboarding, navigate]);

  // 处理单选
  const handleSingleSelect = useCallback((questionId: string, value: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: value,
    }));
  }, []);

  // 处理多选
  const handleMultipleSelect = useCallback((questionId: string, value: string) => {
    setAnswers((prev) => {
      const currentValues = (prev[questionId] as string[]) || [];
      const newValues = currentValues.includes(value)
        ? currentValues.filter((v) => v !== value)
        : [...currentValues, value];
      return {
        ...prev,
        [questionId]: newValues,
      };
    });
  }, []);

  // 处理文本输入
  const handleTextInput = useCallback((questionId: string, value: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: value,
    }));
  }, []);

  // 下一步
  const handleNext = useCallback(() => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep((prev) => prev + 1);
    }
  }, [currentStep]);

  // 上一步
  const handlePrev = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  }, [currentStep]);

  // 完成引导
  const handleComplete = useCallback(() => {
    setIsSubmitting(true);
    completeOnboarding
      .mutateAsync(answers)
      .then(() => {
        navigate('/recommendation', { replace: true });
      })
      .catch((error) => {
        logger.error('Failed to complete onboarding:', error);
      })
      .finally(() => {
        setIsSubmitting(false);
      });
  }, [answers, completeOnboarding, navigate]);

  // 跳过引导
  const handleSkip = useCallback(() => {
    navigate('/recommendation', { replace: true });
  }, [navigate]);

  // 渲染问题组件
  const renderQuestion = (question: QuestionData) => {
    switch (question.type) {
      case 'single':
        return (
          <div className="space-y-3">
            {question.options?.map((option) => (
              <button
                key={option.value}
                onClick={() => handleSingleSelect(question.id, option.value)}
                className={`w-full p-4 rounded-xl text-left transition-all duration-200 ${
                  answers[question.id] === option.value
                    ? 'bg-primary-50 border-2 border-primary-500 text-primary-700'
                    : 'bg-white border-2 border-slate-200 hover:border-primary-300 hover:bg-primary-50/50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{option.label}</span>
                  {answers[question.id] === option.value && (
                    <Check className="w-5 h-5 text-primary-600" />
                  )}
                </div>
              </button>
            ))}
          </div>
        );

      case 'multiple':
        return (
          <div className="space-y-3">
            <p className="text-sm text-slate-500 mb-4">可多选</p>
            {question.options?.map((option) => {
              const isSelected = ((answers[question.id] as string[]) || []).includes(option.value);
              return (
                <button
                  key={option.value}
                  onClick={() => handleMultipleSelect(question.id, option.value)}
                  className={`w-full p-4 rounded-xl text-left transition-all duration-200 ${
                    isSelected
                      ? 'bg-primary-50 border-2 border-primary-500 text-primary-700'
                      : 'bg-white border-2 border-slate-200 hover:border-primary-300 hover:bg-primary-50/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{option.label}</span>
                    {isSelected && (
                      <Check className="w-5 h-5 text-primary-600" />
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        );

      case 'text':
        return (
          <div>
            <textarea
              value={(answers[question.id] as string) || ''}
              onChange={(e) => handleTextInput(question.id, e.target.value)}
              placeholder="请输入您的回答..."
              className="w-full p-4 rounded-xl border-2 border-slate-200 focus:border-primary-500 focus:ring-0 resize-none h-32"
            />
          </div>
        );

      default:
        return null;
    }
  };

  // 获取当前步骤的问题
  const getCurrentStepQuestions = (): QuestionData[] => {
    if (currentStep === 0 || currentStep === STEPS.length - 1) {
      return [];
    }
    // 根据步骤过滤问题
    const stepTypeMap: Record<number, string> = {
      1: 'interests',
      2: 'goals',
      3: 'frequency',
    };
    const stepType = stepTypeMap[currentStep];
    return normalizedSurvey.filter((q) => q.type === stepType || q.id.includes(stepType));
  };

  // 检查当前步骤是否可以继续
  const canProceed = (): boolean => {
    if (currentStep === 0 || currentStep === STEPS.length - 1) {
      return true;
    }
    const questions = getCurrentStepQuestions();
    // 如果没有对应问题，允许继续
    if (questions.length === 0) return true;
    // 检查必填问题是否已回答
    return questions.every((q) => {
      if (!q.required) return true;
      const answer = answers[q.id];
      if (Array.isArray(answer)) return answer.length > 0;
      return !!answer;
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-white">
        <LoadingSpinner size="xl" />
      </div>
    );
  }

  const currentQuestions = getCurrentStepQuestions();

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-white">
      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* 进度条 */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            {STEPS.map((step, index) => (
              <div
                key={step.id}
                className={`flex items-center ${index < STEPS.length - 1 ? 'flex-1' : ''}`}
              >
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                    index <= currentStep
                      ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/30'
                      : 'bg-slate-200 text-slate-500'
                  }`}
                >
                  {index < currentStep ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <step.icon className="w-5 h-5" />
                  )}
                </div>
                {index < STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-1 mx-2 rounded-full transition-all duration-300 ${
                      index < currentStep ? 'bg-primary-600' : 'bg-slate-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="text-center">
            <h2 className="text-lg font-semibold text-slate-900">
              {STEPS[currentStep].title}
            </h2>
            <p className="text-sm text-slate-500">
              步骤 {currentStep + 1} / {STEPS.length}
            </p>
          </div>
        </div>

        {/* 内容区域 */}
        <div className="bg-white rounded-2xl shadow-soft p-6 md:p-8">
          {/* 欢迎页 */}
          {currentStep === 0 && (
            <div className="text-center py-8">
              <div className="w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-primary-500/30">
                <Users className="w-10 h-10 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 mb-4">
                欢迎来到百姓助手
              </h1>
              <p className="text-slate-600 mb-6 max-w-md mx-auto">
                为了给您提供更加个性化的法律服务推荐，请花一分钟时间告诉我们您的兴趣和需求。
              </p>
              <div className="flex flex-wrap justify-center gap-3">
                {['智能推荐', '个性定制', '隐私安全'].map((tag) => (
                  <span
                    key={tag}
                    className="px-4 py-2 bg-primary-50 text-primary-700 rounded-full text-sm font-medium"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 问题区域 */}
          {currentStep > 0 && currentStep < STEPS.length - 1 && (
            <div className="space-y-8">
              {currentQuestions.length > 0 ? (
                currentQuestions.map((question) => (
                  <div key={question.id}>
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">
                      {question.question}
                      {question.required && (
                        <span className="text-red-500 ml-1">*</span>
                      )}
                    </h3>
                    {renderQuestion(question)}
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <p className="text-slate-500">暂无问题，请点击下一步继续</p>
                </div>
              )}
            </div>
          )}

          {/* 完成页 */}
          {currentStep === STEPS.length - 1 && (
            <div className="text-center py-8">
              <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg shadow-green-500/30">
                <Check className="w-10 h-10 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 mb-4">
                设置完成！
              </h1>
              <p className="text-slate-600 mb-6 max-w-md mx-auto">
                感谢您的配合！我们将根据您的偏好为您提供个性化的法律服务和内容推荐。
              </p>
              <div className="bg-slate-50 rounded-xl p-4 mb-6">
                <h4 className="font-medium text-slate-900 mb-2">您的选择</h4>
                <div className="flex flex-wrap gap-2 justify-center">
                  {Object.entries(answers).map(([key, value]) => {
                    if (Array.isArray(value)) {
                      return value.map((v) => (
                        <span
                          key={`${key}-${v}`}
                          className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm"
                        >
                          {v}
                        </span>
                      ));
                    }
                    return (
                      <span
                        key={key}
                        className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm"
                      >
                        {String(value)}
                      </span>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-200">
            <div>
              {currentStep > 0 && (
                <Button
                  variant="ghost"
                  onClick={handlePrev}
                  leftIcon={<ChevronLeft className="w-4 h-4" />}
                >
                  上一步
                </Button>
              )}
            </div>

            <div className="flex items-center gap-3">
              {currentStep < STEPS.length - 1 && (
                <Button variant="ghost" onClick={handleSkip}>
                  跳过
                </Button>
              )}

              {currentStep < STEPS.length - 1 ? (
                <Button
                  variant="primary"
                  onClick={handleNext}
                  disabled={!canProceed()}
                  rightIcon={<ChevronRight className="w-4 h-4" />}
                >
                  下一步
                </Button>
              ) : (
                <Button
                  variant="primary"
                  onClick={handleComplete}
                  isLoading={isSubmitting}
                  leftIcon={<Check className="w-4 h-4" />}
                >
                  开始使用
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* 底部提示 */}
        <p className="text-center text-sm text-slate-500 mt-6">
          您可以随时在设置中修改您的偏好
        </p>
      </div>
    </div>
  );
}

export default OnboardingPage;