/**
 * ContractGenerator - 合同生成器组件
 */

import { useState } from 'react';

import type { ContractTemplate } from '../types';
import { useGenerateContract } from '../hooks/useContracts';

/** 内置合同模板 */
const DEFAULT_TEMPLATES: ContractTemplate[] = [
  {
    id: 'lease',
    name: '房屋租赁合同',
    description: '适用于住宅、商铺等房屋租赁场景',
    contractType: 'lease',
    fields: [
      { key: 'landlord', label: '出租方（甲方）', type: 'text', required: true, placeholder: '请输入出租方姓名或名称' },
      { key: 'tenant', label: '承租方（乙方）', type: 'text', required: true, placeholder: '请输入承租方姓名或名称' },
      { key: 'address', label: '房屋地址', type: 'textarea', required: true, placeholder: '请输入详细地址' },
      { key: 'area', label: '房屋面积（平方米）', type: 'number', required: true, placeholder: '0' },
      { key: 'monthlyRent', label: '月租金（元）', type: 'number', required: true, placeholder: '0' },
      { key: 'deposit', label: '押金（元）', type: 'number', required: true, placeholder: '0' },
      { key: 'leaseTerm', label: '租赁期限（月）', type: 'number', required: true, placeholder: '12' },
      { key: 'startDate', label: '起始日期', type: 'date', required: true },
      { key: 'paymentMethod', label: '付款方式', type: 'select', required: true, options: ['月付', '季付', '半年付', '年付'] },
    ],
  },
  {
    id: 'loan',
    name: '借款合同',
    description: '适用于个人之间的借款场景',
    contractType: 'loan',
    fields: [
      { key: 'lender', label: '出借人', type: 'text', required: true, placeholder: '请输入出借人姓名' },
      { key: 'borrower', label: '借款人', type: 'text', required: true, placeholder: '请输入借款人姓名' },
      { key: 'amount', label: '借款金额（元）', type: 'number', required: true, placeholder: '0' },
      { key: 'interestRate', label: '年利率（%）', type: 'number', required: false, placeholder: '0', defaultValue: '0' },
      { key: 'loanTerm', label: '借款期限（月）', type: 'number', required: true, placeholder: '12' },
      { key: 'startDate', label: '借款日期', type: 'date', required: true },
      { key: 'repaymentMethod', label: '还款方式', type: 'select', required: true, options: ['到期一次性还本付息', '按月付息到期还本', '等额本息', '等额本金'] },
      { key: 'purpose', label: '借款用途', type: 'textarea', required: false, placeholder: '请说明借款用途' },
    ],
  },
  {
    id: 'service',
    name: '服务合同',
    description: '适用于各类服务提供场景',
    contractType: 'service',
    fields: [
      { key: 'serviceProvider', label: '服务方', type: 'text', required: true, placeholder: '请输入服务方名称' },
      { key: 'client', label: '委托方', type: 'text', required: true, placeholder: '请输入委托方名称' },
      { key: 'serviceContent', label: '服务内容', type: 'textarea', required: true, placeholder: '请详细描述服务内容' },
      { key: 'serviceFee', label: '服务费用（元）', type: 'number', required: true, placeholder: '0' },
      { key: 'serviceTerm', label: '服务期限（天）', type: 'number', required: true, placeholder: '30' },
      { key: 'startDate', label: '开始日期', type: 'date', required: true },
      { key: 'paymentTerms', label: '付款条件', type: 'select', required: true, options: ['服务完成后付款', '预付50%服务完成后付50%', '签订时全额支付'] },
    ],
  },
  {
    id: 'confidentiality',
    name: '保密协议',
    description: '适用于商业秘密保护场景',
    contractType: 'confidentiality',
    fields: [
      { key: 'disclosingParty', label: '披露方', type: 'text', required: true, placeholder: '请输入披露方名称' },
      { key: 'receivingParty', label: '接收方', type: 'text', required: true, placeholder: '请输入接收方名称' },
      { key: 'confidentialInfo', label: '保密信息范围', type: 'textarea', required: true, placeholder: '请描述保密信息的范围' },
      { key: 'confidentialityTerm', label: '保密期限（年）', type: 'number', required: true, placeholder: '3' },
      { key: 'governingLaw', label: '适用法律', type: 'select', required: true, options: ['中华人民共和国法律', '其他'] },
      { key: 'disputeResolution', label: '争议解决方式', type: 'select', required: true, options: ['协商解决', '提交仲裁', '向有管辖权的法院起诉'] },
    ],
  },
];

interface ContractGeneratorProps {
  /** 生成成功回调 */
  onGenerateSuccess?: (contract: { title: string; content: string }) => void;
}

/**
 * 合同生成器组件
 */
