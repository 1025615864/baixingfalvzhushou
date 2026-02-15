/**
 * TopicList（专题列表组件）
 * 展示垂直频道的咨询类型和文书类型专题
 */

import type { ConsultationType, DocumentType } from '../types';

interface TopicListProps {
  consultationTypes: ConsultationType[];
  documentTypes: DocumentType[];
  isLoading: boolean;
  onConsultationClick?: (typeKey: string) => void;
  onDocumentClick?: (typeKey: string) => void;
}

/**
 * 专题列表组件
 */
export function TopicList({
  consultationTypes,
  documentTypes,
  isLoading,
  onConsultationClick,
  onDocumentClick,
}: TopicListProps): JSX.Element {
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <div className="h-6 bg-gray-200 rounded w-32 mb-4" />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-lg p-4 animate-pulse">
                <div className="h-5 bg-gray-200 rounded w-24 mb-2" />
                <div className="h-4 bg-gray-200 rounded w-full" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 咨询类型 */}
      {consultationTypes.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            咨询服务
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {consultationTypes.map((type) => (
              <div
                key={type.key}
                onClick={() => onConsultationClick?.(type.key)}
                className="bg-white rounded-lg p-4 border border-gray-100 hover:border-indigo-300 hover:shadow-sm transition-all cursor-pointer group"
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0 group-hover:bg-indigo-100 transition-colors">
                    <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 group-hover:text-indigo-600 transition-colors">
                      {type.name}
                    </h4>
                    <p className="text-sm text-gray-500 mt-0.5 line-clamp-2">
                      {type.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 文书类型 */}
      {documentTypes.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            文书模板
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {documentTypes.map((type) => (
              <div
                key={type.key}
                onClick={() => onDocumentClick?.(type.key)}
                className="bg-white rounded-lg p-4 border border-gray-100 hover:border-emerald-300 hover:shadow-sm transition-all cursor-pointer group"
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center flex-shrink-0 group-hover:bg-emerald-100 transition-colors">
                    <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 group-hover:text-emerald-600 transition-colors">
                      {type.name}
                    </h4>
                    <p className="text-sm text-gray-500 mt-0.5 line-clamp-2">
                      {type.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}