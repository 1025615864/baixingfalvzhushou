/**
 * Document Templates Page
 * 文档模板管理页面（管理员用）
 */

import { useState } from 'react';
import { Plus, Pencil, Trash2, Send, Search, FileText, Eye } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Pagination } from '@/components/ui/Pagination';

import {
  useDocumentTemplates,
  useCreateDocumentTemplate,
  useUpdateDocumentTemplate,
  useDeleteDocumentTemplate,
  usePublishDocumentTemplate,
  usePreviewTemplate,
} from '../hooks/useDocumentTemplates';
import type { DocumentTemplate, DocumentTemplateStatus, DocumentType, TemplateVariable } from '../types';
import { DOCUMENT_TYPE_LABELS } from '../types';

const STATUS_LABELS: Record<DocumentTemplateStatus, string> = {
  draft: '草稿',
  published: '已发布',
  deprecated: '已废弃',
};

/**
 * 文档模板管理页面
 */
export function DocumentTemplatesPage(): JSX.Element {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState<DocumentTemplateStatus | ''>('');
  const [typeFilter, setTypeFilter] = useState<DocumentType | ''>('');
  const [keyword, setKeyword] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<DocumentTemplate | null>(null);
  const [previewContent, setPreviewContent] = useState('');

  // 表单状态
  const [formData, setFormData] = useState({
    key: '',
    name: '',
    description: '',
    documentType: 'contract' as DocumentType,
    category: '',
    content: '',
    variables: [] as TemplateVariable[],
    isDefault: false,
  });

  // 变量表单
  const [variableForm, setVariableForm] = useState({
    name: '',
    type: 'text' as TemplateVariable['type'],
    label: '',
    description: '',
    required: false,
  });

  // 数据查询
  const { data: templatesData, isLoading } = useDocumentTemplates({
    page,
    pageSize,
    status: statusFilter || undefined,
    documentType: typeFilter || undefined,
    keyword: keyword || undefined,
  });

  // Mutations
  const createMutation = useCreateDocumentTemplate();
  const updateMutation = useUpdateDocumentTemplate();
  const deleteMutation = useDeleteDocumentTemplate();
  const publishMutation = usePublishDocumentTemplate();
  const previewMutation = usePreviewTemplate();

  const templates = templatesData?.items ?? [];
  const categories = templatesData?.categories ?? [];
  const totalPages = Math.ceil((templatesData?.total ?? 0) / pageSize);

  // 处理创建
  const handleCreate = (): void => {
    createMutation.mutate(
      {
        key: formData.key,
        name: formData.name,
        description: formData.description,
        documentType: formData.documentType,
        category: formData.category,
        content: formData.content,
        variables: formData.variables,
        isDefault: formData.isDefault,
      },
      {
        onSuccess: () => {
          setIsCreateModalOpen(false);
          resetForm();
        },
      }
    );
  };

  // 处理编辑
  const handleEdit = (template: DocumentTemplate): void => {
    setEditingTemplate(template);
    setFormData({
      key: template.key,
      name: template.name,
      description: template.description,
      documentType: template.documentType,
      category: template.category,
      content: template.content,
      variables: template.variables,
      isDefault: template.isDefault,
    });
    setIsEditModalOpen(true);
  };

  // 处理更新
  const handleUpdate = (): void => {
    if (!editingTemplate) return;
    updateMutation.mutate(
      {
        id: editingTemplate.id,
        request: {
          name: formData.name,
          description: formData.description,
          category: formData.category,
          content: formData.content,
          variables: formData.variables,
          isDefault: formData.isDefault,
        },
      },
      {
        onSuccess: () => {
          setIsEditModalOpen(false);
          setEditingTemplate(null);
          resetForm();
        },
      }
    );
  };

  // 处理删除
  const handleDelete = (id: string): void => {
    if (!window.confirm('确定要删除这个模板吗？')) return;
    deleteMutation.mutate(id);
  };

  // 处理发布
  const handlePublish = (id: string): void => {
    if (!window.confirm('确定要发布这个模板吗？')) return;
    publishMutation.mutate(id);
  };

  // 处理预览
  const handlePreview = async (template: DocumentTemplate): Promise<void> => {
    // 使用默认变量值生成预览
    const variables: Record<string, string> = {};
    template.variables.forEach((v) => {
      variables[v.name] = v.defaultValue || `[${v.label}]`;
    });

    const result = await previewMutation.mutateAsync({
      templateId: template.id,
      variables,
    });
    setPreviewContent(result.content);
    setIsPreviewModalOpen(true);
  };

  // 添加变量
  const handleAddVariable = (): void => {
    if (!variableForm.name.trim() || !variableForm.label.trim()) return;
    setFormData({
      ...formData,
      variables: [
        ...formData.variables,
        {
          name: variableForm.name.trim(),
          type: variableForm.type,
          label: variableForm.label.trim(),
          description: variableForm.description,
          required: variableForm.required,
        },
      ],
    });
    setVariableForm({
      name: '',
      type: 'text',
      label: '',
      description: '',
      required: false,
    });
  };

  // 删除变量
  const handleRemoveVariable = (index: number): void => {
    setFormData({
      ...formData,
      variables: formData.variables.filter((_, i) => i !== index),
    });
  };

  // 重置表单
  const resetForm = (): void => {
    setFormData({
      key: '',
      name: '',
      description: '',
      documentType: 'contract',
      category: '',
      content: '',
      variables: [],
      isDefault: false,
    });
    setVariableForm({
      name: '',
      type: 'text',
      label: '',
      description: '',
      required: false,
    });
  };

  return (
    <div className="container mx-auto py-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">文档模板管理</h1>
          <p className="text-slate-600 mt-1">管理法律文书模板</p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="h-4 w-4 mr-1" />
          新建模板
        </Button>
      </div>

      {/* 筛选栏 */}
      <Card className="mb-6">
        <div className="p-4 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-slate-500" />
            <span className="text-sm text-slate-700">状态：</span>
            <div className="flex gap-2">
              <Button
                variant={statusFilter === '' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setStatusFilter('')}
              >
                全部
              </Button>
              <Button
                variant={statusFilter === 'draft' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setStatusFilter('draft')}
              >
                草稿
              </Button>
              <Button
                variant={statusFilter === 'published' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setStatusFilter('published')}
              >
                已发布
              </Button>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-700">类型：</span>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as DocumentType | '')}
              className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">全部类型</option>
              {Object.entries(DOCUMENT_TYPE_LABELS).map(([key, config]) => (
                <option key={key} value={key}>
                  {config.label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[200px] ml-auto">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索模板名称..."
                value={keyword}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  setKeyword(e.target.value);
                  setPage(1);
                }}
                className="pl-10"
              />
            </div>
          </div>
        </div>
      </Card>

      {/* 模板列表 */}
      <Card>
        {isLoading ? (
          <div className="p-6 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-24 bg-slate-100 rounded animate-pulse" />
            ))}
          </div>
        ) : (
          <>
            <div className="divide-y divide-slate-200">
              {templates.map((template) => (
                <div key={template.id} className="p-4 hover:bg-slate-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-medium text-slate-900">{template.name}</h3>
                        <Badge
                          variant={
                            template.status === 'published'
                              ? 'success'
                              : template.status === 'draft'
                              ? 'warning'
                              : 'default'
                          }
                          size="sm"
                        >
                          {STATUS_LABELS[template.status]}
                        </Badge>
                        {template.isDefault && <Badge variant="primary" size="sm">默认</Badge>}
                      </div>
                      <p className="text-sm text-slate-600 mb-2">{template.description}</p>
                      <div className="flex items-center gap-4 text-sm text-slate-500">
                        <span>Key: {template.key}</span>
                        <span>类型: {DOCUMENT_TYPE_LABELS[template.documentType]?.label || template.documentType}</span>
                        <span>分类: {template.category}</span>
                        <span>版本: v{template.version}</span>
                        <span>使用: {template.usageCount}次</span>
                        <span>变量: {template.variables.length}个</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => { void handlePreview(template); }}
                        disabled={previewMutation.isPending}
                        title="预览"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      {template.status === 'draft' && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(template)}
                            title="编辑"
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handlePublish(template.id)}
                            disabled={publishMutation.isPending}
                            title="发布"
                          >
                            <Send className="h-4 w-4 text-green-500" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(template.id)}
                            disabled={deleteMutation.isPending}
                            title="删除"
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {!templates.length && (
                <div className="p-10 text-center text-slate-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                  <p>暂无文档模板</p>
                  <p className="text-sm mt-1">点击&quot;新建模板&quot;按钮创建</p>
                </div>
              )}
            </div>
            {totalPages > 1 && (
              <div className="p-4 border-t border-slate-200">
                <Pagination
                  currentPage={page}
                  totalPages={totalPages}
                  onPageChange={setPage}
                />
              </div>
            )}
          </>
        )}
      </Card>

      {/* 创建/编辑弹窗 */}
      {(isCreateModalOpen || isEditModalOpen) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold">
                {isCreateModalOpen ? '新建文档模板' : '编辑文档模板'}
              </h2>
            </div>
            <div className="p-6 space-y-4">
              {/* 基本信息 */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    模板Key *
                  </label>
                  <Input
                    value={formData.key}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, key: e.target.value })}
                    placeholder="唯一标识，如：contract_001"
                    disabled={isEditModalOpen}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    模板名称 *
                  </label>
                  <Input
                    value={formData.name}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="模板显示名称"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  描述
                </label>
                <Input
                  value={formData.description}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="模板用途描述"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    文档类型 *
                  </label>
                  <select
                    value={formData.documentType}
                    onChange={(e) => setFormData({ ...formData, documentType: e.target.value as DocumentType })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {Object.entries(DOCUMENT_TYPE_LABELS).map(([key, config]) => (
                      <option key={key} value={key}>{config.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    分类
                  </label>
                  <Input
                    value={formData.category}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, category: e.target.value })}
                    placeholder="模板分类"
                    list="categories"
                  />
                  <datalist id="categories">
                    {categories.map((cat) => (
                      <option key={cat} value={cat} />
                    ))}
                  </datalist>
                </div>
              </div>

              {/* 变量定义 */}
              <div className="border border-slate-200 rounded-lg p-4">
                <h3 className="font-medium text-slate-900 mb-3">模板变量</h3>
                <div className="grid grid-cols-5 gap-2 mb-3">
                  <Input
                    placeholder="变量名"
                    value={variableForm.name}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setVariableForm({ ...variableForm, name: e.target.value })}
                  />
                  <Input
                    placeholder="显示名称"
                    value={variableForm.label}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setVariableForm({ ...variableForm, label: e.target.value })}
                  />
                  <select
                    value={variableForm.type}
                    onChange={(e) => setVariableForm({ ...variableForm, type: e.target.value as TemplateVariable['type'] })}
                    className="px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="text">文本</option>
                    <option value="number">数字</option>
                    <option value="date">日期</option>
                    <option value="select">选择</option>
                    <option value="textarea">多行文本</option>
                  </select>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={variableForm.required}
                      onChange={(e) => setVariableForm({ ...variableForm, required: e.target.checked })}
                    />
                    <span className="text-sm">必填</span>
                  </label>
                  <Button size="sm" onClick={handleAddVariable}>
                    添加
                  </Button>
                </div>
                {formData.variables.length > 0 && (
                  <div className="space-y-2">
                    {formData.variables.map((v, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm bg-slate-50 p-2 rounded">
                        <code className="text-blue-600">{v.name}</code>
                        <span className="text-slate-600">{v.label}</span>
                        <Badge variant="default" size="sm">{v.type}</Badge>
                        {v.required && <Badge variant="danger" size="sm">必填</Badge>}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="ml-auto"
                          onClick={() => handleRemoveVariable(i)}
                        >
                          <Trash2 className="h-3 w-3 text-red-500" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 模板内容 */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  模板内容 *
                </label>
                <textarea
                  value={formData.content}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData({ ...formData, content: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                  rows={10}
                  placeholder="使用 {{变量名}} 插入变量"
                />
              </div>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.isDefault}
                  onChange={(e) => setFormData({ ...formData, isDefault: e.target.checked })}
                />
                <span className="text-sm">设为默认模板</span>
              </label>
            </div>
            <div className="p-6 border-t border-slate-200 flex justify-end gap-3">
              <Button
                variant="ghost"
                onClick={() => {
                  if (isCreateModalOpen) {
                    setIsCreateModalOpen(false);
                  } else {
                    setIsEditModalOpen(false);
                    setEditingTemplate(null);
                  }
                  resetForm();
                }}
              >
                取消
              </Button>
              <Button
                onClick={isCreateModalOpen ? handleCreate : handleUpdate}
                disabled={
                  !formData.key.trim() ||
                  !formData.name.trim() ||
                  !formData.content.trim() ||
                  (isCreateModalOpen ? createMutation.isPending : updateMutation.isPending)
                }
              >
                {isCreateModalOpen
                  ? createMutation.isPending
                    ? '创建中...'
                    : '创建'
                  : updateMutation.isPending
                  ? '保存中...'
                  : '保存'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 预览弹窗 */}
      {isPreviewModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold">模板预览</h2>
            </div>
            <div className="p-6">
              <pre className="bg-slate-50 p-4 rounded-lg text-sm whitespace-pre-wrap font-mono">
                {previewContent}
              </pre>
            </div>
            <div className="p-6 border-t border-slate-200 flex justify-end">
              <Button onClick={() => setIsPreviewModalOpen(false)}>关闭</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
