# 部署指南

本文档详细介绍如何在不同环境中部署多Agent自动化项目开发系统。

## 📋 部署前准备

### 系统要求

- **操作系统**: Linux (推荐 Ubuntu 20.04+), macOS, Windows
- **Python**: 3.9 或更高版本
- **内存**: 最少 2GB，推荐 4GB+
- **存储**: 最少 5GB 可用空间
- **网络**: 稳定的互联网连接（访问Claude API）

### 必需的服务

- **Claude API**: 有效的Anthropic API密钥
- **Git**: 版本控制（可选但推荐）
- **Docker**: 容器化部署（可选）

## 🚀 部署方式

### 方式一：本地Python环境部署

#### 1. 克隆代码

```bash
git clone <repository-url>
cd multi-agent-dev-system
```

#### 2. 创建虚拟环境

```bash
# 使用venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 使用conda
conda create -n multi-agent-dev python=3.9
conda activate multi-agent-dev
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置环境

```bash
cp .env.example .env
# 编辑.env文件，设置必要的配置
```

#### 5. 运行系统

```bash
# 交互式模式
python main.py --interactive

# 命令行模式
python main.py --title "测试项目" --description "这是一个测试项目"
```

### 方式二：Docker容器部署

#### 1. 准备环境

```bash
# 确保Docker和Docker Compose已安装
docker --version
docker-compose --version
```

#### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，至少设置CLAUDE_API_KEY
```

#### 3. 使用部署脚本

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

#### 4. 手动部署（可选）

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f multi-agent-dev
```

### 方式三：生产环境部署

#### 1. 使用Docker Swarm

```bash
# 初始化Swarm
docker swarm init

# 部署服务栈
docker stack deploy -c docker-compose.yml multi-agent-dev
```

#### 2. 使用Kubernetes

创建Kubernetes配置文件：

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multi-agent-dev
spec:
  replicas: 2
  selector:
    matchLabels:
      app: multi-agent-dev
  template:
    metadata:
      labels:
        app: multi-agent-dev
    spec:
      containers:
      - name: multi-agent-dev
        image: multi-agent-dev:latest
        env:
        - name: CLAUDE_API_KEY
          valueFrom:
            secretKeyRef:
              name: claude-api-secret
              key: api-key
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

部署到Kubernetes：

```bash
kubectl apply -f k8s/
```

## 🔧 配置详解

### 环境变量配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `CLAUDE_API_KEY` | ✅ | - | Claude API密钥 |
| `CLAUDE_MODEL` | ❌ | `claude-3-sonnet-20240229` | 使用的模型 |
| `CLAUDE_MAX_TOKENS` | ❌ | `4000` | 最大Token数 |
| `LOG_LEVEL` | ❌ | `INFO` | 日志级别 |
| `MAX_RETRIES` | ❌ | `3` | 最大重试次数 |
| `RESULTS_DIR` | ❌ | `./results` | 结果存储目录 |
| `LOGS_DIR` | ❌ | `./logs` | 日志存储目录 |
| `GIT_ENABLED` | ❌ | `false` | 是否启用Git集成 |
| `METRICS_ENABLED` | ❌ | `true` | 是否启用监控 |

### 高级配置

#### 1. 自定义Agent配置

修改Agent的系统提示和行为：

```python
# 在multi_agent_dev/agents/目录下修改对应的Agent类
class CustomDeveloperAgent(DeveloperAgent):
    def _get_default_system_prompt(self):
        return """
        你是一个专门开发Python Web应用的高级工程师...
        """
```

#### 2. 工作流自定义

修改工作流引擎的执行逻辑：

```python
# 在multi_agent_dev/core/workflow_engine.py中
class CustomWorkflowEngine(WorkflowEngine):
    async def execute_development_workflow(self, requirements):
        # 自定义工作流逻辑
        pass
```

## 📊 监控和日志

### 启用监控

```bash
# 启动带监控的完整服务
./scripts/deploy.sh --with-monitoring
```

访问监控界面：
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### 日志管理

#### 日志级别

```bash
# 设置日志级别
export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

#### 日志轮转

