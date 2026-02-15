/**
 * ChannelForm 组件 - 渠道表单
 */

import { useState, useEffect } from 'react';

import type { Channel, ChannelType, ChannelStatus, CreateChannelRequest, LandingConfig, OfferConfig, TrackingConfig } from '../types';

interface ChannelFormProps {
  channel?: Channel;
  onSubmit: (data: CreateChannelRequest) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const CHANNEL_TYPES: { value: ChannelType; label: string }[] = [
  { value: 'weixin', label: '微信' },
  { value: 'douyin', label: '抖音' },
  { value: 'xiaohongshu', label: '小红书' },
  { value: 'zhihu', label: '知乎' },
  { value: 'bilibili', label: 'B站' },
  { value: 'website', label: '官网' },
  { value: 'other', label: '其他' },
];

const CHANNEL_STATUSES: { value: ChannelStatus; label: string }[] = [
  { value: 'active', label: '启用' },
  { value: 'inactive', label: '停用' },
];

function Input({
  label,
  value,
  onChange,
  placeholder,
  required = false,
  type = 'text',
  disabled = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  type?: string;
  disabled?: boolean;
}): JSX.Element {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
      />
    </div>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  required?: boolean;
}): JSX.Element {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function TextArea({
  label,
  value,
  onChange,
  placeholder,
  rows = 3,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
}): JSX.Element {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      />
    </div>
  );
}

