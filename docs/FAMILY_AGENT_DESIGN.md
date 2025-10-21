# 家族エージェントシステム設計書

## 概要

家族エージェントシステムは、Google ADK（Agent Development Kit）を使用して未来の家族との対話を実現するシステムです。ユーザーのプロファイル情報から家族メンバーのペルソナを生成し、自然な会話を通じて旅行計画を立て、最終的にストーリーと手紙を生成します。

## システムアーキテクチャ

### コンポーネント構成図

```
┌─────────────────────────────────────────────────────────────┐
│                    FamilySessionAgent                        │
│  (セッション管理・進行役)                                     │
│                                                               │
│  - before_agent_callback: プロファイル読み込み              │
│  - run: 会話実行                                            │
│  - after_agent_callback: ストーリー・手紙生成               │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
┌───────▼────────┐            ┌────────▼────────┐
│ FamilyToolSet  │            │   Generators     │
│                │            │                  │
│ - Partner Tool │            │ - StoryGenerator │
│ - Child Tool 1 │            │ - LetterGenerator│
│ - Child Tool 2 │            └──────────────────┘
└────────┬───────┘
         │
┌────────▼──────────┐
│ PersonaFactory    │
│                   │
│ - build_partner() │
│ - build_children()│
└────────┬──────────┘
         │
┌────────▼────────────────┐
│ PersonalityCalculator   │
│ (ビッグファイブ理論)    │
└─────────────────────────┘
```

## 主要コンポーネント詳細

### 1. FamilySessionAgent

**ファイル:** [family/entrypoints.py](../family/entrypoints.py)

**役割:**
- セッション全体の管理
- 家族ツールの調整
- 会話終了時の後処理

**ライフサイクル:**

```python
1. __init__
   ↓
2. before_agent_callback (_ensure_profile)
   - プロファイル読み込み
   - FamilyToolSetの初期化
   - ツールとインストラクションの適用
   ↓
3. run (会話実行)
   - ユーザー入力を受け取る
   - 適切な家族ツールを呼び出す
   - 会話ログを蓄積
   ↓
4. after_agent_callback (_post_process)
   - 旅行情報の確認
   - ストーリー生成
   - 手紙生成
   - JSONファイル保存
   - イベント返却
```

**状態管理:**

```python
callback_context.state = {
    "profile": {...},                    # ユーザープロファイル
    "family_trip_info": {                # 旅行情報
        "destination": "行き先",
        "activities": ["..."]
    },
    "family_conversation_log": [         # 会話ログ
        {"speaker": "...", "message": "..."}
    ]
}
```

### 2. FamilyToolSet

**ファイル:** [family/tooling.py](../family/tooling.py)

**役割:**
- 家族メンバーツールの生成と管理
- PersonaFactoryとの連携

**構造:**

```python
FamilyToolSet
  ├─ factory: PersonaFactory
  └─ tools: List[FamilyTool]
       ├─ FamilyTool(persona=Partner, index=0, kind="partner")
       ├─ FamilyTool(persona=Child1, index=1, kind="child")
       └─ FamilyTool(persona=Child2, index=2, kind="child")
```

**主要メソッド:**

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `build_tools()` | ADK用のツールリストを生成 | `List[FunctionTool]` |
| `tool_names()` | ツール名のリストを返す | `List[str]` |
| `get_personas()` | 全ペルソナを返す | `List[Persona]` |

### 3. FamilyTool

**ファイル:** [family/tooling.py](../family/tooling.py)

**役割:**
- 個別の家族メンバーとの対話
- Gemini APIによる応答生成
- 旅行情報の抽出と保存

**処理フロー:**

```python
call_agent(input_text)
  ↓
1. プロンプト生成 (_build_prompt)
   - ペルソナ情報を埋め込み
   - ルールを明記
   ↓
2. Gemini API呼び出し (model.generate_content)
   ↓
3. JSON応答のパース
   {
     "message": "発言内容",
     "destination": "行き先",
     "activities": ["アクティビティ"]
   }
   ↓
4. 状態への保存
   - family_trip_info に destination/activities を追加
   - family_conversation_log に発言を追加
   ↓
5. 応答を返す
```

### 4. PersonaFactory

