# デプロイメント設計書

## 🚀 デプロイメント戦略

### 環境構成
- **開発環境**: ローカル開発用
- **ステージング環境**: 本番前テスト用
- **本番環境**: 本番サービス用

## 🏗️ インフラ構成

### クラウドプロバイダー
- **メイン**: AWS
- **バックアップ**: Google Cloud Platform

### サービス構成
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │────│   Route 53      │────│   ALB            │
│   (CDN)         │    │   (DNS)         │    │   (Load Balancer)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐             │
                       │   ECS/Fargate   │◄────────────┘
                       │   (Container)   │
                       └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   RDS           │
                       │   (PostgreSQL)  │
                       └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   ElastiCache   │
                       │   (Redis)       │
                       └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   S3            │
                       │   (File Storage)│
                       └─────────────────┘
```

## 🐳 コンテナ化

### Docker構成
```dockerfile
# Frontend Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose（開発環境）
```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ai_family_sim
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ai_family_sim
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## ☸️ Kubernetes構成

### デプロイメント設定
```yaml
# frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: ai-family-simulator/frontend:latest
        ports:
        - containerPort: 80
        env:
        - name: REACT_APP_API_URL
          value: "https://api.ai-family-simulator.com"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
```

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: ai-family-simulator/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          value: "redis://redis-service:6379"
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
```

## 🔧 CI/CD パイプライン

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run tests
      run: |
        cd backend && python -m pytest
        cd frontend && npm test

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Build and push Docker images
      run: |
        docker build -t ai-family-simulator/frontend:${{ github.sha }} ./frontend
        docker build -t ai-family-simulator/backend:${{ github.sha }} ./backend
        docker push ai-family-simulator/frontend:${{ github.sha }}
        docker push ai-family-simulator/backend:${{ github.sha }}

    - name: Deploy to ECS
      run: |
        aws ecs update-service --cluster ai-family-simulator --service frontend --force-new-deployment
        aws ecs update-service --cluster ai-family-simulator --service backend --force-new-deployment
```

## 📊 監視・ログ

### 監視ツール
- **APM**: AWS X-Ray
- **メトリクス**: CloudWatch
- **ログ**: CloudWatch Logs
- **アラート**: SNS + Lambda

### ログ設定
```python
# backend/app/config/logging.py
import logging
import sys

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/ai-family-simulator/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "default",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
```

## 🔒 セキュリティ設定

### SSL/TLS
- **証明書**: AWS Certificate Manager
- **暗号化**: TLS 1.3
- **HSTS**: 有効

### セキュリティヘッダー
```nginx
# nginx.conf
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
add_header Content-Security-Policy "default-src 'self'";
```

### 環境変数管理
```bash
# .env.production
DATABASE_URL=postgresql://user:pass@rds.amazonaws.com:5432/ai_family_sim
REDIS_URL=redis://elasticache.amazonaws.com:6379
JWT_SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
```

## 📈 スケーリング戦略

### 水平スケーリング
- **フロントエンド**: ECS Auto Scaling (2-10 instances)
- **バックエンド**: ECS Auto Scaling (2-20 instances)
- **データベース**: RDS Read Replicas

### キャッシュ戦略
- **Redis**: セッション管理、API レスポンスキャッシュ
- **CloudFront**: 静的ファイル配信
- **ElastiCache**: データベースクエリキャッシュ

## 🚨 災害復旧

### バックアップ戦略
- **データベース**: 日次自動バックアップ、7日間保持
- **ファイル**: S3 Cross-Region Replication
- **設定**: Infrastructure as Code (Terraform)

### 復旧手順
1. **RTO**: 4時間以内
2. **RPO**: 1時間以内
3. **手順**: 自動化された復旧スクリプト
