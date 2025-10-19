# 開発ガイド

## 🚀 セットアップ手順

### 前提条件
- Node.js 18.0.0以上
- Python 3.11.0以上
- Docker & Docker Compose
- Git

### 1. リポジトリのクローン
```bash
git clone https://github.com/your-org/ai-family-simulator.git
cd ai-family-simulator
```

### 2. 環境変数の設定
```bash
cp env.example .env
# .envファイルを編集して必要な値を設定
```

### 3. 依存関係のインストール
```bash
# ルートディレクトリで
npm install

# フロントエンド
cd frontend && npm install

# バックエンド
cd ../backend && pip install -r requirements.txt
```

### 4. データベースのセットアップ
```bash
# Docker Composeでデータベースを起動
docker-compose up -d db redis

# データベースマイグレーション
cd backend && python -m alembic upgrade head
```

### 5. 開発サーバーの起動
```bash
# 全サービスを起動
npm run dev

# または個別に起動
npm run dev:frontend  # フロントエンドのみ
npm run dev:backend   # バックエンドのみ
```

## 🏗️ プロジェクト構造

```
ai-family-simulator/
├── frontend/                 # React/Next.js フロントエンド
│   ├── src/
│   │   ├── components/      # Reactコンポーネント
│   │   ├── pages/          # ページコンポーネント
│   │   ├── hooks/          # カスタムフック
│   │   ├── services/       # API通信
│   │   └── utils/          # ユーティリティ
│   ├── public/             # 静的ファイル
│   └── package.json
├── backend/                 # FastAPI バックエンド
│   ├── app/
│   │   ├── api/            # APIエンドポイント
│   │   ├── models/         # データモデル
│   │   ├── services/       # ビジネスロジック
│   │   └── utils/          # ユーティリティ
│   └── requirements.txt
├── agents/                 # AIエージェント
│   ├── hera/              # ヘーラーエージェント
│   ├── family/            # 家族メンバーエージェント
│   └── content_generator/  # コンテンツ生成エージェント
├── shared/                # 共通ライブラリ
├── docs/                  # ドキュメント
├── tests/                 # テスト
└── deployment/          # デプロイメント設定
```

## 🧪 テスト実行

### フロントエンドテスト
```bash
cd frontend
npm test                    # テスト実行
npm run test:coverage      # カバレッジ付きテスト
npm run test:watch         # ウォッチモード
```

### バックエンドテスト
```bash
cd backend
python -m pytest           # テスト実行
python -m pytest --cov    # カバレッジ付きテスト
python -m pytest -v       # 詳細出力
```

### 統合テスト
```bash
# Docker Composeで全サービスを起動してテスト
docker-compose up -d
npm run test:integration
```

## 🔧 開発ツール

### コードフォーマット
```bash
# フロントエンド
cd frontend && npm run format

# バックエンド
cd backend && python -m black app/
```

### リンティング
```bash
# フロントエンド
cd frontend && npm run lint

# バックエンド
cd backend && python -m flake8 app/
```

### 型チェック
```bash
# フロントエンド
cd frontend && npm run type-check

# バックエンド
cd backend && python -m mypy app/
```

## 🐳 Docker開発

### 開発環境の起動
```bash
# 全サービスを起動
docker-compose up -d

# ログを確認
docker-compose logs -f

# 特定のサービスのログ
docker-compose logs -f frontend
```

### データベース操作
```bash
# データベースに接続
docker-compose exec db psql -U postgres -d ai_family_sim

# マイグレーション実行
docker-compose exec backend python -m alembic upgrade head
```

## 📊 監視・デバッグ

### ログ確認
```bash
# アプリケーションログ
docker-compose logs -f backend

# データベースログ
docker-compose logs -f db
```

### メトリクス確認
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

### デバッグ
```bash
# バックエンドデバッグ
docker-compose exec backend python -m pdb app/main.py

# フロントエンドデバッグ
# ブラウザの開発者ツールを使用
```

## 🚀 デプロイメント

### ステージング環境
```bash
# ステージング環境にデプロイ
npm run deploy:staging
```

### 本番環境
```bash
# 本番環境にデプロイ
npm run deploy:production
```

## 📝 コーディング規約

### フロントエンド
- **コンポーネント**: PascalCase (例: `UserProfile`)
- **ファイル名**: kebab-case (例: `user-profile.tsx`)
- **変数名**: camelCase (例: `userName`)
- **定数**: UPPER_SNAKE_CASE (例: `API_BASE_URL`)

### バックエンド
- **クラス名**: PascalCase (例: `UserService`)
- **関数名**: snake_case (例: `get_user_profile`)
- **変数名**: snake_case (例: `user_name`)
- **定数**: UPPER_SNAKE_CASE (例: `DATABASE_URL`)

## 🔍 トラブルシューティング

### よくある問題

#### 1. ポートが既に使用されている
```bash
# 使用中のポートを確認
lsof -i :3000
lsof -i :8000

# プロセスを終了
kill -9 <PID>
```

#### 2. データベース接続エラー
```bash
# データベースの状態確認
docker-compose ps db

# データベースを再起動
docker-compose restart db
```

#### 3. 依存関係のエラー
```bash
# キャッシュをクリアして再インストール
rm -rf node_modules package-lock.json
npm install

# Python依存関係
pip install --upgrade pip
pip install -r requirements.txt
```

## 📚 参考資料

- [React公式ドキュメント](https://reactjs.org/docs)
- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [Docker公式ドキュメント](https://docs.docker.com/)
- [PostgreSQL公式ドキュメント](https://www.postgresql.org/docs/)
