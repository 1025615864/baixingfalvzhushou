/**
 * VideoConsultationPage - 视频咨询主页面
 * 整合视频咨询列表、预约、房间等功能
 */

import { useState, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Video,
  Calendar,
  Plus,
  ArrowLeft,
  User,
  Clock,
  AlertCircle,
} from 'lucide-react';

import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

import { VideoConsultationList } from '../components/VideoConsultationList';
import { VideoConsultationBooking } from '../components/VideoConsultationBooking';
import { VideoConsultationRoom } from '../components/VideoConsultationRoom';
import { useVideoConsultation } from '../hooks/useVideoConsultation';
import type { VideoConsultation } from '../types';

// 页面视图类型
type PageView = 'list' | 'booking' | 'room' | 'detail';

export function VideoConsultationPage(): JSX.Element {
  const { id, action } = useParams<{ id: string; action: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // 从 URL 参数获取律师 ID（用于预约）
  const lawyerIdParam = searchParams.get('lawyerId');
  const lawyerId = lawyerIdParam ? parseInt(lawyerIdParam, 10) : null;

  // 状态
  const [currentView, setCurrentView] = useState<PageView>(() => {
    if (id && action === 'join') return 'room';
    if (id) return 'detail';
    if (lawyerId) return 'booking';
    return 'list';
  });

  const [selectedConsultation, setSelectedConsultation] = useState<VideoConsultation | null>(null);

  // 如果有 ID，获取咨询详情
  const { data: consultationDetail, isLoading: loadingDetail } = useVideoConsultation(id ?? '');

  // 处理选择咨询
  const handleSelectConsultation = useCallback((consultation: VideoConsultation) => {
    setSelectedConsultation(consultation);
    setCurrentView('detail');
  }, []);

  // 处理加入会议
  const handleJoinMeeting = useCallback((consultation: VideoConsultation) => {
    setSelectedConsultation(consultation);
    setCurrentView('room');
    navigate(`/video-consultation/${consultation.id}/join`, { replace: true });
  }, [navigate]);

  // 处理预约成功
  const handleBookingSuccess = useCallback((consultationId: string) => {
    navigate(`/video-consultation/${consultationId}`);
    setCurrentView('detail');
  }, [navigate]);

  // 处理结束会议
  const handleEndCall = useCallback(() => {
    navigate('/video-consultation');
    setCurrentView('list');
    setSelectedConsultation(null);
  }, [navigate]);

  // 返回列表
  const handleBackToList = useCallback(() => {
    navigate('/video-consultation');
    setCurrentView('list');
    setSelectedConsultation(null);
  }, [navigate]);

  // 开始预约
  const handleStartBooking = useCallback(() => {
    setCurrentView('booking');
  }, []);

  // 渲染列表视图
  const renderListView = (): JSX.Element => (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">视频咨询</h1>
          <p className="text-gray-500 mt-1">与专业律师面对面视频沟通</p>
        </div>
        <Button
          variant="primary"
          onClick={handleStartBooking}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          预约咨询
        </Button>
      </div>

      {/* 功能介绍卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card padding="md" variant="hover">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center">
              <Video className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">视频咨询</h3>
              <p className="text-sm text-gray-500">与律师面对面沟通</p>
            </div>
          </div>
        </Card>

        <Card padding="md" variant="hover">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center">
              <Calendar className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">灵活预约</h3>
              <p className="text-sm text-gray-500">自由选择咨询时段</p>
            </div>
          </div>
        </Card>

        <Card padding="md" variant="hover">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center">
              <User className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">专业律师</h3>
              <p className="text-sm text-gray-500">资深律师在线服务</p>
            </div>
          </div>
        </Card>
      </div>

      {/* 咨询列表 */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">我的咨询</h2>
        <VideoConsultationList
          onSelect={handleSelectConsultation}
          onJoin={handleJoinMeeting}
        />
      </div>
    </div>
  );

  // 渲染预约视图
  const renderBookingView = (): JSX.Element => (
    <div className="max-w-2xl mx-auto">
      {/* 返回按钮 */}
      <Button
        variant="ghost"
        onClick={handleBackToList}
        leftIcon={<ArrowLeft className="w-4 h-4" />}
        className="mb-6"
      >
        返回列表
      </Button>

      {/* 页面标题 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">预约视频咨询</h1>
        <p className="text-gray-500 mt-1">选择时段，填写咨询信息</p>
      </div>

      {/* 预约表单 */}
      {lawyerId ? (
        <VideoConsultationBooking
          lawyerId={lawyerId}
          onSuccess={handleBookingSuccess}
          onCancel={handleBackToList}
        />
      ) : (
        <Card padding="lg">
          <div className="text-center py-8">
            <AlertCircle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">请选择律师</h3>
            <p className="text-gray-500 mb-4">
              您需要先选择一位律师才能预约视频咨询
            </p>
            <Button
              variant="primary"
              onClick={() => navigate('/lawyers')}
            >
              浏览律师
            </Button>
          </div>
        </Card>
      )}
    </div>
  );

  // 渲染详情视图
  const renderDetailView = (): JSX.Element => {
    const consultation = selectedConsultation || consultationDetail;

    if (loadingDetail && !selectedConsultation) {
      return (
        <div className="max-w-2xl mx-auto">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/4" />
            <div className="h-48 bg-gray-200 rounded" />
          </div>
        </div>
      );
    }

    if (!consultation) {
      return (
        <div className="max-w-2xl mx-auto text-center py-12">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">咨询不存在</h3>
          <p className="text-gray-500 mb-4">该咨询记录可能已被删除</p>
          <Button variant="primary" onClick={handleBackToList}>
            返回列表
          </Button>
        </div>
      );
    }

    return (
      <div className="max-w-2xl mx-auto">
        {/* 返回按钮 */}
        <Button
          variant="ghost"
          onClick={handleBackToList}
          leftIcon={<ArrowLeft className="w-4 h-4" />}
          className="mb-6"
        >
          返回列表
        </Button>

        {/* 咨询详情卡片 */}
        <Card padding="lg">
          <CardHeader>
            <div className="flex items-start justify-between">
              <CardTitle>{consultation.subject}</CardTitle>
              <StatusBadge status={consultation.status} />
            </div>
          </CardHeader>

          <CardContent>
            <div className="space-y-4">
              {/* 律师信息 */}
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
                  <User className="w-6 h-6 text-primary-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    {consultation.lawyerName || '待分配律师'}
                  </p>
                  <p className="text-sm text-gray-500">咨询律师</p>
                </div>
              </div>

              {/* 预约时间 */}
              <div className="flex items-center gap-3 text-gray-600">
                <Calendar className="w-5 h-5 text-gray-400" />
                <span>
                  {new Date(consultation.scheduledTime).toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>

              {/* 咨询时长 */}
              <div className="flex items-center gap-3 text-gray-600">
                <Clock className="w-5 h-5 text-gray-400" />
                <span>{consultation.durationMinutes} 分钟</span>
              </div>

              {/* 咨询描述 */}
              {consultation.description && (
                <div className="pt-4 border-t border-gray-100">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">咨询描述</h4>
                  <p className="text-gray-600">{consultation.description}</p>
                </div>
              )}

              {/* 会议信息 */}
              {consultation.meetingRoomId && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">会议信息</h4>
                  <div className="space-y-1">
                    <p className="text-sm">
                      <span className="text-gray-500">会议号：</span>
                      <span className="font-mono font-medium">{consultation.meetingRoomId}</span>
                    </p>
                    {consultation.meetingPassword && (
                      <p className="text-sm">
                        <span className="text-gray-500">密码：</span>
                        <span className="font-mono font-medium">{consultation.meetingPassword}</span>
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* 操作按钮 */}
            <div className="mt-6 pt-6 border-t border-gray-100 flex gap-3">
              {(consultation.status === 'confirmed' || consultation.status === 'in_progress') && (
                <Button
                  variant="primary"
                  fullWidth
                  onClick={() => handleJoinMeeting(consultation)}
                  leftIcon={<Video className="w-4 h-4" />}
                >
                  {consultation.status === 'in_progress' ? '进入咨询' : '加入会议'}
                </Button>
              )}
              {consultation.status === 'pending' && (
                <div className="flex items-center gap-2 text-amber-600">
                  <Clock className="w-4 h-4" />
                  <span>等待律师确认</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  // 渲染房间视图
  const renderRoomView = (): JSX.Element => {
    const consultationId = id || selectedConsultation?.id;

    if (!consultationId) {
      return (
        <div className="max-w-2xl mx-auto text-center py-12">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">无效的咨询</h3>
          <Button variant="primary" onClick={handleBackToList}>
            返回列表
          </Button>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {/* 返回按钮 */}
        <Button
          variant="ghost"
          onClick={handleBackToList}
          leftIcon={<ArrowLeft className="w-4 h-4" />}
          className="text-white hover:bg-white/10"
        >
          退出会议
        </Button>

        {/* 视频房间 */}
        <VideoConsultationRoom
          consultationId={consultationId}
          onEnd={handleEndCall}
        />
      </div>
    );
  };

  // 根据当前视图渲染
  return (
    <div className="min-h-screen bg-gray-50 py-6 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {currentView === 'list' && renderListView()}
        {currentView === 'booking' && renderBookingView()}
        {currentView === 'detail' && renderDetailView()}
        {currentView === 'room' && renderRoomView()}
      </div>
    </div>
  );
}

// 状态徽章组件
interface StatusBadgeProps {
  status: VideoConsultation['status'];
}

function StatusBadge({ status }: StatusBadgeProps): JSX.Element {
  const config: Record<VideoConsultation['status'], { label: string; variant: 'default' | 'primary' | 'success' | 'warning' | 'danger' }> = {
    pending: { label: '待确认', variant: 'warning' },
    confirmed: { label: '已确认', variant: 'primary' },
    in_progress: { label: '进行中', variant: 'success' },
    completed: { label: '已完成', variant: 'default' },
    cancelled: { label: '已取消', variant: 'danger' },
  };

  const { label, variant } = config[status];

  return <Badge variant={variant}>{label}</Badge>;
}

export default VideoConsultationPage;