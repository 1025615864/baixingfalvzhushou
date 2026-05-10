import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, User, Sparkles, Link, Mic, MoreVertical, History, Trash2, MessageSquare, BookOpen, Scale, ArrowRight, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/Button';
import {
  apiSendMessageStream,
  apiGetSessions,
  apiDeleteSession,
  apiCreateSession,
} from '@/features/ai-consultation/api';
import type {
  AIMessage,
  AIMessageMetadata,
  StreamChunk,
  AISession,
  AIConsultationError,
} from '@/features/ai-consultation/types';
import { logger } from '@/shared/lib/logger';

interface LawyerRecommendation {
  id: string;
  name: string;
  specialty: string[];
  rating: number;
  experience: number;
  hourlyRate: number;
  avatarUrl?: string;
  lawFirm?: string;
}

interface ExtendedChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  status: 'sending' | 'streaming' | 'completed' | 'error';
  metadata?: AIMessageMetadata;
  lawyerRecommendations?: LawyerRecommendation[];
}

function generateMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

function extractLawyerRecommendations(metadata?: AIMessageMetadata): LawyerRecommendation[] {
  if (!metadata?.suggestedActions) return [];
  return metadata.suggestedActions
    .filter((action) => action.type === 'consult_lawyer' && action.params)
    .map((action) => ({
      id: action.params?.lawyer_id ?? '',
      name: action.params?.lawyer_name ?? action.label,
      specialty: action.params?.specialty?.split(',') ?? [],
      rating: Number(action.params?.rating ?? 4.5),
      experience: Number(action.params?.experience ?? 5),
      hourlyRate: Number(action.params?.hourly_rate ?? 200),
      avatarUrl: action.params?.avatar_url,
      lawFirm: action.params?.law_firm,
    }));
}

