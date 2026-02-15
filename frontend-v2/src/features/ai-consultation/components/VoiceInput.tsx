/**
 * 语音输入组件
 * 
 * 支持录音、上传、转写、显示结果
 */

import { useVoice, formatDuration } from '../hooks/useVoice';

/** 语音输入组件Props */
interface VoiceInputProps {
  /** 转写完成回调 */
  onTranscriptionComplete: (text: string) => void;
  /** 取消回调 */
  onCancel: () => void;
}

/**
 * 语音输入组件
 */
export function VoiceInput({ onTranscriptionComplete, onCancel }: VoiceInputProps): JSX.Element {
  const { state, startRecording, stopRecording, reset, isSupported } = useVoice();

  // 使用转写结果
  const handleUseResult = () => {
    if (state.transcript) {
      onTranscriptionComplete(state.transcript);
      reset();
    }
  };

  // 重新开始
  const handleRestart = () => {
    reset();
  };

  // 不支持录音
  if (!isSupported) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
        <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div className="flex-1">
          <p className="text-sm font-medium text-red-800">您的浏览器不支持录音功能</p>
          <p className="text-xs text-red-600 mt-1">请尝试使用最新版本的Chrome、Firefox或Safari浏览器</p>
        </div>
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-100 rounded-lg transition-colors"
        >
          关闭
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      {/* 录音状态显示 */}
      <div className="p-6">
        {state.recordingStatus === 'idle' && (
          <div className="text-center">
            <button
              onClick={() => { void startRecording(); }}
              className="w-20 h-20 bg-red-500 hover:bg-red-600 rounded-full flex items-center justify-center
                       mx-auto mb-4 transition-all hover:scale-105 shadow-lg shadow-red-200"
            >
              <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
              </svg>
            </button>
            <p className="text-gray-700 font-medium">点击开始录音</p>
            <p className="text-sm text-gray-400 mt-1">最长可录制60秒</p>
          </div>
        )}

        {state.recordingStatus === 'recording' && (
          <div className="text-center">
            {/* 录音动画 */}
            <div className="relative w-24 h-24 mx-auto mb-4">
              {/* 波纹动画 */}
              <div className="absolute inset-0 bg-red-500 rounded-full animate-ping opacity-20" />
              <div className="absolute inset-2 bg-red-500 rounded-full animate-pulse opacity-40" />
              <button
                onClick={stopRecording}
                className="absolute inset-0 w-full h-full bg-red-500 hover:bg-red-600 rounded-full 
                         flex items-center justify-center transition-colors shadow-lg"
              >
                <div className="w-8 h-8 bg-white rounded-sm" />
              </button>
            </div>
            
            <div className="flex items-center justify-center gap-2 mb-2">
              <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span className="text-red-600 font-medium">正在录音</span>
            </div>
            <p className="text-2xl font-mono text-gray-700">{formatDuration(state.duration)}</p>
            <p className="text-xs text-gray-400 mt-2">点击方块停止录音</p>
          </div>
        )}

        {state.recordingStatus === 'processing' && (
          <div className="text-center py-4">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
            <p className="text-gray-700 font-medium">正在转写...</p>
            <p className="text-sm text-gray-400 mt-1">请稍候</p>
          </div>
        )}

        {state.recordingStatus === 'completed' && state.transcript && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-4 text-green-600">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="font-medium">转写完成</span>
            </div>
            
            <div className="bg-gray-50 rounded-xl p-4 max-h-40 overflow-y-auto">
              <p className="text-gray-800 whitespace-pre-wrap">{state.transcript}</p>
            </div>
          </div>
        )}

        {state.recordingStatus === 'error' && (
          <div className="text-center py-4">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-red-600 font-medium mb-1">转写失败</p>
            <p className="text-sm text-gray-500">{state.error || '请重试'}</p>
          </div>
        )}
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center justify-between px-6 py-4 bg-gray-50 border-t border-gray-200">
        <button
          onClick={() => {
            reset();
            onCancel();
          }}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-200 
                   rounded-lg transition-colors text-sm font-medium"
        >
          取消
        </button>

        <div className="flex items-center gap-2">
          {state.recordingStatus === 'completed' && (
            <>
              <button
                onClick={handleRestart}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-200 
                         rounded-lg transition-colors text-sm font-medium"
              >
                重新录制
              </button>
              <button
                onClick={handleUseResult}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                         transition-colors text-sm font-medium"
              >
                使用这段文字
              </button>
            </>
          )}
          
          {state.recordingStatus === 'error' && (
            <button
              onClick={() => { void startRecording(); }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                       transition-colors text-sm font-medium"
            >
              重试
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/** 语音按钮组件 - 用于触发语音输入 */
interface VoiceButtonProps {
  /** 点击回调 */
  onClick: () => void;
  /** 是否禁用 */
  disabled?: boolean;
}

/**
 * 语音按钮组件
 */
export function VoiceButton({ onClick, disabled }: VoiceButtonProps): JSX.Element {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="p-2.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 
               rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      title="语音输入"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" 
        />
      </svg>
    </button>
  );
}