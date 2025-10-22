# Heraエージェント API設計ドキュメント

## 概要
ヘラエージェント（家族愛AI）とフロントエンド間のやりとりを行うためのAPI設計です。セッション管理・情報抽出・履歴/状態同期を軸に、運用や拡張性も考慮した設計となっています。

---

## エージェント基幹処理とAPI設計

- セッション単位でプロフィール・履歴・状態を管理
- ユーザーメッセージ送信でLLMによる自動抽出＆進捗管理
- 履歴やプロフィール、進捗の取得・明示終了などにも対応

---

## APIエンドポイント一覧

### 1. セッション開始
|メソッド|パス|
|:--|:--|
|POST|/api/sessions|

#### リクエスト
```json
{
  "user_id": "string（任意）"
}
```

#### レスポンス
```json
{
  "session_id": "abc-123-xyz",
  "created_at": "2025-10-22T12:01:23",
  "status": "created"
}
```

---

### 2. メッセージ送信・情報抽出
|メソッド|パス|
|:--|:--|
|POST|/api/sessions/{session_id}/messages|

#### リクエスト
```json
{
  "message": "29歳のエンジニアで東京在住です。家族は妻と子供2人です。"
}
```

#### レスポンス
```json
{
  "reply": "素敵なご家族ですね。奥様やお子様について、もっと教えていただけますか？",
  "conversation_history": [
    {"speaker": "user", "message": "29歳のエンジニア ..."},
    {"speaker": "hera", "message": "素敵なご家族ですね ..."}
  ],
  "user_profile": {
    "age": 29, "work_style": "エンジニア", "location": "東京", 
    "family_structure": {"wife": 1, "children": 2}
  },
  "information_progress": {
    "age": true, "gender": false, "income_range": false
  }
}
```
---

### 3. セッション進捗・状態取得
|メソッド|パス|
|:--|:--|
|GET|/api/sessions/{session_id}/status|

#### レスポンス
```json
{
  "user_profile": { ... },
  "information_progress": { ... },
  "conversation_history": [ ... ]
}
```

---

### 4. セッション終了（完了保存）
|メソッド|パス|
|:--|:--|
|POST|/api/sessions/{session_id}/complete|

#### リクエスト
```json
{}
```

#### レスポンス
```json
{
  "message": "収集が完了しました。ありがとうございました。",
  "user_profile": { ... },
  "information_complete": true
}
```

---

## 実装意図・運用ポイント

- **メッセージ送信APIで「LLM抽出結果」「最新プロファイル」「進捗」すべて返す設計**
- **写真アップロード・拡張性：今後必要に応じ追加可**
- **FastAPI/Flask等の非同期実装しやすい構成**
- **セッションごとにADKHeraAgentを内部で管理・切り替え（tmp保存＋メモリ保持想定）**
- **`user_profile`, `information_progress`フィールドで進捗UIも構築しやすい**

---

## 参考：収集情報フィールド（例）
- `age`（年齢）
- `gender`（性別）
- `income_range`（収入範囲）
- `lifestyle`（ライフスタイル）
- `family_structure`（家族構成）
- `interests`（趣味・興味）
- `work_style`（職業）
- `future_career`（将来のキャリア観）
- `location`（居住地）
- `partner_info`（パートナー情報）
- `children_info`（子ども情報）
- ...（追加可）

---

## 備考/今後の拡張
- 写真アップロードAPIを別途追加可能
- 会話履歴取得・ダウンロード、セッション一括管理、削除など
- OpenAPI（Swagger/Redoc）化も容易

---

以上


