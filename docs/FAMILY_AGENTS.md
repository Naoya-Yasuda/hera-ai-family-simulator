# 家族ペルソナエージェント設計書

## 🏠 家族メンバーエージェント概要

ヘーラーエージェントで収集したユーザー情報を基に、個性的な家族メンバーのペルソナエージェントを生成し、同時対話を実現します。

## 👥 家族メンバーエージェント一覧

### 1. 夫/妻エージェント

#### 基本情報
- **役割**: ユーザーのパートナー
- **生成基準**: ユーザーの年齢、収入、ライフスタイルに基づく
- **性格**: ユーザーと相性の良い性格設定

#### ペルソナ設定例
```json
{
  "name": "美咲",
  "age": 28,
  "personality": {
    "traits": ["優しい", "積極的", "家族思い"],
    "interests": ["料理", "読書", "映画鑑賞"],
    "values": ["家族の絆", "健康", "成長"]
  },
  "speaking_style": {
    "tone": "温かみのある",
    "vocabulary": "親しみやすい",
    "emotions": ["愛情深い", "支え合い"]
  }
}
```

### 2. 子どもエージェント

#### 年齢別設定

##### 幼児（3-6歳）
```json
{
  "name": "たろう",
  "age": 5,
  "personality": {
    "traits": ["好奇心旺盛", "元気", "素直"],
    "interests": ["おもちゃ", "絵本", "公園遊び"],
    "development_stage": "言語発達期"
  },
  "speaking_style": {
    "tone": "可愛らしい",
    "vocabulary": "簡単な言葉",
    "emotions": ["純真", "喜び", "驚き"]
  }
}
```

##### 小学生（7-12歳）
```json
{
  "name": "さくら",
  "age": 9,
  "personality": {
    "traits": ["活発", "勉強好き", "友達思い"],
    "interests": ["スポーツ", "読書", "ゲーム"],
    "development_stage": "社会性発達期"
  },
  "speaking_style": {
    "tone": "元気いっぱい",
    "vocabulary": "年齢相応",
    "emotions": ["興奮", "好奇心", "達成感"]
  }
}
```

##### 中学生（13-15歳）
```json
{
  "name": "ゆうと",
  "age": 14,
  "personality": {
    "traits": ["思春期", "自立心", "友達重視"],
    "interests": ["音楽", "スポーツ", "SNS"],
    "development_stage": "アイデンティティ形成期"
  },
  "speaking_style": {
    "tone": "少し生意気",
    "vocabulary": "若者言葉",
    "emotions": ["反抗期", "友情", "成長"]
  }
}
```

### 3. 祖父母エージェント

#### 祖父エージェント
```json
{
  "name": "じいじ",
  "age": 65,
  "personality": {
    "traits": ["穏やか", "経験豊富", "家族思い"],
    "interests": ["園芸", "将棋", "散歩"],
    "values": ["伝統", "家族の絆", "知恵"]
  },
  "speaking_style": {
    "tone": "落ち着いた",
    "vocabulary": "丁寧語",
    "emotions": ["慈愛", "安心感", "誇り"]
  }
}
```

#### 祖母エージェント
```json
{
  "name": "ばあば",
  "age": 62,
  "personality": {
    "traits": ["優しい", "料理好き", "孫思い"],
    "interests": ["料理", "裁縫", "お花"],
    "values": ["家族の健康", "伝統", "愛情"]
  },
  "speaking_style": {
    "tone": "温かみのある",
    "vocabulary": "優しい言葉",
    "emotions": ["愛情", "心配", "喜び"]
  }
}
```

## 🎭 ペルソナ生成アルゴリズム

### 1. ユーザー情報分析
```python
def analyze_user_profile(user_data):
    """
    ユーザー情報を分析して家族構成を決定
    """
    family_structure = {
        "partner": determine_partner_persona(user_data),
        "children": generate_children_ages(user_data),
        "grandparents": determine_grandparents_presence(user_data)
    }
    return family_structure
```

### 2. 性格生成
```python
def generate_personality_traits(base_traits, user_preferences):
    """
    基本性格にユーザーの好みを反映
    """
    personality = {
        "core_traits": select_core_traits(base_traits),
        "interests": match_interests(user_preferences),
        "values": align_values(user_preferences),
        "speaking_style": generate_speaking_style(age, personality)
    }
    return personality
```

### 3. 対話スタイル生成
```python
def generate_speaking_style(age, personality, role):
    """
    年齢、性格、役割に基づいて対話スタイルを生成
    """
    style = {
        "tone": determine_tone(age, personality),
        "vocabulary": select_vocabulary(age, role),
        "emotions": generate_emotion_range(personality),
        "response_patterns": create_response_patterns(role)
    }
    return style
```

