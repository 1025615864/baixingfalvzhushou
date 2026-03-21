/**
 * FeeCalculatorPage 页面 - 费用计算器
 * 提供法律服务费用估算功能
 */

import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  Calculator,
  Scale,
  FileText,
  Users,
  Building2,
  HelpCircle,
  ChevronRight,
  Info,
  AlertTriangle,
} from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';

/** 服务类型配置 */
interface ServiceType {
  id: string;
  name: string;
  icon: React.ElementType;
  description: string;
  baseFee: number;
  feeUnit: string;
  factors: FeeFactor[];
}

interface FeeFactor {
  id: string;
  name: string;
  multiplier: number;
  description: string;
}

const SERVICE_TYPES: ServiceType[] = [
  {
    id: 'contract-review',
    name: '合同审查',
    icon: FileText,
    description: '专业律师审核合同条款，规避法律风险',
    baseFee: 500,
    feeUnit: '份',
    factors: [
      { id: 'simple', name: '简单合同', multiplier: 1, description: '标准模板合同，页数10页以内' },
      { id: 'medium', name: '中等复杂', multiplier: 2, description: '定制合同，涉及多方或特殊条款' },
      { id: 'complex', name: '复杂合同', multiplier: 4, description: '大型商务合同，涉及跨境或复杂交易结构' },
    ],
  },
  {
    id: 'legal-consultation',
    name: '法律咨询',
    icon: Users,
    description: '一对一专业法律咨询服务',
    baseFee: 300,
    feeUnit: '小时',
    factors: [
      { id: 'junior', name: '初级律师', multiplier: 1, description: '执业1-3年' },
      { id: 'senior', name: '资深律师', multiplier: 2, description: '执业3-10年' },
      { id: 'partner', name: '合伙人律师', multiplier: 4, description: '执业10年以上' },
    ],
  },
  {
    id: 'litigation',
    name: '诉讼代理',
    icon: Scale,
    description: '民事、商事诉讼案件代理',
    baseFee: 5000,
    feeUnit: '件',
    factors: [
      { id: 'simple', name: '简单案件', multiplier: 1, description: '标的额50万以下' },
      { id: 'medium', name: '一般案件', multiplier: 2, description: '标的额50-200万' },
      { id: 'complex', name: '复杂案件', multiplier: 5, description: '标的额200万以上' },
    ],
  },
  {
    id: 'corporate',
    name: '企业法律顾问',
    icon: Building2,
    description: '企业常年法律顾问服务',
    baseFee: 2000,
    feeUnit: '月',
    factors: [
      { id: 'startup', name: '初创企业', multiplier: 1, description: '员工50人以下' },
      { id: 'sme', name: '中型企业', multiplier: 3, description: '员工50-200人' },
      { id: 'large', name: '大型企业', multiplier: 8, description: '员工200人以上' },
    ],
  },
];

/**
 * 费用计算器页面
 */
