/**
 * LawyerReviewModal 组件 - 律师评价弹窗
 */

import { useState, useCallback } from 'react';

import { useSubmitReview } from '../hooks/useLawyerMatching';

interface LawyerReviewModalProps {
  lawyerId: string;
  lawyerName: string;
  bookingId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface RatingDimension {
  key: 'professionalism' | 'responsiveness' | 'attitude' | 'valueForMoney';
  label: string;
  description: string;
}

const RATING_DIMENSIONS: RatingDimension[] = [
  {
    key: 'professionalism',
    label: '专业度',
    description: '律师的专业知识水平',
  },
  {
    key: 'responsiveness',
    label: '响应速度',
    description: '回复及时性',
  },
  {
    key: 'attitude',
    label: '服务态度',
    description: '服务质量和态度',
  },
  {
    key: 'valueForMoney',
    label: '性价比',
    description: '服务价值与费用匹配度',
  },
];

const REVIEW_TAGS = [
  '专业高效',
  '耐心细致',
  '回复及时',
  '建议实用',
  '服务热情',
  '经验丰富',
  '沟通顺畅',
  '值得信赖',
];

export function LawyerReviewModal({
  lawyerId,
  lawyerName,
  bookingId,
  isOpen,
  onClose,
  onSuccess,
}: LawyerReviewModalProps): JSX.Element | null {
  const [overallRating, setOverallRating] = useState<number>(5);
  const [dimensions, setDimensions] = useState<Record<RatingDimension['key'], number>>({
    professionalism: 5,
    responsiveness: 5,
    attitude: 5,
    valueForMoney: 5,
  });
  const [content, setContent] = useState<string>('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [isAnonymous, setIsAnonymous] = useState<boolean>(false);
  const [isRecommended, setIsRecommended] = useState<boolean>(true);

  const submitReview = useSubmitReview();

  const handleDimensionChange = useCallback((key: RatingDimension['key'], value: number) => {
    setDimensions((prev) => ({ ...prev, [key]: value }));
  }, []);

  const handleTagToggle = useCallback((tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  }, []);

  const handleSubmit = useCallback(() => {
    submitReview.mutate(
      {
        lawyerId,
        bookingId,
        rating: overallRating,
        dimensions: {
          professionalism: dimensions.professionalism,
          responsiveness: dimensions.responsiveness,
          attitude: dimensions.attitude,
          valueForMoney: dimensions.valueForMoney,
        },
        content: content.trim(),
        tags: selectedTags,
        isAnonymous,
        isRecommended,
      },
      {
        onSuccess: () => {
          onSuccess();
          onClose();
        },
      }
    );
  }, [
    submitReview,
    lawyerId,
    bookingId,
    overallRating,
    dimensions,
    content,
    selectedTags,
    isAnonymous,
    isRecommended,
    onSuccess,
    onClose,
  ]);

  const handleClose = useCallback(() => {
    if (!submitReview.isPending) {
      onClose();
    }
  }, [submitReview.isPending, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-xl bg-white shadow-xl">
        {/* 头部 */}
        <div className="sticky top-0 flex items-center justify-between border-b border-gray-100 bg-white px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">
            评价律师 - {lawyerName}
          </h2>
          <button
            type="button"
            onClick={handleClose}
            disabled={submitReview.isPending}
            className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 内容 */}
        <div className="p-6 space-y-6">
          {/* 总体评分 */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              总体评分 <span className="text-red-500">*</span>
            </label>
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setOverallRating(star)}
                  className={`h-10 w-10 transition-transform hover:scale-110 ${
                    star <= overallRating ? 'text-yellow-400' : 'text-gray-300'
                  }`}
                >
                  <svg fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                </button>
              ))}
              <span className="ml-2 text-lg font-semibold text-gray-700">
                {overallRating}.0
              </span>
            </div>
          </div>

          {/* 详细评分 */}
          <div>
            <label className="mb-3 block text-sm font-medium text-gray-700">
              详细评分
            </label>
            <div className="space-y-3">
              {RATING_DIMENSIONS.map((dimension) => (
                <div key={dimension.key} className="flex items-center justify-between">
                  <div>
                    <span className="text-sm font-medium text-gray-700">{dimension.label}</span>
                    <span className="ml-2 text-xs text-gray-400">{dimension.description}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => handleDimensionChange(dimension.key, star)}
                        className={`h-6 w-6 ${star <= dimensions[dimension.key] ? 'text-yellow-400' : 'text-gray-300'}`}
                      >
                        <svg fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 标签选择 */}
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              标签（可多选）
            </label>
            <div className="flex flex-wrap gap-2">
              {REVIEW_TAGS.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => handleTagToggle(tag)}
                  className={`rounded-full border px-3 py-1 text-sm transition-colors ${
                    selectedTags.includes(tag)
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-300 bg-white text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>

          {/* 评价内容 */}
          <div>
            <label htmlFor="review-content" className="mb-1 block text-sm font-medium text-gray-700">
              评价内容
            </label>
            <textarea
              id="review-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="分享您的咨询体验，帮助其他用户做出选择..."
              rows={4}
              maxLength={500}
              className="w-full resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-right text-xs text-gray-400">{content.length}/500</p>
          </div>

          {/* 选项 */}
          <div className="space-y-3">
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="checkbox"
                checked={isRecommended}
                onChange={(e) => setIsRecommended(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">推荐这位律师</span>
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="checkbox"
                checked={isAnonymous}
                onChange={(e) => setIsAnonymous(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">匿名评价</span>
            </label>
          </div>

          {/* 错误提示 */}
          {submitReview.error && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
              {submitReview.error.message}
            </div>
          )}
        </div>

        {/* 底部按钮 */}
        <div className="flex gap-3 border-t border-gray-100 px-6 py-4">
          <button
            type="button"
            onClick={handleClose}
            disabled={submitReview.isPending}
            className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-50"
          >
            取消
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitReview.isPending}
            className="flex-1 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
          >
            {submitReview.isPending ? '提交中...' : '提交评价'}
          </button>
        </div>
      </div>
    </div>
  );
}