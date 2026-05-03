.PHONY: install dev test lint clean build run help

help: ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装生产依赖
	pip install -r requirements.txt

dev: ## 安装开发依赖
	pip install -r requirements-dev.txt
	cd web-admin && npm install

test: ## 运行测试
	pytest tests/ -v --cov=tdx --cov-report=html

lint: ## 代码检查
	flake8 *.py
	black --check *.py
	isort --check-only *.py

format: ## 代码格式化
	black *.py
	isort *.py

clean: ## 清理生成文件
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ .pytest_cache/ build/ dist/ *.egg-info/
	rm -f *.db
	cd web-admin && rm -rf node_modules/ dist/

build: ## 构建前端
	cd web-admin && npm run build

run: ## 启动后端服务
	python start_server.py

run-dev: ## 启动开发服务
	python start_server.py --debug

run-all: build run ## 构建并启动所有服务

docker-build: ## 构建 Docker 镜像
	docker build -t tdx-screener .

docker-up: ## 启动 Docker 容器
	docker-compose up -d

docker-down: ## 停止 Docker 容器
	docker-compose down

docker-logs: ## 查看 Docker 日志
	docker-compose logs -f

db-init: ## 初始化数据库
	python -c "from database import db; print('Database initialized')"

db-reset: ## 重置数据库
	rm -f *.db
	python -c "from database import db; print('Database reset')"
