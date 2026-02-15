/**
 * useGenerateQRCode - 二维码生成逻辑 Hook
 */

import { useState, useCallback } from 'react';

// QRCode 模块类型定义
interface QRCodeModule {
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

interface QRCodeOptions {
  /** 二维码宽度 */
  width?: number;
  /** 边距 */
  margin?: number;
  /** 前景色 */
  color?: {
    dark?: string;
    light?: string;
  };
  /** 错误纠正级别 */
  errorCorrectionLevel?: 'L' | 'M' | 'Q' | 'H';
}

interface UseGenerateQRCodeResult {
  /** SVG 字符串 */
  svgString: string;
  /** 数据 URL */
  dataUrl: string;
  /** 是否正在生成 */
  isGenerating: boolean;
  /** 错误信息 */
  error: string | null;
  /** 生成 SVG */
  generateSVG: (value: string, options?: QRCodeOptions) => Promise<string>;
  /** 生成 Data URL */
  generateDataURL: (value: string, options?: QRCodeOptions) => Promise<string>;
  /** 清除错误 */
  clearError: () => void;
}

/**
 * 二维码生成 Hook
 * @returns 二维码生成方法和状态
 */
export function useGenerateQRCode(): UseGenerateQRCodeResult {
  const [svgString, setSvgString] = useState<string>('');
  const [dataUrl, setDataUrl] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * 生成 SVG 格式二维码
   */
  const generateSVG = useCallback(async (value: string, options: QRCodeOptions = {}): Promise<string> => {
    if (!value) {
      setError('二维码内容不能为空');
      return '';
    }

    setIsGenerating(true);
    setError(null);

    try {
      // 动态导入 qrcode 库
      const QRCode = (await import('qrcode')) as unknown as QRCodeModule;

      const svg = await QRCode.toString(value, {
        type: 'svg',
        width: options.width || 200,
        margin: options.margin || 2,
        color: {
          dark: options.color?.dark || '#000000',
          light: options.color?.light || '#FFFFFF',
        },
        errorCorrectionLevel: options.errorCorrectionLevel || 'M',
      });

      setSvgString(svg);
      setIsGenerating(false);
      return svg;
    } catch (err) {
      const errorMsg = '生成二维码失败';
      setError(errorMsg);
      setIsGenerating(false);
      console.error('QR Code generation error:', err);
      return '';
    }
  }, []);

  /**
   * 生成 Data URL 格式二维码
   */
  const generateDataURL = useCallback(async (value: string, options: QRCodeOptions = {}): Promise<string> => {
    if (!value) {
      setError('二维码内容不能为空');
      return '';
    }

    setIsGenerating(true);
    setError(null);

    try {
      const QRCode = (await import('qrcode')) as unknown as QRCodeModule;

      const url = await QRCode.toDataURL(value, {
        width: options.width || 200,
        margin: options.margin || 2,
        color: {
          dark: options.color?.dark || '#000000',
          light: options.color?.light || '#FFFFFF',
        },
        errorCorrectionLevel: options.errorCorrectionLevel || 'M',
      });

      setDataUrl(url);
      setIsGenerating(false);
      return url;
    } catch (err) {
      const errorMsg = '生成二维码失败';
      setError(errorMsg);
      setIsGenerating(false);
      console.error('QR Code generation error:', err);
      return '';
    }
  }, []);

  /**
   * 清除错误
   */
  const clearError = useCallback((): void => {
    setError(null);
  }, []);

  return {
    svgString,
    dataUrl,
    isGenerating,
    error,
    generateSVG,
    generateDataURL,
    clearError,
  };
}

/**
 * 生成带 Logo 的二维码
 * 注意：需要在 Canvas 上绘制，返回 Data URL
 */
export function useGenerateQRCodeWithLogo(): {
  isGenerating: boolean;
  error: string | null;
  generateWithLogo: (value: string, logoUrl: string, options?: QRCodeOptions) => Promise<string>;
  clearError: () => void;
} {
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * 生成带 Logo 的二维码
   */
  const generateWithLogo = useCallback(
    async (value: string, logoUrl: string, options: QRCodeOptions = {}): Promise<string> => {
      if (!value) {
        setError('二维码内容不能为空');
        return '';
      }

      setIsGenerating(true);
      setError(null);

      try {
        const QRCode = (await import('qrcode')) as unknown as QRCodeModule;

        // 生成基础二维码
        const dataUrl = await QRCode.toDataURL(value, {
          width: options.width || 200,
          margin: options.margin || 2,
          color: {
            dark: options.color?.dark || '#000000',
            light: options.color?.light || '#FFFFFF',
          },
          errorCorrectionLevel: 'H', // 使用高级别纠错以支持 logo
        });

        // 创建 Canvas
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          throw new Error('无法创建 canvas 上下文');
        }

        const size = options.width || 200;
        canvas.width = size;
        canvas.height = size;

        // 绘制二维码
        const qrImage = new Image();
        qrImage.crossOrigin = 'anonymous';

        await new Promise<void>((resolve, reject) => {
          qrImage.onload = () => resolve();
          qrImage.onerror = () => reject(new Error('二维码图片加载失败'));
          qrImage.src = dataUrl;
        });

        ctx.drawImage(qrImage, 0, 0, size, size);

        // 绘制 Logo
        if (logoUrl) {
          const logo = new Image();
          logo.crossOrigin = 'anonymous';

          await new Promise<void>((resolve, reject) => {
            logo.onload = () => resolve();
            logo.onerror = () => reject(new Error('Logo 图片加载失败'));
            logo.src = logoUrl;
          });

          const logoSize = size * 0.2;
          const logoX = (size - logoSize) / 2;
          const logoY = (size - logoSize) / 2;

          // 绘制白色背景
          ctx.fillStyle = options.color?.light || '#FFFFFF';
          ctx.fillRect(logoX - 4, logoY - 4, logoSize + 8, logoSize + 8);

          // 绘制 logo
          ctx.drawImage(logo, logoX, logoY, logoSize, logoSize);
        }

        const result = canvas.toDataURL('image/png');
        setIsGenerating(false);
        return result;
      } catch (err) {
        const errorMsg = '生成带 Logo 二维码失败';
        setError(errorMsg);
        setIsGenerating(false);
        console.error('QR Code with logo generation error:', err);
        return '';
      }
    },
    []
  );

  /**
   * 清除错误
   */
  const clearError = useCallback((): void => {
    setError(null);
  }, []);

  return {
    isGenerating,
    error,
    generateWithLogo,
    clearError,
  };
}