**ファイル:** [family/persona_factory.py](../family/persona_factory.py)

**役割:**
- ユーザープロファイルからペルソナを生成
- パートナーと子供のペルソナ作成

**ペルソナ生成ロジック:**

#### パートナー生成 (`build_partner`)

```python
1. relationship_status に応じて分岐
   - "married"/"partnered" → current_partner を使用
   - "single" → ideal_partner を使用
   ↓
2. personality_traits があれば
   → ビッグファイブから日本語特性を生成
   なければ
   → デフォルト特性を使用
   ↓
3. Personaオブジェクトを生成
```

#### 子供生成 (`build_children`)

```python
1. 親の性格特性を取得
   - user_personality_traits
   - partner の personality_traits
   ↓
2. 両方揃っていれば PersonalityCalculator を使用
   ↓
3. 各子供について
   - calculate_child_traits() で性格計算
   - generate_personality_description() で描写生成
   - Personaオブジェクトを生成
```

### 5. PersonalityCalculator

**ファイル:** [family/personality_calculator.py](../family/personality_calculator.py)

**役割:**
- ビッグファイブ理論に基づく性格計算
- 親の性格から子供の性格を遺伝的に推定

**計算式:**

```python
# 基本的な遺伝計算（平均 + ランダム変動）
child_trait = (parent1_trait + parent2_trait) / 2 + random_variation

# 出生順位による調整
if birth_order == 0:  # 第1子
    conscientiousness += 0.1  # よりしっかり者
elif birth_order == 1:  # 第2子
    agreeableness += 0.1      # より協調的
else:  # 第3子以降
    openness += 0.1           # より開放的
```

**ビッグファイブ特性:**

| 特性 | 英名 | 説明 |
|-----|------|------|
| 開放性 | Openness | 新しい経験への開放度 |
| 誠実性 | Conscientiousness | 目標志向性、自己統制 |
| 外向性 | Extraversion | 社交性、活発さ |
| 協調性 | Agreeableness | 他者への配慮、優しさ |
| 神経症傾向 | Neuroticism | 不安や感情の不安定性 |

### 6. StoryGenerator

**ファイル:** [family/story_generator.py](../family/story_generator.py)

**役割:**
- 会話ログから物語的なストーリーを生成
- 3部構成の感動的な物語

**生成プロセス:**

```python
generate_story(conversation_log, trip_info, personas)
  ↓
1. バリデーション
   - destination の存在確認
   - activities の存在確認
   ↓
2. データ整形
   - 家族構成のテキスト化
   - 会話ログのテキスト化
   ↓
3. プロンプト生成
   - テンプレートに埋め込み
   - 3部構成の指示
   ↓
4. Gemini API 呼び出し
   ↓
5. ストーリーを返却（800-1200文字）
```

**ストーリー構成:**

| パート | 内容 | 分量 |
|-------|------|------|
| 導入 | 家族が旅行について話し合う様子 | 2-3段落 |
| 本編 | 旅行先での具体的なシーン描写 | 3-4段落 |
| 結び | 家族の絆や期待感の表現 | 1-2段落 |

### 7. LetterGenerator

**ファイル:** [family/letter_generator.py](../family/letter_generator.py)

**役割:**
- ストーリーを基に手紙形式のメッセージを生成
- 未来の家族からの温かいメッセージ

**生成プロセス:**

```python
generate_letter(story, trip_info, family_members, user_name)
  ↓
1. バリデーション
   - story の存在確認
   - destination/activities の確認
   - family_members の確認
   ↓
2. データ整形
   - 家族構成のテキスト化
   - 家族名のリスト化
   - 日付生成
   ↓
3. プロンプト生成
   - テンプレートに埋め込み
   - 手紙構成の指示
   ↓
4. Gemini API 呼び出し
   ↓
5. 手紙を返却（600-900文字）
```

**手紙構成:**

| パート | 内容 | 分量 |
|-------|------|------|
| 宛名 | 「未来の[ユーザー名]へ」 | 1行 |
| 前書き | 感謝の気持ち | 1-2段落 |
| 本文 | 旅行への期待と想い | 3-4段落 |
| 結び | 現在のあなたへのエール | 1-2段落 |
| 署名 | 日付と家族メンバーの名前 | 3-4行 |

