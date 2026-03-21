/**
 * 文书分类列表组件
 * 支持分类筛选、分类图标和数量显示
 */

import { useState, useMemo } from 'react';
import {
  FileText,
  Briefcase,
  Home,
  Users,
  Building,
  Car,
  Scale,
  FileSignature as FileSign,
  Landmark,
  Shield,
  ChevronDown as ChevronDownIcon,
  ChevronRight,
  Filter,
  Search,
  X,
} from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

import type { LegalDocumentCategory } from '../types';

// 分类图标映射
const CATEGORY_ICONS: Record<string, React.ElementType> = {
  // 民事类
  'civil': FileText,
  'contract': FileSign,
  'tort': Shield,
  // 商事类
  'business': Briefcase,
  'company': Building,
  // 劳动类
  'labor': Users,
  // 婚姻家庭
  'marriage': Home,
  'family': Home,
  // 房产建筑
  'real_estate': Building,
  'construction': Building,
  // 交通
  'traffic': Car,
  // 刑事
  'criminal': Scale,
  // 行政
  'administrative': Landmark,
  // 默认
  'default': FileText,
};

// 分类颜色映射
const CATEGORY_COLORS: Record<string, string> = {
  'civil': 'text-blue-600 bg-blue-50',
  'contract': 'text-indigo-600 bg-indigo-50',
  'business': 'text-purple-600 bg-purple-50',
  'labor': 'text-orange-600 bg-orange-50',
  'marriage': 'text-pink-600 bg-pink-50',
  'real_estate': 'text-teal-600 bg-teal-50',
  'traffic': 'text-amber-600 bg-amber-50',
  'criminal': 'text-red-600 bg-red-50',
  'administrative': 'text-green-600 bg-green-50',
  'default': 'text-gray-600 bg-gray-50',
};

// 分类统计信息类型
interface CategoryStats {
  key: string;
  name: string;
  count: number;
  icon: React.ElementType;
  color: string;
}

interface DocumentCategoryListProps {
  categories: LegalDocumentCategory[];
  selectedCategory: string | null;
  onSelectCategory: (category: string | null) => void;
  categoryCounts?: Record<string, number>;
  isLoading?: boolean;
  collapsible?: boolean;
  defaultExpanded?: boolean;
  showSearch?: boolean;
  showCounts?: boolean;
  className?: string;
}

/**
 * 分类列表项组件
 */
