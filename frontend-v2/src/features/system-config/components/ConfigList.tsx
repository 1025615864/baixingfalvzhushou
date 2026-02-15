/**
 * ConfigList - 配置列表组件
 */

import { useState, useMemo } from 'react';
import { Search, Settings, Shield, Unlock, Calendar, ChevronRight } from 'lucide-react';

import type { ConfigItem, ConfigGroup, ConfigValue } from '../types';

interface ConfigListProps {
  configs: ConfigItem[];
  groups: ConfigGroup[];
  selectedGroup: string | null;
  onSelectGroup: (groupId: string | null) => void;
  onSelectConfig: (config: ConfigItem) => void;
  onViewHistory: (config: ConfigItem) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  isLoading?: boolean;
}

export function ConfigList({
  configs,
  groups,
  selectedGroup,
  onSelectGroup,
  onSelectConfig,
  onViewHistory,
  searchQuery,
  onSearchChange,
  isLoading = false,
}: ConfigListProps): JSX.Element {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  // 过滤配置
  const filteredConfigs = useMemo(() => {
    let result = configs;

    // 按分组过滤
    if (selectedGroup) {
      result = result.filter((config) => config.group === selectedGroup);
    }

    // 按搜索词过滤
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (config) =>
          config.key.toLowerCase().includes(query) ||
          config.description.toLowerCase().includes(query)
      );
    }

    return result;
  }, [configs, selectedGroup, searchQuery]);

  // 按分组组织配置
  const groupedConfigs = useMemo(() => {
    const groups = new Map<string, ConfigItem[]>();
    
    filteredConfigs.forEach((config) => {
      const existing = groups.get(config.group) || [];
      existing.push(config);
      groups.set(config.group, existing);
    });

    return groups;
  }, [filteredConfigs]);

  // 切换分组展开状态
  const toggleGroup = (groupId: string): void => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupId)) {
      newExpanded.delete(groupId);
    } else {
      newExpanded.add(groupId);
    }
    setExpandedGroups(newExpanded);
  };

  // 格式化配置值显示
  const formatValue = (value: ConfigValue, type: string, isSensitive: boolean): string => {
    if (isSensitive) {
      return '••••••••';
    }

    if (value === null || value === undefined) {
      return '未设置';
    }

    switch (type) {
      case 'boolean':
        return value ? '是' : '否';
      case 'json':
        try {
          return JSON.stringify(value).slice(0, 50) + (JSON.stringify(value).length > 50 ? '...' : '');
        } catch {
          return '无效的 JSON';
        }
      case 'array':
        if (Array.isArray(value)) {
          return `[${value.length} 项]`;
        }
        return String(value);
      default:
        return String(value).slice(0, 50) + (String(value).length > 50 ? '...' : '');
    }
  };

  // 获取分组名称
  const getGroupName = (groupId: string): string => {
    const group = groups.find((g) => g.id === groupId);
    return group?.name || groupId;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 搜索栏 */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="搜索配置项..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* 分组标签 */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => onSelectGroup(null)}
          className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
            selectedGroup === null
              ? 'bg-blue-100 text-blue-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          全部
        </button>
        {groups.map((group) => (
          <button
            key={group.id}
            onClick={() => onSelectGroup(group.id)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
              selectedGroup === group.id
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {group.name}
          </button>
        ))}
      </div>

      {/* 配置列表 */}
      <div className="space-y-2">
        {filteredConfigs.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Settings className="mx-auto h-12 w-12 text-gray-300 mb-4" />
            <p>没有找到配置项</p>
            {searchQuery && (
              <p className="text-sm mt-1">尝试调整搜索关键词</p>
            )}
          </div>
        ) : (
          Array.from(groupedConfigs.entries()).map(([groupId, groupConfigs]) => (
            <div key={groupId} className="border border-gray-200 rounded-lg overflow-hidden">
              {/* 分组标题 */}
              <button
                onClick={() => toggleGroup(groupId)}
                className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <ChevronRight
                    className={`h-4 w-4 text-gray-400 transition-transform ${
                      expandedGroups.has(groupId) ? 'rotate-90' : ''
                    }`}
                  />
                  <span className="font-medium text-gray-900">{getGroupName(groupId)}</span>
                  <span className="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">
                    {groupConfigs.length}
                  </span>
                </div>
              </button>

              {/* 配置项列表 */}
              {(expandedGroups.has(groupId) || searchQuery) && (
                <div className="divide-y divide-gray-100">
                  {groupConfigs.map((config) => (
                    <div
                      key={config.id}
                      className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors group"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900 truncate">
                            {config.key}
                          </span>
                          {config.isSensitive && (
                            <span title="敏感配置">
                              <Shield className="h-3.5 w-3.5 text-amber-500" />
                            </span>
                          )}
                          {!config.isEditable && (
                            <span title="只读">
                              <Unlock className="h-3.5 w-3.5 text-gray-400" />
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-500 truncate mt-0.5">
                          {config.description}
                        </p>
                      </div>
                      
                      <div className="flex items-center gap-4 ml-4">
                        <div className="text-right">
                          <div className="text-sm font-medium text-gray-900">
                            {formatValue(config.value, config.type, config.isSensitive)}
                          </div>
                          <div className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                            <Calendar className="h-3 w-3" />
                            {new Date(config.updatedAt).toLocaleDateString()}
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          {config.isEditable && (
                            <button
                              onClick={() => onSelectConfig(config)}
                              className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                              title="编辑"
                            >
                              <Settings className="h-4 w-4" />
                            </button>
                          )}
                          <button
                            onClick={() => onViewHistory(config)}
                            className="p-1.5 text-gray-600 hover:bg-gray-100 rounded"
                            title="查看历史"
                          >
                            <Calendar className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}