/**
 * ChatPage - AI 聊天页面
 * 提供与 AI 法律助手的实时对话功能
 * 连接真实后端 API
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { MessageSquare, Plus, Trash2, X, Sparkles, List } from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/Loading';

import type { ChatMessage } from '../types';
import {
  useSendMessage,
  useChatHistory,
  useChatSessions,
  useDeleteChatSession,
  chatKeys,
} from '../hooks/useChat';
import { MessageList } from '../components/MessageList';
import { ChatInput } from '../components/ChatInput';



export function ChatPage(): JSX.Element {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(sessionId);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);

  // 获取会话列表
  const { data: sessions, isLoading: sessionsLoading } = useChatSessions();

  // 获取当前会话的历史消息
  const { data: historyMessages, isLoading: historyLoading } = useChatHistory(
    currentSessionId ?? ''
  );

  // 发送消息 - 连接真实后端 API
  const sendMessageMutation = useSendMessage({
    onSuccess: (data) => {
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.content,
        timestamp: new Date().toISOString(),
        status: 'completed',
        metadata: data.metadata,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsStreaming(false);

      // 如果是新会话，更新 URL 并刷新会话列表
      if (!currentSessionId && data.sessionId) {
        setCurrentSessionId(data.sessionId);
        navigate(`/chat/${data.sessionId}`, { replace: true });
        // 刷新会话列表
        void queryClient.invalidateQueries({ queryKey: chatKeys.sessions() });
      }
    },
    onError: () => {
      setIsStreaming(false);
      // 添加错误消息
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: '抱歉，发生了错误，请稍后重试。',
        timestamp: new Date().toISOString(),
        status: 'error',
        error: '发送失败',
      };
      setMessages((prev) => [...prev, errorMessage]);
    },
  });

  // 删除会话
  const deleteSessionMutation = useDeleteChatSession();

  // 同步历史消息
  useEffect(() => {
    if (historyMessages) {
      setMessages(historyMessages);
    }
  }, [historyMessages]);

  // 同步 URL 参数中的 sessionId
  useEffect(() => {
    if (sessionId) {
      setCurrentSessionId(sessionId);
    }
  }, [sessionId]);

  // 点击外部关闭侧边栏
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        sidebarRef.current &&
        !sidebarRef.current.contains(event.target as Node) &&
        isSidebarOpen
      ) {
        setIsSidebarOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isSidebarOpen]);

  // 发送消息处理 - 直接发送到后端，后端会自动创建会话
  const handleSendMessage = useCallback(
    (content: string) => {
      // 添加用户消息
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
        status: 'completed',
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsStreaming(true);

      // 直接发送消息到后端，后端会自动创建或使用现有会话
      sendMessageMutation.mutate({
        sessionId: currentSessionId,
        content,
      });
    },
    [currentSessionId, sendMessageMutation]
  );

  // 创建新会话（清空当前对话）
  const handleNewChat = useCallback(() => {
    setCurrentSessionId(undefined);
    setMessages([]);
    navigate('/chat');
    setIsSidebarOpen(false);
  }, [navigate]);

  // 选择会话
  const handleSelectSession = useCallback(
    (id: string) => {
      setCurrentSessionId(id);
      navigate(`/chat/${id}`);
      setIsSidebarOpen(false);
    },
    [navigate]
  );

  // 删除会话
  const handleDeleteSession = useCallback(
    (id: string, event: React.MouseEvent) => {
      event.stopPropagation();
      deleteSessionMutation.mutate(id);
      if (currentSessionId === id) {
        handleNewChat();
      }
    },
    [deleteSessionMutation, currentSessionId, handleNewChat]
  );

  const isLoading = historyLoading || sendMessageMutation.isPending;

  return (
    <div className="flex h-[calc(100vh-64px)] bg-slate-50">
      {/* 侧边栏 - 桌面端 */}
      <aside className="hidden md:flex w-64 flex-col bg-white border-r border-slate-200">
        <div className="p-4 border-b border-slate-200">
          <Button
            variant="primary"
            className="w-full"
            onClick={handleNewChat}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            新建对话
          </Button>
        </div>

        {/* 会话列表 */}
        <div className="flex-1 overflow-y-auto p-2">
          {sessionsLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner size="sm" />
            </div>
          ) : sessions && sessions.length > 0 ? (
            <div className="space-y-1">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => handleSelectSession(session.id)}
                  className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                    currentSessionId === session.id
                      ? 'bg-primary-50 text-primary-700'
                      : 'hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <MessageSquare className="w-4 h-4 flex-shrink-0" />
                    <span className="truncate text-sm">{session.title}</span>
                  </div>
                  <button
                    onClick={(e) => handleDeleteSession(session.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-200 rounded transition-opacity"
                  >
                    <Trash2 className="w-4 h-4 text-slate-400" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-slate-500 py-8 text-sm">
              暂无历史对话
            </div>
          )}
        </div>
      </aside>

      {/* 移动端侧边栏 */}
      {isSidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/50" />
          <aside
            ref={sidebarRef}
            className="absolute left-0 top-0 h-full w-64 bg-white shadow-xl"
          >
            <div className="flex items-center justify-between p-4 border-b border-slate-200">
              <h2 className="font-semibold text-slate-900">历史对话</h2>
              <button
                onClick={() => setIsSidebarOpen(false)}
                className="p-2 hover:bg-slate-100 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4">
              <Button
                variant="primary"
                className="w-full"
                onClick={handleNewChat}
                leftIcon={<Plus className="w-4 h-4" />}
              >
                新建对话
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-2">
              {sessionsLoading ? (
                <div className="flex justify-center py-8">
                  <LoadingSpinner size="sm" />
                </div>
              ) : sessions && sessions.length > 0 ? (
                <div className="space-y-1">
                  {sessions.map((session) => (
                    <div
                      key={session.id}
                      onClick={() => handleSelectSession(session.id)}
                      className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                        currentSessionId === session.id
                          ? 'bg-primary-50 text-primary-700'
                          : 'hover:bg-slate-100'
                      }`}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <MessageSquare className="w-4 h-4 flex-shrink-0" />
                        <span className="truncate text-sm">{session.title}</span>
                      </div>
                      <button
                        onClick={(e) => handleDeleteSession(session.id, e)}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-200 rounded transition-opacity"
                      >
                        <Trash2 className="w-4 h-4 text-slate-400" />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-slate-500 py-8 text-sm">
                  暂无历史对话
                </div>
              )}
            </div>
          </aside>
        </div>
      )}

      {/* 主聊天区域 */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* 头部 */}
        <header className="flex items-center justify-between px-4 py-3 bg-white border-b border-slate-200 md:hidden">
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="p-2 hover:bg-slate-100 rounded-lg"
          >
            <List className="w-5 h-5" />
          </button>
          <h1 className="font-semibold text-slate-900">AI 法律助手</h1>
          <div className="w-9" /> {/* 占位符 */}
        </header>

        {/* 桌面端标题 */}
        <header className="hidden md:flex items-center px-6 py-4 bg-white border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-slate-900">AI 法律助手</h1>
              <p className="text-xs text-slate-500">智能法律咨询，随时为您解答</p>
            </div>
          </div>
        </header>

        {/* 消息列表 */}
        <MessageList messages={messages} isStreaming={isStreaming} />

        {/* 输入区域 */}
        <ChatInput
          onSend={handleSendMessage}
          isLoading={isLoading}
          placeholder="输入您的法律问题..."
        />
      </div>
    </div>
  );
}

export default ChatPage;