export function ContractGenerator({ onGenerateSuccess }: ContractGeneratorProps): JSX.Element {
  const [selectedTemplate, setSelectedTemplate] = useState<ContractTemplate | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [showPreview, setShowPreview] = useState<boolean>(false);

  const generateMutation = useGenerateContract();

  /** 选择模板 */
  const handleSelectTemplate = (template: ContractTemplate): void => {
    setSelectedTemplate(template);
    // 初始化表单值
    const initialValues: Record<string, string> = {};
    template.fields.forEach(field => {
      initialValues[field.key] = field.defaultValue || '';
    });
    setFormValues(initialValues);
    setShowPreview(false);
  };

  /** 返回模板选择 */
  const handleBack = (): void => {
    setSelectedTemplate(null);
    setFormValues({});
    setShowPreview(false);
    generateMutation.reset();
  };

  /** 处理字段变化 */
  const handleFieldChange = (key: string, value: string): void => {
    setFormValues(prev => ({ ...prev, [key]: value }));
  };

  /** 验证表单 */
  const validateForm = (): boolean => {
    if (!selectedTemplate) return false;
    return selectedTemplate.fields
      .filter(field => field.required)
      .every(field => formValues[field.key]?.trim() !== '');
  };

  /** 生成合同 */
  const handleGenerate = async (): Promise<void> => {
    if (!selectedTemplate) return;

    try {
      const contract = await generateMutation.mutateAsync({
        templateId: selectedTemplate.id,
        fields: formValues,
      });
      
      if (contract && onGenerateSuccess) {
        onGenerateSuccess({
          title: contract.title,
          content: contract.content,
        });
      }
    } catch (err) {
      // 错误已由 mutation 处理
    }
  };

  /** 渲染模板选择 */
  const renderTemplateSelection = (): JSX.Element => (
    <div className="space-y-4">
      <div className="text-center mb-6">
        <h3 className="text-lg font-medium text-gray-900">选择合同模板</h3>
        <p className="text-sm text-gray-500 mt-1">根据您的需求选择合适的合同类型</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {DEFAULT_TEMPLATES.map(template => (
          <button
            key={template.id}
            onClick={() => handleSelectTemplate(template)}
            className="p-6 bg-white border border-gray-200 rounded-xl text-left hover:border-blue-500 hover:shadow-md transition-all group"
          >
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-medium text-gray-900 group-hover:text-blue-600">
                  {template.name}
                </h4>
                <p className="text-sm text-gray-500 mt-1">{template.description}</p>
              </div>
              <svg
                className="w-5 h-5 text-gray-400 group-hover:text-blue-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
                {template.fields.length} 个字段
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );

  /** 渲染表单字段 */
  const renderField = (field: ContractTemplate['fields'][0]): JSX.Element => {
    const value = formValues[field.key] || '';

    switch (field.type) {
      case 'textarea':
        return (
          <textarea
            value={value}
            onChange={e => handleFieldChange(field.key, e.target.value)}
            placeholder={field.placeholder}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-vertical"
          />
        );
      
      case 'select':
        return (
          <select
            value={value}
            onChange={e => handleFieldChange(field.key, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
          >
            <option value="">请选择</option>
            {field.options?.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        );
      
      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={e => handleFieldChange(field.key, e.target.value)}
            placeholder={field.placeholder}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        );
      
      case 'date':
        return (
          <input
            type="date"
            value={value}
            onChange={e => handleFieldChange(field.key, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        );
      
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={e => handleFieldChange(field.key, e.target.value)}
            placeholder={field.placeholder}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        );
    }
  };

  /** 渲染表单 */
  const renderForm = (): JSX.Element => {
    if (!selectedTemplate) return <></>;

    return (
      <div className="space-y-6">
        {/* 头部 */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-200">
          <div>
            <h3 className="text-lg font-medium text-gray-900">{selectedTemplate.name}</h3>
            <p className="text-sm text-gray-500">{selectedTemplate.description}</p>
          </div>
          <button
            onClick={handleBack}
            className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            返回
          </button>
        </div>

        {/* 表单字段 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {selectedTemplate.fields.map(field => (
            <div key={field.key} className={field.type === 'textarea' ? 'md:col-span-2' : ''}>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {field.label}
                {field.required && <span className="text-red-500 ml-1">*</span>}
              </label>
              {renderField(field)}
            </div>
          ))}
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center gap-3 pt-4 border-t border-gray-200">
          <button
            onClick={() => void handleGenerate()}
            disabled={!validateForm() || generateMutation.isPending}
            className={`
              flex-1 py-3 px-4 rounded-lg font-medium text-white transition-all
              ${!validateForm() || generateMutation.isPending
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 shadow-sm hover:shadow'
              }
            `}
          >
            {generateMutation.isPending ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                生成中...
              </span>
            ) : (
              '生成合同'
            )}
          </button>
          
          {generateMutation.data && (
            <button
              onClick={() => setShowPreview(!showPreview)}
              className="px-4 py-3 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              {showPreview ? '隐藏预览' : '显示预览'}
            </button>
          )}
        </div>

        {/* 错误提示 */}
        {generateMutation.isError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {generateMutation.error?.message || '生成失败，请重试'}
          </div>
        )}

        {/* 生成结果预览 */}
        {generateMutation.data && showPreview && (
          <div className="mt-6 bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
              <h4 className="font-medium text-gray-900">合同预览</h4>
              <button
                onClick={() => {
                  if (!generateMutation.data) return;
                  const blob = new Blob([generateMutation.data.content], { type: 'text/plain' });
                  const url = window.URL.createObjectURL(blob);
                  const link = document.createElement('a');
                  link.href = url;
                  link.download = `${generateMutation.data.title}.txt`;
                  link.click();
                  window.URL.revokeObjectURL(url);
                }}
                className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                下载
              </button>
            </div>
            <div className="p-4 max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                {generateMutation.data.content}
              </pre>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="w-full bg-white rounded-xl border border-gray-200 p-6">
      {selectedTemplate ? renderForm() : renderTemplateSelection()}
    </div>
  );
}