function CategoryItem({
  category,
  isSelected,
  count,
  onClick,
  showCounts,
}: {
  category: CategoryStats;
  isSelected: boolean;
  count: number;
  onClick: () => void;
  showCounts: boolean;
}) {
  const IconComponent = category.icon;
  const colorClass = category.color;

  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all duration-200 group ${
        isSelected
          ? 'bg-blue-50 text-blue-700 shadow-sm'
          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
      }`}
    >
      <span className={`p-2 rounded-lg ${colorClass} group-hover:scale-105 transition-transform`}>
        <IconComponent className="w-4 h-4" />
      </span>
      <span className="flex-1 text-sm font-medium truncate">{category.name}</span>
      {showCounts && count > 0 && (
        <Badge
          variant={isSelected ? 'primary' : 'default'}
          className={`text-xs ${isSelected ? 'bg-blue-600' : 'bg-gray-100 text-gray-600'}`}
        >
          {count > 99 ? '99+' : count}
        </Badge>
      )}
    </button>
  );
}

/**
 * 分类分组组件
 */
function CategoryGroup({
  groupName,
  categories,
  selectedCategory,
  categoryCounts,
  onSelectCategory,
  showCounts,
  isExpanded,
  onToggle,
}: {
  groupName: string;
  categories: CategoryStats[];
  selectedCategory: string | null;
  categoryCounts: Record<string, number>;
  onSelectCategory: (category: string | null) => void;
  showCounts: boolean;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const totalCount = categories.reduce((sum, cat) => sum + (categoryCounts[cat.key] || 0), 0);

  return (
    <div className="mb-4">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider hover:text-gray-600 transition-colors"
      >
        <span className="flex items-center gap-2">
          {groupName}
          {showCounts && totalCount > 0 && (
            <Badge variant="default" className="text-xs">
              {totalCount}
            </Badge>
          )}
        </span>
        {isExpanded ? (
          <ChevronDownIcon className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
      </button>
      {isExpanded && (
        <div className="mt-1 space-y-1">
          {categories.map((category) => (
            <CategoryItem
              key={category.key}
              category={category}
              isSelected={selectedCategory === category.key}
              count={categoryCounts[category.key] || 0}
              onClick={() => onSelectCategory(category.key)}
              showCounts={showCounts}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * 文书分类列表主组件
 */
export default function DocumentCategoryList({
  categories,
  selectedCategory,
  onSelectCategory,
  categoryCounts = {},
  isLoading = false,
  collapsible = true,
  defaultExpanded = true,
  showSearch = true,
  showCounts = true,
  className = '',
}: DocumentCategoryListProps) {
  const [searchKeyword, setSearchKeyword] = useState('');
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>(() => {
    if (defaultExpanded) {
      const initial: Record<string, boolean> = {};
      categories.forEach((group) => {
        initial[group.name] = true;
      });
      return initial;
    }
    return {};
  });

  // 处理分类数据，添加图标和颜色
  const processedCategories = useMemo(() => {
    return categories.map((group) => ({
      name: group.name,
      categories: group.categories.map((cat) => ({
        key: cat.key,
        name: cat.name,
        count: categoryCounts[cat.key] || 0,
        icon: CATEGORY_ICONS[cat.key] || CATEGORY_ICONS['default'],
        color: CATEGORY_COLORS[cat.key] || CATEGORY_COLORS['default'],
      })),
    }));
  }, [categories, categoryCounts]);

  // 根据搜索关键词过滤分类
  const filteredCategories = useMemo(() => {
    if (!searchKeyword.trim()) {
      return processedCategories;
    }
    const keyword = searchKeyword.toLowerCase();
    return processedCategories
      .map((group) => ({
        ...group,
        categories: group.categories.filter((cat) =>
          cat.name.toLowerCase().includes(keyword)
        ),
      }))
      .filter((group) => group.categories.length > 0);
  }, [processedCategories, searchKeyword]);

  // 切换分组展开状态
  const toggleGroup = (groupName: string) => {
    if (!collapsible) return;
    setExpandedGroups((prev) => ({
      ...prev,
      [groupName]: !prev[groupName],
    }));
  };

  // 展开所有分组
  const expandAll = () => {
    const allExpanded: Record<string, boolean> = {};
    categories.forEach((group) => {
      allExpanded[group.name] = true;
    });
    setExpandedGroups(allExpanded);
  };

  // 折叠所有分组
  const collapseAll = () => {
    const allCollapsed: Record<string, boolean> = {};
    categories.forEach((group) => {
      allCollapsed[group.name] = false;
    });
    setExpandedGroups(allCollapsed);
  };

  // 计算总数
  const totalCount = Object.values(categoryCounts).reduce((sum, count) => sum + count, 0);

  // 清除搜索
  const clearSearch = () => {
    setSearchKeyword('');
  };

  if (isLoading) {
    return (
      <Card className={`p-4 ${className}`}>
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-4 h-4 text-gray-400" />
          <span className="font-medium text-gray-900">文书分类</span>
        </div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-10 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card className={`p-4 ${className}`}>
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <span className="font-medium text-gray-900">文书分类</span>
        </div>
        {collapsible && (
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={expandAll}
              className="text-xs h-6 px-2"
            >
              展开
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={collapseAll}
              className="text-xs h-6 px-2"
            >
              折叠
            </Button>
          </div>
        )}
      </div>

      {/* 搜索框 */}
      {showSearch && (
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            type="text"
            placeholder="搜索分类..."
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            className="pl-9 pr-8 h-9 text-sm"
          />
          {searchKeyword && (
            <button
              onClick={clearSearch}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded hover:bg-gray-100"
            >
              <X className="w-3 h-3 text-gray-400" />
            </button>
          )}
        </div>
      )}

      {/* 全部文书选项 */}
      <button
        onClick={() => onSelectCategory(null)}
        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all duration-200 mb-4 ${
          selectedCategory === null
            ? 'bg-blue-50 text-blue-700 shadow-sm'
            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
        }`}
      >
        <span className={`p-2 rounded-lg text-gray-600 bg-gray-100`}>
          <FileText className="w-4 h-4" />
        </span>
        <span className="flex-1 text-sm font-medium">全部文书</span>
        {showCounts && (
          <Badge
            variant={selectedCategory === null ? 'primary' : 'default'}
            className={`text-xs ${selectedCategory === null ? 'bg-blue-600' : 'bg-gray-100 text-gray-600'}`}
          >
            {totalCount > 999 ? '999+' : totalCount}
          </Badge>
        )}
      </button>

      {/* 分类列表 */}
      <div className="max-h-[calc(100vh-400px)] overflow-y-auto">
        {filteredCategories.length > 0 ? (
          filteredCategories.map((group) => (
            <CategoryGroup
              key={group.name}
              groupName={group.name}
              categories={group.categories}
              selectedCategory={selectedCategory}
              categoryCounts={categoryCounts}
              onSelectCategory={onSelectCategory}
              showCounts={showCounts}
              isExpanded={expandedGroups[group.name] ?? defaultExpanded}
              onToggle={() => toggleGroup(group.name)}
            />
          ))
        ) : (
          <div className="text-center py-8 text-gray-400">
            <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">未找到匹配的分类</p>
          </div>
        )}
      </div>

      {/* 搜索结果提示 */}
      {searchKeyword && filteredCategories.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-xs text-gray-400 text-center">
            找到 {filteredCategories.reduce((sum, g) => sum + g.categories.length, 0)} 个分类
          </p>
        </div>
      )}
    </Card>
  );
}

// 导出子组件供外部使用
export { CategoryItem, CategoryGroup };
export type { DocumentCategoryListProps, CategoryStats };