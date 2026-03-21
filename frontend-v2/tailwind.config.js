/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 主色调 - 深海蓝（专业、权威、可信赖）- 象征法律的庄重
        primary: {
          50: '#eef4ff',
          100: '#d9e8ff',
          200: '#bcd4ff',
          300: '#8eb8ff',
          400: '#5990ff',
          500: '#3366ff',
          600: '#1a44f5',
          700: '#1433e1',
          800: '#172cb6',
          900: '#192b8f',
          950: '#141c57',
        },
        // 辅助色 - 翠绿色（公正、希望、生机）- 象征法律的公正
        secondary: {
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
          800: '#065f46',
          900: '#064e3b',
          950: '#022c22',
        },
        // 强调色 - 中国红（力量、权威、正义）- 象征法律的力量
        accent: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#dc2626',
          600: '#b91c1c',
          700: '#991b1b',
          800: '#7f1d1d',
          900: '#6b1c1c',
          950: '#450a0a',
        },
        // 金色 - 尊贵、高端（VIP、专业服务）
        gold: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#d4a017',
          600: '#b8860b',
          700: '#92400e',
          800: '#78350f',
          900: '#6b3a0f',
          950: '#422006',
        },
        // 中性色 - slate 灰
        slate: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
        // 语义色
        success: {
          50: '#f0fdf4',
          500: '#22c55e',
          600: '#16a34a',
        },
        warning: {
          50: '#fffbeb',
          500: '#f59e0b',
          600: '#d97706',
        },
        error: {
          50: '#fef2f2',
          500: '#ef4444',
          600: '#dc2626',
        },
        info: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
        },
      },
      fontFamily: {
        // 中文字体栈 - 优先使用思源黑体，保证中文显示效果
        sans: [
          'Noto Sans SC',
          'PingFang SC',
          'Microsoft YaHei',
          'Hiragino Sans GB',
          'WenQuanYi Micro Hei',
          'Inter',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'sans-serif',
        ],
        // 标题字体 - 更具力量感
        heading: [
          'Noto Serif SC',
          'Source Han Serif SC',
          'SimSun',
          'Noto Sans SC',
          'serif',
        ],
        // 等宽字体
        mono: [
          'JetBrains Mono',
          'Fira Code',
          'Source Code Pro',
          'Consolas',
          'monospace',
        ],
      },
      fontSize: {
        'display': ['4rem', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '700' }],
        'display-sm': ['3rem', { lineHeight: '1.15', letterSpacing: '-0.02em', fontWeight: '700' }],
        'title': ['2.5rem', { lineHeight: '1.2', letterSpacing: '-0.01em', fontWeight: '600' }],
        'title-sm': ['2rem', { lineHeight: '1.25', letterSpacing: '-0.01em', fontWeight: '600' }],
        'subtitle': ['1.5rem', { lineHeight: '1.35', fontWeight: '500' }],
        'subtitle-sm': ['1.25rem', { lineHeight: '1.4', fontWeight: '500' }],
        'body': ['1rem', { lineHeight: '1.6' }],
        'body-sm': ['0.875rem', { lineHeight: '1.5' }],
        'caption': ['0.75rem', { lineHeight: '1.4' }],
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '88': '22rem',
        '100': '25rem',
        '128': '32rem',
      },
      borderRadius: {
        'sm': '0.25rem',
        'md': '0.5rem',
        'lg': '0.75rem',
        'xl': '1rem',
        '2xl': '1.25rem',
        '3xl': '1.5rem',
        '4xl': '2rem',
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.05), 0 10px 20px -2px rgba(0, 0, 0, 0.03)',
        'soft-md': '0 4px 25px -5px rgba(0, 0, 0, 0.08), 0 10px 25px -5px rgba(0, 0, 0, 0.04)',
        'soft-lg': '0 10px 40px -10px rgba(0, 0, 0, 0.1), 0 20px 40px -10px rgba(0, 0, 0, 0.05)',
        'soft-xl': '0 20px 50px -15px rgba(0, 0, 0, 0.15)',
        'glow': '0 0 20px rgba(51, 102, 255, 0.25)',
        'glow-lg': '0 0 40px rgba(51, 102, 255, 0.35)',
        'glow-gold': '0 0 20px rgba(212, 160, 23, 0.3)',
        'inner-light': 'inset 0 2px 4px 0 rgba(255, 255, 255, 0.1)',
        'card': '0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.06)',
        'card-hover': '0 4px 12px rgba(0, 0, 0, 0.08), 0 12px 28px rgba(0, 0, 0, 0.1)',
        'navbar': '0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.1)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'fade-in-up': 'fadeInUp 0.6s ease-out',
        'fade-in-down': 'fadeInDown 0.4s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
        'bounce-soft': 'bounceSoft 2s infinite',
        'pulse-soft': 'pulseSoft 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 3s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'spin-slow': 'spin 3s linear infinite',
        'ping-slow': 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
        'gradient': 'gradient 8s ease infinite',
        'wave': 'wave 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(30px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInDown: {
          '0%': { opacity: '0', transform: 'translateY(-20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        bounceSoft: {
          '0%, 100%': { transform: 'translateY(-5%)' },
          '50%': { transform: 'translateY(0)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        wave: {
          '0%, 100%': { transform: 'rotate(-3deg)' },
          '50%': { transform: 'rotate(3deg)' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'shimmer': 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)',
        // 法律主题渐变
        'gradient-hero': 'linear-gradient(135deg, #1433e1 0%, #1a44f5 50%, #3366ff 100%)',
        'gradient-hero-dark': 'linear-gradient(135deg, #141c57 0%, #172c72 50%, #1433e1 100%)',
        'gradient-trust': 'linear-gradient(135deg, #047857 0%, #10b981 50%, #34d399 100%)',
        'gradient-gold': 'linear-gradient(135deg, #92400e 0%, #d4a017 50%, #fbbf24 100%)',
        'gradient-justice': 'linear-gradient(135deg, #1433e1 0%, #047857 100%)',
        // 网格和图案
        'grid-pattern': 'linear-gradient(to right, rgba(51, 102, 255, 0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(51, 102, 255, 0.05) 1px, transparent 1px)',
        'dot-pattern': 'radial-gradient(circle, rgba(51, 102, 255, 0.1) 1px, transparent 1px)',
      },
      backgroundSize: {
        'grid-sm': '20px 20px',
        'grid-md': '40px 40px',
        'grid-lg': '60px 60px',
      },
      transitionTimingFunction: {
        'bounce-out': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'spring': 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
      },
      // 自定义毛玻璃效果
      backdropBlur: {
        xs: '2px',
      },
      // 自定义内容宽度
      maxWidth: {
        '8xl': '88rem',
        '9xl': '96rem',
        'content': '1280px',
      },
    },
  },
  plugins: [
    function({ addComponents, addUtilities, theme }) {
      addComponents({
        // 按钮基础样式
        '.btn': {
          '@apply inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed': {},
        },
        '.btn-primary': {
          '@apply btn bg-primary-600 text-white hover:bg-primary-700 hover:shadow-lg hover:shadow-primary-500/25 focus:ring-primary-500 active:scale-[0.98]': {},
        },
        '.btn-secondary': {
          '@apply btn bg-secondary-500 text-white hover:bg-secondary-600 hover:shadow-lg hover:shadow-secondary-500/25 focus:ring-secondary-500 active:scale-[0.98]': {},
        },
        '.btn-accent': {
          '@apply btn bg-accent-500 text-white hover:bg-accent-600 hover:shadow-lg hover:shadow-accent-500/25 focus:ring-accent-500 active:scale-[0.98]': {},
        },
        '.btn-gold': {
          '@apply btn bg-gold-500 text-white hover:bg-gold-600 hover:shadow-lg hover:shadow-gold-500/25 focus:ring-gold-500 active:scale-[0.98]': {},
        },
        '.btn-outline': {
          '@apply btn border-2 border-primary-600 text-primary-600 hover:bg-primary-50 focus:ring-primary-500 active:scale-[0.98]': {},
        },
        '.btn-ghost': {
          '@apply btn text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus:ring-slate-500': {},
        },
        '.btn-white': {
          '@apply btn bg-white text-primary-600 hover:bg-primary-50 focus:ring-white shadow-lg active:scale-[0.98]': {},
        },

        // 卡片样式
        '.card': {
          '@apply bg-white rounded-2xl shadow-card border border-slate-100/80 overflow-hidden transition-all duration-300': {},
        },
        '.card-hover': {
          '@apply card hover:shadow-card-hover hover:-translate-y-1 hover:border-primary-100': {},
        },
        '.card-interactive': {
          '@apply card-hover cursor-pointer active:scale-[0.99]': {},
        },

        // 输入框样式
        '.input': {
          '@apply w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 hover:border-slate-300': {},
        },
        '.input-error': {
          '@apply input border-red-300 focus:ring-red-500/20 focus:border-red-500': {},
        },
        '.input-success': {
          '@apply input border-green-300 focus:ring-green-500/20 focus:border-green-500': {},
        },

        // 标签样式
        '.badge': {
          '@apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium': {},
        },
        '.badge-primary': {
          '@apply badge bg-primary-100 text-primary-700': {},
        },
        '.badge-secondary': {
          '@apply badge bg-secondary-100 text-secondary-700': {},
        },
        '.badge-accent': {
          '@apply badge bg-accent-100 text-accent-700': {},
        },
        '.badge-gold': {
          '@apply badge bg-gold-100 text-gold-700': {},
        },
        '.badge-success': {
          '@apply badge bg-green-100 text-green-700': {},
        },
        '.badge-warning': {
          '@apply badge bg-yellow-100 text-yellow-700': {},
        },
        '.badge-error': {
          '@apply badge bg-red-100 text-red-700': {},
        },

        // 玻璃态效果
        '.glass': {
          '@apply bg-white/80 backdrop-blur-xl border border-white/20': {},
        },
        '.glass-dark': {
          '@apply bg-slate-900/80 backdrop-blur-xl border border-white/10': {},
        },
        '.glass-primary': {
          '@apply bg-primary-600/80 backdrop-blur-xl border border-primary-400/20': {},
        },

        // 导航链接样式
        '.nav-link': {
          '@apply relative text-slate-600 hover:text-primary-600 transition-colors font-medium py-2 px-1': {},
        },
        '.nav-link-active': {
          '@apply text-primary-600 font-semibold': {},
        },

        // 分割线
        '.divider': {
          '@apply h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent': {},
        },
        '.divider-vertical': {
          '@apply w-px bg-gradient-to-b from-transparent via-slate-200 to-transparent': {},
        },

        // 骨架屏
        '.skeleton': {
          '@apply bg-slate-200 animate-pulse rounded': {},
        },
        '.skeleton-shimmer': {
          '@apply bg-gradient-to-r from-slate-200 via-slate-100 to-slate-200 bg-[length:200%_100%] animate-shimmer': {},
        },

        // 法律相关特殊组件
        '.trust-badge': {
          '@apply inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary-50 text-primary-700 rounded-full text-sm font-medium border border-primary-100': {},
        },
        '.verified-badge': {
          '@apply inline-flex items-center gap-1 px-2 py-0.5 bg-green-50 text-green-700 rounded-full text-xs font-medium': {},
        },
        '.lawyer-badge': {
          '@apply inline-flex items-center gap-1.5 px-3 py-1 bg-gold-50 text-gold-700 rounded-lg text-sm font-medium border border-gold-200': {},
        },
      });

      addUtilities({
        // 文字渐变
        '.text-gradient': {
          '@apply bg-clip-text text-transparent bg-gradient-to-r from-primary-600 to-secondary-500': {},
        },
        '.text-gradient-gold': {
          '@apply bg-clip-text text-transparent bg-gradient-to-r from-gold-500 to-gold-600': {},
        },
        '.text-gradient-primary': {
          '@apply bg-clip-text text-transparent bg-gradient-to-br from-primary-500 to-primary-700': {},
        },

        // 背景渐变
        '.bg-gradient-primary': {
          '@apply bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800': {},
        },
        '.bg-gradient-secondary': {
          '@apply bg-gradient-to-br from-secondary-500 via-secondary-600 to-secondary-700': {},
        },
        '.bg-gradient-hero': {
          'background': 'linear-gradient(135deg, #1433e1 0%, #1a44f5 50%, #3366ff 100%)',
        },
        '.bg-gradient-trust': {
          'background': 'linear-gradient(135deg, #047857 0%, #10b981 50%, #34d399 100%)',
        },

        // 聚焦环
        '.ring-focus': {
          '@apply focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:ring-offset-2': {},
        },

        // 悬停效果
        '.hover-lift': {
          '@apply transition-all duration-300 hover:-translate-y-1 hover:shadow-card-hover': {},
        },
        '.hover-scale': {
          '@apply transition-transform duration-300 hover:scale-105': {},
        },
        '.hover-glow': {
          '@apply transition-shadow duration-300 hover:shadow-glow': {},
        },
        '.hover-brightness': {
          '@apply transition-all duration-200 hover:brightness-110': {},
        },

        // 文字截断
        '.line-clamp-1': {
          display: '-webkit-box',
          '-webkit-line-clamp': '1',
          '-webkit-box-orient': 'vertical',
          overflow: 'hidden',
        },
        '.line-clamp-2': {
          display: '-webkit-box',
          '-webkit-line-clamp': '2',
          '-webkit-box-orient': 'vertical',
          overflow: 'hidden',
        },
        '.line-clamp-3': {
          display: '-webkit-box',
          '-webkit-line-clamp': '3',
          '-webkit-box-orient': 'vertical',
          overflow: 'hidden',
        },

        // 网格背景
        '.bg-grid': {
          'background-image': 'linear-gradient(to right, rgba(51, 102, 255, 0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(51, 102, 255, 0.05) 1px, transparent 1px)',
          'background-size': '40px 40px',
        },
        '.bg-dots': {
          'background-image': 'radial-gradient(circle, rgba(51, 102, 255, 0.1) 1px, transparent 1px)',
          'background-size': '20px 20px',
        },

        // 动画延迟
        '.delay-100': { animationDelay: '100ms' },
        '.delay-200': { animationDelay: '200ms' },
        '.delay-300': { animationDelay: '300ms' },
        '.delay-400': { animationDelay: '400ms' },
        '.delay-500': { animationDelay: '500ms' },
        '.delay-600': { animationDelay: '600ms' },
        '.delay-700': { animationDelay: '700ms' },
        '.delay-800': { animationDelay: '800ms' },
      });
    },
  ],
};
