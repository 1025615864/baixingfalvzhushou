import { useState } from 'react';

import {
  ConsultationList,
  ConsultationDetail,
  CreateConsultationModal,
} from '@/features/consultation';

export function ConsultationPage(): JSX.Element {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleSelect = (id: string): void => {
    setSelectedId(id);
  };

  const handleBack = (): void => {
    setSelectedId(null);
  };

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">我的咨询</h1>
          <p className="text-gray-600 mt-1">查看和管理您的法律咨询记录</p>
        </div>
        {!selectedId && (
          <button
            onClick={(): void => setIsModalOpen(true)}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
            type="button"
          >
            <span>+</span>
            发起咨询
          </button>
        )}
      </div>

      {selectedId ? (
        <ConsultationDetail id={selectedId} onBack={handleBack} />
      ) : (
        <ConsultationList onSelect={handleSelect} />
      )}

      <CreateConsultationModal
        isOpen={isModalOpen}
        onClose={(): void => setIsModalOpen(false)}
      />
    </div>
  );
}