export function ChannelForm({
  channel,
  onSubmit,
  onCancel,
  isLoading = false,
}: ChannelFormProps): JSX.Element {
  // 基本信息
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<ChannelType>('weixin');
  const [status, setStatus] = useState<ChannelStatus>('active');

  // 落地页配置
  const [landingTitle, setLandingTitle] = useState('');
  const [landingSubtitle, setLandingSubtitle] = useState('');
  const [heroBgColor, setHeroBgColor] = useState('#07c160');
  const [welcomeMessage, setWelcomeMessage] = useState('');
  const [ctaText, setCtaText] = useState('');

  // 优惠配置
  const [offerTitle, setOfferTitle] = useState('');
  const [offerDescription, setOfferDescription] = useState('');
  const [discountAmount, setDiscountAmount] = useState(0);
  const [discountType, setDiscountType] = useState<'fixed' | 'percentage'>('fixed');
  const [promoCode, setPromoCode] = useState('');

  // 追踪配置
  const [attributionWindow, setAttributionWindow] = useState(30);
  const [enableTracking, setEnableTracking] = useState(true);

  const isEditMode = !!channel;

  // 初始化表单数据
  useEffect(() => {
    if (channel) {
      setName(channel.name);
      setSlug(channel.slug);
      setDescription(channel.description || '');
      setType(channel.type);
      setStatus(channel.status);

      if (channel.landingConfig) {
        setLandingTitle(channel.landingConfig.title);
        setLandingSubtitle(channel.landingConfig.subtitle);
        setHeroBgColor(channel.landingConfig.heroBackgroundColor);
        setWelcomeMessage(channel.landingConfig.welcomeMessage);
        setCtaText(channel.landingConfig.ctaText);
      }

      if (channel.offerConfig) {
        setOfferTitle(channel.offerConfig.title);
        setOfferDescription(channel.offerConfig.description);
        setDiscountAmount(channel.offerConfig.discountAmount);
        setDiscountType(channel.offerConfig.discountType);
        setPromoCode(channel.offerConfig.promoCode);
      }

      if (channel.trackingConfig) {
        setAttributionWindow(channel.trackingConfig.attributionWindow);
        setEnableTracking(channel.trackingConfig.enableTracking);
      }
    }
  }, [channel]);

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();

    const landingConfig: LandingConfig = {
      title: landingTitle || `${name} - 您的法律顾问`,
      subtitle: landingSubtitle || '专业、高效、贴心的法律服务',
      heroBackgroundColor: heroBgColor,
      welcomeMessage: welcomeMessage || `欢迎使用 ${name}`,
      ctaText: ctaText || '立即咨询',
      features: [
        { id: '1', title: '专业律师', description: '超1000名执业律师在线' },
        { id: '2', title: '价格透明', description: '费用公开透明，无隐形消费' },
        { id: '3', title: '响应快速', description: '平均响应时间小于5分钟' },
      ],
      guidanceSteps: [
        { id: '1', step: 1, title: '注册登录', description: '使用手机号快速注册', actionType: 'register' },
        { id: '2', step: 2, title: '选择服务', description: '选择您需要的法律咨询服务', actionType: 'consult' },
        { id: '3', step: 3, title: '完成咨询', description: '与律师在线沟通解决问题', actionType: 'register' },
      ],
    };

    const offerConfig: OfferConfig | undefined = offerTitle
      ? {
          id: `${slug}_offer`,
          title: offerTitle,
          description: offerDescription,
          discountAmount: discountAmount,
          discountType: discountType,
          promoCode: promoCode || slug.toUpperCase(),
          bannerStyle: discountType === 'percentage' ? 'primary' : 'gradient',
        }
      : undefined;

    const trackingConfig: TrackingConfig = {
      attributionWindow: attributionWindow,
      enableTracking: enableTracking,
    };

    const data: CreateChannelRequest = {
      name,
      slug,
      description: description || undefined,
      type,
      status,
      landingConfig,
      offerConfig,
      trackingConfig,
    };

    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* 基本信息 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">基本信息</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Input
            label="渠道名称"
            value={name}
            onChange={setName}
            placeholder="例如：微信公众号"
            required
          />
          <Input
            label="渠道标识"
            value={slug}
            onChange={setSlug}
            placeholder="例如：weixin"
            required
            disabled={isEditMode}
          />
          <Select
            label="渠道类型"
            value={type}
            onChange={(value) => setType(value as ChannelType)}
            options={CHANNEL_TYPES}
            required
          />
          <Select
            label="渠道状态"
            value={status}
            onChange={(value) => setStatus(value as ChannelStatus)}
            options={CHANNEL_STATUSES}
            required
          />
          <div className="md:col-span-2">
            <TextArea
              label="渠道描述"
              value={description}
              onChange={setDescription}
              placeholder="请输入渠道描述..."
            />
          </div>
        </div>
      </div>

      {/* 落地页配置 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">落地页配置</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Input
            label="页面标题"
            value={landingTitle}
            onChange={setLandingTitle}
            placeholder="例如：百姓助手 - 您的法律顾问"
          />
          <Input
            label="副标题"
            value={landingSubtitle}
            onChange={setLandingSubtitle}
            placeholder="例如：专业、高效、贴心的法律服务"
          />
          <Input
            label="主题色"
            value={heroBgColor}
            onChange={setHeroBgColor}
            type="color"
          />
          <Input
            label="欢迎语"
            value={welcomeMessage}
            onChange={setWelcomeMessage}
            placeholder="例如：您好！欢迎来到百姓助手"
          />
          <div className="md:col-span-2">
            <Input
              label="行动按钮文案"
              value={ctaText}
              onChange={setCtaText}
              placeholder="例如：立即咨询"
            />
          </div>
        </div>
      </div>

      {/* 优惠配置 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">优惠配置</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Input
            label="优惠标题"
            value={offerTitle}
            onChange={setOfferTitle}
            placeholder="例如：新用户专享优惠"
          />
          <Input
            label="优惠描述"
            value={offerDescription}
            onChange={setOfferDescription}
            placeholder="例如：首次咨询立减50元"
          />
          <Input
            label="优惠金额/比例"
            value={String(discountAmount)}
            onChange={(value) => setDiscountAmount(Number(value) || 0)}
            type="number"
          />
          <Select
            label="优惠类型"
            value={discountType}
            onChange={(value) => setDiscountType(value as 'fixed' | 'percentage')}
            options={[
              { value: 'fixed', label: '固定金额' },
              { value: 'percentage', label: '百分比' },
            ]}
          />
          <div className="md:col-span-2">
            <Input
              label="优惠码"
              value={promoCode}
              onChange={setPromoCode}
              placeholder="例如：WEIXIN50"
            />
          </div>
        </div>
      </div>

      {/* 追踪配置 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">追踪配置</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Input
            label="归因窗口（天）"
            value={String(attributionWindow)}
            onChange={(value) => setAttributionWindow(Number(value) || 30)}
            type="number"
          />
          <div className="flex items-center h-full pt-6">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={enableTracking}
                onChange={(e) => setEnableTracking(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">启用追踪</span>
            </label>
          </div>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center justify-end space-x-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-6 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          取消
        </button>
        <button
          type="submit"
          disabled={isLoading || !name || !slug}
          className="px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isLoading ? '保存中...' : isEditMode ? '保存修改' : '创建渠道'}
        </button>
      </div>
    </form>
  );
}