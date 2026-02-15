/**
 * Avatar 组件
 * 用户头像组件，支持多种尺寸和状态
 */

import { User } from 'lucide-react';

export interface AvatarProps {
  src?: string;
  alt?: string;
  name?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  status?: 'online' | 'offline' | 'busy' | 'away';
  verified?: boolean;
  className?: string;
}

export function Avatar({
  src,
  alt,
  name,
  size = 'md',
  status,
  verified = false,
  className = '',
}: AvatarProps): JSX.Element {
  const sizeClasses = {
    xs: 'w-6 h-6 text-xs',
    sm: 'w-8 h-8 text-sm',
    md: 'w-10 h-10 text-base',
    lg: 'w-12 h-12 text-lg',
    xl: 'w-16 h-16 text-xl',
  };

  const statusColors = {
    online: 'bg-green-500',
    offline: 'bg-slate-400',
    busy: 'bg-red-500',
    away: 'bg-yellow-500',
  };

  const statusSizes = {
    xs: 'w-1.5 h-1.5',
    sm: 'w-2 h-2',
    md: 'w-2.5 h-2.5',
    lg: 'w-3 h-3',
    xl: 'w-4 h-4',
  };

  const getInitials = (name: string): string => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className={`relative inline-flex ${className}`}>
      <div
        className={`${sizeClasses[size]} rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center text-white font-semibold overflow-hidden shadow-md`}
      >
        {src ? (
          <img
            src={src}
            alt={alt || name || 'Avatar'}
            className="w-full h-full object-cover"
          />
        ) : name ? (
          <span>{getInitials(name)}</span>
        ) : (
          <User className="w-1/2 h-1/2" />
        )}
      </div>

      {/* 状态指示器 */}
      {status && (
        <span
          className={`absolute bottom-0 right-0 ${statusSizes[size]} ${statusColors[status]} rounded-full ring-2 ring-white`}
        />
      )}

      {/* 认证徽章 */}
      {verified && (
        <span className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-primary-600 rounded-full flex items-center justify-center ring-2 ring-white">
          <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        </span>
      )}
    </div>
  );
}

// 头像组
export interface AvatarGroupProps {
  avatars: Array<{
    src?: string;
    name?: string;
  }>;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function AvatarGroup({
  avatars,
  max = 4,
  size = 'md',
  className = '',
}: AvatarGroupProps): JSX.Element {
  const displayAvatars = avatars.slice(0, max);
  const remaining = avatars.length - max;

  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
  };

  const offsetClasses = {
    sm: '-ml-2',
    md: '-ml-3',
    lg: '-ml-4',
  };

  return (
    <div className={`flex items-center ${className}`}>
      {displayAvatars.map((avatar, index) => (
        <div
          key={index}
          className={`${index > 0 ? offsetClasses[size] : ''} ring-2 ring-white rounded-xl`}
        >
          <Avatar src={avatar.src} name={avatar.name} size={size} />
        </div>
      ))}
      {remaining > 0 && (
        <div
          className={`${offsetClasses[size]} ${sizeClasses[size]} rounded-xl bg-slate-100 flex items-center justify-center text-slate-600 font-medium ring-2 ring-white`}
        >
          +{remaining}
        </div>
      )}
    </div>
  );
}
