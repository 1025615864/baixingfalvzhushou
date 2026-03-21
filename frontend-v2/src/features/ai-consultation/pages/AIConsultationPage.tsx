/**
 * AIConsultationPage - AI 咨询页面
 * 
 * 用户与 AI 进行法律咨询的主页面
 * 集成分享、语音转写、文件分析功能
 */

import { useState, useCallback, useRef, useEffect } from 'react';

import type { AIMessage, SuggestedAction } from '../types';
import {
  useSessions,
  useCreateSession,
  useStreamMessage,
  useSession,
} from '../hooks/useAIConsultation';
import { ReadableMessage } from '../components/ReadableMessage';
import { ShareDialog } from '../components/ShareDialog';
import { VoiceInput, VoiceButton } from '../components/VoiceInput';
import { FileUpload, FileUploadButton } from '../components/FileUpload';

/**
 * AI 咨询页面
 */
export function AIConsultationPage(): JSX.Element {
  const [inputMessage, setInputMessage] = useState('');
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>();
  const [isShareDialogOpen, setIsShareDialogOpen] = useState(false);
  const [showVoiceInput, setShowVoiceInput] = useState(false);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: sessions, isLoading: isLoadingSessions } = useSessions({ pageSize: 20 });
  const createSession = useCreateSession();
  const { streamState, sendStreamMessage, abortStream } = useStreamMessage();

  // 使用 useSession hook 获取当前会话的消息
  const { data: currentSession } = useSession(currentSessionId);

  // 自动滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [currentSession?.messages, streamState.content, scrollToBottom]);

  // 创建新会话
  const handleNewChat = useCallback(async () => {
    try {
      const newSession = await createSession.mutateAsync({
        title: '新咨询',
      });
      setCurrentSessionId(newSession.id);
      setInputMessage('');
      setIsShareDialogOpen(false);
    } catch {
      // 错误处理
    }
  }, [createSession]);

  // 发送消息
  const handleSendMessage = useCallback(async () => {
    if (!inputMessage.trim()) return;

    const content = inputMessage.trim();
    setInputMessage('');

    // 如果没有当前会话，先创建
    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        const newSession = await createSession.mutateAsync({
          title: content.slice(0, 20) + (content.length > 20 ? '...' : ''),
        });
        sessionId = newSession.id;
        setCurrentSessionId(sessionId);
      } catch {
        return;
      }
    }

    // 发送流式消息
    sendStreamMessage({
      sessionId,
      content,
      stream: true,
    });
  }, [inputMessage, currentSessionId, createSession, sendStreamMessage]);

  // 处理键盘事件
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        void handleSendMessage();
      }
    },
    [handleSendMessage]
  );

  // 处理建议操作点击 - 优化：添加转化追踪埋点
  const handleActionClick = useCallback((action: SuggestedAction) => {
    switch (action.type) {
      case 'ask_followup':
        if (action.params?.question) {
          setInputMessage(action.params.question);
        }
        break;
      case 'consult_lawyer':
        // 跳转到律师咨询页面 - 添加转化追踪
        window.location.href = '/lawyer?from=ai-consultation&action=book_lawyer';
        // TODO: 接入正式埋点服务后在此上报转化事件
        break;
      default:
        break;
    }
  }, []);

  // 语音转写完成
  const handleVoiceComplete = useCallback((text: string) => {
    setInputMessage((prev) => prev + text);
    setShowVoiceInput(false);
  }, []);

  // 文件分析完成
  const handleFileAnalysisComplete = useCallback(
    (result: { text: string; summary: string }) => {
      // 使用分析结果作为消息发送
      const messageContent = `文件分析结果：\n\n${result.summary}\n\n详细内容：\n${result.text}`;
      setInputMessage(messageContent);
      setShowFileUpload(false);
    },
    []
  );

  // 合并消息列表（包括流式消息）
  const allMessages: AIMessage[] = (currentSession?.messages || []).map((msg) => ({
    ...msg,
    status: msg.status === 'streaming' ? 'completed' : msg.status,
  }));

  // 如果有流式消息，添加到列表
  if (streamState.isStreaming || streamState.message) {
    const streamingMessage: AIMessage = {
      id: streamState.message?.id || `streaming-${Date.now()}`,
      sessionId: currentSessionId || '',
      role: 'assistant',
      content: streamState.content,
      status: streamState.isStreaming ? 'streaming' : 'completed',
      createdAt: streamState.message?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      metadata: streamState.message?.metadata,
    };
    allMessages.push(streamingMessage);
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* 左侧边栏 - 会话列表 */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* 顶部标题 */}
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-lg font-bold text-gray-900" data-testid="page-title">法律咨询</h1>
          <p className="text-xs text-gray-500 mt-1">智能助手为您解答法律问题</p>
        </div>

        {/* 新建对话按钮 */}
        <div className="p-3">
          <button
            onClick={() => {
              void handleNewChat();
            }}
            disabled={createSession.isPending}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5
                     bg-blue-600 text-white rounded-lg hover:bg-blue-700
                     transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>新建对话</span>
          </button>
        </div>

        {/* 会话列表 */}
        <div className="flex-1 overflow-y-auto">
          {isLoadingSessions ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : sessions && sessions.length > 0 ? (
            <div className="p-2 space-y-1">
              {sessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => setCurrentSessionId(session.id)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors
                    ${currentSessionId === session.id
                      ? 'bg-blue-50 text-blue-700 border border-blue-200'
                      : 'hover:bg-gray-100 text-gray-700'
                    }`}
                >
                  <div className="font-medium truncate">{session.title}</div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    {new Date(session.lastActivityAt).toLocaleDateString('zh-CN')}
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="p-4 text-center text-sm text-gray-400">暂无历史对话</div>
          )}
        </div>

        {/* 底部提示 */}
        <div className="p-3 border-t border-gray-200 text-xs text-gray-400 text-center">
          AI 回答仅供参考，具体法律问题请咨询专业律师
        </div>
      </div>

      {/* 右侧主区域 */}
      <div className="flex-1 flex flex-col">
        {/* 顶部工具栏 */}
        {currentSessionId && (
          <div className="flex items-center justify-end gap-2 px-4 py-2 bg-white border-b border-gray-200">
            <button
              onClick={() => setIsShareDialogOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 
                       hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              title="分享会话"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                />
              </svg>
              <span>分享</span>
            </button>
          </div>
        )}

        {/* 消息列表 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {allMessages.length === 0 ? (
            // 空状态 - 显示欢迎信息
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-2xl flex items-center justify-center mb-6">
                <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">有什么法律问题？</h2>
              <p className="text-gray-500 max-w-md mb-8">
                我可以为您解答各类法律问题，包括劳动法、合同法、婚姻法等。
                请注意，我的回答仅供参考，不构成正式法律意见。
              </p>
              <div className="grid grid-cols-2 gap-3 max-w-lg w-full">
                {[
                  '劳动合同解除如何赔偿？',
                  '欠钱不还怎么办？',
                  '离婚财产如何分割？',
                  '租房押金不退怎么办？',
                ].map((question, index) => (
                  <button
                    key={index}
                    onClick={() => setInputMessage(question)}
                    className="p-3 text-left text-sm bg-white border border-gray-200 
                             rounded-lg hover:border-blue-300 hover:bg-blue-50 
                             transition-colors text-gray-700"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            // 消息列表
            <>
              {allMessages.map((message, index) => (
                <div key={`${message.id}-${index}`} data-testid="chat-message">
                  <ReadableMessage
                    message={message}
                    showTimestamp={true}
                    showConfidence={message.role === 'assistant' && message.status === 'completed'}
                    showActions={message.role === 'assistant' && index === allMessages.length - 1}
                    onActionClick={handleActionClick}
                  />
                </div>
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* 语音输入面板 */}
        {showVoiceInput && (
          <div className="px-4 py-2 bg-white border-t border-gray-200">
            <VoiceInput
              onTranscriptionComplete={handleVoiceComplete}
              onCancel={() => setShowVoiceInput(false)}
            />
          </div>
        )}

        {/* 文件上传面板 */}
        {showFileUpload && (
          <div className="px-4 py-2 bg-white border-t border-gray-200">
            <FileUpload
              onAnalysisComplete={handleFileAnalysisComplete}
              onCancel={() => setShowFileUpload(false)}
            />
          </div>
        )}

        {/* 输入区域 */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <div className="max-w-4xl mx-auto">
            <div className="relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入您的法律问题..."
                disabled={streamState.isStreaming}
                rows={3}
                data-testid="chat-input"
                className="w-full px-4 py-3 pr-32 bg-gray-50 border border-gray-200
                         rounded-xl resize-none focus:outline-none focus:ring-2
                         focus:ring-blue-500 focus:border-transparent
                         disabled:opacity-50 disabled:cursor-not-allowed
                         text-gray-800 placeholder-gray-400"
              />

              {/* 工具按钮组 */}
              <div className="absolute right-3 bottom-3 flex items-center gap-1">
                <FileUploadButton
                  onClick={() => setShowFileUpload(!showFileUpload)}
                  disabled={streamState.isStreaming}
                />
                <VoiceButton
                  onClick={() => setShowVoiceInput(!showVoiceInput)}
                  disabled={streamState.isStreaming}
                />
                {/* 发送按钮 */}
                <button
                  onClick={() => {
                    void handleSendMessage();
                  }}
                  disabled={!inputMessage.trim() || streamState.isStreaming}
                  data-testid="send-button"
                  className="ml-1 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700
                           disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {streamState.isStreaming ? (
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                      />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* 底部提示 */}
            <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
              <div className="flex items-center gap-4">
                <span>按 Enter 发送，Shift + Enter 换行</span>
                {streamState.isStreaming && (
                  <button
                    onClick={abortStream}
                    className="text-red-500 hover:text-red-600 flex items-center gap-1"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                    <span>停止生成</span>
                  </button>
                )}
              </div>
              <span>AI 生成内容可能存在误差</span>
            </div>
          </div>
        </div>
      </div>

      {/* 分享对话框 */}
      {currentSessionId && (
        <ShareDialog
          sessionId={currentSessionId}
          isOpen={isShareDialogOpen}
          onClose={() => setIsShareDialogOpen(false)}
        />
      )}
    </div>
  );
}