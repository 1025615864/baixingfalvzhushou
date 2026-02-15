/**
 * ConfigHistory - 配置历史组件
 */

import { useMemo } from 'react';
import { History, Calendar, User, ChevronRight, Filter, Download } from 'lucide-react';

import type { ConfigHistory, ConfigValue } from '../types';

interface ConfigHistoryProps {
  histories: ConfigHistory[];
  total: number;
  isLoading?: boolean;
  onLoadMore?: () => void;
  hasMore?: boolean;
  selectedConfigKey?: string | null;
  onSelectConfigKey?: (key: string | null) => void;
}

export function ConfigHistory({
  histories,
  total,
  isLoading = false,
  onLoadMore,
  hasMore = false,
  selectedConfigKey,
  onSelectConfigKey,
}: ConfigHistoryProps): JSX.Element {
  // 获取唯一的配置键列表
  const configKeys = useMemo(() => {
    const keys = new Set<string>();
    histories.forEach((h) => keys.add(h.configKey));
    return Array.from(keys);
  }, [histories]);

  // 过滤历史记录
  const filteredHistories = useMemo(() => {
    if (!selectedConfigKey) return histories;
    return histories.filter((h) => h.configKey === selectedConfigKey);
  }, [histories, selectedConfigKey]);

  // 格式化值显示
  const formatValue = (value: ConfigValue): string => {
    if (value === null || value === undefined) {
      return '未设置';
    }
    if (typeof value === 'object') {
      const str = JSON.stringify(value);
      return str.length > 50 ? str.slice(0, 50) + '...' : str;
    }
    return String(value).slice(0, 50) + (String(value).length > 50 ? '...' : '');
  };

  // 导出历史记录
  const handleExport = (): void => {
    const data = histories.map((h) => ({
      配置键: h.configKey,
      旧值: formatValue(h.oldValue),
      新值: formatValue(h.newValue),
      修改人: h.updatedByName || h.updatedBy,
      修改时间: new Date(h.updatedAt).toLocaleString(),
      变更原因: h.changeReason || '-',
    }));

    const csv = [
      Object.keys(data[0]).join(','),
      ...data.map((row) =>
        Object.values(row)
          .map((v) => `"${String(v).replace(/"/g, '""')}"`)
          .join(',')
      ),
    ].join('\n');

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `config-history-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
  };

  if (isLoading && histories.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 头部工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="text-lg font-medium text-gray-900">配置变更历史</h3>
          <span className="text-sm text-gray-500">共 {total} 条记录</span>
        </div>
        <button
          onClick={handleExport}
          disabled={histories.length === 0}
          className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Download className="h-4 w-4" />
          导出
        </button>
      </div>

      {/* 过滤器 */}
      <div className="flex flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-400" />
          <span className="text-sm text-gray-600">筛选:</span>
        </div>
        <button
          onClick={() => onSelectConfigKey?.(null)}
          className={`px-3 py-1 rounded-full text-sm ${
            !selectedConfigKey
              ? 'bg-blue-100 text-blue-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          全部
        </button>
        {configKeys.slice(0, 10).map((key) => (
          <button
            key={key}
            onClick={() => onSelectConfigKey?.(key)}
            className={`px-3 py-1 rounded-full text-sm max-w-[200px] truncate ${
              selectedConfigKey === key
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title={key}
          >
            {key}
          </button>
        ))}
      </div>

      {/* 历史列表 */}
      <div className="space-y-3">
        {filteredHistories.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <History className="mx-auto h-12 w-12 text-gray-300 mb-4" />
            <p>暂无变更历史</p>
          </div>
        ) : (
          filteredHistories.map((history) => (
            <div
              key={history.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* 配置键 */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-mono text-sm font-medium text-gray-900">
                      {history.configKey}
                    </span>
                  </div>

                  {/* 值变更 */}
                  <div className="flex items-center gap-3 text-sm">
                    <div className="flex-1 px-3 py-2 bg-red-50 border border-red-100 rounded text-red-700 line-through">
                      {formatValue(history.oldValue)}
                    </div>
                    <ChevronRight className="h-4 w-4 text-gray-400 flex-shrink-0" />
                    <div className="flex-1 px-3 py-2 bg-green-50 border border-green-100 rounded text-green-700">
                      {formatValue(history.newValue)}
                    </div>
                  </div>

                  {/* 变更信息 */}
                  <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <User className="h-3 w-3" />
                      <span>{history.updatedByName || history.updatedBy}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      <span>{new Date(history.updatedAt).toLocaleString()}</span>
                    </div>
                  </div>

                  {/* 变更原因 */}
                  {history.changeReason && (
                    <div className="mt-2 text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded inline-block">
                      原因: {history.changeReason}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 加载更多 */}
      {hasMore && (
        <div className="flex justify-center pt-4">
          <button
            onClick={onLoadMore}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 disabled:opacity-50"
          >
            {isLoading ? '加载中...' : '加载更多'}
          </button>
        </div>
      )}
    </div>
  );
}