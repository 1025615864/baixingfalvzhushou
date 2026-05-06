FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8007

ENV SERVICE_PORT=8007
ENV DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/community
ENV REDIS_URL=redis://localhost:6379
ENV KAFKA_BOOTSTRAP_SERVERS=localhost:9092
ENV CONSUL_ENABLED=false

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]