function LawyerCard({ lawyer, onConsult }: { lawyer: LawyerRecommendation; onConsult: (id: string) => void }): JSX.Element {
  return (
    <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-primary-50 to-white rounded-xl border border-primary-100 hover:shadow-md transition-shadow">
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
        {lawyer.name.charAt(0)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-900 text-sm">{lawyer.name}</span>
          <span className="text-xs text-amber-600">★ {lawyer.rating.toFixed(1)}</span>
        </div>
        <div className="text-xs text-slate-500 truncate">
          {lawyer.lawFirm && `${lawyer.lawFirm} · `}{lawyer.experience}年经验 · ¥{lawyer.hourlyRate}/时
        </div>
        <div className="flex gap-1 mt-1">
          {lawyer.specialty.slice(0, 3).map((spec) => (
            <span key={spec} className="px-1.5 py-0.5 bg-primary-100 text-primary-700 text-xs rounded">
              {spec}
            </span>
          ))}
        </div>
      </div>
      <button
        onClick={() => onConsult(lawyer.id)}
        className="flex-shrink-0 px-3 py-1.5 bg-primary-600 text-white text-xs rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-1"
      >
        咨询 <ArrowRight className="w-3 h-3" />
      </button>
    </div>
  );
}

function LegalReferenceBadge({ reference }: { reference: { lawName: string; articleNumber: string; content: string } }): JSX.Element {
  return (
    <div className="flex items-start gap-2 p-2 bg-blue-50 rounded-lg text-xs">
      <BookOpen className="w-3.5 h-3.5 text-blue-600 flex-shrink-0 mt-0.5" />
      <div>
        <span className="font-medium text-blue-800">{reference.lawName} {reference.articleNumber}</span>
        <p className="text-blue-600 mt-0.5 line-clamp-2">{reference.content}</p>
      </div>
    </div>
  );
}

function ConfidenceIndicator({ confidence }: { confidence: number }): JSX.Element {
  const level = confidence >= 0.8 ? 'high' : confidence >= 0.5 ? 'medium' : 'low';
  const colors = {
    high: 'text-green-600 bg-green-50',
    medium: 'text-amber-600 bg-amber-50',
    low: 'text-red-600 bg-red-50',
  };
  const labels = { high: '高置信度', medium: '中置信度', low: '低置信度' };

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${colors[level]}`}>
      <Scale className="w-3 h-3" />
      {labels[level]} ({Math.round(confidence * 100)}%)
    </span>
  );
}

function MessageBubble({ message, onLawyerConsult }: { message: ExtendedChatMessage; onLawyerConsult: (id: string) => void }): JSX.Element {
  const isUser = message.role === 'user';
  const lawyers = message.lawyerRecommendations ?? extractLawyerRecommendations(message.metadata);
  const legalRefs = message.metadata?.legalReferences ?? [];
  const confidence = message.metadata?.confidence;

  return (
    <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center ${
        isUser
          ? 'bg-gradient-to-br from-primary-500 to-primary-600'
          : 'bg-gradient-to-br from-secondary-500 to-secondary-600'
      }`}>
        {isUser ? <User className="w-5 h-5 text-white" /> : <Sparkles className="w-5 h-5 text-white" />}
      </div>

      <div className={`max-w-[80%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-2`}>
        <div className={`inline-block px-4 py-3 rounded-2xl ${
          isUser
            ? 'bg-primary-600 text-white rounded-br-md'
            : 'bg-slate-100 text-slate-900 rounded-bl-md'
        }`}>
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>

        {!isUser && message.metadata && (
          <div className="flex flex-wrap items-center gap-2">
            {confidence !== undefined && <ConfidenceIndicator confidence={confidence} />}
            <span className="text-xs text-slate-400">
              {new Date(message.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        )}

        {!isUser && legalRefs.length > 0 && (
          <div className="space-y-1.5 w-full">
            {legalRefs.slice(0, 3).map((ref, idx) => (
              <LegalReferenceBadge key={`${ref.lawName}-${ref.articleNumber}-${idx}`} reference={ref} />
            ))}
          </div>
        )}

        {!isUser && lawyers.length > 0 && (
          <div className="space-y-2 w-full">
            <div className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <Scale className="w-3 h-3" /> 推荐律师
            </div>
            {lawyers.map((lawyer) => (
              <LawyerCard key={lawyer.id} lawyer={lawyer} onConsult={onLawyerConsult} />
            ))}
          </div>
        )}

        {isUser && (
          <span className="text-xs text-slate-400">
            {new Date(message.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>
    </div>
  );
}

function MessageList({ messages, isStreaming, onLawyerConsult }: { messages: ExtendedChatMessage[]; isStreaming: boolean; onLawyerConsult: (id: string) => void }): JSX.Element {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-primary-500/30">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h3 className="text-xl font-semibold text-slate-900 mb-2">开始您的法律咨询</h3>
          <p className="text-slate-600 mb-6">
            我是您的AI法律助手，可以为您解答各类法律问题，包括合同纠纷、劳动争议、婚姻家庭等
          </p>
          <div className="flex flex-wrap gap-2 justify-center">
            {[
              { label: '劳动合同纠纷', category: 'labor' },
              { label: '房屋租赁问题', category: 'contract' },
              { label: '交通事故处理', category: 'tort' },
              { label: '离婚财产分割', category: 'family' },
            ].map((topic) => (
              <button
                key={topic.category}
                className="px-3 py-1.5 bg-slate-100 hover:bg-primary-50 hover:text-primary-600 text-slate-600 text-sm rounded-lg transition-colors"
              >
                {topic.label}
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
        <MessageBubble key={message.id} message={message} onLawyerConsult={onLawyerConsult} />
      ))}
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
      <div ref={bottomRef} />
    </div>
  );
}

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
            <button type="button" className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors" title="上传文件">
              <Link className="w-4 h-4" />
            </button>
            <button type="button" className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors" title="语音输入">
              <Mic className="w-4 h-4" />
            </button>
          </div>
        </div>
        <Button type="submit" variant="primary" size="lg" isLoading={isLoading} className="flex-shrink-0 rounded-xl">
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
  const [messages, setMessages] = useState<ExtendedChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<AISession[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const abortRef = useRef<(() => void) | null>(null);
  const navigate = useNavigate();

  const loadSessions = useCallback(async () => {
    try {
      const result = await apiGetSessions({ pageSize: 20 });
      setSessions(result.sessions);
    } catch (error) {
      logger.warn('加载会话列表失败:', error);
    }
  }, []);

  useEffect(() => {
    void loadSessions();
  }, [loadSessions]);

  const handleNewChat = useCallback(() => {
    if (abortRef.current) abortRef.current();
    setMessages([]);
    setCurrentSessionId(null);
    setIsStreaming(false);
  }, []);

  const handleSelectSession = useCallback(async (sessionId: string) => {
    try {
      const session = await (await import('@/features/ai-consultation/api')).apiGetSession(sessionId);
      setCurrentSessionId(sessionId);
      setMessages(session.messages.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        timestamp: m.createdAt,
        status: m.status,
        metadata: m.metadata,
      })));
      setSidebarOpen(false);
    } catch (error) {
      logger.warn('加载会话失败:', error);
    }
  }, []);

  const handleDeleteSession = useCallback(async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiDeleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (currentSessionId === sessionId) {
        handleNewChat();
      }
    } catch (error) {
      logger.warn('删除会话失败:', error);
    }
  }, [currentSessionId, handleNewChat]);

  const handleSendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isStreaming) return;

    const userMessage: ExtendedChatMessage = {
      id: generateMessageId(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
      status: 'completed',
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsStreaming(true);

    const assistantMessageId = generateMessageId();
    const assistantMessage: ExtendedChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      status: 'streaming',
    };
    setMessages((prev) => [...prev, assistantMessage]);

    let sessionId = currentSessionId;

    try {
      const controller = apiSendMessageStream(
        {
          sessionId,
          content,
          stream: true,
        },
        (chunk: StreamChunk) => {
          if (chunk.type === 'content' && chunk.data) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMessageId
                  ? { ...m, content: m.content + chunk.data }
                  : m
              )
            );
          } else if (chunk.type === 'metadata' && chunk.metadata) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMessageId
                  ? { ...m, metadata: chunk.metadata }
                  : m
              )
            );
          } else if (chunk.type === 'metadata' && chunk.data) {
            try {
              const parsed = JSON.parse(chunk.data);
              if (parsed.sessionId && !sessionId) {
                sessionId = parsed.sessionId;
                setCurrentSessionId(parsed.sessionId);
                void loadSessions();
              }
              if (parsed.stage) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMessageId
                      ? { ...m, content: m.content || `正在${parsed.stage}...` }
                      : m
                  )
                );
              }
            } catch { /* ignore parse errors */ }
          } else if (chunk.type === 'done' && chunk.data) {
            try {
              const parsed = JSON.parse(chunk.data);
              if (parsed.sessionId && !sessionId) {
                sessionId = parsed.sessionId;
                setCurrentSessionId(parsed.sessionId);
                void loadSessions();
              }
            } catch { /* ignore */ }
          }
        },
        (error: AIConsultationError) => {
          logger.error('流式响应错误:', error);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessageId
                ? { ...m, status: 'error', content: m.content || `抱歉，发生了错误：${error.message}` }
                : m
            )
          );
          setIsStreaming(false);
        },
        () => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMessageId
                ? { ...m, status: 'completed' }
                : m
            )
          );
          setIsStreaming(false);
        }
      );

      abortRef.current = controller.abort;
    } catch (error) {
      logger.error('发送消息失败:', error);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMessageId
            ? { ...m, status: 'error', content: '抱歉，发送消息时发生错误，请稍后重试。' }
            : m
        )
      );
      setIsStreaming(false);
    }
  }, [isStreaming, currentSessionId, loadSessions]);

  const handleLawyerConsult = useCallback((lawyerId: string) => {
    navigate(`/lawyer/${lawyerId}`);
  }, [navigate]);

  return (
    <div className="h-[calc(100vh-64px)] flex bg-slate-50">
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/30 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 fixed lg:static z-50 w-64 h-full flex flex-col bg-white border-r border-slate-200 transition-transform duration-200`}>
        <div className="p-4 border-b border-slate-100">
          <Button variant="primary" fullWidth leftIcon={<Sparkles className="w-4 h-4" />} onClick={handleNewChat}>
            新对话
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {sessions.length > 0 ? (
            <div className="space-y-0.5">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={`group flex items-center gap-3 px-3 py-2.5 text-sm rounded-lg transition-colors cursor-pointer ${
                    currentSessionId === session.id ? 'bg-primary-50 text-primary-700' : 'text-slate-700 hover:bg-slate-50'
                  }`}
                  onClick={() => void handleSelectSession(session.id)}
                >
                  <MessageSquare className="w-4 h-4 flex-shrink-0" />
                  <span className="truncate flex-1">{session.title || '新对话'}</span>
                  <button
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-500 transition-all"
                    onClick={(e) => void handleDeleteSession(session.id, e)}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-sm text-slate-400 py-8">暂无对话记录</div>
          )}
        </div>
        <div className="p-4 border-t border-slate-100">
          <button
            className="flex items-center gap-2 text-sm text-slate-500 hover:text-red-600 transition-colors"
            onClick={() => {
              if (sessions.length > 0) {
                void Promise.all(sessions.map((s) => apiDeleteSession(s.id)));
                handleNewChat();
                void loadSessions();
              }
            }}
          >
            <Trash2 className="w-4 h-4" />
            清空对话
          </button>
        </div>
      </aside>

      <main className="flex-1 flex flex-col bg-white rounded-2xl m-4 shadow-soft overflow-hidden">
        <header className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-white">
          <div className="flex items-center gap-3">
            <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors lg:hidden" onClick={() => setSidebarOpen(true)}>
              <History className="w-5 h-5" />
            </button>
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-900">AI法律咨询</h1>
              <p className="text-sm text-slate-500">随时为您解答法律问题</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
              <MoreVertical className="w-5 h-5" />
            </button>
          </div>
        </header>

        <MessageList messages={messages} isStreaming={isStreaming} onLawyerConsult={handleLawyerConsult} />
        <ChatInput onSend={(msg) => void handleSendMessage(msg)} isLoading={isStreaming} />
      </main>
    </div>
  );
}
