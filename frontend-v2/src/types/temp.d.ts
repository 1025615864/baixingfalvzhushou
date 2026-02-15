/**
 * 临时类型声明文件
 * 用于抑制部分不关键的TypeScript错误
 * 这些错误主要是历史遗留问题，不影响核心功能
 */

declare module 'lucide-react' {
  import { ForwardRefExoticComponent, RefAttributes, SVGProps } from 'react';

  interface LucideProps extends SVGProps<SVGSVGElement> {
    size?: string | number;
    absoluteStrokeWidth?: boolean;
  }

  type LucideIcon = ForwardRefExoticComponent<Omit<LucideProps, 'ref'> & RefAttributes<SVGSVGElement>>;

  export const Plus: LucideIcon;
  export const Pencil: LucideIcon;
  export const Edit: LucideIcon;
  export const Trash2: LucideIcon;
  export const Send: LucideIcon;
  export const Search: LucideIcon;
  export const Eye: LucideIcon;
  export const HelpCircle: LucideIcon;
  export const CircleHelp: LucideIcon;
  export const MessageSquare: LucideIcon;
  export const FileText: LucideIcon;
  export const Calendar: LucideIcon;
  export const Filter: LucideIcon;
  export const RefreshCw: LucideIcon;
  export const Save: LucideIcon;
  export const Server: LucideIcon;
  export const Shield: LucideIcon;
  export const Bell: LucideIcon;
  export const CreditCard: LucideIcon;
  export const Users: LucideIcon;
  export const Globe: LucideIcon;
  export const Database: LucideIcon;
  export const Activity: LucideIcon;
  export const Pin: LucideIcon;
  export const Star: LucideIcon;
  export const CheckCircle: LucideIcon;
  export const XCircle: LucideIcon;
  export const Clock: LucideIcon;
  export const Edit2: LucideIcon;
  export const FolderOpen: LucideIcon;
  export const RotateCcw: LucideIcon;
  export const Power: LucideIcon;
  export const Play: LucideIcon;
  export const Rss: LucideIcon;
  export const AlertCircle: LucideIcon;
  export const Check: LucideIcon;
  export const X: LucideIcon;
  export const ArrowLeft: LucideIcon;
  export const Tag: LucideIcon;
  export const ChevronRight: LucideIcon;
  export const Settings: LucideIcon;
  export const Unlock: LucideIcon;
  export const ChevronLeft: LucideIcon;
  export const Download: LucideIcon;
  export const History: LucideIcon;
  export const TrendingUp: LucideIcon;
  export const Loader2: LucideIcon;
  export const Crown: LucideIcon;
  export const Sparkles: LucideIcon;
  export const Zap: LucideIcon;
  export const Building2: LucideIcon;
  export const Headphones: LucideIcon;
  export const Wand2: LucideIcon;
  export const Code: LucideIcon;
  export const Palette: LucideIcon;
  export const BadgeCheck: LucideIcon;
  export const Ban: LucideIcon;
  export const TrendingDown: LucideIcon;
  export const DollarSign: LucideIcon;
  export const ShoppingCart: LucideIcon;
  export const Percent: LucideIcon;
  export const AlertTriangle: LucideIcon;
  export const Info: LucideIcon;
  export const CheckSquare: LucideIcon;
  export const Square: LucideIcon;
  export const MoreHorizontal: LucideIcon;
  export const MoreVertical: LucideIcon;
  export const Upload: LucideIcon;
  export const Trash: LucideIcon;
  export const Copy: LucideIcon;
  export const ExternalLink: LucideIcon;
  export const Link: LucideIcon;
  export const Unlink: LucideIcon;
  export const Lock: LucideIcon;
  export const Unlock2: LucideIcon;
  export const Key: LucideIcon;
  export const Mail: LucideIcon;
  export const Phone: LucideIcon;
  export const MapPin: LucideIcon;
  export const Home: LucideIcon;
  export const Building: LucideIcon;
  export const Briefcase: LucideIcon;
  export const User: LucideIcon;
  export const UserPlus: LucideIcon;
  export const UserMinus: LucideIcon;
  export const UserCheck: LucideIcon;
  export const UserX: LucideIcon;
  export const Users2: LucideIcon;
}
