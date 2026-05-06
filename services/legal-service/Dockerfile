FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8004 50052

ENV SERVICE_PORT=8004
ENV GRPC_PORT=50052
ENV DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/legal_service
ENV REDIS_URL=redis://localhost:6379
ENV KAFKA_BOOTSTRAP_SERVERS=localhost:9092
ENV CONSUL_ENABLED=false
ENV KAFKA_ENABLED=false
ENV RATE_LIMIT_ENABLED=true

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]