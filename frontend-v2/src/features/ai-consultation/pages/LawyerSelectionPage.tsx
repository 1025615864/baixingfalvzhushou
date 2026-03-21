/**
 * LawyerSelectionPage - 律师选择页面
 * 
 * 用户选择律师进行咨询的页面
 */

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

/**
 * 律师数据接口
 */
interface Lawyer {
  id: string;
  name: string;
  title: string;
  specialties: string[];
  experience: number;
  rating: number;
  avatar?: string;
}

// Mock 律师数据
const MOCK_LAWYERS: Lawyer[] = [
  {
    id: '1',
    name: '张律师',
    title: '高级合伙人',
    specialties: ['劳动法', '合同法', '婚姻家庭'],
    experience: 10,
    rating: 4.9,
  },
  {
    id: '2',
    name: '李律师',
    title: '资深律师',
    specialties: ['劳动法', '工伤赔偿'],
    experience: 8,
    rating: 4.8,
  },
  {
    id: '3',
    name: '王律师',
    title: '执业律师',
    specialties: ['合同纠纷', '债权债务'],
    experience: 5,
    rating: 4.7,
  },
];

/**
 * 律师选择页面
 */
export function LawyerSelectionPage(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [selectedLawyerId, setSelectedLawyerId] = useState<string | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);

  const handleSelectLawyer = (lawyerId: string) => {
    setIsSelecting(true);
    setSelectedLawyerId(lawyerId);
    
    // 模拟选择成功
    setTimeout(() => {
      setIsSelecting(false);
      // 导航到聊天页面
      navigate(`/consultation/${id}/chat`);
    }, 1000);
  };

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900" data-testid="page-title">选择律师</h1>
        <p className="text-gray-600 mt-1">为您咨询的案件选择专业律师</p>
      </div>

      {/* 律师列表 */}
      <div className="grid gap-4 md:grid-cols-2">
        {MOCK_LAWYERS.map((lawyer) => (
          <div
            key={lawyer.id}
            data-testid="lawyer-card"
            className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 transition-all ${
              selectedLawyerId === lawyer.id ? 'ring-2 ring-blue-500 border-transparent' : ''
            }`}
          >
            <div className="flex items-start gap-4">
              {/* 头像 */}
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-xl font-bold flex-shrink-0">
                {lawyer.name.charAt(0)}
              </div>

              {/* 信息 */}
              <div className="flex-1">
                <h3 className="text-lg font-bold text-gray-900">{lawyer.name}</h3>
                <p className="text-sm text-gray-600">{lawyer.title}</p>
                
                {/* 专业领域 */}
                <div className="flex flex-wrap gap-1 mt-2">
                  {lawyer.specialties.map((specialty) => (
                    <span
                      key={specialty}
                      className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full"
                    >
                      {specialty}
                    </span>
                  ))}
                </div>

                {/* 经验和评分 */}
                <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                  <span>{lawyer.experience}年经验</span>
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    {lawyer.rating}
                  </span>
                </div>
              </div>
            </div>

            {/* 选择按钮 */}
            <div className="mt-4 pt-4 border-t border-gray-100">
              <button
                data-testid="select-lawyer-btn"
                onClick={() => { void handleSelectLawyer(lawyer.id); }}
                disabled={isSelecting || selectedLawyerId === lawyer.id}
                className={`w-full py-2 rounded-lg font-medium transition-colors ${
                  selectedLawyerId === lawyer.id
                    ? 'bg-green-600 text-white'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {selectedLawyerId === lawyer.id ? '已选择' : isSelecting ? '选择中...' : '选择此律师'}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* 选择成功提示 */}
      {selectedLawyerId && !isSelecting && (
        <div data-testid="lawyer-selected" className="fixed bottom-4 right-4 bg-green-600 text-white px-4 py-3 rounded-lg shadow-lg">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>律师选择成功！正在跳转...</span>
          </div>
        </div>
      )}
    </div>
  );
}