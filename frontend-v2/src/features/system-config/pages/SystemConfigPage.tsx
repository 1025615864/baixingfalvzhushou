/**
 * SystemConfigPage - 系统配置页面
 */

import { logger } from '@/shared/lib/logger';
import { useState } from 'react';
import { Settings, RefreshCw, Download, History } from 'lucide-react';

import type { ConfigItem, ConfigValue } from '../types';
import { useConfigList, useUpdateConfig, useResetConfig, useConfigHistory, useExportConfig, useRefreshConfigCache } from '../hooks/useSystemConfig';
import { ConfigList } from '../components/ConfigList';
import { ConfigEditor } from '../components/ConfigEditor';
import { ConfigHistory as ConfigHistoryComponent } from '../components/ConfigHistory';

export function SystemConfigPage(): JSX.Element {
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedConfig, setSelectedConfig] = useState<ConfigItem | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedHistoryConfigKey, setSelectedHistoryConfigKey] = useState<string | null>(null);

  const { data: configData, isLoading: isLoadingConfigs, refetch: refetchConfigs } = useConfigList({
    group: selectedGroup || undefined,
    search: searchQuery || undefined,
  });

  const { data: historyData, isLoading: isLoadingHistory } = useConfigHistory({
    limit: 50,
  });

  const updateConfigMutation = useUpdateConfig();
  const resetConfigMutation = useResetConfig();
  const exportConfigMutation = useExportConfig();
  const refreshCacheMutation = useRefreshConfigCache();

  const handleEditConfig = (config: ConfigItem): void => {
    setSelectedConfig(config);
    setIsEditorOpen(true);
  };

  const handleViewHistory = (config: ConfigItem): void => {
    setSelectedHistoryConfigKey(config.key);
    setShowHistory(true);
  };

  const handleSaveConfig = async (configId: string, value: ConfigValue, reason?: string): Promise<void> => {
    try {
      await updateConfigMutation.mutateAsync({ configId, value, reason });
      setIsEditorOpen(false);
      setSelectedConfig(null);
    } catch (error) {
      logger.error('保存配置失败:', error);
      alert('保存配置失败，请重试');
    }
  };

  const handleResetConfig = async (configId: string, reason?: string): Promise<void> => {
    try {
      await resetConfigMutation.mutateAsync({ configId, reason });
      setIsEditorOpen(false);
      setSelectedConfig(null);
    } catch (error) {
      logger.error('重置配置失败:', error);
      alert('重置配置失败，请重试');
    }
  };

  const handleExport = async (): Promise<void> => {
    try {
      const result = await exportConfigMutation.mutateAsync();
      const blob = new Blob([result.exportData], { type: 'application/json' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = result.filename;
      link.click();
    } catch (error) {
      logger.error('导出配置失败:', error);
      alert('导出配置失败，请重试');
    }
  };

  const handleRefreshCache = async (): Promise<void> => {
    try {
      await refreshCacheMutation.mutateAsync();
      alert('配置缓存已刷新');
    } catch (error) {
      logger.error('刷新缓存失败:', error);
      alert('刷新缓存失败，请重试');
    }
  };

  const handleRefresh = (): void => {
    void refetchConfigs();
  };

  const configs = configData?.configs || [];
  const groups = configData?.groups || [];
  const histories = historyData?.histories || [];
  const totalHistories = historyData?.total || 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Settings className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">系统配置</h1>
                <p className="text-sm text-gray-500">管理系统配置项和查看变更历史</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={handleRefresh}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                <RefreshCw className="h-4 w-4" />
                刷新
              </button>
              <button
                onClick={() => void handleRefreshCache()}
                disabled={refreshCacheMutation.isPending}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${refreshCacheMutation.isPending ? 'animate-spin' : ''}`} />
                刷新缓存
              </button>
              <button
                onClick={() => void handleExport()}
                disabled={exportConfigMutation.isPending}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                <Download className="h-4 w-4" />
                导出
              </button>
              <button
                onClick={() => setShowHistory(!showHistory)}
                className={`flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md ${
                  showHistory
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                <History className="h-4 w-4" />
                历史记录
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className={`${showHistory ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <ConfigList
                configs={configs}
                groups={groups}
                selectedGroup={selectedGroup}
                onSelectGroup={setSelectedGroup}
                onSelectConfig={handleEditConfig}
                onViewHistory={handleViewHistory}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                isLoading={isLoadingConfigs}
              />
            </div>
          </div>

          {showHistory && (
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 max-h-[800px] overflow-y-auto">
                <ConfigHistoryComponent
                  histories={histories}
                  total={totalHistories}
                  isLoading={isLoadingHistory}
                  selectedConfigKey={selectedHistoryConfigKey}
                  onSelectConfigKey={setSelectedHistoryConfigKey}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      <ConfigEditor
        config={selectedConfig}
        isOpen={isEditorOpen}
        onClose={() => {
          setIsEditorOpen(false);
          setSelectedConfig(null);
        }}
        onSave={(configId, value, reason) => void handleSaveConfig(configId, value, reason)}
        onReset={(configId, reason) => void handleResetConfig(configId, reason)}
        isSaving={updateConfigMutation.isPending || resetConfigMutation.isPending}
      />
    </div>
  );
}