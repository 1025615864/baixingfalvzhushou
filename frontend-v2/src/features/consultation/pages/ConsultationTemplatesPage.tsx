/**
 * Consultation Templates Page
 * 咨询模板管理页面（管理员用）
 */

import { useState } from 'react';
import { Plus, Pencil, Trash2, Send, Search, MessageSquare, Eye, CircleHelp } from 'lucide-react';

import { Card, Input, Button, Badge, Pagination } from '@/components/ui';

import {
  useConsultationTemplates,
  useCreateConsultationTemplate,
  useUpdateConsultationTemplate,
  useDeleteConsultationTemplate,
  usePublishConsultationTemplate,
} from '../hooks/useConsultationTemplates';
import type { ConsultationTemplate, ConsultationTemplateStatus, ConsultationCategory, ConsultationQuestion } from '../types';

const STATUS_LABELS: Record<ConsultationTemplateStatus, string> = {
  draft: '草稿',
  published: '已发布',
  deprecated: '已废弃',
};

const CATEGORY_LABELS: Record<ConsultationCategory, string> = {
  legal: '法律咨询',
  contract: '合同审查',
  dispute: '纠纷调解',
  other: '其他',
};

const QUESTION_TYPE_LABELS: Record<ConsultationQuestion['type'], string> = {
  text: '文本',
  textarea: '多行文本',
  select: '下拉选择',
  radio: '单选',
  checkbox: '多选',
  date: '日期',
  number: '数字',
};

/**
 * 咨询模板管理页面
 */
