# データベース設計書

## 🗄️ データベース概要

- **データベース**: PostgreSQL
- **ORM**: SQLAlchemy (Python) / Prisma (TypeScript)
- **キャッシュ**: Redis
- **ファイルストレージ**: AWS S3 / Google Cloud Storage

## 📊 テーブル設計

### 1. ユーザー管理

#### users テーブル
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);
```

#### user_profiles テーブル
```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    age INTEGER,
    income_range VARCHAR(50),
    lifestyle JSONB,
    family_structure JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### user_photos テーブル
```sql
CREATE TABLE user_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    photo_type VARCHAR(20) NOT NULL, -- 'self', 'partner'
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. セッション管理

#### chat_sessions テーブル
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL, -- 'hera', 'family_member'
    context JSONB,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'completed', 'cancelled'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### chat_messages テーブル
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL, -- 'user', 'agent'
    message_type VARCHAR(20) NOT NULL, -- 'text', 'audio', 'image'
    content TEXT,
    audio_file_path VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. コンテンツ管理

#### generated_content テーブル
```sql
CREATE TABLE generated_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL, -- 'story', 'image', 'letter', 'video'
    title VARCHAR(255),
    content_data JSONB,
    file_path VARCHAR(500),
    file_size INTEGER,
    generation_prompt TEXT,
    ai_model VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### content_templates テーブル
```sql
CREATE TABLE content_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_type VARCHAR(50) NOT NULL, -- 'letter', 'story', 'image'
    template_name VARCHAR(255) NOT NULL,
    template_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. メディア管理

#### media_files テーブル
```sql
CREATE TABLE media_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content_id UUID REFERENCES generated_content(id) ON DELETE CASCADE,
    file_type VARCHAR(50) NOT NULL, -- 'image', 'video', 'audio'
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    duration INTEGER, -- for video/audio files
    resolution VARCHAR(20), -- for image/video files
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔗 リレーションシップ

### 主要な関係
1. **users** → **user_profiles** (1:1)
2. **users** → **user_photos** (1:N)
3. **users** → **chat_sessions** (1:N)
4. **chat_sessions** → **chat_messages** (1:N)
5. **users** → **generated_content** (1:N)
6. **chat_sessions** → **generated_content** (1:N)
7. **generated_content** → **media_files** (1:N)

## 📈 インデックス設計

### パフォーマンス向上のためのインデックス
```sql
-- ユーザー検索用
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);

-- セッション検索用
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_status ON chat_sessions(status);
CREATE INDEX idx_chat_sessions_created_at ON chat_sessions(created_at);

-- メッセージ検索用
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);

-- コンテンツ検索用
CREATE INDEX idx_generated_content_user_id ON generated_content(user_id);
CREATE INDEX idx_generated_content_type ON generated_content(content_type);
CREATE INDEX idx_generated_content_created_at ON generated_content(created_at);
```

## 🔒 セキュリティ考慮事項

### データ暗号化
- **個人情報**: 年齢、収入範囲等の機密情報は暗号化
- **音声データ**: 音声ファイルは暗号化して保存
- **画像データ**: 顔写真等の個人画像は暗号化

### データ保持ポリシー
- **セッションデータ**: 30日間保持
- **生成コンテンツ**: ユーザーが削除するまで保持
- **ログデータ**: 90日間保持

### プライバシー保護
- **匿名化**: 分析用データは個人を特定できない形で保存
- **データ削除**: ユーザー削除時は関連データも完全削除
- **アクセス制御**: ユーザーは自分のデータのみアクセス可能
