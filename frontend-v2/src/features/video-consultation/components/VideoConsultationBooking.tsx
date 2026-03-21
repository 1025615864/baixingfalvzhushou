/**
 * VideoConsultationBooking - 视频咨询预约组件
 * 包含选择律师、选择时段、显示会员折扣价格
 */

import { useState } from 'react';
import {
  User,
  Video,
  Tag,
  AlertCircle,
  CheckCircle,
  ArrowLeft,
  Crown,
} from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

import {
  useCreateVideoConsultation,
  useLawyerVideoFee,
  useMemberDiscount,
  useMyUsage,
} from '../hooks/useVideoConsultation';
import type { VideoSlot, CreateVideoConsultationRequest } from '../types';

import { LawyerSchedulePicker } from './LawyerSchedulePicker';

// 咨询类别选项
const CATEGORY_OPTIONS = [
  { value: 'civil', label: '民事咨询' },
  { value: 'criminal', label: '刑事咨询' },
  { value: 'contract', label: '合同纠纷' },
  { value: 'labor', label: '劳动争议' },
  { value: 'family', label: '婚姻家庭' },
  { value: 'property', label: '房产纠纷' },
  { value: 'intellectual', label: '知识产权' },
  { value: 'corporate', label: '公司法务' },
  { value: 'other', label: '其他咨询' },
];

interface VideoConsultationBookingProps {
  lawyerId: number;
  lawyerName?: string;
  lawyerAvatar?: string;
  lawyerSpecialty?: string;
  onSuccess?: (consultationId: string) => void;
  onCancel?: () => void;
}

