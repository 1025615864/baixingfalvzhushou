/**
 * lucide-react 类型声明扩展
 * 为项目中使用的图标添加类型定义
 */

declare module 'lucide-react' {
  import type { FC, SVGProps } from 'react';

  export interface LucideProps extends SVGProps<SVGSVGElement> {
    size?: number | string;
    color?: string;
    strokeWidth?: number | string;
  }

  export type LucideIcon = FC<LucideProps>;

  // 基础图标
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
  export const Gift: LucideIcon;
  export const Landmark: LucideIcon;
  export const Settings: LucideIcon;
  
  // 视频相关
  export const Video: LucideIcon;
  export const VideoOff: LucideIcon;
  export const Mic: LucideIcon;
  export const MicOff: LucideIcon;
  export const Phone: LucideIcon;
  export const PhoneOff: LucideIcon;
  export const ScreenShare: LucideIcon;
  export const ScreenShareOff: LucideIcon;
  
  // UI 相关
  export const Maximize: LucideIcon;
  export const Minimize: LucideIcon;
  export const Maximize2: LucideIcon;
  export const Minimize2: LucideIcon;
  export const ZoomIn: LucideIcon;
  export const ZoomOut: LucideIcon;
  export const RotateCw: LucideIcon;
  export const RotateCcw: LucideIcon;
  export const Share: LucideIcon;
  export const Share2: LucideIcon;
  export const Sliders: LucideIcon;
  export const SlidersHorizontal: LucideIcon;
  
  // 箭头相关
  export const ChevronUp: LucideIcon;
  export const ChevronDown: LucideIcon;
  export const ChevronLeft: LucideIcon;
  export const ChevronRight: LucideIcon;
  export const ArrowUp: LucideIcon;
  export const ArrowDown: LucideIcon;
  export const ArrowLeft: LucideIcon;
  export const ArrowRight: LucideIcon;
  export const ArrowUpDown: LucideIcon;
  
  // 常用图标
  export const FileSignature: LucideIcon;
  export const AlignLeft: LucideIcon;
  export const Coins: LucideIcon;
  export const Minus: LucideIcon;
  export const Infinity: LucideIcon;
  export const Download: LucideIcon;
  export const Eye: LucideIcon;
  export const EyeOff: LucideIcon;
  export const Heart: LucideIcon;
  export const Tag: LucideIcon;
  export const Clock: LucideIcon;
  export const UserCheck: LucideIcon;
  export const AlertCircle: LucideIcon;
  export const CheckCircle: LucideIcon;
  export const Copy: LucideIcon;
  export const Printer: LucideIcon;
  export const Shield: LucideIcon;
  export const HelpCircle: LucideIcon;
  export const User: LucideIcon;
  export const Wifi: LucideIcon;
  export const WifiOff: LucideIcon;
  export const Volume2: LucideIcon;
  export const VolumeX: LucideIcon;
  export const Search: LucideIcon;
  export const Filter: LucideIcon;
  export const Grid: LucideIcon;
  export const List: LucideIcon;
  export const LayoutGrid: LucideIcon;
  export const CreditCard: LucideIcon;
  export const Loader2: LucideIcon;
  export const TrendingUp: LucideIcon;
  export const History: LucideIcon;
  export const Briefcase: LucideIcon;
  export const Home: LucideIcon;
  export const Users: LucideIcon;
  export const Building: LucideIcon;
  export const Car: LucideIcon;
  export const Scale: LucideIcon;
  export const Wallet: LucideIcon;
  export const Info: LucideIcon;
  
  // 额外图标
  export const BarChart3: LucideIcon;
  export const ListOrdered: LucideIcon;
  export const BookOpen: LucideIcon;
  export const Monitor: LucideIcon;
  export const Calculator: LucideIcon;
  export const Gavel: LucideIcon;
  export const Smile: LucideIcon;
  export const Bookmark: LucideIcon;
  export const Target: LucideIcon;
  export const ThumbsUp: LucideIcon;
  export const Award: LucideIcon;
  export const Lightbulb: LucideIcon;
  export const Camera: LucideIcon;
  export const Smartphone: LucideIcon;
  export const Moon: LucideIcon;
  export const Sun: LucideIcon;
  export const GraduationCap: LucideIcon;
}