export function ConsultationTemplatesPage(): JSX.Element {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState<ConsultationTemplateStatus | ''>('');
  const [categoryFilter, setCategoryFilter] = useState<ConsultationCategory | ''>('');
  const [keyword, setKeyword] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<ConsultationTemplate | null>(null);
  const [previewTemplate, setPreviewTemplate] = useState<ConsultationTemplate | null>(null);

  // 表单状态
  const [formData, setFormData] = useState({
    key: '',
    name: '',
    description: '',
    category: 'legal' as ConsultationCategory,
    questions: [] as ConsultationQuestion[],
    isDefault: false,
  });

  // 问题表单
  const [questionForm, setQuestionForm] = useState({
    id: '',
    type: 'text' as ConsultationQuestion['type'],
    label: '',
    placeholder: '',
    required: false,
    options: '',
  });

  // 数据查询
  const { data: templatesData, isLoading } = useConsultationTemplates({
    page,
    pageSize,
    status: statusFilter || undefined,
    category: categoryFilter || undefined,
    keyword: keyword || undefined,
  });

  // Mutations
  const createMutation = useCreateConsultationTemplate();
  const updateMutation = useUpdateConsultationTemplate();
  const deleteMutation = useDeleteConsultationTemplate();
  const publishMutation = usePublishConsultationTemplate();

  const templates = templatesData?.items ?? [];
  const totalPages = Math.ceil((templatesData?.total ?? 0) / pageSize);

  // 处理创建
  const handleCreate = (): void => {
    createMutation.mutate(
      {
        key: formData.key,
        name: formData.name,
        description: formData.description,
        category: formData.category,
        questions: formData.questions,
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
  const handleEdit = (template: ConsultationTemplate): void => {
    setEditingTemplate(template);
    setFormData({
      key: template.key,
      name: template.name,
      description: template.description,
      category: template.category,
      questions: template.questions,
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
          questions: formData.questions,
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
  const handlePreview = (template: ConsultationTemplate): void => {
    setPreviewTemplate(template);
    setIsPreviewModalOpen(true);
  };

  // 添加问题
  const handleAddQuestion = (): void => {
    if (!questionForm.label.trim()) return;
    const newQuestion: ConsultationQuestion = {
      id: `q_${Date.now()}`,
      type: questionForm.type,
      label: questionForm.label.trim(),
      placeholder: questionForm.placeholder || undefined,
      required: questionForm.required,
    };
    if (['select', 'radio', 'checkbox'].includes(questionForm.type) && questionForm.options) {
      newQuestion.options = questionForm.options.split(',').map((o) => o.trim()).filter(Boolean);
    }
    setFormData({
      ...formData,
      questions: [...formData.questions, newQuestion],
    });
    setQuestionForm({
      id: '',
      type: 'text',
      label: '',
      placeholder: '',
      required: false,
      options: '',
    });
  };

  // 删除问题
  const handleRemoveQuestion = (index: number): void => {
    setFormData({
      ...formData,
      questions: formData.questions.filter((_, i) => i !== index),
    });
  };

  // 重置表单
  const resetForm = (): void => {
    setFormData({
      key: '',
      name: '',
      description: '',
      category: 'legal',
      questions: [],
      isDefault: false,
    });
    setQuestionForm({
      id: '',
      type: 'text',
      label: '',
      placeholder: '',
      required: false,
      options: '',
    });
  };

  return (
    <div className="container mx-auto py-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">咨询模板管理</h1>
          <p className="text-slate-600 mt-1">管理咨询预约表单模板</p>
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
            <MessageSquare className="h-4 w-4 text-slate-500" />
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
            <span className="text-sm text-slate-700">分类：</span>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value as ConsultationCategory | '')}
              className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">全部分类</option>
              {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
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
                        <span>分类: {CATEGORY_LABELS[template.category]}</span>
                        <span>问题: {template.questions.length}个</span>
                        <span>使用: {template.usageCount}次</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handlePreview(template)}
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
                  <CircleHelp className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                  <p>暂无咨询模板</p>
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
                {isCreateModalOpen ? '新建咨询模板' : '编辑咨询模板'}
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
                    placeholder="唯一标识，如：legal_consult_001"
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
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  咨询分类 *
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value as ConsultationCategory })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>

              {/* 问题定义 */}
              <div className="border border-slate-200 rounded-lg p-4">
                <h3 className="font-medium text-slate-900 mb-3">咨询问题</h3>
                <div className="grid grid-cols-6 gap-2 mb-3">
                  <Input
                    placeholder="问题标签"
                    value={questionForm.label}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuestionForm({ ...questionForm, label: e.target.value })}
                    className="col-span-2"
                  />
                  <select
                    value={questionForm.type}
                    onChange={(e) => setQuestionForm({ ...questionForm, type: e.target.value as ConsultationQuestion['type'] })}
                    className="px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {Object.entries(QUESTION_TYPE_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                  <Input
                    placeholder="提示文字"
                    value={questionForm.placeholder}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuestionForm({ ...questionForm, placeholder: e.target.value })}
                  />
                  {['select', 'radio', 'checkbox'].includes(questionForm.type) && (
                    <Input
                      placeholder="选项（逗号分隔）"
                      value={questionForm.options}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuestionForm({ ...questionForm, options: e.target.value })}
                    />
                  )}
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={questionForm.required}
                      onChange={(e) => setQuestionForm({ ...questionForm, required: e.target.checked })}
                    />
                    <span className="text-sm">必填</span>
                  </label>
                  <Button size="sm" onClick={handleAddQuestion}>
                    添加
                  </Button>
                </div>
                {formData.questions.length > 0 && (
                  <div className="space-y-2">
                    {formData.questions.map((q, i) => (
                      <div key={q.id} className="flex items-center gap-2 text-sm bg-slate-50 p-2 rounded">
                        <span className="font-medium">{i + 1}.</span>
                        <span>{q.label}</span>
                        <Badge variant="default" size="sm">{QUESTION_TYPE_LABELS[q.type]}</Badge>
                        {q.required && <Badge variant="danger" size="sm">必填</Badge>}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="ml-auto"
                          onClick={() => handleRemoveQuestion(i)}
                        >
                          <Trash2 className="h-3 w-3 text-red-500" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
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
                  formData.questions.length === 0 ||
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
      {isPreviewModalOpen && previewTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold">模板预览: {previewTemplate.name}</h2>
            </div>
            <div className="p-6 space-y-4">
              {previewTemplate.questions.map((q, i) => (
                <div key={q.id}>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    {i + 1}. {q.label}
                    {q.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  {q.type === 'text' && (
                    <Input placeholder={q.placeholder} disabled />
                  )}
                  {q.type === 'textarea' && (
                    <textarea
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50"
                      placeholder={q.placeholder}
                      rows={3}
                      disabled
                    />
                  )}
                  {q.type === 'number' && (
                    <Input type="number" placeholder={q.placeholder} disabled />
                  )}
                  {q.type === 'date' && (
                    <Input type="date" disabled />
                  )}
                  {q.type === 'select' && (
                    <select className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50" disabled>
                      <option>请选择...</option>
                      {q.options?.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  )}
                  {q.type === 'radio' && (
                    <div className="space-y-2">
                      {q.options?.map((opt) => (
                        <label key={opt} className="flex items-center gap-2">
                          <input type="radio" name={q.id} disabled />
                          <span className="text-sm">{opt}</span>
                        </label>
                      ))}
                    </div>
                  )}
                  {q.type === 'checkbox' && (
                    <div className="space-y-2">
                      {q.options?.map((opt) => (
                        <label key={opt} className="flex items-center gap-2">
                          <input type="checkbox" disabled />
                          <span className="text-sm">{opt}</span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              ))}
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
