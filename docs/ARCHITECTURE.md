# アーキテクチャ設計書

## 🏗️ システム全体構成

```
ai-family-simulator/
├── frontend/                 # フロントエンド（React/Next.js）
├── backend/                  # バックエンド（FastAPI）
├── agents/                   # AIエージェント群
├── shared/                    # 共通ライブラリ
├── docs/                      # ドキュメント
├── tests/                     # テスト
├── deployment/               # デプロイメント設定
└── scripts/                  # ユーティリティスクリプト
```

## 🎯 コンポーネント設計

### フロントエンド（frontend/）
```
frontend/
├── src/
│   ├── components/           # Reactコンポーネント
│   │   ├── ui/              # 基本UIコンポーネント
│   │   ├── forms/           # フォームコンポーネント
│   │   ├── chat/            # チャット関連コンポーネント
│   │   └── media/           # メディア表示コンポーネント
│   ├── pages/               # ページコンポーネント
│   ├── hooks/               # カスタムフック
│   ├── services/            # API通信サービス
│   ├── utils/               # ユーティリティ関数
│   └── types/               # TypeScript型定義
├── public/                  # 静的ファイル
└── package.json
```

### バックエンド（backend/）
```
backend/
├── app/
│   ├── api/                 # APIエンドポイント
│   ├── models/              # データモデル
│   ├── services/            # ビジネスロジック
│   ├── utils/               # ユーティリティ
│   └── config/              # 設定ファイル
├── tests/                   # バックエンドテスト
└── requirements.txt
```

### AIエージェント（agents/）
```
agents/
├── hera/                    # ヘーラーエージェント
├── family/                  # 家族メンバーエージェント
├── content_generator/       # コンテンツ生成エージェント
└── shared/                  # エージェント共通機能
```

## 🔄 データフロー

1. **ユーザー入力** → フロントエンド
2. **音声認識** → Web Speech API
3. **エージェント対話** → バックエンド → AIエージェント
4. **コンテンツ生成** → AI API（GPT, DALL-E等）
5. **リアルタイム表示** → WebSocket/SSE
6. **メディア配信** → CDN

## 🛡️ セキュリティ設計

- **認証**: JWT トークンベース
- **データ暗号化**: ユーザー情報の暗号化保存
- **API セキュリティ**: Rate Limiting, CORS設定
- **プライバシー**: 個人情報の最小化と匿名化
