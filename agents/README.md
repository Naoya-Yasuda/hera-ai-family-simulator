# AIエージェント 動作確認ガイド

## 📋 概要

このディレクトリには、Google ADKベースのヘーラーエージェント（`adk_hera_agent.py`）が含まれています。このガイドでは、ADK Web UIを使用したエージェントの動作確認方法を説明します。

## 🚀 クイックスタート

### 1. 環境準備

```bash
# プロジェクトルートに移動
cd /path/to/hera-ai-family-simulator

# 仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
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
# Google Cloud設定
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=asia-northeast1
GEMINI_API_KEY=your-gemini-api-key

# Google Cloud認証（オプション）
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
```

### 3. ADK Web UIでヘーラーエージェントを起動

```bash
# ADK Web UIを起動
adk web
```

**アクセス**: `http://localhost:8000`

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

- **音声入力**: マイクボタンで音声入力が可能
- **音声出力**: ヘーラーエージェントの音声応答
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

#### 1. Google Cloud認証エラー
```bash
# サービスアカウントキーを設定
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"

# または、gcloud CLIで認証
gcloud auth application-default login
```

#### 2. Gemini API キーエラー
```bash
# .envファイルでGEMINI_API_KEYを確認
echo $GEMINI_API_KEY

# 正しいAPIキーを設定
export GEMINI_API_KEY="your-actual-api-key"
```

#### 3. ポートが既に使用されている
```bash
# 使用中のポートを確認
lsof -i :8000

# プロセスを終了
kill -9 <PID>

# または別のポートを使用
uvicorn app:app --port 8001
```

#### 4. 依存関係のエラー
```bash
# 仮想環境を再作成
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 5. ADK Web UIが起動しない
```bash
# ADKが正しくインストールされているか確認
pip list | grep google-adk

# 再インストール
pip uninstall google-adk
pip install google-adk
```

## 📚 参考資料

### Google ADK ドキュメント
- [Google ADK公式ドキュメント](https://developers.google.com/adk)
- [ADK エージェント開発ガイド](https://developers.google.com/adk/agents)

### Google Cloud サービス
- [Google Cloud AI Platform](https://cloud.google.com/ai-platform)
- [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text)
- [Google Cloud Text-to-Speech](https://cloud.google.com/text-to-speech)

### Gemini API
- [Gemini API ドキュメント](https://ai.google.dev/docs)
- [Gemini API クイックスタート](https://ai.google.dev/docs/quickstart)

## 🚀 次のステップ

1. **エージェントのカスタマイズ**: 人格設定や指示の調整
2. **ツールの追加**: カスタムツールの実装
3. **音声品質の向上**: 音声認識・合成の最適化
4. **統合テスト**: フロントエンドとの統合テスト

---

**注意**: このガイドは開発環境での動作確認を目的としています。本番環境での使用前に、セキュリティ設定とパフォーマンステストを実施してください。
