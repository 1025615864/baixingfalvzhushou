# Embedding Service

独立的Embedding模型微服务，解决三个服务重复加载模型的问题。

## 快速开始

```bash
cd services/embedding-service
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8006 --reload
```

## API端点

- `POST /embed/texts` - 批量文本Embedding
- `POST /embed/query` - 单条查询Embedding
- `GET /health` - 健康检查
- `GET /` - 服务信息

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| EMBEDDING_MODEL | shibing624/text2vec-base-chinese | Embedding模型 |
| EMBEDDING_DEVICE | cpu | 运行设备 |
| SERVICE_PORT | 8006 | 服务端口 |
| ENVIRONMENT | development | 运行环境 |
