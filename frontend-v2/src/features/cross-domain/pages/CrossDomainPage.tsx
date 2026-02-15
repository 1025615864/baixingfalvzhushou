/**
 * CrossDomainPage - 跨域管理页面
 */

import { useState } from 'react';

import type { DomainConfig, DomainFormData } from '../types';
import { useDomainList, useAddDomain, useUpdateDomain, useDeleteDomain, useVerifyDomain } from '../hooks/useCrossDomain';
import { DomainList } from '../components/DomainList';
import { DomainForm } from '../components/DomainForm';

/**
 * 跨域管理页面
 */
export function CrossDomainPage(): JSX.Element {
  const [showForm, setShowForm] = useState<boolean>(false);
  const [editingDomain, setEditingDomain] = useState<DomainConfig | null>(null);
  const [verifyingDomain, setVerifyingDomain] = useState<DomainConfig | null>(null);

  const { data: domains, isLoading, error } = useDomainList();
  const addMutation = useAddDomain();
  const updateMutation = useUpdateDomain(editingDomain?.id || 0);
  const deleteMutation = useDeleteDomain();
  const verifyMutation = useVerifyDomain();

  const handleAdd = (): void => {
    setEditingDomain(null);
    setShowForm(true);
  };

  const handleEdit = (domain: DomainConfig): void => {
    setEditingDomain(domain);
    setShowForm(true);
  };

  const handleDelete = (domainId: number): void => {
    if (!window.confirm('确定要删除该域名吗？此操作不可恢复。')) return;
    void deleteMutation.mutateAsync(domainId);
  };

  const handleVerify = (domain: DomainConfig): void => {
    setVerifyingDomain(domain);
  };

  const handleSubmit = (formData: DomainFormData): void => {
    const requestData = {
      domain: formData.domain,
      description: formData.description,
      allowedOrigins: formData.allowedOrigins.split('\n').map(o => o.trim()).filter(Boolean),
      allowedMethods: formData.allowedMethods,
      allowedHeaders: formData.allowedHeaders.split('\n').map(h => h.trim()).filter(Boolean),
      allowCredentials: formData.allowCredentials,
      maxAge: formData.maxAge,
    };

    if (editingDomain) {
      void updateMutation.mutateAsync(requestData).then(() => {
        setShowForm(false);
        setEditingDomain(null);
      });
    } else {
      void addMutation.mutateAsync(requestData).then(() => {
        setShowForm(false);
      });
    }
  };

  const handleVerifySubmit = (method: 'dns' | 'file' | 'meta'): void => {
    if (!verifyingDomain) return;

    void verifyMutation.mutateAsync({
      domainId: verifyingDomain.id,
      verificationMethod: method,
    }).then(() => {
      setVerifyingDomain(null);
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      {/* 页面头部 */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">跨域管理</h1>
            <p className="mt-2 text-sm text-gray-600">
              管理您的域名跨域配置，控制哪些网站可以访问您的资源
            </p>
          </div>
          {!showForm && (
            <button
              onClick={handleAdd}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              添加域名
            </button>
          )}
        </div>
      </div>

      {/* 主内容区 */}
      <div className="max-w-7xl mx-auto">
        {showForm ? (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                {editingDomain ? '编辑域名' : '添加域名'}
              </h2>
              <button
                onClick={() => {
                  setShowForm(false);
                  setEditingDomain(null);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="max-w-2xl">
              <DomainForm
                domain={editingDomain}
                onSubmit={handleSubmit}
                onCancel={() => {
                  setShowForm(false);
                  setEditingDomain(null);
                }}
                isSubmitting={addMutation.isPending || updateMutation.isPending}
              />
            </div>
          </div>
        ) : (
          <DomainList
            domains={domains || []}
            isLoading={isLoading}
            error={error}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onVerify={handleVerify}
          />
        )}
      </div>

      {/* 验证弹窗 */}
      {verifyingDomain && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-2">验证域名</h3>
            <p className="text-sm text-gray-600 mb-4">
              请选择验证方式以验证域名 <strong>{verifyingDomain.domain}</strong> 的所有权
            </p>
            
            <div className="space-y-3 mb-6">
              <button
                onClick={() => handleVerifySubmit('dns')}
                disabled={verifyMutation.isPending}
                className="w-full p-4 text-left border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
              >
                <div className="font-medium text-gray-900">DNS 验证</div>
                <div className="text-sm text-gray-500 mt-1">在域名的 DNS 记录中添加 TXT 记录</div>
              </button>
              
              <button
                onClick={() => handleVerifySubmit('file')}
                disabled={verifyMutation.isPending}
                className="w-full p-4 text-left border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
              >
                <div className="font-medium text-gray-900">文件验证</div>
                <div className="text-sm text-gray-500 mt-1">上传验证文件到网站根目录</div>
              </button>
              
              <button
                onClick={() => handleVerifySubmit('meta')}
                disabled={verifyMutation.isPending}
                className="w-full p-4 text-left border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
              >
                <div className="font-medium text-gray-900">Meta 标签验证</div>
                <div className="text-sm text-gray-500 mt-1">在网站首页添加 Meta 标签</div>
              </button>
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setVerifyingDomain(null)}
                disabled={verifyMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}