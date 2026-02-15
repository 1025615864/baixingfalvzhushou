/**
 * DeviceList - 设备管理列表组件
 */

import { useState } from 'react';
import {
  DesktopOutlined,
  MobileOutlined,
  TabletOutlined,
  QuestionCircleOutlined,
  EnvironmentOutlined,
  ClockCircleOutlined,
  LogoutOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';

import type { DeviceType } from '../types';
import { useDeviceList, useRevokeDevice, formatDateTime } from '../hooks/useSecurity';

interface DeviceListProps {
  currentDeviceId?: string;
}

const deviceIcons: Record<DeviceType, React.ReactNode> = {
  desktop: <DesktopOutlined className="text-2xl text-blue-500" />,
  mobile: <MobileOutlined className="text-2xl text-green-500" />,
  tablet: <TabletOutlined className="text-2xl text-purple-500" />,
  unknown: <QuestionCircleOutlined className="text-2xl text-gray-500" />,
};

/**
 * 设备管理列表组件
 */
export function DeviceList({ currentDeviceId }: DeviceListProps): JSX.Element {
  const [revokingDeviceId, setRevokingDeviceId] = useState<string | null>(null);
  
  const { data: devices, isLoading, error } = useDeviceList();
  const revokeMutation = useRevokeDevice();

  const handleRevoke = (deviceId: string): void => {
    setRevokingDeviceId(deviceId);
    void (async (): Promise<void> => {
      try {
        await revokeMutation.mutateAsync({ deviceId });
      } catch {
        // 错误已在 mutation 中处理
      } finally {
        setRevokingDeviceId(null);
      }
    })();
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4" />
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center text-red-600">
          <ExclamationCircleOutlined className="mr-2" />
          <span>加载设备列表失败</span>
        </div>
      </div>
    );
  }

  const deviceList = devices || [];
  const currentDevice = deviceList.find(d => d.isCurrentDevice || d.id === currentDeviceId);
  const otherDevices = deviceList.filter(d => !d.isCurrentDevice && d.id !== currentDeviceId);

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* 标题 */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">设备管理</h3>
        <p className="text-sm text-gray-500 mt-1">
          管理已登录的设备，您可以随时退出其他设备
        </p>
      </div>

      <div className="divide-y divide-gray-200">
        {/* 当前设备 */}
        {currentDevice && (
          <div className="p-4 bg-blue-50">
            <div className="flex items-start">
              <div className="p-3 bg-white rounded-lg shadow-sm mr-4">
                {deviceIcons[currentDevice.deviceType]}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center">
                  <h4 className="text-sm font-semibold text-gray-900">
                    {currentDevice.deviceName}
                  </h4>
                  <span className="ml-2 px-2 py-0.5 text-xs font-medium text-green-700 bg-green-100 rounded-full">
                    当前设备
                  </span>
                </div>
                <div className="mt-1 text-xs text-gray-500 space-y-1">
                  <div className="flex items-center">
                    <DesktopOutlined className="mr-1" />
                    {currentDevice.browser} • {currentDevice.os}
                  </div>
                  <div className="flex items-center">
                    <EnvironmentOutlined className="mr-1" />
                    {currentDevice.ipAddress}
                    {currentDevice.location && ` • ${currentDevice.location}`}
                  </div>
                  <div className="flex items-center">
                    <ClockCircleOutlined className="mr-1" />
                    最后活跃: {formatDateTime(currentDevice.lastActiveAt)}
                  </div>
                </div>
              </div>
              <div className="flex items-center text-green-600">
                <CheckCircleOutlined className="mr-1" />
                <span className="text-xs">在线</span>
              </div>
            </div>
          </div>
        )}

        {/* 其他设备 */}
        {otherDevices.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            没有其他登录设备
          </div>
        ) : (
          otherDevices.map((device) => (
            <div key={device.id} className="p-4 hover:bg-gray-50 transition-colors">
              <div className="flex items-start">
                <div className="p-3 bg-gray-100 rounded-lg mr-4">
                  {deviceIcons[device.deviceType]}
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-semibold text-gray-900">
                    {device.deviceName}
                  </h4>
                  <div className="mt-1 text-xs text-gray-500 space-y-1">
                    <div className="flex items-center">
                      <DesktopOutlined className="mr-1" />
                      {device.browser} • {device.os}
                    </div>
                    <div className="flex items-center">
                      <EnvironmentOutlined className="mr-1" />
                      {device.ipAddress}
                      {device.location && ` • ${device.location}`}
                    </div>
                    <div className="flex items-center">
                      <ClockCircleOutlined className="mr-1" />
                      最后活跃: {formatDateTime(device.lastActiveAt)}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleRevoke(device.id)}
                  disabled={revokeMutation.isPending && revokingDeviceId === device.id}
                  className="ml-4 px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 rounded-md hover:bg-red-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  <LogoutOutlined className="mr-1" />
                  {revokeMutation.isPending && revokingDeviceId === device.id ? '退出中...' : '退出'}
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 退出所有其他设备 */}
      {otherDevices.length > 0 && (
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={() => {
              void (async (): Promise<void> => {
                for (const device of otherDevices) {
                  try {
                    await revokeMutation.mutateAsync({ deviceId: device.id });
                  } catch {
                    // 继续退出其他设备
                  }
                }
              })();
            }}
            disabled={revokeMutation.isPending}
            className="w-full py-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-md hover:bg-red-50 transition-colors disabled:opacity-50"
          >
            退出所有其他设备 ({otherDevices.length})
          </button>
        </div>
      )}
    </div>
  );
}