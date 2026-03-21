/**
 * VideoConsultationRoom - 视频咨询房间组件
 * 集成视频通话功能，显示通话状态和控制
 */

import { useState, useEffect, useRef } from 'react';
import {
  Video,
  VideoOff,
  Mic,
  MicOff,
  Phone,
  PhoneOff,
  Clock,
  User,
  AlertCircle,
  Wifi,
  WifiOff,
  Maximize2 as Maximize,
  Volume2,
  VolumeX,
  ScreenShare,
  ScreenShareOff,
} from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';

import {
  useVideoConsultation,
  useStartVideoConsultation,
  useEndVideoConsultation,
} from '../hooks/useVideoConsultation';
import type { VideoConsultation } from '../types';

// 通话状态类型
type CallStatus = 'idle' | 'connecting' | 'connected' | 'disconnected' | 'failed';

// 连接质量类型
type ConnectionQuality = 'excellent' | 'good' | 'poor' | 'unknown';

interface VideoConsultationRoomProps {
  consultationId: string | number;
  onEnd?: (consultation: VideoConsultation) => void;
}

export function VideoConsultationRoom({
  consultationId,
  onEnd,
}: VideoConsultationRoomProps): JSX.Element {
  // 获取咨询详情
  const { data: consultation, isLoading: loadingConsultation } = useVideoConsultation(consultationId);

  // 通话状态
  const [callStatus, setCallStatus] = useState<CallStatus>('idle');
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);
  const [isSpeakerOn, setIsSpeakerOn] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [connectionQuality, setConnectionQuality] = useState<ConnectionQuality>('unknown');
  const [callDuration, setCallDuration] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Refs
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Mutations
  const startMutation = useStartVideoConsultation();
  const endMutation = useEndVideoConsultation();

  // 模拟连接
  const _simulateVideoConnection = async (): Promise<void> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve();
      }, 2000);
    });
  };

  // 通话时长计时器
  useEffect(() => {
    if (callStatus === 'connected') {
      timerRef.current = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [callStatus]);

  // 模拟连接质量检测
  useEffect(() => {
    if (callStatus === 'connected') {
      const qualityInterval = setInterval(() => {
        const random = Math.random();
        let quality: ConnectionQuality;
        if (random > 0.7) {
          quality = 'excellent';
        } else if (random > 0.3) {
          quality = 'good';
        } else {
          quality = 'poor';
        }
        setConnectionQuality(quality);
      }, 5000);

      return () => clearInterval(qualityInterval);
    }
    return undefined;
  }, [callStatus]);

  const _qualities: ConnectionQuality[] = ['excellent', 'good', 'poor'];

  // 格式化通话时长
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // 加入会议
  const handleJoinMeeting = async (): Promise<void> => {
    try {
      setCallStatus('connecting');
      setErrorMessage(null);

      // 调用开始 API
      await startMutation.mutateAsync(consultationId);

      // 模拟视频连接（实际项目中需要集成真实的视频 SDK）
      await _simulateVideoConnection();

      setCallStatus('connected');
    } catch {
      setCallStatus('failed');
      setErrorMessage('连接失败，请稍后重试');
    }
  };

  // 结束通话
  const handleEndCall = async (): Promise<void> => {
    try {
      const confirmed = window.confirm('确定要结束本次视频咨询吗？');
      if (!confirmed) return;

      await endMutation.mutateAsync(consultationId);

      setCallStatus('disconnected');

      if (consultation) {
        onEnd?.(consultation);
      }
    } catch {
      setErrorMessage('结束通话失败');
    }
  };

  const _result = { success: true };

  // 切换静音
  const toggleMute = (): void => {
    setIsMuted((prev) => !prev);
    // 实际项目中需要调用视频 SDK 的静音方法
  };

  // 切换视频
  const toggleVideo = (): void => {
    setIsVideoOff((prev) => !prev);
    // 实际项目中需要调用视频 SDK 的视频开关方法
  };

  // 切换扬声器
  const toggleSpeaker = (): void => {
    setIsSpeakerOn((prev) => !prev);
  };

  // 切换屏幕共享
  const toggleScreenShare = async (): Promise<void> => {
    if (!isScreenSharing) {
      // 请求屏幕共享权限
      // 实际项目中需要使用 getDisplayMedia API
      setIsScreenSharing(true);
    } else {
      setIsScreenSharing(false);
    }
    await Promise.resolve();
  };

  // 切换全屏
  const toggleFullscreen = (): void => {
    if (!containerRef.current) return;

    if (!isFullscreen) {
      void containerRef.current.requestFullscreen?.();
    } else {
      void document.exitFullscreen?.();
    }
    setIsFullscreen((prev) => !prev);
  };

  // 加载中状态
  if (loadingConsultation) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-900 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4" />
          <p className="text-white">加载会议信息...</p>
        </div>
      </div>
    );
  }

  // 通话前/空闲状态
  if (callStatus === 'idle') {
    return (
      <div className="space-y-6">
        {/* 会议信息 */}
        <Card padding="lg">
          <div className="text-center">
            <div className="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-4">
              <Video className="w-10 h-10 text-primary-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              视频咨询
            </h2>
            <p className="text-gray-500 mb-1">
              律师：{consultation?.lawyerName || '待确认'}
            </p>
            <p className="text-gray-400 text-sm mb-4">
              主题：{consultation?.subject}
            </p>

            {/* 会议信息 */}
            {consultation?.meetingRoomId && (
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <p className="text-sm text-gray-500">会议号</p>
                <p className="text-lg font-mono font-semibold text-gray-900">
                  {consultation.meetingRoomId}
                </p>
                {consultation.meetingPassword && (
                  <>
                    <p className="text-sm text-gray-500 mt-2">会议密码</p>
                    <p className="text-lg font-mono font-semibold text-gray-900">
                      {consultation.meetingPassword}
                    </p>
                  </>
                )}
              </div>
            )}

            <Button
              variant="primary"
              size="lg"
              onClick={() => void handleJoinMeeting()}
              isLoading={startMutation.isPending}
              leftIcon={<Phone className="w-5 h-5" />}
            >
              加入会议
            </Button>

            <div className="mt-4 flex items-center justify-center gap-2 text-sm text-gray-400">
              <Clock className="w-4 h-4" />
              <span>预计时长：{consultation?.durationMinutes || 30}分钟</span>
            </div>
          </div>
        </Card>

        {/* 温馨提示 */}
        <Card padding="md" className="bg-blue-50 border-blue-200">
          <h4 className="text-sm font-medium text-blue-800 mb-2">温馨提示</h4>
          <ul className="text-sm text-blue-600 space-y-1">
            <li>• 请确保网络稳定，建议使用 WiFi 或 4G/5G 网络</li>
            <li>• 请在安静的环境中进行咨询</li>
            <li>• 咨询过程中请保持麦克风和摄像头正常工作</li>
            <li>• 如遇问题，可退出后重新加入</li>
          </ul>
        </Card>
      </div>
    );
  }

  // 连接中状态
  if (callStatus === 'connecting') {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-900 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4" />
          <p className="text-white text-lg">正在连接会议...</p>
          <p className="text-gray-400 text-sm mt-2">请稍候</p>
        </div>
      </div>
    );
  }

  // 连接失败状态
  if (callStatus === 'failed') {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-900 rounded-lg">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <p className="text-white text-lg mb-2">连接失败</p>
          <p className="text-gray-400 text-sm mb-4">{errorMessage}</p>
          <Button
            variant="primary"
            onClick={() => {
              setCallStatus('idle');
              setErrorMessage(null);
            }}
          >
            重新连接
          </Button>
        </div>
      </div>
    );
  }

  // 通话中状态
  return (
    <div
      ref={containerRef}
      className="relative bg-gray-900 rounded-lg overflow-hidden"
      style={{ minHeight: '500px' }}
    >
      {/* 远程视频（大画面） */}
      <div className="absolute inset-0">
        <video
          ref={remoteVideoRef}
          autoPlay
          playsInline
          className="w-full h-full object-cover"
          poster="/video-placeholder.jpg"
        />
        {/* 没有视频时的占位符 */}
        <div className="absolute inset-0 flex items-center justify-center bg-gray-800">
          <div className="text-center">
            <User className="w-24 h-24 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">{consultation?.lawyerName || '律师'}</p>
          </div>
        </div>
      </div>

      {/* 本地视频（小画面） */}
      <div className="absolute top-4 right-4 w-32 h-44 md:w-40 md:h-56 rounded-lg overflow-hidden shadow-lg border-2 border-white/20">
        <video
          ref={localVideoRef}
          autoPlay
          playsInline
          muted
          className={`w-full h-full object-cover ${isVideoOff ? 'hidden' : ''}`}
        />
        {isVideoOff && (
          <div className="absolute inset-0 bg-gray-700 flex items-center justify-center">
            <VideoOff className="w-8 h-8 text-gray-400" />
          </div>
        )}
      </div>

      {/* 顶部信息栏 */}
      <div className="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/60 to-transparent">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Badge
              variant={callStatus === 'connected' ? 'success' : 'warning'}
              size="md"
            >
              {callStatus === 'connected' ? '通话中' : '连接中'}
            </Badge>
            <span className="text-white font-mono text-lg">
              {formatDuration(callDuration)}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* 连接质量指示器 */}
            <ConnectionQualityIndicator quality={connectionQuality} />
          </div>
        </div>
      </div>

      {/* 错误提示 */}
      {errorMessage && (
        <div className="absolute top-16 left-4 right-4">
          <div className="bg-red-500/90 text-white px-4 py-2 rounded-lg text-sm flex items-center">
            <AlertCircle className="w-4 h-4 mr-2" />
            {errorMessage}
          </div>
        </div>
      )}

      {/* 底部控制栏 */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/60 to-transparent">
        <div className="flex items-center justify-center gap-3">
          {/* 静音按钮 */}
          <ControlButton
            icon={isMuted ? <MicOff /> : <Mic />}
            label={isMuted ? '取消静音' : '静音'}
            active={isMuted}
            onClick={toggleMute}
          />

          {/* 视频开关 */}
          <ControlButton
            icon={isVideoOff ? <VideoOff /> : <Video />}
            label={isVideoOff ? '开启视频' : '关闭视频'}
            active={isVideoOff}
            onClick={toggleVideo}
          />

          {/* 结束通话 */}
          <button
            onClick={() => void handleEndCall()}
            className="w-14 h-14 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center transition-all shadow-lg"
          >
            <PhoneOff className="w-6 h-6" />
          </button>

          {/* 扬声器 */}
          <ControlButton
            icon={isSpeakerOn ? <Volume2 /> : <VolumeX />}
            label={isSpeakerOn ? '关闭扬声器' : '开启扬声器'}
            active={!isSpeakerOn}
            onClick={toggleSpeaker}
          />

          {/* 屏幕共享 */}
          <ControlButton
            icon={isScreenSharing ? <ScreenShareOff /> : <ScreenShare />}
            label={isScreenSharing ? '停止共享' : '屏幕共享'}
            active={isScreenSharing}
            onClick={() => void toggleScreenShare()}
          />
        </div>

        {/* 更多控制按钮 */}
        <div className="flex items-center justify-center gap-3 mt-3">
          <ControlButton
            icon={<Maximize />}
            label="全屏"
            small
            onClick={() => void toggleFullscreen()}
          />
        </div>
      </div>
    </div>
  );
}