export function VideoConsultationBooking({
  lawyerId,
  lawyerName = '律师',
  lawyerAvatar,
  lawyerSpecialty,
  onSuccess,
  onCancel,
}: VideoConsultationBookingProps): JSX.Element {
  // 表单状态
  const [selectedSlot, setSelectedSlot] = useState<VideoSlot | null>(null);
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');

  // 获取数据
  const { data: feeData, isLoading: feeLoading } = useLawyerVideoFee(lawyerId);
  const { data: memberDiscount } = useMemberDiscount();
  const { data: usageData } = useMyUsage();

  // 创建预约
  const createMutation = useCreateVideoConsultation();

  // 计算费用
  const baseFee = feeData?.fee ?? 0;
  const duration = feeData?.duration ?? 30;
  const discountRate = memberDiscount?.discountRate ?? 1;
  const isFree = memberDiscount?.isFree ?? false;
  const hasFreeQuota = (usageData?.remainingFree ?? 0) > 0;

  // 最终费用
  const finalFee = isFree || hasFreeQuota ? 0 : baseFee * discountRate;

  // 表单验证
  const isFormValid = selectedSlot && subject.trim().length >= 2;

  // 提交表单
  const handleSubmit = (): void => {
    if (!isFormValid || !selectedSlot) return;

    const scheduledTime = `${selectedSlot.date}T${selectedSlot.startTime}:00`;

    const request: CreateVideoConsultationRequest = {
      lawyerId,
      subject: subject.trim(),
      description: description.trim() || undefined,
      category: category || undefined,
      scheduledTime,
    };

    createMutation.mutate(request, {
      onSuccess: (result) => {
        onSuccess?.(result.id);
      },
    });
  };

  return (
    <div className="space-y-6">
      {/* 律师信息 */}
      <Card padding="md" className="bg-gradient-to-r from-primary-50 to-white">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center overflow-hidden">
            {lawyerAvatar ? (
              <img
                src={lawyerAvatar}
                alt={lawyerName}
                className="w-full h-full object-cover"
              />
            ) : (
              <User className="w-8 h-8 text-primary-600" />
            )}
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">{lawyerName}</h3>
            {lawyerSpecialty && (
              <p className="text-sm text-gray-500 mt-0.5">{lawyerSpecialty}</p>
            )}
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="primary" size="sm">
                <Video className="w-3 h-3 mr-1" />
                视频咨询
              </Badge>
              {!feeLoading && (
                <span className="text-sm text-gray-500">
                  咨询时长: {duration}分钟
                </span>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* 会员优惠信息 */}
      {memberDiscount && (
        <Card padding="md" className="bg-amber-50 border-amber-200">
          <div className="flex items-start gap-3">
            <Crown className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-amber-800">
                {memberDiscount.tier}会员专享
              </p>
              {isFree || hasFreeQuota ? (
                <p className="text-sm text-amber-600 mt-1">
                  本月剩余 {usageData?.remainingFree ?? 0} 次免费视频咨询
                </p>
              ) : (
                <p className="text-sm text-amber-600 mt-1">
                  享受 {Math.round(discountRate * 10)} 折优惠，原价 ¥{baseFee}，现价 ¥
                  {(baseFee * discountRate).toFixed(0)}
                </p>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* 时段选择 */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
          <Tag className="w-4 h-4 mr-2" />
          选择咨询时段
        </h4>
        <LawyerSchedulePicker
          lawyerId={lawyerId}
          selectedSlot={selectedSlot ?? undefined}
          onSlotSelect={setSelectedSlot}
        />
      </div>

      {/* 咨询信息表单 */}
      <Card padding="md">
        <h4 className="text-sm font-medium text-gray-700 mb-4 flex items-center">
          <AlertCircle className="w-4 h-4 mr-2" />
          咨询信息
        </h4>

        <div className="space-y-4">
          {/* 咨询主题 */}
          <div>
            <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-1">
              咨询主题 <span className="text-red-500">*</span>
            </label>
            <input
              id="subject"
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="请简要描述您要咨询的问题"
              maxLength={100}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all"
            />
            <p className="text-xs text-gray-400 mt-1">{subject.length}/100</p>
          </div>

          {/* 咨询类别 */}
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
              咨询类别
            </label>
            <select
              id="category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all"
            >
              <option value="">请选择类别</option>
              {CATEGORY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* 详细描述 */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              详细描述
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="请详细描述您的问题，以便律师更好地为您服务（选填）"
              rows={4}
              maxLength={500}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-all resize-none"
            />
            <p className="text-xs text-gray-400 mt-1">{description.length}/500</p>
          </div>
        </div>
      </Card>

      {/* 费用明细 */}
      <Card padding="md" className="bg-gray-50">
        <h4 className="text-sm font-medium text-gray-700 mb-3">费用明细</h4>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">基础费用</span>
            <span className="text-gray-900">¥{baseFee}</span>
          </div>
          {(isFree || hasFreeQuota) && (
            <div className="flex justify-between text-sm">
              <span className="text-green-600">会员免费</span>
              <span className="text-green-600">-¥{baseFee}</span>
            </div>
          )}
          {!isFree && !hasFreeQuota && discountRate < 1 && (
            <div className="flex justify-between text-sm">
              <span className="text-green-600">会员折扣 ({Math.round(discountRate * 10)}折)</span>
              <span className="text-green-600">
                -¥{(baseFee - baseFee * discountRate).toFixed(0)}
              </span>
            </div>
          )}
          <div className="border-t border-gray-200 pt-2 mt-2">
            <div className="flex justify-between">
              <span className="font-medium text-gray-900">应付金额</span>
              <span className="text-lg font-bold text-primary-600">
                {finalFee === 0 ? '免费' : `¥${finalFee.toFixed(0)}`}
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* 操作按钮 */}
      <div className="flex gap-3">
        {onCancel && (
          <Button
            variant="outline"
            fullWidth
            onClick={onCancel}
            leftIcon={<ArrowLeft className="w-4 h-4" />}
          >
            返回
          </Button>
        )}
        <Button
          variant="primary"
          fullWidth
          onClick={handleSubmit}
          disabled={!isFormValid}
          isLoading={createMutation.isPending}
          leftIcon={<CheckCircle className="w-4 h-4" />}
        >
          确认预约
        </Button>
      </div>

      {/* 提示信息 */}
      <div className="text-xs text-gray-400 text-center space-y-1">
        <p>• 预约成功后，请按时进入视频咨询房间</p>
        <p>• 如需取消，请提前1小时操作</p>
        <p>• 咨询过程中请保持网络稳定</p>
      </div>
    </div>
  );
}