使用logrotate配置日志轮转：

```bash
# /etc/logrotate.d/multi-agent-dev
/app/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 app app
}
```

### 健康检查

```bash
# 运行健康检查
python scripts/health_check.py

# Docker健康检查
docker-compose exec multi-agent-dev python scripts/health_check.py
```

## 🔒 安全配置

### API密钥管理

#### 1. 环境变量（推荐）

```bash
export CLAUDE_API_KEY="your-api-key"
```

#### 2. Docker Secrets

```yaml
# docker-compose.yml
services:
  multi-agent-dev:
    secrets:
      - claude_api_key
    environment:
      - CLAUDE_API_KEY_FILE=/run/secrets/claude_api_key

secrets:
  claude_api_key:
    file: ./secrets/claude_api_key.txt
```

#### 3. Kubernetes Secrets

```bash
kubectl create secret generic claude-api-secret \
  --from-literal=api-key=your-api-key
```

### 网络安全

#### 1. 防火墙配置

```bash
# 只允许必要的端口
ufw allow 8000/tcp  # 监控端口
ufw allow 22/tcp    # SSH
ufw enable
```

#### 2. 反向代理

使用Nginx作为反向代理：

```nginx
# /etc/nginx/sites-available/multi-agent-dev
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🚨 故障排除

### 常见问题

#### 1. Claude API连接失败

```bash
# 检查网络连接
curl -I https://api.anthropic.com

# 验证API密钥
python -c "
from multi_agent_dev.api.claude_client import ClaudeAPIClient
client = ClaudeAPIClient()
print('API密钥有效')
"
```

#### 2. 内存不足

```bash
# 检查内存使用
free -h
docker stats

# 调整Docker内存限制
# 在docker-compose.yml中修改deploy.resources.limits.memory
```

#### 3. 权限问题

```bash
# 检查文件权限
ls -la results/ logs/

# 修复权限
sudo chown -R $USER:$USER results/ logs/
chmod -R 755 results/ logs/
```

### 日志分析

#### 1. 查看应用日志

```bash
# 本地部署
tail -f logs/multi_agent_dev.log

# Docker部署
docker-compose logs -f multi-agent-dev
```

#### 2. 查看系统日志

```bash
# 系统日志
journalctl -u docker
journalctl -f

# Docker日志
docker logs <container-id>
```

### 性能优化

#### 1. 调整并发数

```bash
# 在.env文件中
MAX_CONCURRENT_TASKS=3  # 根据系统性能调整
```

#### 2. 优化Token使用

```bash
# 减少最大Token数以节省成本
CLAUDE_MAX_TOKENS=2000
```

#### 3. 启用缓存

```python
# 在配置中启用结果缓存
CACHE_ENABLED=true
CACHE_TTL=3600  # 缓存1小时
```

## 📈 扩展部署

### 水平扩展

#### 1. 负载均衡

使用HAProxy或Nginx进行负载均衡：

```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - multi-agent-dev-1
      - multi-agent-dev-2
```

#### 2. 数据库分离

使用外部数据库存储结果：

```yaml
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: multi_agent_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### 高可用部署

#### 1. 多实例部署

```bash
# 启动多个实例
docker-compose up -d --scale multi-agent-dev=3
```

#### 2. 故障转移

配置健康检查和自动重启：

```yaml
services:
  multi-agent-dev:
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "scripts/health_check.py"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 🔄 更新和维护

### 版本更新

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build --no-cache

# 重启服务
docker-compose up -d
```

### 数据备份

```bash
# 备份结果数据
tar -czf backup-$(date +%Y%m%d).tar.gz results/ logs/

# 定期备份脚本
#!/bin/bash
BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "$BACKUP_DIR/multi-agent-dev-$DATE.tar.gz" results/ logs/
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

### 监控维护

```bash
# 清理旧日志
find logs/ -name "*.log" -mtime +7 -delete

# 清理旧结果
find results/ -name "*.json" -mtime +30 -delete

# 重启监控服务
docker-compose restart prometheus grafana
```

---

如有部署问题，请参考[故障排除文档](TROUBLESHOOTING.md)或提交Issue。
