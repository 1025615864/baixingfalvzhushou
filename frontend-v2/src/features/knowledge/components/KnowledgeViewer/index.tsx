import { createSafeHtml } from '@/shared/lib/security/xss';

/**
 * 知识查看器组件
 * 显示知识内容，支持基本的文本格式化
 */

interface KnowledgeViewerProps {
  content: string;
  className?: string;
}

/**
 * 知识查看器组件 - 渲染格式化内容
 */
export function KnowledgeViewer({ content, className = '' }: KnowledgeViewerProps): JSX.Element {
  // 简单的内容格式化处理
  const formattedContent = content
    // 处理换行
    .split('\n')
    .map((line, index) => {
      // 处理标题（## 或 ### 开头）
      if (line.startsWith('## ')) {
        return (
          <h2
            key={index}
            className="text-xl font-semibold text-gray-800 mt-6 mb-3"
          >
            {line.replace('## ', '')}
          </h2>
        );
      }
      if (line.startsWith('### ')) {
        return (
          <h3
            key={index}
            className="text-lg font-medium text-gray-700 mt-5 mb-2"
          >
            {line.replace('### ', '')}
          </h3>
        );
      }
      if (line.startsWith('# ')) {
        return (
          <h1
            key={index}
            className="text-2xl font-bold text-gray-900 mt-8 mb-4 pb-2 border-b border-gray-200"
          >
            {line.replace('# ', '')}
          </h1>
        );
      }

      // 处理列表项（- 或 * 开头）
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        return (
          <li key={index} className="ml-6 text-gray-700 mb-1">
            {line.trim().replace(/^[-*] /, '')}
          </li>
        );
      }

      // 处理数字列表
      if (/^\d+\.\s/.test(line.trim())) {
        return (
          <li key={index} className="ml-6 text-gray-700 mb-1 list-decimal">
            {line.trim().replace(/^\d+\.\s/, '')}
          </li>
        );
      }

      // 处理引用块（> 开头）
      if (line.trim().startsWith('> ')) {
        return (
          <blockquote
            key={index}
            className="border-l-4 border-primary-300 pl-4 py-2 my-4 bg-gray-50 italic text-gray-600"
          >
            {line.trim().replace('> ', '')}
          </blockquote>
        );
      }

      // 处理分隔线
      if (line.trim() === '---' || line.trim() === '***') {
        return <hr key={index} className="my-6 border-gray-200" />;
      }

      // 处理加粗文本 **text**
      const boldProcessed = line.replace(
        /\*\*(.*?)\*\*/g,
        '<strong class="font-semibold text-gray-900">$1</strong>'
      );

      // 处理斜体文本 *text*
      const italicProcessed = boldProcessed.replace(
        /\*(.*?)\*/g,
        '<em class="italic text-gray-700">$1</em>'
      );

      // 普通段落
      if (line.trim() === '') {
        return <div key={index} className="h-4" />;
      }

      return (
        <p
          key={index}
          className="text-gray-700 leading-relaxed mb-4"
          dangerouslySetInnerHTML={createSafeHtml(italicProcessed)}
        />
      );
    });

  return (
    <div className={`knowledge-content ${className}`}>
      {formattedContent}
    </div>
  );
}