export const FeeCalculatorPage: React.FC = () => {
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [selectedFactor, setSelectedFactor] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);

  const currentService = useMemo(() => {
    return SERVICE_TYPES.find((s) => s.id === selectedService);
  }, [selectedService]);

  const currentFactor = useMemo(() => {
    return currentService?.factors.find((f) => f.id === selectedFactor);
  }, [currentService, selectedFactor]);

  const estimatedFee = useMemo(() => {
    if (!currentService || !currentFactor) return 0;
    return currentService.baseFee * currentFactor.multiplier * quantity;
  }, [currentService, currentFactor, quantity]);

  const handleServiceSelect = (serviceId: string) => {
    setSelectedService(serviceId);
    setSelectedFactor(null);
    setQuantity(1);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* 页面头部 */}
      <div className="bg-gradient-hero text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm">
              <Calculator className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">费用计算器</h1>
              <p className="text-white/80 mt-1">透明公开的法律服务费用估算</p>
            </div>
          </div>
          <p className="text-white/70 max-w-2xl">
            通过我们的费用计算器，您可以快速估算所需法律服务的费用范围。
            实际费用可能因案件具体情况而有所调整，最终以律师报价为准。
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* 服务类型选择 */}
        <div className="mb-12">
          <h2 className="text-xl font-semibold text-slate-900 mb-6">选择服务类型</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {SERVICE_TYPES.map((service) => {
              const Icon = service.icon;
              const isSelected = selectedService === service.id;
              
              return (
                <button
                  key={service.id}
                  onClick={() => handleServiceSelect(service.id)}
                  className={`
                    p-6 rounded-2xl border-2 text-left transition-all duration-300
                    ${isSelected
                      ? 'border-primary-500 bg-primary-50 shadow-lg shadow-primary-500/10'
                      : 'border-slate-200 bg-white hover:border-primary-300 hover:shadow-md'
                    }
                  `}
                >
                  <div className={`
                    w-12 h-12 rounded-xl flex items-center justify-center mb-4
                    ${isSelected ? 'bg-primary-500 text-white' : 'bg-slate-100 text-slate-600'}
                  `}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <h3 className={`font-semibold mb-2 ${isSelected ? 'text-primary-700' : 'text-slate-900'}`}>
                    {service.name}
                  </h3>
                  <p className="text-sm text-slate-500">{service.description}</p>
                  <p className="text-xs text-slate-400 mt-3">
                    起步价 ¥{service.baseFee}/{service.feeUnit}
                  </p>
                </button>
              );
            })}
          </div>
        </div>

        {/* 费用计算区域 */}
        {currentService && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* 左侧：选择复杂度和数量 */}
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>{currentService.name} - 复杂度选择</CardTitle>
                  <CardDescription>根据您的具体情况选择合适的复杂度等级</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {currentService.factors.map((factor) => {
                      const isSelected = selectedFactor === factor.id;
                      
                      return (
                        <button
                          key={factor.id}
                          onClick={() => setSelectedFactor(factor.id)}
                          className={`
                            w-full p-4 rounded-xl border-2 text-left transition-all
                            ${isSelected
                              ? 'border-primary-500 bg-primary-50'
                              : 'border-slate-200 hover:border-primary-300'
                            }
                          `}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <span className={`font-medium ${isSelected ? 'text-primary-700' : 'text-slate-900'}`}>
                                {factor.name}
                              </span>
                              <p className="text-sm text-slate-500 mt-1">{factor.description}</p>
                            </div>
                            <div className="text-right">
                              <span className="text-lg font-bold text-primary-600">
                                ¥{currentService.baseFee * factor.multiplier}
                              </span>
                              <span className="text-slate-400 text-sm">/{currentService.feeUnit}</span>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              {selectedFactor && (
                <Card>
                  <CardHeader>
                    <CardTitle>数量/时长</CardTitle>
                    <CardDescription>根据实际需求调整数量</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4">
                      <button
                        onClick={() => setQuantity(Math.max(1, quantity - 1))}
                        className="w-10 h-10 rounded-xl border border-slate-200 flex items-center justify-center hover:bg-slate-50"
                      >
                        -
                      </button>
                      <input
                        type="number"
                        value={quantity}
                        onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                        className="w-24 h-10 text-center border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                      <button
                        onClick={() => setQuantity(quantity + 1)}
                        className="w-10 h-10 rounded-xl border border-slate-200 flex items-center justify-center hover:bg-slate-50"
                      >
                        +
                      </button>
                      <span className="text-slate-500">{currentService.feeUnit}</span>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* 右侧：费用预估 */}
            <div className="lg:col-span-1">
              <div className="sticky top-24">
                <Card className="bg-gradient-to-br from-slate-900 to-slate-800 text-white">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <Calculator className="w-5 h-5 text-primary-400" />
                      <span className="text-slate-300">预估费用</span>
                    </div>
                    
                    {selectedFactor ? (
                      <>
                        <div className="text-4xl font-bold mb-4">
                          ¥{estimatedFee.toLocaleString()}
                        </div>
                        <div className="space-y-2 text-sm text-slate-400">
                          <div className="flex justify-between">
                            <span>基础费用</span>
                            <span>¥{currentService.baseFee}/{currentService.feeUnit}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>复杂度系数</span>
                            <span>×{currentFactor?.multiplier}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>数量</span>
                            <span>×{quantity}</span>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="text-slate-400 py-8 text-center">
                        <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p>请选择复杂度等级</p>
                      </div>
                    )}

                    <div className="mt-6 pt-6 border-t border-slate-700">
                      <div className="flex items-start gap-2 text-xs text-amber-400">
                        <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                        <p>
                          以上费用仅供参考，实际费用可能因案件具体情况而有所调整。
                          建议咨询专业律师获取准确报价。
                        </p>
                      </div>
                    </div>

                    <div className="mt-6 space-y-3">
                      <Link to="/lawyer">
                        <Button variant="primary" fullWidth>
                          找律师咨询
                        </Button>
                      </Link>
                      <Link to="/chat">
                        <Button variant="outline" fullWidth className="border-white/30 text-white hover:bg-white/10">
                          AI 智能咨询
                        </Button>
                      </Link>
                    </div>
                  </CardContent>
                </Card>

                {/* 常见问题 */}
                <Card className="mt-6">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <HelpCircle className="w-5 h-5 text-primary-500" />
                      常见问题
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4 text-sm">
                      <div>
                        <p className="font-medium text-slate-900">费用包含哪些服务？</p>
                        <p className="text-slate-500 mt-1">费用通常包含初步咨询、材料审查、方案制定等基础服务。</p>
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">如何确定最终费用？</p>
                        <p className="text-slate-500 mt-1">律师会在了解案件详情后提供详细报价单，双方协商确定。</p>
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">可以分期付款吗？</p>
                        <p className="text-slate-500 mt-1">部分案件支持分期付款，具体可与律师协商。</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        )}

        {/* 未选择服务时的提示 */}
        {!selectedService && (
          <div className="text-center py-16">
            <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Calculator className="w-10 h-10 text-slate-400" />
            </div>
            <h3 className="text-xl font-semibold text-slate-900 mb-2">选择服务类型开始计算</h3>
            <p className="text-slate-500 max-w-md mx-auto">
              请从上方选择您需要的服务类型，我们将为您提供详细的费用估算
            </p>
          </div>
        )}

        {/* 底部导航 */}
        <div className="mt-16 pt-8 border-t border-slate-200">
          <div className="flex flex-wrap justify-center gap-6">
            <Link
              to="/help"
              className="flex items-center gap-2 text-slate-600 hover:text-primary-600 transition-colors"
            >
              <HelpCircle className="w-5 h-5" />
              <span>帮助中心</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
            <Link
              to="/faq"
              className="flex items-center gap-2 text-slate-600 hover:text-primary-600 transition-colors"
            >
              <Info className="w-5 h-5" />
              <span>常见问题</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
            <Link
              to="/contact"
              className="flex items-center gap-2 text-slate-600 hover:text-primary-600 transition-colors"
            >
              <Users className="w-5 h-5" />
              <span>联系我们</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FeeCalculatorPage;