## 💬 同時対話システム

### 1. 対話管理
```python
class FamilyChatManager:
    def __init__(self, family_members):
        self.members = family_members
        self.conversation_history = []
        self.active_speakers = []

    def process_message(self, user_message):
        """
        ユーザーメッセージを処理し、適切な家族メンバーが応答
        """
        responses = []
        for member in self.members:
            if member.should_respond(user_message):
                response = member.generate_response(user_message)
                responses.append({
                    "member": member.name,
                    "response": response,
                    "emotion": member.current_emotion
                })
        return responses
```

### 2. 感情管理
```python
class EmotionManager:
    def __init__(self):
        self.emotion_states = {}
        self.emotion_transitions = {}

    def update_emotion(self, member, context, conversation):
        """
        会話の文脈に基づいて感情状態を更新
        """
        new_emotion = self.calculate_emotion(member, context, conversation)
        self.emotion_states[member.name] = new_emotion
        return new_emotion
```

### 3. 幸せなひとときの定義
```python
def define_happy_moments(conversation_context):
    """
    対話を通じて家族の幸せな瞬間を具体的に描写
    """
    happy_moments = {
        "activities": extract_activities(conversation_context),
        "emotions": extract_emotions(conversation_context),
        "interactions": extract_interactions(conversation_context),
        "memories": create_memory_scenarios(conversation_context)
    }
    return happy_moments
```

## 🎨 視覚的表現

### 1. アバター表示
- **リアルタイム表情**: 感情に応じた表情変化
- **ジェスチャー**: 会話内容に応じた動作
- **服装**: 年齢と性格に応じた服装設定

### 2. 対話UI
- **吹き出し**: 各メンバーの発言を視覚的に区別
- **感情アイコン**: 現在の感情状態を表示
- **会話フロー**: 自然な会話の流れを表現

### 3. 幸せな瞬間の可視化
- **シーン描写**: 対話で生まれた幸せな瞬間をイラスト化
- **感情マップ**: 家族全体の感情状態を可視化
- **記憶アルバム**: 対話で生まれた思い出を保存

## 🔄 対話フロー例

### シナリオ: 家族で旅行の計画
```
ユーザー: "今度の休みに家族で旅行に行きたいな"

たろう(5歳): "わーい！海に行きたい！泳ぎたい！"
さくら(9歳): "私も海がいい！でも山も行ってみたいな"
美咲(妻): "海も山も素敵ね。みんなで楽しめる場所を探しましょう"
じいじ(65歳): "温泉もいいかもしれないな。家族みんなでゆっくりできる"
ばあば(62歳): "そうね、みんなで美味しいものを食べに行きましょう"
```

### 感情の変化
- **たろう**: 興奮 → 期待
- **さくら**: 好奇心 → ワクワク
- **美咲**: 愛情 → 計画への意欲
- **じいじ**: 穏やか → 家族への愛情
- **ばあば**: 優しさ → 家族への思い

## 📊 データ保存

### 1. 一時ファイル構造
```
/tmp/user_sessions/
├── {session_id}/
│   ├── user_profile.json
│   ├── family_members.json
│   ├── conversation_history.json
│   ├── happy_moments.json
│   └── generated_content/
│       ├── stories/
│       ├── images/
│       └── videos/
```

### 2. セッション管理
```python
class SessionManager:
    def __init__(self, session_id):
        self.session_id = session_id
        self.temp_dir = f"/tmp/user_sessions/{session_id}"
        self.user_profile = None
        self.family_members = []
        self.conversation_history = []

    def save_user_profile(self, profile):
        """ユーザープロファイルを一時保存"""
        with open(f"{self.temp_dir}/user_profile.json", "w") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

    def save_family_members(self, members):
        """家族メンバー情報を一時保存"""
        with open(f"{self.temp_dir}/family_members.json", "w") as f:
            json.dump(members, f, ensure_ascii=False, indent=2)
```

## 🎯 成功指標

### 1. 対話品質
- **自然さ**: 人間らしい対話の実現
- **一貫性**: キャラクターの性格の一貫性
- **感情表現**: 豊かな感情表現

### 2. ユーザー体験
- **没入感**: 家族との対話への没入感
- **感情移入**: 家族メンバーへの感情移入
- **満足度**: 対話体験の満足度

### 3. 技術指標
- **応答時間**: リアルタイム対話の応答時間
- **同時接続**: 同時対話の安定性
- **データ保存**: 一時ファイルの適切な管理
