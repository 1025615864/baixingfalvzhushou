# 百姓助手后端测试命令
# 使用方法: make [命令]

.PHONY: help test test-cov test-unit test-integration test-fast test-e2e test-coverage-html test-quick test-parallel clean install-dev

# 默认目标
help:
	@echo "可用命令:"
	@echo "  make test          - 运行所有测试"
	@echo "  make test-cov      - 运行测试并生成覆盖率报告"
	@echo "  make test-unit     - 只运行单元测试"
	@echo "  make test-integration - 只运行集成测试"
	@echo "  make test-fast     - 运行快速测试（排除慢速和外部测试）"
	@echo "  make test-quick    - 快速测试（无覆盖率，最小输出）"
	@echo "  make test-parallel - 并行运行测试（需要pytest-xdist）"
	@echo "  make test-e2e      - 运行端到端测试"
	@echo "  make test-coverage-html - 生成HTML覆盖率报告"
	@echo "  make clean         - 清理测试缓存和报告"
	@echo "  make install-dev   - 安装开发依赖"

# 运行所有测试
test:
	python -m pytest

# 快速测试（无覆盖率，最小输出）
test-quick:
	python -m pytest -q --no-header

# 运行测试并生成覆盖率报告
test-cov:
	python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=60

# 只运行单元测试
test-unit:
	python -m pytest -m unit

# 只运行集成测试
test-integration:
	python -m pytest -m integration

# 运行快速测试（排除慢速和外部API测试）
test-fast:
	python -m pytest -m "not slow and not external" -q

# 并行运行测试（需要安装 pytest-xdist）
test-parallel:
	python -m pytest -n auto -q

# 运行端到端测试
test-e2e:
	python -m pytest tests/e2e/ -m e2e

# 生成HTML覆盖率报告
test-coverage-html:
	python -m pytest --cov=app --cov-report=html --cov-report=term
	@echo "覆盖率报告已生成到 htmlcov/index.html"

# 运行特定文件的测试
test-file:
	@read -p "输入测试文件路径: " file; \
	python -m pytest $$file

# 清理测试缓存和报告
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	find . -type f -name "tests/test.log" -delete 2>/dev/null || true
	@echo "清理完成"

# 安装开发依赖
install-dev:
	pip install -r requirements-dev.txt

# 运行测试并生成 JUnit 报告（用于 CI）
test-ci:
	python -m pytest --cov=app --cov-report=xml --cov-report=term -v --junitxml=test-results.xml

# 监视模式（需要安装 pytest-watch）
test-watch:
	ptw -- -v

# 并行运行测试（需要安装 pytest-xdist）
test-parallel:
	python -m pytest -n auto -v
