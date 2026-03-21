/**
 * AvatarUpload - 头像上传组件
 * 支持图片预览、裁剪和上传
 */

import { useState, useRef } from 'react';
import { Camera, Upload, X } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { useToast } from '@/components/ui/useToast';

interface AvatarUploadProps {
  currentAvatar?: string;
  onAvatarChange: (avatarUrl: string) => void;
  disabled?: boolean;
}

export function AvatarUpload({
  currentAvatar,
  onAvatarChange,
  disabled = false,
}: AvatarUploadProps): JSX.Element {
  const toast = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>): void => {
    const file = event.target.files?.[0];
    if (!file) return;

    // 验证文件类型
    if (!file.type.startsWith('image/')) {
      toast.error('请选择图片文件');
      return;
    }

    // 验证文件大小（最大 5MB）
    if (file.size > 5 * 1024 * 1024) {
      toast.error('图片大小不能超过 5MB');
      return;
    }

    setIsUploading(true);

    // 创建预览 URL
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);

    // 读取文件并转换为 base64
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      onAvatarChange(result);
      toast.success('头像已更新');
      setIsUploading(false);
    };
    reader.onerror = () => {
      toast.error('读取图片失败');
      URL.revokeObjectURL(objectUrl);
      setPreviewUrl(null);
      setIsUploading(false);
    };
    reader.readAsDataURL(file);

    // 重置 input 值，允许重复选择同一文件
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemove = (): void => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    onAvatarChange('');
    toast.success('头像已移除');
  };

  const displayAvatar = previewUrl || currentAvatar;

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative group">
        <div className="w-32 h-32 rounded-full overflow-hidden bg-gray-100 border-4 border-white shadow-lg">
          {displayAvatar ? (
            <img
              src={displayAvatar}
              alt="头像"
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400">
              <Camera className="w-12 h-12" />
            </div>
          )}
        </div>

        {!disabled && (
          <>
            {/* 上传按钮覆盖层 */}
            <div className="absolute inset-0 bg-black/50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer">
              <Upload className="w-8 h-8 text-white" />
            </div>

            {/* 移除按钮 */}
            {displayAvatar && (
              <button
                onClick={handleRemove}
                className="absolute top-0 right-0 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-lg"
                type="button"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </>
        )}
      </div>

      {!disabled && (
        <>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
            disabled={isUploading}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            leftIcon={<Upload className="w-4 h-4" />}
          >
            {isUploading ? '上传中...' : '更换头像'}
          </Button>
          <p className="text-xs text-gray-500">
            支持 JPG、PNG 格式，最大 5MB
          </p>
        </>
      )}
    </div>
  );
}
