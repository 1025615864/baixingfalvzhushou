/**
 * UserProfilePage - 用户资料页面
 * 
 * 功能：用户基本信息展示和编辑、头像上传、个人简介
 */

import { useState, useEffect } from 'react';
import { User, MapPin, Building2, Link as LinkIcon, Briefcase } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input, Textarea } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/components/ui/useToast';

import type { UpdateProfileDTO } from '../types';
import { AvatarUpload } from '../components/AvatarUpload';
import { useUserProfile, useUpdateProfile } from '../hooks/useUserProfile';

/**
 * 用户资料编辑表单
 */
export function UserProfilePage(): JSX.Element {
  const toast = useToast();
  const { data: profile, isLoading, error } = useUserProfile();
  const updateProfile = useUpdateProfile();

  const [formData, setFormData] = useState<UpdateProfileDTO>({
    nickname: '',
    bio: '',
    location: '',
    company: '',
    title: '',
    website: '',
  });

  // 加载用户数据时填充表单
  useEffect(() => {
    if (profile) {
      setFormData({
        nickname: profile.name || '',
        bio: profile.bio || '',
        location: profile.location || '',
        company: profile.company || '',
        title: profile.title || '',
        website: profile.website || '',
      });
    }
  }, [profile]);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ): void => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleAvatarChange = (): void => {
    // 头像更新由 AvatarUpload 组件内部处理
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();

    try {
      await updateProfile.mutateAsync(formData);
      toast.success('个人资料已更新');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '更新失败');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-red-500 mb-4">加载用户资料失败</p>
              <Button variant="primary" onClick={() => window.location.reload()}>
                重新加载
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">个人资料</h1>
        <p className="text-gray-500 mt-1">管理您的个人信息和头像</p>
      </div>

      <div className="grid gap-6">
        {/* 头像卡片 */}
        <Card>
          <CardHeader>
            <CardTitle>头像</CardTitle>
          </CardHeader>
          <CardContent>
            <AvatarUpload
              currentAvatar={profile?.avatar ?? undefined}
              onAvatarChange={handleAvatarChange}
            />
          </CardContent>
        </Card>

        {/* 基本信息卡片 */}
        <Card>
          <CardHeader>
            <CardTitle>基本信息</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={(e) => void handleSubmit(e)} className="space-y-6">
              {/* 昵称 */}
              <Input
                label="昵称"
                name="nickname"
                value={formData.nickname}
                onChange={handleInputChange}
                placeholder="请输入您的昵称"
                leftIcon={<User className="w-5 h-5" />}
              />

              {/* 个人简介 */}
              <Textarea
                label="个人简介"
                name="bio"
                value={formData.bio}
                onChange={handleInputChange}
                placeholder="介绍一下自己..."
                rows={4}
              />

              {/* 所在地 */}
              <Input
                label="所在地"
                name="location"
                value={formData.location}
                onChange={handleInputChange}
                placeholder="例如：北京市"
                leftIcon={<MapPin className="w-5 h-5" />}
              />

              {/* 公司和职位 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="公司"
                  name="company"
                  value={formData.company}
                  onChange={handleInputChange}
                  placeholder="您所在的公司"
                  leftIcon={<Building2 className="w-5 h-5" />}
                />
                <Input
                  label="职位"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  placeholder="您的职位"
                  leftIcon={<Briefcase className="w-5 h-5" />}
                />
              </div>

              {/* 个人网站 */}
              <Input
                label="个人网站"
                name="website"
                value={formData.website}
                onChange={handleInputChange}
                placeholder="https://example.com"
                leftIcon={<LinkIcon className="w-5 h-5" />}
              />

              {/* 提交按钮 */}
              <div className="flex justify-end pt-4">
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={updateProfile.isPending}
                  disabled={updateProfile.isPending}
                >
                  {updateProfile.isPending ? '保存中...' : '保存更改'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* 账户信息卡片 */}
        <Card>
          <CardHeader>
            <CardTitle>账户信息</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-4">
              <div className="flex justify-between py-2 border-b border-gray-100">
                <dt className="text-gray-500">用户名</dt>
                <dd className="text-gray-900 font-medium">{profile?.name}</dd>
              </div>
              <div className="flex justify-between py-2 border-b border-gray-100">
                <dt className="text-gray-500">邮箱</dt>
                <dd className="text-gray-900">{profile?.email}</dd>
              </div>
              {profile?.phone && (
                <div className="flex justify-between py-2 border-b border-gray-100">
                  <dt className="text-gray-500">手机号</dt>
                  <dd className="text-gray-900">{profile.phone}</dd>
                </div>
              )}
              <div className="flex justify-between py-2">
                <dt className="text-gray-500">注册时间</dt>
                <dd className="text-gray-900">
                  {profile?.createdAt
                    ? new Date(profile.createdAt).toLocaleDateString('zh-CN')
                    : '-'}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default UserProfilePage;
