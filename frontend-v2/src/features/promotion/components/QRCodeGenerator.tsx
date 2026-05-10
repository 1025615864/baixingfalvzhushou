/**
 * QRCodeGenerator - 二维码生成器组件
 * 功能：动态生成二维码、支持下载 PNG/SVG、分享文案生成
 * 使用 qrcode 库
 */

import { logger } from '@/shared/lib/logger';
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';

// QRCode 模块类型定义
export interface QRCodeModule {
  toString: (
    value: string,
    options?: {
      type?: 'svg' | 'terminal' | 'utf8';
      width?: number;
      margin?: number;
      color?: { dark?: string; light?: string };
      errorCorrectionLevel?: 'L' | 'M' | 'Q' | 'H';
    }
  ) => Promise<string>;
  toDataURL: (
    value: string,
    options?: {
      type?: 'image/png' | 'image/jpeg' | 'image/webp';
      width?: number;
      margin?: number;
      color?: { dark?: string; light?: string };
      errorCorrectionLevel?: 'L' | 'M' | 'Q' | 'H';
    }
  ) => Promise<string>;
}

interface QRCodeGeneratorProps {
  /** 二维码内容（URL或文本） */
  value: string;
  /** 二维码尺寸 */
  size?: number;
  /** 前景色 */
  fgColor?: string;
  /** 背景色 */
  bgColor?: string;
  /** 错误纠正级别 */
  level?: 'L' | 'M' | 'Q' | 'H';
  /** 是否包含logo */
  includeLogo?: boolean;
  /** logo URL */
  logoUrl?: string;
  /** 标题 */
  title?: string;
  /** 描述 */
  description?: string;
  className?: string;
  onDownload?: (format: 'png' | 'svg') => void;
}

/**
 * 二维码生成器组件
 * 注意：实际项目中需要安装 qrcode 库
 * npm install qrcode
 */
