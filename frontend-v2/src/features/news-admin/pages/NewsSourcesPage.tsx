/**
 * News Sources Page
 * 新闻来源管理页面
 */

import { useState } from 'react';
import { Plus, Edit2, Trash2, Power, Play, Rss, AlertCircle } from 'lucide-react';

import { Card, Button, Badge } from '@/components/ui';

import { useSources, useCreateSource, useUpdateSource, useDeleteSource, useTriggerIngest, useSourceHealth } from '../hooks/useNewsAdmin';
import type { NewsSource, NewsSourceHealth, CreateSourceRequest, UpdateSourceRequest } from '../types';

/**
 * 新闻来源管理页面
 */
export function NewsSourcesPage(): JSX.Element {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingSource, setEditingSource] = useState<NewsSource | null>(null);

  // 数据查询
  const { data: sources, isLoading: isLoadingSources } = useSources();
  const { data: healthData, isLoading: isLoadingHealth } = useSourceHealth();

  // Mutations
  const createMutation = useCreateSource();
  const updateMutation = useUpdateSource();
  const deleteMutation = useDeleteSource();
  const triggerMutation = useTriggerIngest();

  // 健康状态映射
  const healthMap = new Map<number, NewsSourceHealth>(
    healthData?.map((h: NewsSourceHealth) => [h.sourceId, h]) ?? []
  );

  // 处理创建
  const handleCreate = (data: CreateSourceRequest | UpdateSourceRequest): void => {
    // 创建模式下，data必须是CreateSourceRequest
    createMutation.mutate(data as CreateSourceRequest, {
      onSuccess: () => {
        setIsCreateModalOpen(false);
      },
    });
  };

  // 处理编辑
  const handleEdit = (data: CreateSourceRequest | UpdateSourceRequest): void => {
    if (!editingSource) return;
    // 编辑模式下，data是UpdateSourceRequest
    updateMutation.mutate(
      { id: editingSource.id, request: data as UpdateSourceRequest },
      {
        onSuccess: () => {
          setIsEditModalOpen(false);
          setEditingSource(null);
        },
      }
    );
  };

  // 处理删除
  const handleDelete = (source: NewsSource): void => {
    if (window.confirm(`确定要删除来源"${source.name}"吗？此操作不可恢复。`)) {
      deleteMutation.mutate(source.id);
    }
  };

  // 处理启停
  const handleToggle = (source: NewsSource): void => {
    const action = source.isEnabled ? '禁用' : '启用';
    if (window.confirm(`确定要${action}来源"${source.name}"吗？`)) {
      updateMutation.mutate({
        id: source.id,
        request: { isEnabled: !source.isEnabled },
      });
    }
  };

  // 处理立即抓取
  const handleTrigger = (sourceId: number): void => {
    triggerMutation.mutate(sourceId);
  };

  // 打开编辑弹窗
  const openEditModal = (source: NewsSource): void => {
    setEditingSource(source);
    setIsEditModalOpen(true);
  };

  const isLoading = isLoadingSources || isLoadingHealth;

  return (
    <div className="container mx-auto py-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">新闻来源管理</h1>
          <p className="text-slate-600 mt-1">管理 RSS 订阅源和抓取配置</p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          新建来源
        </Button>
      </div>

      {/* 来源列表 */}
      <Card>
        {isLoading ? (
          <div className="p-6 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-20 bg-slate-100 rounded animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="divide-y divide-slate-200">
            {sources?.map((source: NewsSource) => {
              const health = healthMap.get(source.id);
              return (
                <SourceItem
                  key={source.id}
                  source={source}
                  health={health}
                  onEdit={() => openEditModal(source)}
                  onDelete={() => handleDelete(source)}
                  onToggle={() => handleToggle(source)}
                  onTrigger={() => handleTrigger(source.id)}
                />
              );
            })}
            {!sources?.length && (
              <div className="p-10 text-center text-slate-500">
                <Rss className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                <p>暂无新闻来源</p>
                <p className="text-sm mt-1">点击&quot;新建来源&quot;按钮添加 RSS 订阅源</p>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* 创建弹窗 */}
      <SourceModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreate}
        isLoading={createMutation.isPending}
        title="新建来源"
      />

      {/* 编辑弹窗 */}
      <SourceModal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setEditingSource(null);
        }}
        onSubmit={handleEdit}
        initialData={editingSource}
        isLoading={updateMutation.isPending}
        title="编辑来源"
      />
    </div>
  );
}

