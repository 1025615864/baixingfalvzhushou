/**
 * News Topics Page
 * 新闻专题管理页面
 */

import { useState } from 'react';
import { Plus, Edit2, Trash2, FolderOpen } from 'lucide-react';

import { Card, Button, Badge } from '@/components/ui';

import { useTopics, useCreateTopic, useUpdateTopic, useDeleteTopic } from '../hooks/useNewsAdmin';
import type { NewsTopic, CreateTopicRequest, UpdateTopicRequest } from '../types';

/**
 * 新闻专题管理页面
 */
export function NewsTopicsPage(): JSX.Element {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingTopic, setEditingTopic] = useState<NewsTopic | null>(null);

  // 数据查询
  const { data: topics, isLoading } = useTopics();

  // Mutations
  const createMutation = useCreateTopic();
  const updateMutation = useUpdateTopic();
  const deleteMutation = useDeleteTopic();

  // 处理创建
  const handleCreate = (data: CreateTopicRequest | UpdateTopicRequest): void => {
    // 创建模式下，data必须是CreateTopicRequest
    createMutation.mutate(data as CreateTopicRequest, {
      onSuccess: () => {
        setIsCreateModalOpen(false);
      },
    });
  };

  // 处理编辑
  const handleEdit = (data: CreateTopicRequest | UpdateTopicRequest): void => {
    if (!editingTopic) return;
    // 编辑模式下，data是UpdateTopicRequest
    updateMutation.mutate(
      { id: editingTopic.id, request: data as UpdateTopicRequest },
      {
        onSuccess: () => {
          setIsEditModalOpen(false);
          setEditingTopic(null);
        },
      }
    );
  };

  // 处理删除
  const handleDelete = (topic: NewsTopic): void => {
    if (window.confirm(`确定要删除专题"${topic.title}"吗？此操作不可恢复。`)) {
      deleteMutation.mutate(topic.id);
    }
  };

  // 打开编辑弹窗
  const openEditModal = (topic: NewsTopic): void => {
    setEditingTopic(topic);
    setIsEditModalOpen(true);
  };

  return (
    <div className="container mx-auto py-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">新闻专题管理</h1>
          <p className="text-slate-600 mt-1">管理新闻专题和分类</p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          新建专题
        </Button>
      </div>

      {/* 专题列表 */}
      <Card>
        {isLoading ? (
          <div className="p-6 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-20 bg-slate-100 rounded animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="divide-y divide-slate-200">
            {topics?.map((topic) => (
              <TopicItem
                key={topic.id}
                topic={topic}
                onEdit={() => openEditModal(topic)}
                onDelete={() => handleDelete(topic)}
              />
            ))}
            {!topics?.length && (
              <div className="p-10 text-center text-slate-500">
                <FolderOpen className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                <p>暂无新闻专题</p>
                <p className="text-sm mt-1">点击&quot;新建专题&quot;按钮创建专题</p>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* 创建弹窗 */}
      <TopicModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreate}
        isLoading={createMutation.isPending}
        title="新建专题"
      />

      {/* 编辑弹窗 */}
      <TopicModal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setEditingTopic(null);
        }}
        onSubmit={handleEdit}
        initialData={editingTopic}
        isLoading={updateMutation.isPending}
        title="编辑专题"
      />
    </div>
  );
}

// ==================== 子组件 ====================

interface TopicItemProps {
  topic: NewsTopic;
  onEdit: () => void;
  onDelete: () => void;
}

function TopicItem({ topic, onEdit, onDelete }: TopicItemProps): JSX.Element {
  return (
    <div className="p-4 hover:bg-slate-50">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-slate-900">{topic.title}</h3>
            <Badge variant={topic.isActive ? 'success' : 'default'} size="sm">
              {topic.isActive ? '启用' : '禁用'}
            </Badge>
          </div>
          {topic.description && (
            <p className="text-sm text-slate-500 mt-1">{topic.description}</p>
          )}
          <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
            <span>排序: {topic.sortOrder}</span>
            <span>文章数: {topic.autoLimit}</span>
            {topic.createdAt && (
              <span>
                创建时间: {new Date(topic.createdAt).toLocaleDateString('zh-CN')}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 ml-4">
          <Button variant="ghost" size="sm" onClick={onEdit} title="编辑">
            <Edit2 className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={onDelete} title="删除">
            <Trash2 className="h-4 w-4 text-red-500" />
          </Button>
        </div>
      </div>
    </div>
  );
}

interface TopicModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateTopicRequest | UpdateTopicRequest) => void;
  initialData?: NewsTopic | null;
  isLoading: boolean;
  title: string;
}

function TopicModal({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  isLoading,
  title,
}: TopicModalProps): JSX.Element | null {
  const [formData, setFormData] = useState<CreateTopicRequest>(() => ({
    title: '',
    description: '',
    sortOrder: 0,
    isActive: true,
    ...((initialData as Partial<NewsTopic> | undefined) ?? {}),
  }));

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
              专题名称 *
            </label>
            <input
              type="text"
              value={String(formData.title ?? '')}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                const newTitle = e.target.value;
                setFormData((prev) => ({ ...prev, title: newTitle }));
              }}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="例如：法治建设"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              描述
            </label>
            <textarea
              value={formData.description ?? ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="专题描述..."
              rows={3}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              排序
            </label>
            <input
              type="number"
              value={formData.sortOrder}
              onChange={(e) =>
                setFormData({ ...formData, sortOrder: Number(e.target.value) })
              }
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              min={0}
            />
            <p className="text-xs text-slate-500 mt-1">数字越小排序越靠前</p>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="isActive"
              checked={formData.isActive}
              onChange={(e) => setFormData({ ...formData, isActive: e.target.checked })}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="isActive" className="text-sm text-slate-700">
              启用此专题
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
