/**
 * AIResponseFormatter - AI 响应格式化组件
 *
 * 用于格式化显示 AI 的响应内容，支持 Markdown 解析、代码高亮等
 */

import { useMemo } from 'react';

import type { AISource, LegalReference } from '../types';

interface AIResponseFormatterProps {
  /** 响应内容 */
  content: string;
  /** 是否显示引用来源 */
  showSources?: boolean;
  /** 引用来源列表 */
  sources?: AISource[];
  /** 是否显示法律引用 */
  showLegalReferences?: boolean;
  /** 法律引用列表 */
  legalReferences?: LegalReference[];
  /** 自定义类名 */
  className?: string;
}

/**
 * 解析简单的 Markdown 格式
 */
function parseMarkdown(text: string): string {
  // 处理标题
  let html = text
    // 处理代码块
    .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre class="bg-gray-100 p-3 rounded-lg my-2 overflow-x-auto"><code>$2</code></pre>')
    // 处理行内代码
    .replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono text-red-600">$1</code>')
    // 处理粗体
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold">$1</strong>')
    // 处理斜体
    .replace(/\*([^*]+)\*/g, '<em class="italic">$1</em>')
    // 处理删除线
    .replace(/~~([^~]+)~~/g, '<del class="line-through">$1</del>')
    // 处理链接
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 hover:text-blue-800 hover:underline" target="_blank" rel="noopener noreferrer">$1</a>')
    // 处理无序列表
    .replace(/^- (.+)$/gm, '<li class="ml-4 list-disc">$1</li>')
    // 处理有序列表
    .replace(/^\d+\. (.+)$/gm, '<li class="ml-4 list-decimal">$1</li>')
    // 处理引用
    .replace(/^> (.+)$/gm, '<blockquote class="border-l-4 border-blue-500 pl-4 py-1 my-2 text-gray-600 italic">$1</blockquote>')
    // 处理水平分割线
    .replace(/^---$/gm, '<hr class="my-4 border-gray-200">')
    // 处理段落（简单的换行处理）
    .replace(/\n\n/g, '</p><p class="mb-2">')
    .replace(/\n/g, '<br>');

  // 包裹段落
  if (!html.startsWith('<')) {
    html = `<p class="mb-2">${html}</p>`;
  }

  return html;
}

/**
 * 获取来源类型图标
 */
function getSourceTypeIcon(type: string): string {
  const iconMap: Record<string, string> = {
    law: '⚖️',
    case: '📋',
    article: '📄',
    document: '📎',
    knowledge_base: '📚',
  };
  return iconMap[type] || '📄';
}

/**
 * 获取来源类型标签
 */
function getSourceTypeLabel(type: string): string {
  const labelMap: Record<string, string> = {
    law: '法律法规',
    case: '案例',
    article: '文章',
    document: '文档',
    knowledge_base: '知识库',
  };
  return labelMap[type] || '其他';
}

/**
 * AI 响应格式化组件
 */
export function AIResponseFormatter({
  content,
  showSources = true,
  sources = [],
  showLegalReferences = true,
  legalReferences = [],
  className = '',
}: AIResponseFormatterProps): JSX.Element {
  // 解析 Markdown 内容
  const parsedContent = useMemo(() => parseMarkdown(content), [content]);

  // 过滤有效的来源
  const validSources = useMemo(() => 
    sources.filter(s => s.title && s.title.trim() !== ''),
  [sources]);

  // 过滤有效的法律引用
  const validLegalReferences = useMemo(() => 
    legalReferences.filter(l => l.lawName && l.lawName.trim() !== ''),
  [legalReferences]);

  const hasSources = validSources.length > 0;
  const hasLegalReferences = validLegalReferences.length > 0;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 主要内容 */}
      <div 
        className="prose prose-sm max-w-none text-gray-800 leading-relaxed"
        dangerouslySetInnerHTML={{ __html: parsedContent }}
      />

      {/* 法律引用 */}
      {showLegalReferences && hasLegalReferences && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <h4 className="text-sm font-medium text-gray-600 mb-2 flex items-center gap-2">
            <span>📜</span>
            <span>相关法律依据</span>
          </h4>
          <div className="space-y-2">
            {validLegalReferences.map((reference, index) => (
              <div 
                key={`${reference.lawName}-${reference.articleNumber}-${index}`}
                className="bg-blue-50 rounded-lg p-3 text-sm"
              >
                <div className="font-medium text-blue-800 mb-1">
                  {reference.lawName} {reference.articleNumber}
                </div>
                <div className="text-blue-700 text-xs leading-relaxed">
                  {reference.content}
                </div>
                {reference.fullTextUrl && (
                  <a 
                    href={reference.fullTextUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 mt-2 text-xs text-blue-600 hover:text-blue-800"
                  >
                    <span>查看完整条文</span>
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 引用来源 */}
      {showSources && hasSources && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <h4 className="text-sm font-medium text-gray-600 mb-2 flex items-center gap-2">
            <span>🔗</span>
            <span>参考来源</span>
          </h4>
          <div className="flex flex-wrap gap-2">
            {validSources.map((source, index) => (
              <div 
                key={`${source.id}-${index}`}
                className="group flex items-center gap-2 bg-gray-50 hover:bg-gray-100 
                         rounded-full px-3 py-1.5 text-xs transition-colors"
              >
                <span className="text-base">{getSourceTypeIcon(source.type)}</span>
                <span className="text-gray-600">{getSourceTypeLabel(source.type)}</span>
                {source.url ? (
                  <a 
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 hover:underline max-w-[150px] truncate"
                    title={source.title}
                  >
                    {source.title}
                  </a>
                ) : (
                  <span className="text-gray-800 max-w-[150px] truncate" title={source.title}>
                    {source.title}
                  </span>
                )}
                {source.relevanceScore !== undefined && (
                  <span className="text-gray-400">
                    {Math.round(source.relevanceScore * 100)}%
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}