// ==================== 子组件 ====================

interface SourceItemProps {
  source: NewsSource;
  health?: {
    recentTotal: number;
    recentFailed: number;
    failureRate: number;
    lastStatus?: string | null;
    lastRunAt?: string | null;
    lastError?: string | null;
  };
  onEdit: () => void;
  onDelete: () => void;
  onToggle: () => void;
  onTrigger: () => void;
}

function SourceItem({
  source,
  health,
  onEdit,
  onDelete,
  onToggle,
  onTrigger,
}: SourceItemProps): JSX.Element {
  const failureRate = health?.failureRate ?? 0;
  const isHealthy = failureRate < 0.3;

  return (
    <div className="p-4 hover:bg-slate-50">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-slate-900">{source.name}</h3>
            <Badge variant={source.isEnabled ? 'success' : 'default'} size="sm">
              {source.isEnabled ? '启用' : '禁用'}
            </Badge>
            {health && (
              <Badge variant={isHealthy ? 'success' : 'danger'} size="sm">
                健康度 {Math.round((1 - failureRate) * 100)}%
              </Badge>
            )}
          </div>
          <p className="text-sm text-slate-500 mt-1 truncate">{source.feedUrl}</p>
          <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
            <span>类型: {source.sourceType}</span>
            {source.category && <span>分类: {source.category}</span>}
            {source.site && (
              <a
                href={source.site}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                访问网站
              </a>
            )}
          </div>
          {health?.lastError && (
            <div className="flex items-center gap-2 mt-2 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span className="truncate">{health.lastError}</span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 ml-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={onTrigger}
            title="立即抓取"
          >
            <Play className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggle}
            title={source.isEnabled ? '禁用' : '启用'}
          >
            <Power className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onEdit}
            title="编辑"
          >
            <Edit2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onDelete}
            title="删除"
          >
            <Trash2 className="h-4 w-4 text-red-500" />
          </Button>
        </div>
      </div>
    </div>
  );
}

interface SourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateSourceRequest | UpdateSourceRequest) => void;
  initialData?: NewsSource | null;
  isLoading: boolean;
  title: string;
}

function SourceModal({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  isLoading,
  title,
}: SourceModalProps): JSX.Element | null {
  const [formData, setFormData] = useState<CreateSourceRequest>({
    name: initialData?.name ?? '',
    feedUrl: initialData?.feedUrl ?? '',
    site: initialData?.site ?? '',
    category: initialData?.category ?? '',
    isEnabled: initialData?.isEnabled ?? true,
    fetchTimeoutSeconds: initialData?.fetchTimeoutSeconds ?? 30,
    maxItemsPerFeed: initialData?.maxItemsPerFeed ?? 50,
  });

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
        <div className="p-6 border-b border-slate-200">
          <h2 className="text-lg font-semibold">{title}</h2>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              来源名称 *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="例如：人民日报"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              RSS 地址 *
            </label>
            <input
              type="url"
              value={formData.feedUrl}
              onChange={(e) => setFormData({ ...formData, feedUrl: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="https://example.com/feed.xml"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              网站地址
            </label>
            <input
              type="url"
              value={formData.site ?? ''}
              onChange={(e) => setFormData({ ...formData, site: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="https://example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              分类
            </label>
            <select
              value={formData.category ?? ''}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">请选择分类</option>
              <option value="general">综合</option>
              <option value="legal">法律</option>
              <option value="politics">时政</option>
              <option value="economy">经济</option>
              <option value="society">社会</option>
              <option value="technology">科技</option>
              <option value="other">其他</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                超时时间（秒）
              </label>
              <input
                type="number"
                value={formData.fetchTimeoutSeconds}
                onChange={(e) =>
                  setFormData({ ...formData, fetchTimeoutSeconds: Number(e.target.value) })
                }
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                min={5}
                max={300}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                最大条目数
              </label>
              <input
                type="number"
                value={formData.maxItemsPerFeed}
                onChange={(e) =>
                  setFormData({ ...formData, maxItemsPerFeed: Number(e.target.value) })
                }
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                min={1}
                max={200}
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="isEnabled"
              checked={formData.isEnabled}
              onChange={(e) => setFormData({ ...formData, isEnabled: e.target.checked })}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="isEnabled" className="text-sm text-slate-700">
              启用此来源
            </label>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="ghost" onClick={onClose}>
              取消
            </Button>
            <Button type="submit" isLoading={isLoading}>
              保存
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