## データフロー

### 全体フロー

```
[ユーザー] "週末どこ行きたい？"
    ↓
[FamilySessionAgent]
    ↓
[FamilyToolSet] 適切なツールを選択
    ↓
[FamilyTool: パートナー]
    ↓ call_agent
[Gemini API] プロンプト → JSON応答
    ↓
[状態管理] family_trip_info, family_conversation_log に保存
    ↓
[FamilySessionAgent] 応答を返す
    ↓
[ユーザー] さらに会話...
    ↓
... (繰り返し) ...
    ↓
[会話終了]
    ↓
[_post_process]
    ├→ [StoryGenerator] ストーリー生成
    ├→ [LetterGenerator] 手紙生成
    └→ [ファイル保存] family_plan.json
    ↓
[ユーザーにストーリーを返信]
```

### 状態遷移図

```
[初期状態]
    ↓ before_agent_callback
[プロファイル読み込み完了]
    ↓ ツール初期化
[会話可能状態]
    ↓ run (繰り返し)
[会話中（ログ蓄積）]
    ↓ 旅行情報収集完了
[生成準備完了]
    ↓ after_agent_callback
[ストーリー生成中]
    ↓
[手紙生成中]
    ↓
[保存完了・終了]
```

## エラーハンドリング

### エラー処理戦略

| コンポーネント | エラーケース | 対処方法 |
|--------------|-------------|---------|
| StoryGenerator | API エラー | フォールバック簡易サマリー |
| LetterGenerator | API エラー | 空文字列（ストーリーのみ返却） |
| PersonaFactory | 性格特性不足 | デフォルト値を使用 |
| FamilyTool | JSON パースエラー | テキストのみ使用 |

### ロギング

全てのコンポーネントは Python logging を使用：

```python
import logging
logger = logging.getLogger(__name__)

# 使用例
logger.info("処理開始")
logger.warning("注意が必要")
logger.error("エラー発生", exc_info=True)
```

## パフォーマンス考慮事項

### API 呼び出し最適化

| 処理 | API 呼び出し回数 | 所要時間（目安） |
|-----|----------------|-----------------|
| 家族メンバー1人の応答 | 1回 | 2-5秒 |
| ストーリー生成 | 1回 | 5-10秒 |
| 手紙生成 | 1回 | 5-10秒 |
| 性格描写生成（子供1人） | 1回 | 2-5秒 |

**合計（3人家族、5ターン会話の場合）:**
- 会話中: 10回（20-50秒）
- 生成: 2回（10-20秒）
- **総計: 30-70秒**

### 非同期処理

全ての生成処理は `async/await` を使用して非同期実行：

```python
# 非同期実行の例
async def _post_process(self, callback_context):
    # ストーリー生成（非同期）
    story = await story_generator.generate_story(...)

    # 手紙生成（非同期）
    letter = await letter_generator.generate_letter(...)
```

## セキュリティ考慮事項

### データ保護

1. **個人情報の最小化**
   - 必要最小限の情報のみ収集
   - セッションIDでファイルを分離

2. **ファイルアクセス制御**
   - セッションディレクトリはユーザーごとに分離
   - 適切なファイルパーミッション設定

3. **API キー管理**
   - 環境変数で管理
   - コードにハードコードしない

## 拡張性

### 今後の拡張可能性

1. **マルチモーダル対応**
   - 画像生成との統合
   - 音声出力の追加

2. **カスタマイズ機能**
   - ストーリーのテンプレート選択
   - 手紙のフォーマット変更

3. **多言語対応**
   - プロンプトの多言語化
   - 出力言語の選択

4. **パーソナライゼーション強化**
   - ユーザーの過去の会話履歴を活用
   - より詳細な性格モデル

## 関連ドキュメント

- [family/README.md](../family/README.md) - モジュール詳細
- [STORY_GENERATION.md](STORY_GENERATION.md) - ストーリー生成仕様
- [LETTER_GENERATION.md](LETTER_GENERATION.md) - 手紙生成仕様
- [ARCHITECTURE.md](ARCHITECTURE.md) - システム全体アーキテクチャ
- [GOOGLE_ADK_ARCHITECTURE.md](GOOGLE_ADK_ARCHITECTURE.md) - ADK 詳細
