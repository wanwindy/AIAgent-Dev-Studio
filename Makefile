# 多Agent自动化项目开发系统 Makefile

.PHONY: help install test lint format clean run example docker-build docker-run docker-stop health

# 默认目标
help:
	@echo "多Agent自动化项目开发系统"
	@echo "=========================="
	@echo ""
	@echo "可用命令:"
	@echo "  install      - 安装依赖"
	@echo "  test         - 运行测试"
	@echo "  lint         - 代码检查"
	@echo "  format       - 代码格式化"
	@echo "  clean        - 清理临时文件"
	@echo "  run          - 运行示例"
	@echo "  example      - 运行交互式示例"
	@echo "  docker-build - 构建Docker镜像"
	@echo "  docker-run   - 运行Docker容器"
	@echo "  docker-stop  - 停止Docker容器"
	@echo "  health       - 健康检查"
	@echo "  deploy       - 部署系统"
	@echo ""

# 安装依赖
install:
	@echo "安装Python依赖..."
	pip install -r requirements.txt
	@echo "依赖安装完成"

# 运行测试
test:
	@echo "运行单元测试..."
	python -m pytest tests/ -v
	@echo "测试完成"

# 代码检查
lint:
	@echo "运行代码检查..."
	flake8 multi_agent_dev/ main.py --max-line-length=100
	mypy multi_agent_dev/ --ignore-missing-imports
	@echo "代码检查完成"

# 代码格式化
format:
	@echo "格式化代码..."
	black multi_agent_dev/ main.py examples/ tests/ --line-length=100
	@echo "代码格式化完成"

# 清理临时文件
clean:
	@echo "清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf temp_projects/
	@echo "清理完成"

# 运行示例
run:
	@echo "运行快速示例..."
	python run_example.py

# 运行交互式示例
example:
	@echo "运行交互式示例..."
	python run_example.py --interactive

# 构建Docker镜像
docker-build:
	@echo "构建Docker镜像..."
	docker-compose build
	@echo "Docker镜像构建完成"

# 运行Docker容器
docker-run:
	@echo "启动Docker容器..."
	docker-compose up -d
	@echo "Docker容器已启动"
	@echo "健康检查: http://localhost:8000/health"
	@echo "指标监控: http://localhost:8000/metrics"

# 停止Docker容器
docker-stop:
	@echo "停止Docker容器..."
	docker-compose down
	@echo "Docker容器已停止"

# 健康检查
health:
	@echo "执行健康检查..."
	python scripts/health_check.py

# 部署系统
deploy:
	@echo "部署系统..."
	chmod +x scripts/deploy.sh
	./scripts/deploy.sh

# 部署带监控的系统
deploy-monitoring:
	@echo "部署系统（包含监控）..."
	chmod +x scripts/deploy.sh
	./scripts/deploy.sh --with-monitoring

# 查看日志
logs:
	@echo "查看应用日志..."
	tail -f logs/multi_agent_dev.log

# 查看Docker日志
docker-logs:
	@echo "查看Docker日志..."
	docker-compose logs -f multi-agent-dev

# 开发环境设置
dev-setup: install
	@echo "设置开发环境..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "已创建.env文件，请编辑并设置API密钥"; \
	fi
	mkdir -p logs results generated_projects
	@echo "开发环境设置完成"

# 生产环境检查
prod-check:
	@echo "生产环境检查..."
	@if [ -z "$$CLAUDE_API_KEY" ]; then \
		echo "错误: CLAUDE_API_KEY环境变量未设置"; \
		exit 1; \
	fi
	@echo "环境检查通过"

# 备份数据
backup:
	@echo "备份数据..."
	tar -czf backup-$$(date +%Y%m%d_%H%M%S).tar.gz results/ logs/ generated_projects/
	@echo "备份完成"

# 监控指标
metrics:
	@echo "获取系统指标..."
	curl -s http://localhost:8000/metrics | python -m json.tool

# 完整的CI/CD流程
ci: clean lint test
	@echo "CI流程完成"

# 发布准备
release: ci format
	@echo "发布准备完成"
