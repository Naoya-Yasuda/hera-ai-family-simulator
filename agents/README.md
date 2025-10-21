# AIエージェント 動作確認ガイド

## 📋 概要

このディレクトリには、Google ADKベースのヘーラーエージェント（`adk_hera_agent.py`）が含まれています。このガイドでは、ADK Web UIを使用したエージェントの動作確認方法を説明します。

## 🚀 クイックスタート

### 1. 環境準備

```bash
# プロジェクトルートに移動
cd /path/to/hera-ai-family-simulator

# 仮想環境の作成 一度だけ
python3 -m venv venv

# 仮想環境有効化
source venv/bin/activate  # Windows: venv\Scripts\activate (.\.venv\Scripts\Activate.ps1)

# 依存関係のインストール 一度だけ
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
# 環境変数ファイルをコピー
cp env.example .env

# .envファイルを編集して必要な値を設定
nano .env  # またはお好みのエディタ
```

**必要な環境変数**:
```bash
# Gemini API設定
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-pro
```

### 3. ADK Web UIでヘーラーエージェントを起動

```bash
# プロジェクトルートで実行（重要！）
cd /path/to/hera-ai-family-simulator
source venv/bin/activate
export PYTHONPATH="/path/to/hera-ai-family-simulator"
adk web
```

**アクセス**: `http://localhost:8000`

## ⚠️ 重要な注意事項

### 実行場所
- **必ずプロジェクトルートで実行**: `cd /path/to/hera-ai-family-simulator`
- **agentsディレクトリ内では実行しない**: `cd agents` ❌

### 必要なファイル構造
```
hera-ai-family-simulator/          # ← ここでadk webを実行
├── agents/
│   ├── __init__.py               # ← 必要
│   ├── root_agent.py             # ← 必要
│   └── hera/
│       └── adk_hera_agent.py
├── .env                          # ← 必要
└── requirements.txt
```

## 🧪 動作確認手順

### ADK Web UI での確認

1. **ブラウザで `http://localhost:8000` にアクセス**
2. **ヘーラーエージェントとの対話を開始**
3. **以下の情報を自然な対話で収集**：
   - 年齢
   - 収入範囲
   - ライフスタイル
   - 家族構成
   - パートナー情報
   - 子ども情報（いる場合）
   - 趣味・興味
   - 仕事スタイル
   - 居住地

### 動作確認のポイント

- **自然な対話**: 温かみのある口調での応答
- **文脈理解**: 会話の流れを理解した応答
- **情報抽出**: 対話内容からの自動情報抽出

## 📊 ヘーラーエージェントの機能

### 収集される情報

- **年齢**: ユーザーの年齢
- **収入範囲**: 収入の大まかな範囲
- **ライフスタイル**: 生活スタイルや趣味
- **家族構成**: 現在の家族構成
- **パートナー情報**: パートナーの詳細
- **子ども情報**: 子どもの情報（いる場合）
- **趣味・興味**: 個人的な興味や趣味
- **仕事スタイル**: 職業や働き方
- **居住地**: 住んでいる地域

## 🐛 トラブルシューティング

### よくある問題と解決方法

#### 1. Gemini API キーエラー
```bash
# .envファイルでGEMINI_API_KEYを確認
echo $GEMINI_API_KEY

# 正しいAPIキーを設定
export GEMINI_API_KEY="your-actual-api-key"
```

#### 2. ポートが既に使用されている
```bash
# 使用中のポートを確認
lsof -i :8000

# プロセスを終了
kill -9 <PID>

```

#### 3. 依存関係のエラー
```bash
# 仮想環境を再作成
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. ADK Web UIが起動しない
```bash
# ADKが正しくインストールされているか確認
pip list | grep google-adk

# 再インストール
pip uninstall google-adk
pip install google-adk
```

#### 5. root_agentが見つからないエラー
```bash
# エラー: "No root_agent found for 'agents'"

# 解決方法1: プロジェクトルートで実行
cd /path/to/hera-ai-family-simulator  # ← プロジェクトルート
adk web

# 解決方法2: 必要なファイルを作成
touch agents/__init__.py
touch agents/root_agent.py

# 解決方法3: ディレクトリ構造を確認
ls -la agents/
# 以下のファイルが必要:
# __init__.py
# root_agent.py
# hera/adk_hera_agent.py
```

## 📚 参考資料

### Google ADK ドキュメント
- [Google ADK公式ドキュメント](https://developers.google.com/adk)
- [ADK エージェント開発ガイド](https://developers.google.com/adk/agents)

### Google Cloud サービス
- [Google Cloud AI Platform](https://cloud.google.com/ai-platform)

### Gemini API
- [Gemini API ドキュメント](https://ai.google.dev/docs)
- [Gemini API クイックスタート](https://ai.google.dev/docs/quickstart)

## 🚀 次のステップ

1. **エージェントのカスタマイズ**: 人格設定や指示の調整
2. **ツールの追加**: カスタムツールの実装
3. **統合テスト**: フロントエンドとの統合テスト

---

**注意**: このガイドは開発環境での動作確認を目的としています。本番環境での使用前に、セキュリティ設定とパフォーマンステストを実施してください。
