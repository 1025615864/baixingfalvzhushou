/**
 * DomainForm - 域名表单组件
 */

import { useState, useEffect } from 'react';

import type { DomainConfig, DomainFormData, HttpMethod } from '../types';

interface DomainFormProps {
  domain?: DomainConfig | null;
  onSubmit: (data: DomainFormData) => void;
  onCancel: () => void;
  isSubmitting: boolean;
}

const HTTP_METHODS: HttpMethod[] = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'];

const DEFAULT_HEADERS = [
  'Content-Type',
  'Authorization',
  'X-Requested-With',
  'Accept',
  'Origin',
  'X-CSRF-Token',
];

/**
 * 域名表单组件
 */
export function DomainForm({ domain, onSubmit, onCancel, isSubmitting }: DomainFormProps): JSX.Element {
  const [formData, setFormData] = useState<DomainFormData>({
    domain: '',
    description: '',
    allowedOrigins: '',
    allowedMethods: ['GET', 'POST'],
    allowedHeaders: '',
    allowCredentials: false,
    maxAge: 86400,
  });

  useEffect(() => {
    if (domain) {
      setFormData({
        domain: domain.domain,
        description: domain.description || '',
        allowedOrigins: domain.allowedOrigins.join('\n'),
        allowedMethods: domain.allowedMethods,
        allowedHeaders: domain.allowedHeaders.join('\n'),
        allowCredentials: domain.allowCredentials,
        maxAge: domain.maxAge,
      });
    }
  }, [domain]);

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleMethodToggle = (method: HttpMethod): void => {
    setFormData(prev => ({
      ...prev,
      allowedMethods: prev.allowedMethods.includes(method)
        ? prev.allowedMethods.filter(m => m !== method)
        : [...prev.allowedMethods, method],
    }));
  };

  const handleSelectAllMethods = (): void => {
    setFormData(prev => ({
      ...prev,
      allowedMethods: prev.allowedMethods.length === HTTP_METHODS.length ? [] : [...HTTP_METHODS],
    }));
  };

  const handleAddDefaultHeaders = (): void => {
    const currentHeaders = formData.allowedHeaders
      .split('\n')
      .map(h => h.trim())
      .filter(Boolean);

    const newHeaders = [...new Set([...currentHeaders, ...DEFAULT_HEADERS])];
    setFormData(prev => ({
      ...prev,
      allowedHeaders: newHeaders.join('\n'),
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* 域名 */}
      <div>
        <label htmlFor="domain" className="block text-sm font-medium text-gray-700 mb-1">
          域名 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="domain"
          value={formData.domain}
          onChange={(e) => setFormData(prev => ({ ...prev, domain: e.target.value }))}
          placeholder="example.com"
          disabled={!!domain}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
        />
        <p className="mt-1 text-xs text-gray-500">请输入完整的域名，如 example.com</p>
      </div>

      {/* 描述 */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
          描述
        </label>
        <input
          type="text"
          id="description"
          value={formData.description}
          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
          placeholder="域名用途描述"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* 允许的源 */}
      <div>
        <label htmlFor="allowedOrigins" className="block text-sm font-medium text-gray-700 mb-1">
          允许的源（Access-Control-Allow-Origin）
        </label>
        <textarea
          id="allowedOrigins"
          value={formData.allowedOrigins}
          onChange={(e) => setFormData(prev => ({ ...prev, allowedOrigins: e.target.value }))}
          placeholder="https://app.example.com&#10;https://www.example.com&#10;*"
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
        />
        <p className="mt-1 text-xs text-gray-500">每行一个域名，使用 * 允许所有源</p>
      </div>

      {/* 允许的 HTTP 方法 */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-gray-700">
            允许的 HTTP 方法
          </label>
          <button
            type="button"
            onClick={handleSelectAllMethods}
            className="text-xs text-blue-600 hover:text-blue-700"
          >
            {formData.allowedMethods.length === HTTP_METHODS.length ? '取消全选' : '全选'}
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {HTTP_METHODS.map((method) => (
            <button
              key={method}
              type="button"
              onClick={() => handleMethodToggle(method)}
              className={`px-3 py-1.5 text-sm font-medium rounded-md border transition-colors ${
                formData.allowedMethods.includes(method)
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
              }`}
            >
              {method}
            </button>
          ))}
        </div>
      </div>

      {/* 允许的请求头 */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label htmlFor="allowedHeaders" className="block text-sm font-medium text-gray-700">
            允许的请求头（Access-Control-Allow-Headers）
          </label>
          <button
            type="button"
            onClick={handleAddDefaultHeaders}
            className="text-xs text-blue-600 hover:text-blue-700"
          >
            添加默认请求头
          </button>
        </div>
        <textarea
          id="allowedHeaders"
          value={formData.allowedHeaders}
          onChange={(e) => setFormData(prev => ({ ...prev, allowedHeaders: e.target.value }))}
          placeholder="Content-Type&#10;Authorization"
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
        />
        <p className="mt-1 text-xs text-gray-500">每行一个请求头名称</p>
      </div>

      {/* 允许凭证 */}
      <div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={formData.allowCredentials}
            onChange={(e) => setFormData(prev => ({ ...prev, allowCredentials: e.target.checked }))}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">允许携带凭证（Access-Control-Allow-Credentials）</span>
        </label>
        <p className="mt-1 text-xs text-gray-500 ml-6">
          允许跨域请求携带 Cookie、HTTP 认证等凭证信息
        </p>
      </div>

      {/* 预检缓存时间 */}
      <div>
        <label htmlFor="maxAge" className="block text-sm font-medium text-gray-700 mb-1">
          预检请求缓存时间（秒）
        </label>
        <input
          type="number"
          id="maxAge"
          value={formData.maxAge}
          onChange={(e) => setFormData(prev => ({ ...prev, maxAge: parseInt(e.target.value, 10) || 0 }))}
          min={0}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p className="mt-1 text-xs text-gray-500">
          浏览器缓存预检请求结果的时间，默认 86400 秒（24小时）
        </p>
      </div>

      {/* 按钮 */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50"
        >
          取消
        </button>
        <button
          type="submit"
          disabled={isSubmitting || !formData.domain.trim()}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {isSubmitting ? '保存中...' : domain ? '保存修改' : '添加域名'}
        </button>
      </div>
    </form>
  );
}