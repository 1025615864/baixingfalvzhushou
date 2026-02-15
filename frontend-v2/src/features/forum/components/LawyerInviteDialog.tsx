// ============================================
// 律师邀请对话框组件
// ============================================

import { useState, useCallback, useMemo, useEffect } from 'react';

import { useLawyers, useCreateInvitation } from '../hooks/useInvitations';
import type { LawyerInfo } from '../types';

// 简单的防抖实现
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

interface LawyerInviteDialogProps {
  postId: number;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const DEFAULT_MESSAGE = '您好，我有一个法律问题想请教您，希望您能帮忙解答。谢谢！';

export function LawyerInviteDialog({
  postId,
  isOpen,
  onClose,
  onSuccess,
}: LawyerInviteDialogProps) {
  const [searchKeyword, setSearchKeyword] = useState('');
  const [selectedLawyer, setSelectedLawyer] = useState<LawyerInfo | null>(null);
  const [message, setMessage] = useState(DEFAULT_MESSAGE);
  const [step, setStep] = useState<'select' | 'confirm'>('select');

  const debouncedKeyword = useDebounce(searchKeyword, 300);

  const { data: lawyersData, isLoading: isLoadingLawyers } = useLawyers(debouncedKeyword);
  const { mutate: createInvitation, isPending: isSubmitting } = useCreateInvitation();

  const lawyers = useMemo(() => lawyersData?.items ?? [], [lawyersData]);

  const handleSelectLawyer = useCallback((lawyer: LawyerInfo) => {
    setSelectedLawyer(lawyer);
    setStep('confirm');
  }, []);

  const handleBack = useCallback(() => {
    setStep('select');
    setSelectedLawyer(null);
  }, []);

  const handleClose = useCallback(() => {
    onClose();
    // 重置状态
    setTimeout(() => {
      setStep('select');
      setSelectedLawyer(null);
      setMessage(DEFAULT_MESSAGE);
      setSearchKeyword('');
    }, 300);
  }, [onClose]);

  const handleSubmit = useCallback(() => {
    if (!selectedLawyer) return;

    createInvitation(
      {
        post_id: postId,
        lawyer_id: selectedLawyer.id,
        message: message.trim() || DEFAULT_MESSAGE,
      },
      {
        onSuccess: () => {
          onSuccess?.();
          handleClose();
        },
      }
    );
  }, [createInvitation, postId, selectedLawyer, message, onSuccess, handleClose]);

  const renderStarRating = useCallback((rating: number) => {
    return (
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <svg
            key={star}
            className={`w-4 h-4 ${
              star <= Math.round(rating) ? 'text-amber-400 fill-current' : 'text-gray-300'
            }`}
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
        <span className="ml-1 text-sm text-gray-600">{rating.toFixed(1)}</span>
      </div>
    );
  }, []);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 遮罩层 */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={handleClose}
      />

      {/* 对话框 */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-xl font-semibold text-gray-900">
            {step === 'select' ? '邀请律师解答' : '确认邀请'}
          </h2>
          <button
            onClick={handleClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
            aria-label="关闭"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 内容区域 */}
        <div className="flex-1 overflow-y-auto p-6">
          {step === 'select' ? (
            <>
              {/* 搜索框 */}
              <div className="relative mb-6">
                <input
                  type="text"
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  placeholder="搜索律师姓名或专业领域..."
                  className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
                <svg
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                {isLoadingLawyers && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                )}
              </div>

              {/* 律师列表 */}
              <div className="space-y-3">
                {isLoadingLawyers && lawyers.length === 0 ? (
                  // 加载骨架屏
                  Array.from({ length: 3 }, (_, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl animate-pulse"
                    >
                      <div className="w-14 h-14 bg-gray-200 rounded-full" />
                      <div className="flex-1 space-y-2">
                        <div className="h-5 bg-gray-200 rounded w-1/3" />
                        <div className="h-4 bg-gray-200 rounded w-1/2" />
                      </div>
                    </div>
                  ))
                ) : lawyers.length === 0 ? (
                  <div className="text-center py-12">
                    <svg
                      className="w-16 h-16 text-gray-300 mx-auto mb-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0z"
                      />
                    </svg>
                    <p className="text-gray-500">未找到匹配的律师</p>
                    {searchKeyword && (
                      <button
                        onClick={() => setSearchKeyword('')}
                        className="mt-2 text-blue-600 hover:text-blue-700"
                      >
                        清除搜索
                      </button>
                    )}
                  </div>
                ) : (
                  lawyers.map((lawyer) => (
                    <button
                      key={lawyer.id}
                      onClick={() => handleSelectLawyer(lawyer)}
                      className="w-full flex items-start gap-4 p-4 bg-white border border-gray-100 rounded-xl hover:border-blue-300 hover:shadow-md transition-all text-left group"
                    >
                      {/* 头像 */}
                      <div className="relative flex-shrink-0">
                        {lawyer.avatar ? (
                          <img
                            src={lawyer.avatar}
                            alt={lawyer.name}
                            className="w-14 h-14 rounded-full object-cover ring-2 ring-gray-100"
                          />
                        ) : (
                          <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-xl font-medium">
                            {lawyer.name[0]}
                          </div>
                        )}
                      </div>

                      {/* 信息 */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                              {lawyer.name}
                            </h3>
                            <p className="text-sm text-gray-500">{lawyer.title}</p>
                          </div>
                          <div className="flex-shrink-0">
                            {renderStarRating(lawyer.rating)}
                          </div>
                        </div>

                        {lawyer.law_firm && (
                          <p className="text-sm text-gray-500 mt-1">{lawyer.law_firm}</p>
                        )}

                        {/* 专业领域 */}
                        {lawyer.specialties.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            {lawyer.specialties.slice(0, 3).map((specialty) => (
                              <span
                                key={specialty}
                                className="px-2 py-0.5 text-xs bg-blue-50 text-blue-600 rounded-full"
                              >
                                {specialty}
                              </span>
                            ))}
                            {lawyer.specialties.length > 3 && (
                              <span className="px-2 py-0.5 text-xs text-gray-400">
                                +{lawyer.specialties.length - 3}
                              </span>
                            )}
                          </div>
                        )}

                        {/* 评价数 */}
                        <p className="text-xs text-gray-400 mt-2">
                          {lawyer.review_count} 条评价
                        </p>
                      </div>

                      {/* 箭头 */}
                      <svg
                        className="w-5 h-5 text-gray-300 group-hover:text-blue-500 self-center transition-colors"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    </button>
                  ))
                )}
              </div>
            </>
          ) : (
            /* 确认步骤 */
            selectedLawyer && (
              <div className="space-y-6">
                {/* 选中的律师信息 */}
                <div className="flex items-start gap-4 p-4 bg-blue-50 rounded-xl">
                  {selectedLawyer.avatar ? (
                    <img
                      src={selectedLawyer.avatar}
                      alt={selectedLawyer.name}
                      className="w-16 h-16 rounded-full object-cover ring-2 ring-white"
                    />
                  ) : (
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-2xl font-medium ring-2 ring-white">
                      {selectedLawyer.name[0]}
                    </div>
                  )}
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {selectedLawyer.name}
                    </h3>
                    <p className="text-gray-600">{selectedLawyer.title}</p>
                    {renderStarRating(selectedLawyer.rating)}
                  </div>
                </div>

                {/* 留言输入 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    邀请留言（可选）
                  </label>
                  <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    rows={4}
                    placeholder="请输入您想对律师说的话..."
                    className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    默认消息将被使用如果您不填写
                  </p>
                </div>

                {/* 提示信息 */}
                <div className="flex items-start gap-3 p-4 bg-amber-50 rounded-xl">
                  <svg
                    className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <p className="text-sm text-amber-800">
                    邀请发送后，律师将在48小时内回复。您可以在&ldquo;我的邀请&rdquo;中查看邀请状态。
                  </p>
                </div>
              </div>
            )
          )}
        </div>

        {/* 底部按钮 */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100 bg-gray-50">
          {step === 'select' ? (
            <button
              onClick={handleClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-lg transition-colors"
            >
              取消
            </button>
          ) : (
            <button
              onClick={handleBack}
              disabled={isSubmitting}
              className="flex items-center gap-1 px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              返回
            </button>
          )}

          {step === 'confirm' && (
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  发送中...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  发送邀请
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}