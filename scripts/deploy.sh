#!/bin/bash

# 多Agent自动化项目开发系统部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_info "依赖检查完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p results
    mkdir -p logs
    mkdir -p generated_projects
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    
    log_info "目录创建完成"
}

# 检查环境变量
check_environment() {
    log_info "检查环境配置..."
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            log_warn ".env文件不存在，从.env.example复制"
            cp .env.example .env
            log_warn "请编辑.env文件并设置正确的配置值"
        else
            log_error ".env文件和.env.example都不存在"
            exit 1
        fi
    fi
    
    # 检查关键环境变量
    source .env
    
    if [ -z "$CLAUDE_API_KEY" ] || [ "$CLAUDE_API_KEY" = "your_claude_api_key_here" ]; then
        log_error "请在.env文件中设置有效的CLAUDE_API_KEY"
        exit 1
    fi
    
    log_info "环境配置检查完成"
}

# 构建Docker镜像
build_image() {
    log_info "构建Docker镜像..."
    
    docker-compose build
    
    log_info "Docker镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 启动主服务
    docker-compose up -d multi-agent-dev
    
    # 检查是否启用监控
    if [ "$1" = "--with-monitoring" ]; then
        log_info "启动监控服务..."
        docker-compose --profile monitoring up -d
    fi
    
    log_info "服务启动完成"
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."
    
    # 等待服务启动
    sleep 10
    
    # 检查主服务
    if docker-compose ps multi-agent-dev | grep -q "Up"; then
        log_info "多Agent开发系统服务运行正常"
    else
        log_error "多Agent开发系统服务启动失败"
        docker-compose logs multi-agent-dev
        exit 1
    fi
    
    # 检查健康状态
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_info "服务健康检查通过"
    else
        log_warn "服务健康检查失败，可能仍在启动中"
    fi
    
    log_info "服务状态检查完成"
}

# 显示访问信息
show_access_info() {
    log_info "部署完成！"
    echo ""
    echo "服务访问信息："
    echo "- 多Agent开发系统: http://localhost:8000"
    echo "- 监控指标: http://localhost:8000/metrics"
    
    if docker-compose ps prometheus &> /dev/null; then
        echo "- Prometheus: http://localhost:9090"
    fi
    
    if docker-compose ps grafana &> /dev/null; then
        echo "- Grafana: http://localhost:3000 (admin/admin)"
    fi
    
    echo ""
    echo "常用命令："
    echo "- 查看日志: docker-compose logs -f multi-agent-dev"
    echo "- 停止服务: docker-compose down"
    echo "- 重启服务: docker-compose restart"
    echo "- 进入容器: docker-compose exec multi-agent-dev bash"
}

# 主函数
main() {
    log_info "开始部署多Agent自动化项目开发系统..."
    
    check_dependencies
    create_directories
    check_environment
    build_image
    start_services "$1"
    check_services
    show_access_info
    
    log_info "部署完成！"
}

# 帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --with-monitoring    同时启动Prometheus和Grafana监控服务"
    echo "  --help              显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                   # 仅启动主服务"
    echo "  $0 --with-monitoring # 启动主服务和监控服务"
}

# 解析命令行参数
case "$1" in
    --help)
        show_help
        exit 0
        ;;
    --with-monitoring)
        main "$1"
        ;;
    "")
        main
        ;;
    *)
        log_error "未知选项: $1"
        show_help
        exit 1
        ;;
esac
