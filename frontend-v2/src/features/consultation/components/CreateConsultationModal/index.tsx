import { useState } from 'react';

import { useCreateConsultation } from '../../hooks/useCreateConsultation';
import type { ConsultationCategory } from '../../types';

interface CreateConsultationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function CreateConsultationModal({
  isOpen,
  onClose,
  onSuccess,
}: CreateConsultationModalProps): JSX.Element | null {
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState<ConsultationCategory>('legal');

  const createMutation = useCreateConsultation();

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    
    void createMutation.mutateAsync({
      subject,
      description,
      category,
      lawyerId: 'lawyer1',
    }).then(() => {
      // 重置表单
      setSubject('');
      setDescription('');
      setCategory('legal');
      
      onSuccess?.();
      onClose();
    });
  };

  const categoryOptions: { value: ConsultationCategory; label: string }[] = [
    { value: 'legal', label: '法律咨询' },
    { value: 'contract', label: '合同审查' },
    { value: 'dispute', label: '纠纷调解' },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">发起咨询</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            type="button"
            aria-label="关闭"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          <div>
            <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-1">
              咨询标题
            </label>
            <input
              id="subject"
              type="text"
              value={subject}
              onChange={(e): void => setSubject(e.target.value)}
              placeholder="简要描述您的问题"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              required
            />
          </div>

          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
              咨询类型
            </label>
            <select
              id="category"
              value={category}
              onChange={(e): void => setCategory(e.target.value as ConsultationCategory)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {categoryOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              问题描述
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e): void => setDescription(e.target.value)}
              placeholder="详细描述您的问题"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={4}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending || !subject.trim() || !description.trim()}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {createMutation.isPending ? '提交中...' : '提交咨询'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}