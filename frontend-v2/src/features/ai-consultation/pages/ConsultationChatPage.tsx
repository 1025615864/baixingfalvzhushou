/**
 * ConsultationChatPage - 咨询聊天页面
 * 
 * 用户与律师进行实时聊天的页面
 */

import { useState, useRef, useEffect } from 'react';
import { useParams } from 'react-router-dom';

/**
 * 聊天消息接口
 */
interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'lawyer';
  timestamp: string;
}

// Mock 初始消息
const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: '1',
    content: '您好，我是张律师，请问有什么可以帮您？',
    role: 'lawyer',
    timestamp: new Date(Date.now() - 60000).toISOString(),
  },
];

/**
 * 咨询聊天页面
 */
export function ConsultationChatPage(): JSX.Element {
  const { id } = useParams<{ id: string }>(); // eslint-disable-line @typescript-eslint/no-unused-vars
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    setIsSending(true);

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      role: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputValue('');

    // 模拟律师回复
    setTimeout(() => {
      const replyMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: '收到您的问题，我会尽快为您解答。关于您提到的情况，需要进一步了解具体细节...',
        role: 'lawyer',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, replyMessage]);
      setIsSending(false);
    }, 1500);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* 顶部标题 */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <h1 className="text-lg font-bold text-gray-900" data-testid="page-title">咨询聊天</h1>
        <p className="text-sm text-gray-500">与律师实时沟通</p>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            data-testid="chat-message"
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs md:max-w-md lg:max-w-lg px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-gray-200 text-gray-900'
              }`}
            >
              <p className="text-sm">{message.content}</p>
              <p
                className={`text-xs mt-1 ${
                  message.role === 'user' ? 'text-blue-100' : 'text-gray-400'
                }`}
              >
                {new Date(message.timestamp).toLocaleTimeString('zh-CN', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-2">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入您的问题..."
              disabled={isSending}
              data-testid="chat-input"
              rows={2}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 resize-none"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isSending}
              data-testid="send-button"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {isSending ? '发送中...' : '发送'}
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2">按 Enter 发送，Shift + Enter 换行</p>
        </div>
      </div>
    </div>
  );
}