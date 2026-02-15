/**
 * AI咨询语音转写功能Hook
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';

import type {
  TranscriptionResponse,
  VoiceUploadRequest,
  TranscriptionState,
} from '../types';
import { apiTranscribeVoice } from '../api';

// ==================== Hook 返回类型 ====================

/** 语音功能Hook返回类型 */
interface UseVoiceReturn {
  /** 转写状态 */
  state: TranscriptionState;
  /** 开始录音 */
  startRecording: () => Promise<void>;
  /** 停止录音 */
  stopRecording: () => void;
  /** 重置状态 */
  reset: () => void;
  /** 是否支持录音 */
  isSupported: boolean;
}

// ==================== 常量 ====================

/** 最大录音时长（毫秒） */
const MAX_RECORDING_DURATION = 60 * 1000; // 60秒

/** 录音采样率 */
const SAMPLE_RATE = 16000;

// ==================== Hook ====================

/**
 * 语音转写Hook
 */
export function useVoice(): UseVoiceReturn {
  const [state, setState] = useState<TranscriptionState>({
    recordingStatus: 'idle',
    transcript: '',
    error: null,
    duration: 0,
  });

  const [isSupported, setIsSupported] = useState<boolean>(true);
  
  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);
  const streamRef = useRef<MediaStream | null>(null);

  // 语音转写mutation
  const transcribeMutation = useMutation<TranscriptionResponse, Error, VoiceUploadRequest>({
    mutationFn: apiTranscribeVoice,
  });

  // 检查浏览器支持
  useEffect(() => {
    const checkSupport = (): void => {
      const supported = !!(
        typeof navigator !== 'undefined' &&
        navigator.mediaDevices &&
        typeof navigator.mediaDevices.getUserMedia === 'function' &&
        typeof window !== 'undefined' &&
        typeof window.MediaRecorder !== 'undefined'
      );
      setIsSupported(supported);
    };
    
    checkSupport();
  }, []);

  // 清理函数
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    };
  }, []);

  /** 开始录音 */
  const startRecording = useCallback(async (): Promise<void> => {
    if (!isSupported) {
      setState(prev => ({
        ...prev,
        recordingStatus: 'error',
        error: '您的浏览器不支持录音功能',
      }));
      return;
    }

    try {
      // 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      streamRef.current = stream;

      // 创建MediaRecorder
      const mimeType = getSupportedMimeType();
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // 收集音频数据
      mediaRecorder.ondataavailable = (event: BlobEvent) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // 录音停止处理
      mediaRecorder.onstop = async () => {
        // 停止计时器
        if (recordingTimerRef.current) {
          clearInterval(recordingTimerRef.current);
          recordingTimerRef.current = null;
        }

        // 停止所有音频轨道
        stream.getTracks().forEach(track => track.stop());

        setState(prev => ({
          ...prev,
          recordingStatus: 'processing',
        }));

        try {
          // 创建音频文件
          const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
          const audioFile = new File([audioBlob], `recording_${Date.now()}.webm`, {
            type: mimeType,
          });

          // 上传到服务器进行转写
          const result = await transcribeMutation.mutateAsync({
            audioFile,
            isFinal: true,
          });

          setState(prev => ({
            ...prev,
            recordingStatus: 'completed',
            transcript: result.text,
          }));
        } catch (error) {
          setState(prev => ({
            ...prev,
            recordingStatus: 'error',
            error: error instanceof Error ? error.message : '语音转写失败',
          }));
        }
      };

      // 开始录音
      mediaRecorder.start(1000); // 每秒收集一次数据
      startTimeRef.current = Date.now();

      // 更新状态
      setState({
        recordingStatus: 'recording',
        transcript: '',
        error: null,
        duration: 0,
      });

      // 启动计时器
      recordingTimerRef.current = setInterval(() => {
        const duration = Math.floor((Date.now() - startTimeRef.current) / 1000);
        setState(prev => ({ ...prev, duration }));

        // 检查是否达到最大录音时长
        if (Date.now() - startTimeRef.current >= MAX_RECORDING_DURATION) {
          stopRecording();
        }
      }, 1000);
    } catch (error) {
      setState(prev => ({
        ...prev,
        recordingStatus: 'error',
        error: error instanceof Error ? error.message : '无法访问麦克风',
      }));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSupported, transcribeMutation]); // stopRecording is intentionally excluded - it has no dependencies and causes circular reference

  /** 停止录音 */
  const stopRecording = useCallback((): void => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  /** 重置状态 */
  const reset = useCallback((): void => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
    }
    
    mediaRecorderRef.current = null;
    audioChunksRef.current = [];
    streamRef.current = null;
    recordingTimerRef.current = null;
    startTimeRef.current = 0;

    setState({
      recordingStatus: 'idle',
      transcript: '',
      error: null,
      duration: 0,
    });
  }, []);

  return {
    state,
    startRecording,
    stopRecording,
    reset,
    isSupported,
  };
}

// ==================== 辅助函数 ====================

/**
 * 获取浏览器支持的MIME类型
 */
function getSupportedMimeType(): string {
  const types = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/mp4',
    'audio/wav',
  ];

  for (const type of types) {
    if (MediaRecorder.isTypeSupported(type)) {
      return type;
    }
  }

  return 'audio/webm'; // 默认类型
}

/**
 * 格式化录音时长显示
 */
export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * 检查是否为支持的音频文件类型
 */
export function isSupportedAudioFile(file: File): boolean {
  const supportedTypes = [
    'audio/webm',
    'audio/ogg',
    'audio/mp3',
    'audio/wav',
    'audio/mpeg',
    'audio/mp4',
    'audio/aac',
  ];
  return supportedTypes.includes(file.type);
}

/**
 * 获取音频文件扩展名
 */
export function getAudioExtension(mimeType: string): string {
  const mimeToExt: Record<string, string> = {
    'audio/webm': 'webm',
    'audio/ogg': 'ogg',
    'audio/mp3': 'mp3',
    'audio/wav': 'wav',
    'audio/mpeg': 'mp3',
    'audio/mp4': 'm4a',
    'audio/aac': 'aac',
  };
  return mimeToExt[mimeType] || 'webm';
}