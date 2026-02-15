/**
 * 分类筛选组件
 * 用于按分类筛选法律知识
 */

import { useCategories } from '../../hooks/useKnowledge';

interface CategoryFilterProps {
  selectedCategory: string | null;
  onSelectCategory: (category: string | null) => void;
}

/**
 * 分类筛选组件
 */
export function CategoryFilter({
  selectedCategory,
  onSelectCategory,
}: CategoryFilterProps): JSX.Element {
  const { data: categoriesData, isLoading, isError } = useCategories();

  if (isLoading) {
    return (
      <div className="flex flex-wrap gap-2">
        {Array.from({ length: 6 }, (_, index) => (
          <div
            key={index}
            className="h-8 w-20 bg-gray-200 rounded-full animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-sm text-gray-500">
        无法加载分类
      </div>
    );
  }

  const categories = categoriesData?.categories || [];

  return (
    <div className="flex flex-wrap gap-2">
      {/* 全部选项 */}
      <button
        onClick={() => onSelectCategory(null)}
        className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
          selectedCategory === null
            ? 'bg-primary-600 text-white'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }`}
      >
        全部
      </button>

      {/* 分类选项 */}
      {categories.map((category) => (
        <button
          key={category.id}
          onClick={() => onSelectCategory(category.name)}
          className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
            selectedCategory === category.name
              ? 'bg-primary-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {category.name}
        </button>
      ))}
    </div>
  );
}