import { Suspense, lazy, useCallback, useState } from 'react';
import { Button, Card, Col, Row, Statistic, message } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, PlusOutlined } from '@ant-design/icons';

import {
  useAIProviders,
  useAIModelConfigs,
  useCreateAIModelConfig,
  useUpdateAIModelConfig,
  useDeleteAIModelConfig,
  useTestAIModelConfig,
  useTriggerHealthCheck,
  useAIConfigStatsSummary,
} from '../hooks/useAIConfig';
import type {
  AIModelConfigItem,
  CreateAIModelConfigRequest,
  UpdateAIModelConfigRequest,
} from '../types/ai-config';

const LazyAIConfigTable = lazy(() => import('./AIConfigTable').then((module) => ({ default: module.AIConfigTable })));
const LazyAIConfigForm = lazy(() => import('./AIConfigForm').then((module) => ({ default: module.AIConfigForm })));

function AdminAIConfigSkeleton({ rows = 4 }: { rows?: number }): JSX.Element {
  return (
    <div className="space-y-4">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-24 animate-pulse rounded-lg bg-slate-100" />
      ))}
    </div>
  );
}

export function AdminAIConfigPanel(): JSX.Element {
  const [editingAIConfig, setEditingAIConfig] = useState<AIModelConfigItem | null>(null);
  const [aiConfigFormVisible, setAIConfigFormVisible] = useState<boolean>(false);
  const [testingConfigIds, setTestingConfigIds] = useState<Set<number>>(new Set());
  const [healthCheckingIds, setHealthCheckingIds] = useState<Set<number>>(new Set());

  const { data: aiProvidersData } = useAIProviders(true);
  const {
    data: aiConfigsData,
    isLoading: aiConfigsLoading,
    refetch: refetchAIConfigs,
  } = useAIModelConfigs(undefined, true);
  const { data: aiConfigStats, isLoading: aiConfigStatsLoading } = useAIConfigStatsSummary(undefined, true);

  const createAIConfigMutation = useCreateAIModelConfig();
  const updateAIConfigMutation = useUpdateAIModelConfig();
  const deleteAIConfigMutation = useDeleteAIModelConfig();
  const testAIConfigMutation = useTestAIModelConfig();
  const healthCheckMutation = useTriggerHealthCheck();

  const handleAddAIConfig = useCallback(() => {
    setEditingAIConfig(null);
    setAIConfigFormVisible(true);
  }, []);

  const handleEditAIConfig = useCallback((config: AIModelConfigItem) => {
    setEditingAIConfig(config);
    setAIConfigFormVisible(true);
  }, []);

  const handleSaveAIConfig = useCallback(
    (data: CreateAIModelConfigRequest | UpdateAIModelConfigRequest) => {
      void (async () => {
        try {
          if (editingAIConfig) {
            await updateAIConfigMutation.mutateAsync({
              configId: editingAIConfig.id,
              data: data as UpdateAIModelConfigRequest,
            });
            void message.success('AI配置已更新');
          } else {
            await createAIConfigMutation.mutateAsync(data as CreateAIModelConfigRequest);
            void message.success('AI配置已创建');
          }
          setAIConfigFormVisible(false);
          setEditingAIConfig(null);
          void refetchAIConfigs();
        } catch {
          void message.error(editingAIConfig ? '更新AI配置失败' : '创建AI配置失败');
        }
      })();
    },
    [editingAIConfig, createAIConfigMutation, updateAIConfigMutation, refetchAIConfigs]
  );

  const handleDeleteAIConfig = useCallback(
    (configId: number) => {
      void (async () => {
        try {
          await deleteAIConfigMutation.mutateAsync(configId);
          void message.success('AI配置已删除');
          void refetchAIConfigs();
        } catch {
          void message.error('删除AI配置失败');
        }
      })();
    },
    [deleteAIConfigMutation, refetchAIConfigs]
  );

  const handleToggleAIConfigEnabled = useCallback(
    (configId: number, currentStatus: boolean) => {
      void (async () => {
        try {
          await updateAIConfigMutation.mutateAsync({
            configId,
            data: { enabled: !currentStatus },
          });
          void message.success(`AI配置已${currentStatus ? '禁用' : '启用'}`);
          void refetchAIConfigs();
        } catch {
          void message.error('操作失败');
        }
      })();
    },
    [updateAIConfigMutation, refetchAIConfigs]
  );

  const handleTestAIConfig = useCallback(
    (configId: number) => {
      void (async () => {
        setTestingConfigIds((prev) => new Set(prev).add(configId));
        try {
          const result = await testAIConfigMutation.mutateAsync(configId);
          if (result.status === 'success') {
            void message.success(`测试通过，延迟: ${result.latency_ms}ms`);
          } else {
            void message.error(`测试失败: ${result.message}`);
          }
          void refetchAIConfigs();
        } catch {
          void message.error('测试失败');
        } finally {
          setTestingConfigIds((prev) => {
            const next = new Set(prev);
            next.delete(configId);
            return next;
          });
        }
      })();
    },
    [testAIConfigMutation, refetchAIConfigs]
  );

  const handleHealthCheckAIConfig = useCallback(
    (configId: number) => {
      void (async () => {
        setHealthCheckingIds((prev) => new Set(prev).add(configId));
        try {
          const result = await healthCheckMutation.mutateAsync(configId);
          if (result.success) {
            void message.success(`健康检查通过，延迟: ${result.latency_ms}ms`);
          } else {
            void message.warning(`健康检查异常: ${result.health_check_message}`);
          }
          void refetchAIConfigs();
        } catch {
          void message.error('健康检查失败');
        } finally {
          setHealthCheckingIds((prev) => {
            const next = new Set(prev);
            next.delete(configId);
            return next;
          });
        }
      })();
    },
    [healthCheckMutation, refetchAIConfigs]
  );

  return (
    <>
      <Card
        title="AI模型配置"
        className="shadow-sm"
        extra={(
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAddAIConfig}
          >
            添加配置
          </Button>
        )}
      >
        <Row gutter={16} className="mb-4">
          <Col span={6}>
            <Statistic title="总配置" value={aiConfigStats?.total || 0} loading={aiConfigStatsLoading} />
          </Col>
          <Col span={6}>
            <Statistic
              title="已启用"
              value={aiConfigStats?.enabled || 0}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="健康"
              value={aiConfigStats?.healthy || 0}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="异常"
              value={(aiConfigStats?.unhealthy || 0) + (aiConfigStats?.degraded || 0)}
              valueStyle={{ color: aiConfigStats?.unhealthy || aiConfigStats?.degraded ? '#cf1322' : '#3f8600' }}
              prefix={(aiConfigStats?.unhealthy || aiConfigStats?.degraded) ? <CloseCircleOutlined /> : <CheckCircleOutlined />}
            />
          </Col>
        </Row>

        <Suspense fallback={<AdminAIConfigSkeleton rows={4} />}>
          <LazyAIConfigTable
            configs={aiConfigsData?.items || []}
            loading={aiConfigsLoading}
            onEdit={handleEditAIConfig}
            onDelete={handleDeleteAIConfig}
            onToggleEnabled={handleToggleAIConfigEnabled}
            onTest={handleTestAIConfig}
            onHealthCheck={handleHealthCheckAIConfig}
            testingIds={testingConfigIds}
            healthCheckingIds={healthCheckingIds}
          />
        </Suspense>
      </Card>

      {aiConfigFormVisible && (
        <Suspense fallback={null}>
          <LazyAIConfigForm
            visible={aiConfigFormVisible}
            config={editingAIConfig}
            providers={aiProvidersData || []}
            onCancel={() => {
              setAIConfigFormVisible(false);
              setEditingAIConfig(null);
            }}
            onConfirm={handleSaveAIConfig}
            loading={createAIConfigMutation.isPending || updateAIConfigMutation.isPending}
          />
        </Suspense>
      )}
    </>
  );
}
