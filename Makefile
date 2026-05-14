.PHONY: help up up-all up-infra up-micro down restart logs ps test lint build

help:
	@echo "百姓法律助手 - 开发命令"
	@echo ""
	@echo "  make up            启动核心服务 (db/redis/backend/frontend/minio)"
	@echo "  make up-infra      启动核心 + 基础设施 (kafka/监控)"
	@echo "  make up-micro      启动核心 + 微服务集群"
	@echo "  make up-all        启动全部服务"
	@echo "  make down          停止所有服务"
	@echo "  make restart       重启核心服务"
	@echo "  make logs          查看后端日志"
	@echo "  make ps            查看运行中的服务"
	@echo "  make test          运行后端测试"
	@echo "  make test-e2e      运行 E2E 测试"
	@echo "  make lint          运行代码检查"
	@echo "  make build         构建所有镜像"
	@echo "  make migrate       运行数据库迁移"
	@echo "  make backup        备份所有数据库"

up:
	docker compose up -d

up-infra:
	docker compose --profile infra up -d

up-micro:
	docker compose --profile microservice up -d

up-all:
	docker compose --profile infra --profile microservice up -d

down:
	docker compose --profile infra --profile microservice down

restart:
	docker compose restart backend

logs:
	docker compose logs -f backend

ps:
	docker compose --profile infra --profile microservice ps

test:
	docker compose exec backend python -m pytest backend/tests/ -v --tb=short

test-e2e:
	docker compose exec backend python -m pytest tests/e2e/ -v --tb=short

lint:
	docker compose exec backend python -m ruff check backend/ services/

build:
	docker compose --profile infra --profile microservice build

migrate:
	docker compose exec backend python -m alembic upgrade head

backup:
	bash scripts/backup_all_dbs.sh

db-shell:
	docker compose exec db psql -U postgres -d baixing_law

redis-cli:
	docker compose exec redis redis-cli -a $${REDIS_PASSWORD}

kafka-topics:
	docker compose exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --list
