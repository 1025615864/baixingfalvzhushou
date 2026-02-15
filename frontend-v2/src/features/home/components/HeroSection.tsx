/**
 * HeroSection 组件 - 首页横幅
 * 美化后的Hero区域，带有动态背景和更好的视觉效果
 */

import { Link } from 'react-router-dom';
import { ChevronRight, Sparkles, Shield, Zap } from 'lucide-react';

import { Button } from '@/components/ui/Button';

import type { HomeBanner } from '../types';

interface HeroSectionProps {
  banners: HomeBanner[];
  isLoading?: boolean;
}

export function HeroSection({ banners, isLoading = false }: HeroSectionProps): JSX.Element {
  // 获取第一个激活的横幅
  const activeBanner = banners.find((banner) => banner.isActive) ?? banners[0];

  if (isLoading) {
    return (
      <section className="relative w-full min-h-[500px] bg-gradient-hero py-20 md:py-32 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse text-center">
            <div className="h-12 bg-white/10 rounded-2xl w-3/4 mx-auto mb-6" />
            <div className="h-6 bg-white/10 rounded-xl w-1/2 mx-auto mb-4" />
            <div className="h-6 bg-white/10 rounded-xl w-2/3 mx-auto mb-10" />
            <div className="h-14 bg-white/10 rounded-xl w-48 mx-auto" />
          </div>
        </div>
      </section>
    );
  }

  // 默认横幅内容
  const defaultContent = {
    title: '您的AI法律助手',
    subtitle: '专业、高效、可信赖',
    description: '百姓助手利用先进的人工智能技术，为您提供24小时在线法律咨询服务，让法律问题变得简单易懂',
    buttonText: '立即咨询',
    buttonLink: '/chat',
    secondaryButtonText: '了解更多',
    secondaryButtonLink: '/knowledge',
  };

  const content = {
    ...defaultContent,
    ...(activeBanner || {}),
  };

  return (
    <section className="relative w-full min-h-[600px] bg-gradient-hero py-20 md:py-32 overflow-hidden">
      {/* 背景装饰 */}
      <div className="absolute inset-0 overflow-hidden">
        {/* 网格图案 */}
        <div 
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />
        
        {/* 渐变光晕 */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-secondary-500/20 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary-600/10 rounded-full blur-3xl" />
        
        {/* 浮动元素 */}
        <div className="absolute top-20 right-20 w-20 h-20 bg-white/5 rounded-2xl rotate-12 animate-float hidden lg:block" />
        <div className="absolute bottom-32 left-20 w-16 h-16 bg-white/5 rounded-xl -rotate-12 animate-float hidden lg:block" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/3 right-1/4 w-12 h-12 bg-secondary-400/20 rounded-lg rotate-45 animate-float hidden lg:block" style={{ animationDelay: '0.5s' }} />
      </div>

      {/* 背景图片 */}
      {activeBanner?.imageUrl && (
        <div
          className="absolute inset-0 bg-cover bg-center opacity-10"
          style={{ backgroundImage: `url(${activeBanner.imageUrl})` }}
        />
      )}

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-4xl mx-auto">
          {/* 标签 */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full border border-white/20 mb-8 animate-fade-in-up">
            <Sparkles className="w-4 h-4 text-accent-400" />
            <span className="text-sm font-medium text-white/90">AI 驱动的法律服务平台</span>
          </div>

          {/* 主标题 */}
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
            {content.title}
            <span className="block mt-2 bg-clip-text text-transparent bg-gradient-to-r from-accent-300 to-accent-400">
              {content.subtitle || '专业法律服务触手可及'}
            </span>
          </h1>

          {/* 描述 */}
          <p className="text-lg md:text-xl text-white/70 mb-10 max-w-2xl mx-auto leading-relaxed animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
            {content.description || defaultContent.description}
          </p>

          {/* 按钮组 */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
            <Link to={content.buttonLink || defaultContent.buttonLink}>
              <Button 
                variant="white" 
                size="lg"
                rightIcon={<ChevronRight className="w-5 h-5" />}
                className="shadow-xl shadow-black/20"
              >
                {content.buttonText || defaultContent.buttonText}
              </Button>
            </Link>
            <Link to={content.secondaryButtonLink || defaultContent.secondaryButtonLink}>
              <Button 
                variant="outline" 
                size="lg"
                className="border-white/30 text-white hover:bg-white/10 hover:border-white/50"
              >
                {content.secondaryButtonText || defaultContent.secondaryButtonText}
              </Button>
            </Link>
          </div>

          {/* 特性标签 */}
          <div className="flex flex-wrap items-center justify-center gap-6 mt-12 animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
            <div className="flex items-center gap-2 text-white/60">
              <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-accent-400" />
              </div>
              <span className="text-sm">即时响应</span>
            </div>
            <div className="flex items-center gap-2 text-white/60">
              <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center">
                <Shield className="w-4 h-4 text-secondary-400" />
              </div>
              <span className="text-sm">隐私保护</span>
            </div>
            <div className="flex items-center gap-2 text-white/60">
              <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center">
                <svg className="w-4 h-4 text-primary-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <span className="text-sm">专业可靠</span>
            </div>
          </div>
        </div>
      </div>

      {/* 底部渐变过渡 */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-slate-50 to-transparent" />
    </section>
  );
}
