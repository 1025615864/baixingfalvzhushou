/**
 * 律师主页编辑器组件
 * 用于律师编辑和预览个人主页
 */

import React, { useState, useEffect } from 'react';

import type { CreateHomepageRequest, UpdateHomepageRequest } from '../types';
import { useMyHomepage, useCreateHomepage, useUpdateHomepage } from '../hooks/useHomepage';

interface HomepageEditorProps {
  onSaveSuccess?: () => void;
}

type TabType = 'basic' | 'content' | 'contact' | 'seo';

export const HomepageEditor: React.FC<HomepageEditorProps> = ({
  onSaveSuccess,
}) => {
  const { data: existingHomepage, isLoading } = useMyHomepage();
  const createMutation = useCreateHomepage();
  const updateMutation = useUpdateHomepage();

  const [activeTab, setActiveTab] = useState<TabType>('basic');
  const [formData, setFormData] = useState<CreateHomepageRequest & UpdateHomepageRequest>({
    bannerImage: '',
    profileImage: '',
    slogan: '',
    bio: '',
    specialtiesDisplay: '',
    achievements: '',
    education: '',
    serviceAreas: '',
    serviceHours: '',
    responseTime: '',
    contactPhone: '',
    contactEmail: '',
    wechatQrcode: '',
    weiboUrl: '',
    linkedinUrl: '',
    zhihuUrl: '',
    caseStudies: '',
    videoUrl: '',
    videoCover: '',
    seoTitle: '',
    seoDescription: '',
    seoKeywords: '',
    themeColor: '#3B82F6',
    backgroundColor: '#FFFFFF',
    isPublished: false,
  });

  // 加载现有数据
  useEffect(() => {
    if (existingHomepage) {
      setFormData({
        bannerImage: existingHomepage.bannerImage || '',
        profileImage: existingHomepage.profileImage || '',
        slogan: existingHomepage.slogan || '',
        bio: existingHomepage.bio || '',
        specialtiesDisplay: existingHomepage.specialtiesDisplay || '',
        achievements: existingHomepage.achievements || '',
        education: existingHomepage.education || '',
        serviceAreas: existingHomepage.serviceAreas || '',
        serviceHours: existingHomepage.serviceHours || '',
        responseTime: existingHomepage.responseTime || '',
        contactPhone: existingHomepage.contactPhone || '',
        contactEmail: existingHomepage.contactEmail || '',
        wechatQrcode: existingHomepage.wechatQrcode || '',
        weiboUrl: existingHomepage.weiboUrl || '',
        linkedinUrl: existingHomepage.linkedinUrl || '',
        zhihuUrl: existingHomepage.zhihuUrl || '',
        caseStudies: existingHomepage.caseStudies || '',
        videoUrl: existingHomepage.videoUrl || '',
        videoCover: existingHomepage.videoCover || '',
        seoTitle: existingHomepage.seoTitle || '',
        seoDescription: existingHomepage.seoDescription || '',
        seoKeywords: existingHomepage.seoKeywords || '',
        themeColor: existingHomepage.themeColor || '#3B82F6',
        backgroundColor: existingHomepage.backgroundColor || '#FFFFFF',
        isPublished: existingHomepage.isPublished,
      });
    }
  }, [existingHomepage]);

  const handleChange = (field: keyof typeof formData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    if (existingHomepage) {
      void updateMutation.mutateAsync(formData).then(() => {
        onSaveSuccess?.();
      });
    } else {
      void createMutation.mutateAsync(formData).then(() => {
        onSaveSuccess?.();
      });
    }
  };

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
    );
  }

  const tabs: { id: TabType; label: string }[] = [
    { id: 'basic', label: '基本信息' },
    { id: 'content', label: '内容展示' },
    { id: 'contact', label: '联系方式' },
    { id: 'seo', label: 'SEO设置' },
  ];

  return (
    <div className="bg-white shadow rounded-lg">
      {/* Tab 导航 */}
      <div className="border-b border-gray-200">
        <nav className="flex -mb-px" aria-label="Tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                w-1/4 py-4 px-1 text-center border-b-2 font-medium text-sm
                ${activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* 表单内容 */}
      <div className="p-6 space-y-6">
        {activeTab === 'basic' && (
          <div className="space-y-6">
            {/* 横幅图片 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                主页横幅
              </label>
              <div className="mt-1 flex items-center">
                <input
                  type="text"
                  value={formData.bannerImage}
                  onChange={e => handleChange('bannerImage', e.target.value)}
                  placeholder="输入图片URL"
                  className="flex-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
              </div>
            </div>

            {/* 个人形象照 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                个人形象照
              </label>
              <div className="mt-1 flex items-center">
                <input
                  type="text"
                  value={formData.profileImage}
                  onChange={e => handleChange('profileImage', e.target.value)}
                  placeholder="输入图片URL"
                  className="flex-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
              </div>
            </div>

            {/* 个人标语 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                个人标语
              </label>
              <input
                type="text"
                value={formData.slogan}
                onChange={e => handleChange('slogan', e.target.value)}
                placeholder="例如：专业、高效、值得信赖"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            {/* 主题颜色 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  主题颜色
                </label>
                <div className="mt-1 flex items-center space-x-2">
                  <input
                    type="color"
                    value={formData.themeColor}
                    onChange={e => handleChange('themeColor', e.target.value)}
                    className="h-10 w-20 rounded border border-gray-300"
                  />
                  <input
                    type="text"
                    value={formData.themeColor}
                    onChange={e => handleChange('themeColor', e.target.value)}
                    className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  背景颜色
                </label>
                <div className="mt-1 flex items-center space-x-2">
                  <input
                    type="color"
                    value={formData.backgroundColor}
                    onChange={e => handleChange('backgroundColor', e.target.value)}
                    className="h-10 w-20 rounded border border-gray-300"
                  />
                  <input
                    type="text"
                    value={formData.backgroundColor}
                    onChange={e => handleChange('backgroundColor', e.target.value)}
                    className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'content' && (
          <div className="space-y-6">
            {/* 个人简介 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                个人简介
              </label>
              <textarea
                value={formData.bio}
                onChange={e => handleChange('bio', e.target.value)}
                rows={4}
                placeholder="详细介绍您的执业经历、专业特长等"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            {/* 擅长领域 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                擅长领域
              </label>
              <textarea
                value={formData.specialtiesDisplay}
                onChange={e => handleChange('specialtiesDisplay', e.target.value)}
                rows={3}
                placeholder="列出您擅长的法律领域"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            {/* 成就荣誉 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                成就荣誉
              </label>
              <textarea
                value={formData.achievements}
                onChange={e => handleChange('achievements', e.target.value)}
                rows={3}
                placeholder="展示您的重要成就和荣誉"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            {/* 教育背景 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                教育背景
              </label>
              <textarea
                value={formData.education}
                onChange={e => handleChange('education', e.target.value)}
                rows={3}
                placeholder="您的教育经历"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            {/* 案例展示 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                案例展示
              </label>
              <textarea
                value={formData.caseStudies}
                onChange={e => handleChange('caseStudies', e.target.value)}
                rows={4}
                placeholder="展示您的成功案例"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>
          </div>
        )}

        {activeTab === 'contact' && (
          <div className="space-y-6">
            {/* 服务时间 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                服务时间
              </label>
              <input
                type="text"
                value={formData.serviceHours}
                onChange={e => handleChange('serviceHours', e.target.value)}
                placeholder="例如：周一至周五 9:00-18:00"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            {/* 响应时间承诺 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                响应时间承诺
              </label>
              <input
                type="text"
                value={formData.responseTime}
                onChange={e => handleChange('responseTime', e.target.value)}
                placeholder="例如：2小时内响应"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            {/* 联系电话 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                联系电话
              </label>
              <input
                type="tel"
                value={formData.contactPhone}
                onChange={e => handleChange('contactPhone', e.target.value)}
                placeholder="客户联系您的电话号码"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            {/* 联系邮箱 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                联系邮箱
              </label>
              <input
                type="email"
                value={formData.contactEmail}
                onChange={e => handleChange('contactEmail', e.target.value)}
                placeholder="您的电子邮箱"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            {/* 微信二维码 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                微信二维码
              </label>
              <input
                type="text"
                value={formData.wechatQrcode}
                onChange={e => handleChange('wechatQrcode', e.target.value)}
                placeholder="微信二维码图片URL"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            {/* 社交媒体链接 */}
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  微博链接
                </label>
                <input
                  type="url"
                  value={formData.weiboUrl}
                  onChange={e => handleChange('weiboUrl', e.target.value)}
                  placeholder="https://weibo.com/..."
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  LinkedIn链接
                </label>
                <input
                  type="url"
                  value={formData.linkedinUrl}
                  onChange={e => handleChange('linkedinUrl', e.target.value)}
                  placeholder="https://linkedin.com/in/..."
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  知乎链接
                </label>
                <input
                  type="url"
                  value={formData.zhihuUrl}
                  onChange={e => handleChange('zhihuUrl', e.target.value)}
                  placeholder="https://zhihu.com/people/..."
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'seo' && (
          <div className="space-y-6">
            {/* SEO标题 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                SEO标题
              </label>
              <input
                type="text"
                value={formData.seoTitle}
                onChange={e => handleChange('seoTitle', e.target.value)}
                placeholder="网页标题，显示在搜索引擎结果中"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">建议长度：30-60个字符</p>
            </div>

            {/* SEO描述 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                SEO描述
              </label>
              <textarea
                value={formData.seoDescription}
                onChange={e => handleChange('seoDescription', e.target.value)}
                rows={3}
                placeholder="网页描述，显示在搜索引擎结果中"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">建议长度：80-160个字符</p>
            </div>

            {/* SEO关键词 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                SEO关键词
              </label>
              <input
                type="text"
                value={formData.seoKeywords}
                onChange={e => handleChange('seoKeywords', e.target.value)}
                placeholder="关键词1, 关键词2, 关键词3"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">多个关键词用逗号分隔</p>
            </div>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex justify-end space-x-3 pt-6 border-t">
          <button
            type="button"
            onClick={() => handleChange('isPublished', !formData.isPublished)}
            className={`px-4 py-2 border rounded-md shadow-sm text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 ${
              formData.isPublished
                ? 'border-green-300 text-green-700 bg-green-50 hover:bg-green-100 focus:ring-green-500'
                : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50 focus:ring-blue-500'
            }`}
          >
            {formData.isPublished ? '已发布' : '保存为草稿'}
          </button>

          <button
            type="button"
            onClick={handleSave}
            disabled={createMutation.isPending || updateMutation.isPending}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {createMutation.isPending || updateMutation.isPending
              ? '保存中...'
              : existingHomepage
                ? '更新主页'
                : '创建主页'}
          </button>
        </div>

        {/* 错误提示 */}
        {(createMutation.isError || updateMutation.isError) && (
          <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  {(createMutation.error || updateMutation.error)?.message || '保存失败，请重试'}
                </h3>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HomepageEditor;