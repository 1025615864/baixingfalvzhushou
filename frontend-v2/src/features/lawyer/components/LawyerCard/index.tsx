import React from 'react';
import { Link } from 'react-router-dom';

import type { Lawyer } from '../../types';

interface LawyerCardProps {
  lawyer: Lawyer;
  onClick?: (id: string) => void;
  onConsult?: (id: string) => void;
}

export const LawyerCard: React.FC<LawyerCardProps> = ({ lawyer, onClick, onConsult }) => {
  const specialtyList = lawyer.specialties ? lawyer.specialties.split(/[,，]/).map((s: string) => s.trim()).filter(Boolean) : [];

  const handleCardClick = (): void => {
    onClick?.(lawyer.id);
  };

  const handleConsultClick = (e: React.MouseEvent): void => {
    e.stopPropagation();
    onConsult?.(lawyer.id);
  };

  return (
    <div
      className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow cursor-pointer"
      onClick={handleCardClick}
      role="button"
      tabIndex={0}
    >
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {lawyer.avatar ? (
            <img
              src={lawyer.avatar}
              alt={lawyer.name}
              className="w-16 h-16 rounded-full object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded-full bg-gray-200 flex items-center justify-center text-2xl">
              {lawyer.name.charAt(0)}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-lg font-semibold text-gray-900">{lawyer.name}</h3>
            {lawyer.isVerified && (
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                已认证
              </span>
            )}
          </div>

          <p className="text-sm text-gray-500 mb-2">
            {lawyer.title || '律师'}{lawyer.firmName ? ` · ${lawyer.firmName}` : ''}
          </p>

          <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
            <span>执业{lawyer.experienceYears}年</span>
            <span>{lawyer.caseCount}个案件</span>
            <span className="flex items-center gap-1">
              <span className="text-yellow-500">★</span>
              {lawyer.rating.toFixed(1)} ({lawyer.reviewCount}条评价)
            </span>
          </div>

          {/* Specialties */}
          {specialtyList.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {specialtyList.slice(0, 5).map((specialty: string) => (
                <span
                  key={specialty}
                  className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-md"
                >
                  {specialty}
                </span>
              ))}
            </div>
          )}

          {/* Introduction */}
          {lawyer.introduction && (
            <p className="text-sm text-gray-600 line-clamp-2 mb-3">
              {lawyer.introduction}
            </p>
          )}

          {/* Price & Action */}
          <div className="flex items-center justify-between">
            <div className="text-primary-600 font-semibold">
              ¥{lawyer.consultationFee}
              <span className="text-gray-400 text-sm font-normal">/次</span>
            </div>
            {onConsult ? (
              <button
                type="button"
                onClick={handleConsultClick}
                className="px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                立即咨询
              </button>
            ) : (
              <Link
                to={`/lawyers/${lawyer.id}`}
                className="px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                立即咨询
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};