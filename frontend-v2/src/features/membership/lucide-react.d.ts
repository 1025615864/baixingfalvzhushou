/**
 * lucide-react 类型声明
 * 由于该依赖未安装，临时添加类型声明
 */

declare module 'lucide-react' {
  import type { FC, SVGProps } from 'react';

  export interface LucideProps extends SVGProps<SVGSVGElement> {
    size?: number | string;
    color?: string;
    strokeWidth?: number | string;
  }

  export type LucideIcon = FC<LucideProps>;

  export const Check: LucideIcon;
  export const X: LucideIcon;
  export const MessageSquare: LucideIcon;
  export const FileText: LucideIcon;
  export const Headphones: LucideIcon;
  export const Wand2: LucideIcon;
  export const Code: LucideIcon;
  export const Palette: LucideIcon;
  export const Crown: LucideIcon;
  export const Sparkles: LucideIcon;
  export const Zap: LucideIcon;
  export const Building2: LucideIcon;
  export const Star: LucideIcon;
}