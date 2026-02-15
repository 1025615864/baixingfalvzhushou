/**
 * 评论分页组件
 */

interface CommentPaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

/**
 * 评论分页组件
 */
export function CommentPagination({
  currentPage,
  totalPages,
  onPageChange,
}: CommentPaginationProps): JSX.Element | null {
  if (totalPages <= 1) {
    return null;
  }

  // 计算要显示的页码
  const getPageNumbers = (): (number | string)[] => {
    const pages: (number | string)[] = [];
    const maxVisiblePages = 5;

    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // 总是显示第一页
      pages.push(1);

      if (currentPage > 3) {
        pages.push('...');
      }

      // 显示当前页附近的页码
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (currentPage < totalPages - 2) {
        pages.push('...');
      }

      // 总是显示最后一页
      pages.push(totalPages);
    }

    return pages;
  };

  const pageNumbers = getPageNumbers();

  return (
    <div className="flex items-center justify-center gap-2 py-4">
      {/* 上一页 */}
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-md
                   hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        type="button"
      >
        上一页
      </button>

      {/* 页码 */}
      <div className="flex items-center gap-1">
        {pageNumbers.map((page, index) => (
          <div key={index}>
            {page === '...' ? (
              <span className="px-3 py-1.5 text-sm text-gray-400">...</span>
            ) : (
              <button
                onClick={() => onPageChange(page as number)}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors
                  ${
                    currentPage === page
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'
                  }`}
                type="button"
              >
                {page}
              </button>
            )}
          </div>
        ))}
      </div>

      {/* 下一页 */}
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-md
                   hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        type="button"
      >
        下一页
      </button>
    </div>
  );
}

export default CommentPagination;