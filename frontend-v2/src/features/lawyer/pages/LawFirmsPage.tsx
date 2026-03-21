/**
 * Law Firms Page
 * 律所管理页面（管理员用）
 */

import { useState } from 'react';
import { Search, Plus, Pencil, Trash2, BadgeCheck, Ban, RotateCcw, Building2 } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

import {
  useLawFirms,
  useCreateLawFirm,
  useUpdateLawFirm,
  useDeleteLawFirm,
  useVerifyLawFirm,
  useToggleLawFirmActive,
} from '../hooks/useLawFirms';
import type { LawFirm } from '../types';

/**
 * 律所管理页面
 */
export function LawFirmsPage(): JSX.Element {
  const [keyword, setKeyword] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingFirm, setEditingFirm] = useState<LawFirm | null>(null);
  const [activeAction, setActiveAction] = useState<{ id: string; kind: 'verify' | 'active' | 'delete' } | null>(null);

  const [createForm, setCreateForm] = useState({
    name: '',
    city: '',
    phone: '',
    address: '',
    description: '',
  });

  const [editForm, setEditForm] = useState({
    name: '',
    city: '',
    phone: '',
    address: '',
    description: '',
  });

  // 数据查询
  const { data: firms = [], isLoading } = useLawFirms({
    keyword: keyword || undefined,
    includeInactive: true,
  });

  // Mutations
  const createMutation = useCreateLawFirm();
  const updateMutation = useUpdateLawFirm();
  const deleteMutation = useDeleteLawFirm();
  const verifyMutation = useVerifyLawFirm();
  const toggleActiveMutation = useToggleLawFirmActive();

  // 处理创建
  const handleCreate = () => {
    createMutation.mutate(createForm, {
      onSuccess: () => {
        setShowCreateModal(false);
        setCreateForm({ name: '', city: '', phone: '', address: '', description: '' });
      },
    });
  };

  // 处理编辑
  const handleEdit = (firm: LawFirm) => {
    setEditingFirm(firm);
    setEditForm({
      name: firm.name,
      city: firm.city ?? '',
      phone: firm.phone ?? '',
      address: firm.address ?? '',
      description: firm.description ?? '',
    });
    setShowEditModal(true);
  };

  // 处理更新
  const handleUpdate = () => {
    if (!editingFirm) return;
    updateMutation.mutate(
      { id: editingFirm.id, request: editForm },
      {
        onSuccess: () => {
          setShowEditModal(false);
          setEditingFirm(null);
        },
      }
    );
  };

  // 处理删除
  const handleDelete = (id: string) => {
    setActiveAction({ id, kind: 'delete' });
    deleteMutation.mutate(id, {
      onSettled: () => setActiveAction(null),
    });
  };

  // 处理验证
  const handleVerify = (id: string, verified: boolean) => {
    setActiveAction({ id, kind: 'verify' });
    verifyMutation.mutate(
      { id, verified },
      { onSettled: () => setActiveAction(null) }
    );
  };

  // 处理启用/禁用
  const handleToggleActive = (id: string, isActive: boolean) => {
    setActiveAction({ id, kind: 'active' });
    toggleActiveMutation.mutate(
      { id, isActive },
      { onSettled: () => setActiveAction(null) }
    );
  };

  return (
    <div className="container mx-auto py-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">律所管理</h1>
          <p className="text-slate-600 mt-1">管理和维护律所信息</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4 mr-1" />
          新建律所
        </Button>
      </div>

      {/* 搜索栏 */}
      <Card className="mb-6">
        <div className="p-4 flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="搜索律所名称..."
              value={keyword}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setKeyword(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
      </Card>

      {/* 律所列表 */}
      <Card>
        {isLoading ? (
          <div className="p-6 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-20 bg-slate-100 rounded animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="divide-y divide-slate-200">
            {firms.map((firm) => (
              <div key={firm.id} className="p-4 hover:bg-slate-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <Building2 className="h-5 w-5 text-slate-500" />
                      <h3 className="font-medium text-slate-900">{firm.name}</h3>
                      {firm.isVerified ? (
                        <Badge variant="success" size="sm">已认证</Badge>
                      ) : (
                        <Badge variant="default" size="sm">未认证</Badge>
                      )}
                      {!firm.isActive && (
                        <Badge variant="danger" size="sm">已禁用</Badge>
                      )}
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-slate-500">
                      <div>
                        <span className="text-slate-400">城市：</span>
                        {firm.city ?? '-'}
                      </div>
                      <div>
                        <span className="text-slate-400">电话：</span>
                        {firm.phone ?? '-'}
                      </div>
                      <div>
                        <span className="text-slate-400">律师数：</span>
                        {firm.lawyerCount}
                      </div>
                      <div>
                        <span className="text-slate-400">评分：</span>
                        {firm.rating.toFixed(1)}
                      </div>
                    </div>
                    {firm.address && (
                      <div className="mt-1 text-sm text-slate-500">
                        <span className="text-slate-400">地址：</span>
                        {firm.address}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEdit(firm)}
                      title="编辑"
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleVerify(firm.id, !firm.isVerified)}
                      disabled={activeAction?.id === firm.id && activeAction?.kind === 'verify'}
                      title={firm.isVerified ? '取消认证' : '认证'}
                    >
                      {activeAction?.id === firm.id && activeAction?.kind === 'verify' ? (
                        <RotateCcw className="h-4 w-4 animate-spin" />
                      ) : firm.isVerified ? (
                        <BadgeCheck className="h-4 w-4 text-green-500" />
                      ) : (
                        <BadgeCheck className="h-4 w-4 text-slate-400" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleToggleActive(firm.id, !firm.isActive)}
                      disabled={activeAction?.id === firm.id && activeAction?.kind === 'active'}
                      title={firm.isActive ? '禁用' : '启用'}
                    >
                      {activeAction?.id === firm.id && activeAction?.kind === 'active' ? (
                        <RotateCcw className="h-4 w-4 animate-spin" />
                      ) : firm.isActive ? (
                        <Ban className="h-4 w-4 text-orange-500" />
                      ) : (
                        <BadgeCheck className="h-4 w-4 text-green-500" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(firm.id)}
                      disabled={activeAction?.id === firm.id && activeAction?.kind === 'delete'}
                      title="删除"
                    >
                      {activeAction?.id === firm.id && activeAction?.kind === 'delete' ? (
                        <RotateCcw className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4 text-red-500" />
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            ))}
            {!firms.length && (
              <div className="p-10 text-center text-slate-500">
                <Building2 className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                <p>暂无律所</p>
                <p className="text-sm mt-1">点击&quot;新建律所&quot;按钮添加</p>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* 创建弹窗 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold">新建律所</h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  律所名称 *
                </label>
                <Input
                  value={createForm.name}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setCreateForm({ ...createForm, name: e.target.value })
                  }
                  placeholder="请输入律所名称"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  城市
                </label>
                <Input
                  value={createForm.city}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setCreateForm({ ...createForm, city: e.target.value })
                  }
                  placeholder="请输入城市"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  联系电话
                </label>
                <Input
                  value={createForm.phone}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setCreateForm({ ...createForm, phone: e.target.value })
                  }
                  placeholder="请输入联系电话"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  地址
                </label>
                <Input
                  value={createForm.address}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setCreateForm({ ...createForm, address: e.target.value })
                  }
                  placeholder="请输入地址"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  简介
                </label>
                <textarea
                  value={createForm.description}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                    setCreateForm({ ...createForm, description: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={3}
                  placeholder="请输入律所简介"
                />
              </div>
            </div>
            <div className="p-6 border-t border-slate-200 flex justify-end gap-3">
              <Button variant="ghost" onClick={() => setShowCreateModal(false)}>
                取消
              </Button>
              <Button
                onClick={handleCreate}
                disabled={!createForm.name.trim() || createMutation.isPending}
              >
                {createMutation.isPending ? '创建中...' : '创建'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑弹窗 */}
      {showEditModal && editingFirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold">编辑律所</h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  律所名称 *
                </label>
                <Input
                  value={editForm.name}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setEditForm({ ...editForm, name: e.target.value })
                  }
                  placeholder="请输入律所名称"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  城市
                </label>
                <Input
                  value={editForm.city}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setEditForm({ ...editForm, city: e.target.value })
                  }
                  placeholder="请输入城市"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  联系电话
                </label>
                <Input
                  value={editForm.phone}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setEditForm({ ...editForm, phone: e.target.value })
                  }
                  placeholder="请输入联系电话"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  地址
                </label>
                <Input
                  value={editForm.address}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setEditForm({ ...editForm, address: e.target.value })
                  }
                  placeholder="请输入地址"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  简介
                </label>
                <textarea
                  value={editForm.description}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                    setEditForm({ ...editForm, description: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={3}
                  placeholder="请输入律所简介"
                />
              </div>
            </div>
            <div className="p-6 border-t border-slate-200 flex justify-end gap-3">
              <Button variant="ghost" onClick={() => setShowEditModal(false)}>
                取消
              </Button>
              <Button
                onClick={handleUpdate}
                disabled={!editForm.name.trim() || updateMutation.isPending}
              >
                {updateMutation.isPending ? '保存中...' : '保存'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