// 控制按钮组件
interface ControlButtonProps {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  small?: boolean;
  onClick: () => void;
}

function ControlButton({
  icon,
  label,
  active = false,
  small = false,
  onClick,
}: ControlButtonProps): JSX.Element {
  const sizeClasses = small ? 'w-10 h-10' : 'w-12 h-12';
  const iconSize = small ? 'w-4 h-4' : 'w-5 h-5';

  return (
    <button
      onClick={onClick}
      className={`
        ${sizeClasses} rounded-full flex items-center justify-center transition-all
        ${active
          ? 'bg-white text-gray-900'
          : 'bg-gray-700/80 text-white hover:bg-gray-600'
        }
      `}
      title={label}
    >
      <span className={iconSize}>{icon}</span>
    </button>
  );
}

// 连接质量指示器
interface ConnectionQualityIndicatorProps {
  quality: ConnectionQuality;
}

function ConnectionQualityIndicator({
  quality,
}: ConnectionQualityIndicatorProps): JSX.Element {
  const config = {
    excellent: { icon: Wifi, color: 'text-green-400', label: '网络优秀' },
    good: { icon: Wifi, color: 'text-yellow-400', label: '网络良好' },
    poor: { icon: WifiOff, color: 'text-red-400', label: '网络较差' },
    unknown: { icon: Wifi, color: 'text-gray-400', label: '检测中...' },
  };

  const { icon: Icon, color, label } = config[quality];

  return (
    <div className={`flex items-center gap-1 ${color}`} title={label}>
      <Icon className="w-4 h-4" />
      <span className="text-xs">{label}</span>
    </div>
  );
}