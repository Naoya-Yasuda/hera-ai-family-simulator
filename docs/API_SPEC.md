# API仕様書

## 🔌 エンドポイント一覧

### 認証関連
```
POST /api/auth/login
POST /api/auth/logout
POST /api/auth/refresh
```

### ユーザー情報管理
```
GET    /api/users/profile
PUT    /api/users/profile
POST   /api/users/upload-photo
DELETE /api/users/photo
```

### AIエージェント対話
```
POST   /api/chat/start-hera-session
POST   /api/chat/hera-message
POST   /api/chat/start-family-session
POST   /api/chat/family-message
GET    /api/chat/session/{session_id}
DELETE /api/chat/session/{session_id}
```

### コンテンツ生成
```
POST   /api/content/generate-story
POST   /api/content/generate-image
POST   /api/content/generate-letter
POST   /api/content/generate-video
```

### メディア管理
```
GET    /api/media/{media_id}
POST   /api/media/upload
DELETE /api/media/{media_id}
```

## 📝 詳細仕様

### 1. ユーザー情報登録
```json
POST /api/users/profile
{
  "age": 28,
  "income_range": "500-800万円",
  "lifestyle": {
    "location": "都市部",
    "hobbies": ["読書", "映画鑑賞"],
    "work_style": "リモートワーク"
  },
  "family_structure": {
    "partner": true,
    "children": 0,
    "pets": false
  }
}
```

### 2. ヘーラーエージェントセッション開始
```json
POST /api/chat/start-hera-session
{
  "user_id": "user_123",
  "session_type": "information_gathering"
}
```

### 3. ヘーラーエージェントメッセージ送信
```json
POST /api/chat/hera-message
{
  "session_id": "session_456",
  "message": "こんにちは、家族について教えてください",
  "message_type": "text",
  "audio_data": "base64_encoded_audio" // 音声の場合
}
```

### 4. 家族チャットセッション開始
```json
POST /api/chat/start-family-session
{
  "session_id": "session_456",
  "user_profile": {
    "age": 28,
    "income_range": "500-800万円",
    "lifestyle": {...},
    "family_structure": {...}
  }
}
```

### 5. 家族チャットメッセージ送信
```json
POST /api/chat/family-message
{
  "session_id": "session_456",
  "message": "家族で旅行に行きたいです",
  "message_type": "text",
  "audio_data": "base64_encoded_audio" // 音声の場合
}
```

### 4. ストーリー生成
```json
POST /api/content/generate-story
{
  "session_id": "session_456",
  "story_type": "daily_life",
  "characters": ["夫", "妻", "子供"],
  "setting": "家庭",
  "mood": "温かい"
}
```

### 5. 画像生成
```json
POST /api/content/generate-image
{
  "prompt": "家族で海辺を散歩している様子",
  "style": "realistic",
  "characters": ["夫", "妻", "子供"],
  "setting": "海辺"
}
```

## 🔄 WebSocket イベント

### クライアント → サーバー
```json
{
  "type": "message",
  "data": {
    "session_id": "session_456",
    "message": "こんにちは",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### サーバー → クライアント
```json
{
  "type": "hera_response",
  "data": {
    "session_id": "session_456",
    "agent": "hera",
    "message": "こんにちは！家族について教えてください",
    "timestamp": "2024-01-01T10:00:01Z"
  }
}
```

```json
{
  "type": "family_responses",
  "data": {
    "session_id": "session_456",
    "responses": [
      {
        "member": "美咲",
        "message": "家族で旅行に行きましょう！",
        "emotion": "excited",
        "timestamp": "2024-01-01T10:00:01Z"
      },
      {
        "member": "たろう",
        "message": "わーい！海に行きたい！",
        "emotion": "happy",
        "timestamp": "2024-01-01T10:00:02Z"
      }
    ]
  }
}
```

```json
{
  "type": "content_generated",
  "data": {
    "content_type": "story",
    "content_id": "story_789",
    "preview": "家族の日常ストーリーが生成されました...",
    "timestamp": "2024-01-01T10:00:05Z"
  }
}
```

## 🛡️ エラーハンドリング

### エラーレスポンス形式
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "必須フィールドが不足しています",
    "details": {
      "field": "age",
      "reason": "required"
    },
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### エラーコード一覧
- `VALIDATION_ERROR`: 入力値検証エラー
- `AUTHENTICATION_ERROR`: 認証エラー
- `AUTHORIZATION_ERROR`: 権限エラー
- `RATE_LIMIT_ERROR`: レート制限エラー
- `AI_SERVICE_ERROR`: AIサービスエラー
- `MEDIA_ERROR`: メディア処理エラー
- `INTERNAL_ERROR`: 内部サーバーエラー
