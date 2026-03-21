# 告警规则配置

## 1. 服务可用性告警

| 告警名称 | 条件 | 严重级别 | 说明 |
|---------|------|---------|------|
| ServiceDown | up{job=~".*-service"} == 0 持续1分钟 | critical | 服务实例宕机 |
| ServiceHighLatency | P95响应延迟 > 2s 持续5分钟 | warning | 服务响应延迟过高 |

## 2. 数据库告警

| 告警名称 | 条件 | 严重级别 | 说明 |
|---------|------|---------|------|
| DatabaseConnectionPoolExhausted | 连接池利用率 > 95% 持续5分钟 | critical | 连接池即将耗尽 |
| DatabaseSlowQueries | 慢查询 > 10/s 持续5分钟 | warning | 慢查询过多 |
| DatabaseHighCPU | CPU使用率 > 80% 持续10分钟 | warning | 数据库CPU过高 |

## 3. Redis告警

| 告警名称 | 条件 | 严重级别 | 说明 |
|---------|------|---------|------|
| RedisHighMemoryUsage | 内存使用率 > 80% 持续5分钟 | warning | 内存使用率过高 |
| RedisTooManyConnections | 连接数 > 10000 持续5分钟 | warning | 连接数过多 |

## 4. 支付服务告警

| 告警名称 | 条件 | 严重级别 | 说明 |
|---------|------|---------|------|
| PaymentFailureRate | 失败率 > 5% 持续5分钟 | critical | 支付失败率过高 |
| PaymentCallbackDelay | P95延迟 > 5s 持续5分钟 | warning | 回调处理延迟 |
| InsufficientBalance | 余额不足错误 > 10次/小时 | warning | 余额不足错误增多 |

## 5. AI服务告警

| 告警名称 | 条件 | 严重级别 | 说明 |
|---------|------|---------|------|
| AIServiceTimeout | P95响应 > 10s 持续5分钟 | critical | AI响应超时 |
| AIHighTokenUsage | Token消耗 > 100万/小时 | warning | Token使用量过高 |
| AIModelFailure | 失败率 > 10% 持续5分钟 | critical | 模型调用失败率过高 |

## 6. Kafka告警

| 告警名称 | 条件 | 严重级别 | 说明 |
|---------|------|---------|------|
| KafkaConsumerLag | 消费者滞后 > 10000条 持续10分钟 | warning | 消息消费滞后 |
| KafkaTopicBacklog | 消息积压 > 100万 持续10分钟 | warning | Topic积压过多 |
| KafkaPartitionUnavailable | 不可用分区 > 0 持续1分钟 | critical | 分区不可用 |

## 7. 资源使用告警

| 告警名称 | 条件 | 严重级别 | 说明 |
|---------|------|---------|------|
| PodHighCPU | CPU使用率 > 90% 持续10分钟 | warning | Pod CPU过高 |
| PodHighMemory | 内存使用率 > 90% 持续5分钟 | warning | Pod内存过高 |
| HPAAtMaxReplicas | 副本数 == 最大副本数 持续10分钟 | warning | 压力过大需扩容 |
| PodRestartingTooMuch | 重启频率 > 0.1/s 持续5分钟 | warning | Pod异常重启 |

## 8. Alertmanager 路由配置

```yaml
# alertmanager-config.yaml
route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
    group_wait: 10s
  - match:
      alertname: 'Payment*'
    receiver: 'payment-alerts'
  - match:
      alertname: 'AI*'
    receiver: 'ai-alerts'

receivers:
- name: 'default'
  webhook_configs:
  - url: 'http://notification-service:8009/alerts'

- name: 'critical-alerts'
  webhook_configs:
  - url: 'http://notification-service:8009/alerts/critical'
  - url: 'http://sms-service:8080/send'  # 紧急短信

- name: 'payment-alerts'
  webhook_configs:
  - url: 'http://payment-ops-slack'

- name: 'ai-alerts'
  webhook_configs:
  - url: 'http://ai-ops-slack'
```
