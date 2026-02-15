import { useState } from 'react';
import { Send, User, Sparkles, Link, Mic, MoreVertical, History, Trash2, MessageSquare } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import type { ChatMessage } from '@/features/chat/types';

// 模拟消息列表组件
function MessageList({ messages, isStreaming }: { messages: ChatMessage[]; isStreaming: boolean }): JSX.Element {
  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-primary-500/30">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h3 className="text-xl font-semibold text-slate-900 mb-2">
            开始您的法律咨询
          </h3>
          <p className="text-slate-600 mb-6">
            我是您的AI法律助手，可以为您解答各类法律问题，包括合同纠纷、劳动争议、婚姻家庭等
          </p>
          <div className="flex flex-wrap gap-2 justify-center">
            {['劳动合同纠纷', '房屋租赁问题', '交通事故处理', '离婚财产分割'].map((topic) => (
              <button
                key={topic}
                className="px-3 py-1.5 bg-slate-100 hover:bg-primary-50 hover:text-primary-600 text-slate-600 text-sm rounded-lg transition-colors"
              >
                {topic}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
        >
          {/* 头像 */}
          <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center ${
            message.role === 'user'
              ? 'bg-gradient-to-br from-primary-500 to-primary-600'
              : 'bg-gradient-to-br from-secondary-500 to-secondary-600'
          }`}>
            {message.role === 'user' ? (
              <User className="w-5 h-5 text-white" />
            ) : (
              <Sparkles className="w-5 h-5 text-white" />
            )}
          </div>

          {/* 消息内容 */}
          <div className={`max-w-[80%] ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className={`inline-block px-4 py-3 rounded-2xl ${
              message.role === 'user'
                ? 'bg-primary-600 text-white rounded-br-md'
                : 'bg-slate-100 text-slate-900 rounded-bl-md'
            }`}>
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
            </div>
            <span className="text-xs text-slate-400 mt-1 block">
              {new Date(message.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>
      ))}

      {/* 加载状态 */}
      {isStreaming && (
        <div className="flex gap-4">
          <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-secondary-500 to-secondary-600 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div className="bg-slate-100 rounded-2xl rounded-bl-md px-4 py-3">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// 聊天输入组件
function ChatInput({ onSend, isLoading }: { onSend: (message: string) => void; isLoading: boolean }): JSX.Element {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSend(input);
      setInput('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t border-slate-100 bg-white">
      <div className="flex items-end gap-2 max-w-4xl mx-auto">
        <div className="flex-1 relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="输入您的问题..."
            rows={1}
            className="w-full px-4 py-3 pr-24 bg-slate-50 border border-slate-200 rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 focus:bg-white transition-all"
            style={{ minHeight: '52px', maxHeight: '120px' }}
          />
          <div className="absolute right-2 bottom-2 flex items-center gap-1">
            <button
              type="button"
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              title="上传文件"
            >
              <Link className="w-4 h-4" />
            </button>
            <button
              type="button"
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              title="语音输入"
            >
              <Mic className="w-4 h-4" />
            </button>
          </div>
        </div>
        <Button
          type="submit"
          variant="primary"
          size="lg"
          isLoading={isLoading}
          className="flex-shrink-0 rounded-xl"
        >
          <Send className="w-5 h-5" />
        </Button>
      </div>
      <p className="text-xs text-slate-400 text-center mt-2">
        AI生成的内容仅供参考，不构成法律建议。重要法律问题请咨询专业律师。
      </p>
    </form>
  );
}

export function ChatPage(): JSX.Element {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const handleSendMessage = (content: string): void => {
    if (!content.trim() || isStreaming) return;

    const userMessage: ChatMessage = {
      id: generateMessageId(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
      status: 'completed',
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsStreaming(true);

    // 模拟AI响应
    setTimeout(() => {
      const aiMessage: ChatMessage = {
        id: generateMessageId(),
        role: 'assistant',
        content: '感谢您的咨询。根据您描述的情况，我建议您：\n\n1. 首先收集相关证据材料\n2. 了解相关法律规定\n3. 考虑与对方协商解决\n4. 如需进一步帮助，可以预约专业律师咨询\n\n请问您还有其他问题吗？',
        timestamp: new Date().toISOString(),
        status: 'completed',
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsStreaming(false);
    }, 2000);
  };

  return (
    <div className="h-[calc(100vh-64px)] flex bg-slate-50">
      {/* 侧边栏 - 对话历史 */}
      <aside className="hidden lg:flex w-64 flex-col bg-white border-r border-slate-200">
        <div className="p-4 border-b border-slate-100">
          <Button variant="primary" fullWidth leftIcon={<Sparkles className="w-4 h-4" />}>
            新对话
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider px-3 py-2">
            今天
          </div>
          {['劳动合同纠纷咨询', '房屋租赁合同审查', '交通事故赔偿计算'].map((title, index) => (
            <button
              key={index}
              className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-slate-700 hover:bg-slate-50 rounded-lg transition-colors text-left"
            >
              <MessageSquare className="w-4 h-4 text-slate-400 flex-shrink-0" />
              <span className="truncate">{title}</span>
            </button>
          ))}
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider px-3 py-2 mt-4">
            昨天
          </div>
          {['离婚财产分割问题', '公司股权纠纷咨询'].map((title, index) => (
            <button
              key={index}
              className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-slate-700 hover:bg-slate-50 rounded-lg transition-colors text-left"
            >
              <MessageSquare className="w-4 h-4 text-slate-400 flex-shrink-0" />
              <span className="truncate">{title}</span>
            </button>
          ))}
        </div>
        <div className="p-4 border-t border-slate-100">
          <button className="flex items-center gap-2 text-sm text-slate-500 hover:text-red-600 transition-colors">
            <Trash2 className="w-4 h-4" />
            清空对话
          </button>
        </div>
      </aside>

      {/* 主聊天区域 */}
      <main className="flex-1 flex flex-col bg-white rounded-2xl m-4 shadow-soft overflow-hidden">
        {/* 头部 */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-900">AI法律咨询</h1>
              <p className="text-sm text-slate-500">随时为您解答法律问题</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors lg:hidden">
              <History className="w-5 h-5" />
            </button>
            <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
              <MoreVertical className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* 消息列表 */}
        <MessageList messages={messages} isStreaming={isStreaming} />

        {/* 输入区域 */}
        <ChatInput onSend={(msg): void => { void handleSendMessage(msg); }} isLoading={isStreaming} />
      </main>
    </div>
  );
}

function generateMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}