export function QRCodeGenerator({
  value,
  size = 200,
  fgColor = '#000000',
  bgColor = '#FFFFFF',
  level = 'M',
  includeLogo = false,
  logoUrl,
  title,
  description,
  className = '',
  onDownload,
}: QRCodeGeneratorProps): JSX.Element {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [svgString, setSvgString] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  /**
   * 生成二维码 SVG
   */
  const generateQRSvg = useCallback(async () => {
    if (!value) return;

    setIsGenerating(true);
    setError(null);

    try {
      // 动态导入 qrcode 库
      const QRCode = (await import('qrcode')) as unknown as QRCodeModule;
      
      // 生成 SVG
      const svg = await QRCode.toString(value, {
        type: 'svg',
        width: size,
        margin: 2,
        color: {
          dark: fgColor,
          light: bgColor,
        },
        errorCorrectionLevel: level,
      });
      
      setSvgString(svg);
    } catch (err) {
      setError('生成二维码失败');
      logger.error('QR Code generation error:', err);
    } finally {
      setIsGenerating(false);
    }
  }, [value, size, fgColor, bgColor, level]);

  /**
   * 绘制带 Logo 的二维码到 Canvas
   */
  const drawQRWithLogo = useCallback(async () => {
    if (!canvasRef.current || !value) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    setIsGenerating(true);
    setError(null);

    try {
      const QRCode = (await import('qrcode')) as unknown as QRCodeModule;
      
      // 生成数据 URL
      const dataUrl = await QRCode.toDataURL(value, {
        width: size,
        margin: 2,
        color: {
          dark: fgColor,
          light: bgColor,
        },
        errorCorrectionLevel: 'H', // 使用高级别纠错以支持 logo
      });

      // 加载二维码图片
      const qrImage = new Image();
      qrImage.crossOrigin = 'anonymous';
      
      await new Promise<void>((resolve, reject) => {
        qrImage.onload = () => resolve();
        qrImage.onerror = () => reject(new Error('Failed to load QR code'));
        qrImage.src = dataUrl;
      });

      // 设置 canvas 尺寸
      canvas.width = size;
      canvas.height = size;

      // 绘制二维码
      ctx.drawImage(qrImage, 0, 0, size, size);

      // 绘制 logo
      if (includeLogo && logoUrl) {
        const logo = new Image();
        logo.crossOrigin = 'anonymous';
        
        await new Promise<void>((resolve, reject) => {
          logo.onload = () => resolve();
          logo.onerror = () => reject(new Error('Failed to load logo'));
          logo.src = logoUrl;
        });

        const logoSize = size * 0.2;
        const logoX = (size - logoSize) / 2;
        const logoY = (size - logoSize) / 2;

        // 绘制白色背景
        ctx.fillStyle = bgColor;
        ctx.fillRect(logoX - 4, logoY - 4, logoSize + 8, logoSize + 8);

        // 绘制 logo
        ctx.drawImage(logo, logoX, logoY, logoSize, logoSize);
      }

      setIsGenerating(false);
    } catch (err) {
      setError('生成二维码失败');
      setIsGenerating(false);
      logger.error('QR Code generation error:', err);
    }
  }, [value, size, fgColor, bgColor, includeLogo, logoUrl]);

  // 初始生成
  useEffect(() => {
    if (includeLogo) {
      void drawQRWithLogo();
    } else {
      void generateQRSvg();
    }
  }, [includeLogo, drawQRWithLogo, generateQRSvg]);

  /**
   * 下载 PNG
   */
  const downloadPNG = useCallback(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const link = document.createElement('a');
    link.download = `qrcode-${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
    onDownload?.('png');
  }, [onDownload]);

  /**
   * 下载 SVG
   */
  const downloadSVG = useCallback(() => {
    if (!svgString) return;

    const blob = new Blob([svgString], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.download = `qrcode-${Date.now()}.svg`;
    link.href = url;
    link.click();
    URL.revokeObjectURL(url);
    onDownload?.('svg');
  }, [svgString, onDownload]);

  /**
   * 复制链接
   */
  const copyLink = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // 复制失败
    }
  }, [value]);

  /**
   * 分享文案
   */
  const shareText = useMemo(() => {
    return `${title || '推荐给您'}\n${description || '扫描二维码了解更多'}\n${value}`;
  }, [title, description, value]);

  /**
   * 复制分享文案
   */
  const copyShareText = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(shareText);
      alert('分享文案已复制到剪贴板');
    } catch {
      // 复制失败
    }
  }, [shareText]);

  if (error) {
    return (
      <div className={`p-6 bg-red-50 rounded-xl text-center ${className}`}>
        <div className="text-red-500 mb-2">
          <svg className="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="text-red-600">{error}</p>
        <button
          onClick={() => { void (includeLogo ? drawQRWithLogo() : generateQRSvg()); }}
          className="mt-4 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl shadow-lg p-6 ${className}`}>
      {/* 标题和描述 */}
      {(title || description) && (
        <div className="text-center mb-6">
          {title && <h3 className="text-lg font-bold text-gray-900">{title}</h3>}
          {description && <p className="text-sm text-gray-500 mt-1">{description}</p>}
        </div>
      )}

      {/* 二维码显示区域 */}
      <div className="flex justify-center mb-6">
        <div 
          className="relative p-4 bg-white rounded-xl shadow-inner"
          style={{ backgroundColor: bgColor }}
        >
          {isGenerating ? (
            <div 
              className="flex items-center justify-center bg-gray-100 rounded-lg"
              style={{ width: size, height: size }}
            >
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
            </div>
          ) : includeLogo ? (
            <canvas
              ref={canvasRef}
              className="rounded-lg"
              style={{ maxWidth: '100%', height: 'auto' }}
            />
          ) : (
            <div 
              className="rounded-lg overflow-hidden"
              dangerouslySetInnerHTML={{ __html: svgString }}
              style={{ width: size, height: size }}
            />
          )}
          
          {/* Logo 叠加层 */}
          {includeLogo && !isGenerating && logoUrl && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="w-12 h-12 bg-white rounded-full shadow-md flex items-center justify-center">
                <img src={logoUrl} alt="Logo" className="w-8 h-8 object-contain" />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 链接显示 */}
      <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg mb-4">
        <input
          type="text"
          value={value}
          readOnly
          className="flex-1 bg-transparent text-sm text-gray-600 outline-none"
        />
        <button
          onClick={() => void copyLink()}
          className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
            copied 
              ? 'bg-green-100 text-green-700' 
              : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
          }`}
        >
          {copied ? '已复制' : '复制'}
        </button>
      </div>

      {/* 操作按钮 */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={downloadPNG}
          disabled={isGenerating || !svgString}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          下载 PNG
        </button>
        
        <button
          onClick={downloadSVG}
          disabled={isGenerating || !svgString}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
          </svg>
          下载 SVG
        </button>
      </div>

      {/* 分享按钮 */}
      <button
        onClick={() => void copyShareText()}
        className="w-full mt-3 flex items-center justify-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
        </svg>
        复制分享文案
      </button>

      {/* 提示信息 */}
      <div className="mt-4 p-3 bg-amber-50 rounded-lg text-xs text-amber-700">
        <p className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          提示：使用 PNG 格式可直接分享，SVG 格式适合打印
        </p>
      </div>
    </div>
  );
}

/**
 * 简化的二维码显示组件
 */
interface QRCodeDisplayProps {
  value: string;
  size?: number;
  className?: string;
}

export function QRCodeDisplay({ value, size = 150, className = '' }: QRCodeDisplayProps): JSX.Element {
  const [svgString, setSvgString] = useState<string>('');

  useEffect(() => {
    const generateQR = async () => {
      try {
        const QRCode = (await import('qrcode')) as unknown as QRCodeModule;
        const svg = await QRCode.toString(value, {
          type: 'svg',
          width: size,
          margin: 1,
        });
        setSvgString(svg);
      } catch (err) {
        logger.error('Failed to generate QR code:', err);
      }
    };

    void generateQR();
  }, [value, size]);

  return (
    <div 
      className={`inline-block ${className}`}
      dangerouslySetInnerHTML={{ __html: svgString }}
      style={{ width: size, height: size }}
    />
  );
}