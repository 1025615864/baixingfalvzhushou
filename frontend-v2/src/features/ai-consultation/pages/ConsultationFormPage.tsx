/**
 * ConsultationFormPage - 法律咨询表单页面
 *
 * 用户填写法律咨询表单的页面
 */

import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

import { useCreateSession } from '../hooks/useAIConsultation';

/**
 * 法律咨询表单页面
 */
export function ConsultationFormPage(): JSX.Element {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('labor');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  
  const navigate = useNavigate();
  const createSession = useCreateSession();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!title.trim() || !content.trim()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const newSession = await createSession.mutateAsync({
        title,
        category: category as unknown as 'labor' | 'marriage' | 'contract' | 'other',
      });
      
      // 显示成功提示
      setIsSuccess(true);
      
      // 2 秒后导航到咨询详情页面
      setTimeout(() => {
        navigate(`/consultation/${newSession.id}`);
      }, 2000);
    } catch {
      console.error('创建咨询失败');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-6 max-w-2xl">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6" data-testid="page-title">法律咨询</h1>
        
        {isSuccess ? (
          <div data-testid="consultation-success" className="text-center py-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">咨询提交成功</h2>
            <p className="text-gray-600">正在跳转到咨询详情页面...</p>
          </div>
        ) : (
        <form onSubmit={(e) => { void handleSubmit(e); }} className="space-y-4">
          {/* 咨询标题 */}
          <div>
            <label htmlFor="consultation-title" className="block text-sm font-medium text-gray-700 mb-1">
              咨询标题
            </label>
            <input
              id="consultation-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="简要描述您的问题"
              data-testid="consultation-title"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {/* 咨询类型 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              咨询类型
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="category"
                  value="labor"
                  checked={category === 'labor'}
                  onChange={(e) => setCategory(e.target.value)}
                  data-testid="consultation-type-labor"
                  className="mr-2"
                />
                <span>劳动纠纷</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="category"
                  value="marriage"
                  checked={category === 'marriage'}
                  onChange={(e) => setCategory(e.target.value)}
                  data-testid="consultation-type-marriage"
                  className="mr-2"
                />
                <span>婚姻家庭</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="category"
                  value="contract"
                  checked={category === 'contract'}
                  onChange={(e) => setCategory(e.target.value)}
                  data-testid="consultation-type-contract"
                  className="mr-2"
                />
                <span>合同纠纷</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="category"
                  value="other"
                  checked={category === 'other'}
                  onChange={(e) => setCategory(e.target.value)}
                  data-testid="consultation-type-other"
                  className="mr-2"
                />
                <span>其他</span>
              </label>
            </div>
          </div>

          {/* 咨询内容 */}
          <div>
            <label htmlFor="consultation-content" className="block text-sm font-medium text-gray-700 mb-1">
              问题描述
            </label>
            <textarea
              id="consultation-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="详细描述您的问题，包括时间、地点、人物和具体经过"
              data-testid="consultation-content"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={6}
              required
            />
          </div>

          {/* 提交按钮 */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => navigate('/consultation/history')}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !title.trim() || !content.trim()}
              data-testid="submit-consultation"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? '提交中...' : '提交咨询'}
            </button>
          </div>
        </form>
        )}
      </div>
    </div>
  );
}