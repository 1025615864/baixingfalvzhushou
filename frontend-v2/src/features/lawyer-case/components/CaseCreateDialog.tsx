import { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useCreateCase } from '../hooks/useCases';

const CATEGORY_OPTIONS = [
  { value: 'civil', label: '民事纠纷' },
  { value: 'criminal', label: '刑事辩护' },
  { value: 'contract', label: '合同纠纷' },
  { value: 'labor', label: '劳动争议' },
  { value: 'family', label: '婚姻家庭' },
  { value: 'property', label: '房产纠纷' },
  { value: 'intellectual', label: '知识产权' },
  { value: 'corporate', label: '公司法务' },
  { value: 'other', label: '其他' },
];

interface CaseCreateDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function CaseCreateDialog({ isOpen, onClose, onSuccess }: CaseCreateDialogProps): JSX.Element | null {
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('');
  const [clientName, setClientName] = useState('');
  const [priority, setPriority] = useState(0);

  const createMutation = useCreateCase();

  if (!isOpen) return null;

  const handleSubmit = () => {
    if (!title.trim()) return;
    createMutation.mutate(
      {
        title: title.trim(),
        category,
        clientName: clientName.trim() || undefined,
        priority,
      },
      {
        onSuccess: () => {
          setTitle('');
          setCategory('');
          setClientName('');
          setPriority(0);
          onSuccess();
          onClose();
        },
      }
    );
  };

  const isFormValid = title.trim().length >= 2 && category;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md bg-white rounded-xl shadow-xl">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">创建案件</h2>
          <button onClick={onClose} className="p-1 rounded-full text-gray-400 hover:bg-gray-100">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              案件标题 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="请输入案件标题"
              maxLength={100}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              案件类别 <span className="text-red-500">*</span>
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            >
              <option value="">请选择类别</option>
              {CATEGORY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">当事人姓名</label>
            <input
              type="text"
              value={clientName}
              onChange={(e) => setClientName(e.target.value)}
              placeholder="请输入当事人姓名"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">优先级</label>
            <div className="flex gap-2">
              {[
                { value: 0, label: '普通' },
                { value: 1, label: '紧急' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setPriority(opt.value)}
                  className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors ${
                    priority === opt.value
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-300 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {createMutation.error && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
              {(createMutation.error as Error).message}
            </div>
          )}
        </div>

        <div className="flex gap-3 border-t px-6 py-4">
          <Button variant="outline" fullWidth onClick={onClose}>取消</Button>
          <Button
            variant="primary"
            fullWidth
            onClick={handleSubmit}
            disabled={!isFormValid}
            isLoading={createMutation.isPending}
          >
            创建案件
          </Button>
        </div>
      </div>
    </div>
  );
}