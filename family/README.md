# Family Module

## 概要

家族エージェントシステムの実装モジュールです。Google ADK（Agent Development Kit）を使用して、未来の家族メンバーとの対話、ストーリー生成、手紙生成を実現します。

## ディレクトリ構造

```
family/
├── __init__.py                    # モジュール初期化
├── entrypoints.py                 # セッション管理・エントリーポイント
├── tooling.py                     # 家族ツール実装
├── family_agent.py                # 基本エージェントクラス（レガシー）
├── persona_factory.py             # ペルソナ生成ファクトリ
├── personality_calculator.py      # 性格計算（ビッグファイブ理論）
├── story_generator.py             # ストーリー生成
├── letter_generator.py            # 手紙生成
├── root_agent.py                  # ルートエージェント
└── README.md                      # このファイル
```

## 主要コンポーネント

### 1. FamilySessionAgent ([entrypoints.py](entrypoints.py))

セッション全体を管理する進行役エージェントです。

**責務:**
- 家族メンバーとの対話を調整
- 会話ログと旅行情報の収集
- 会話終了時のストーリー・手紙生成
- 生成コンテンツの保存

**使用例:**
```python
from family import create_family_session

# セッション作成
agent = create_family_session(context={"profile": user_profile})

# 実行
response = await agent.run("週末どこに行きたい?")
```

### 2. FamilyToolSet ([tooling.py](tooling.py))

家族メンバーのツール群を管理するクラスです。

**責務:**
- PersonaFactoryからペルソナを生成
- 各家族メンバーのツール作成
- ツールの一覧管理

**主要メソッド:**
- `build_tools()`: Google ADK用のツールリストを返す
- `tool_names()`: ツール名のリストを返す
- `get_personas()`: 全ペルソナのリストを返す

### 3. PersonaFactory ([persona_factory.py](persona_factory.py))

ユーザープロファイルから家族メンバーのペルソナを生成します。

**責務:**
- パートナーペルソナの生成
- 子供ペルソナの生成（性格計算付き）
- ビッグファイブ理論に基づく性格継承

**生成されるペルソナの要素:**
- `name`: 名前
- `role`: 役割（パートナー、第1子など）
- `speaking_style`: 話し方
- `traits`: 性格特性リスト
- `goals`: 目標・願い
- `background`: 背景情報
- `history`: 過去の会話履歴

### 4. StoryGenerator ([story_generator.py](story_generator.py))

会話ログから物語的なストーリーを生成します。

**責務:**
- 3部構成のストーリー作成（導入→本編→結び）
- 家族の個性を反映した描写
- 感情的で共感を呼ぶ表現

**生成されるストーリーの構成:**
1. **導入部**: 家族が旅行について話し合う様子（2-3段落）
2. **本編**: 旅行先での具体的なシーン描写（3-4段落）
3. **結び**: 家族の絆や期待感の表現（1-2段落）

**使用例:**
```python
from family.story_generator import StoryGenerator

generator = StoryGenerator()
story = await generator.generate_story(
    conversation_log=[
        {"speaker": "パートナー", "message": "公園に行きたいな"},
        {"speaker": "第1子", "message": "遊具で遊びたい！"}
    ],
    trip_info={
        "destination": "都立公園",
        "activities": ["ピクニック", "遊具遊び"]
    },
    personas=personas
)
```

### 5. LetterGenerator ([letter_generator.py](letter_generator.py))

ストーリーを基に手紙形式のメッセージを生成します。

**責務:**
- 未来の家族からの温かい手紙作成
- ユーザーへの感謝と励まし
- 適切な手紙フォーマット

**生成される手紙の構成:**
1. **宛名**: 「未来の[ユーザー名]へ」
2. **前書き**: 感謝の気持ち（1-2段落）
3. **本文**: 旅行への期待と想い（3-4段落）
4. **結び**: 現在のあなたへのエール（1-2段落）
5. **署名**: 日付と家族メンバーの名前

**使用例:**
```python
from family.letter_generator import LetterGenerator

generator = LetterGenerator()
letter = await generator.generate_letter(
    story=generated_story,
    trip_info=trip_info,
    family_members=personas,
    user_name="太郎"
)
```

### 6. PersonalityCalculator ([personality_calculator.py](personality_calculator.py))

ビッグファイブ理論に基づいて子供の性格を計算します。

**責務:**
- 親の性格特性から子供の性格を遺伝計算
- 出生順位による性格調整
- LLMを使った性格描写生成

**性格特性（ビッグファイブ）:**
- `openness`: 開放性
- `conscientiousness`: 誠実性
- `extraversion`: 外向性
- `agreeableness`: 協調性
- `neuroticism`: 神経症傾向

## データフロー

### 会話フロー

```
ユーザー入力
  ↓
FamilySessionAgent
  ↓
FamilyToolSet（家族メンバーツール呼び出し）
  ↓
各FamilyTool（パートナー、子供）
  ↓
会話ログ・旅行情報の蓄積
  ↓
_post_process（会話終了時）
  ├→ StoryGenerator（ストーリー生成）
  ├→ LetterGenerator（手紙生成）
  └→ JSONファイル保存
```

### データ保存形式

生成されたコンテンツは `family_plan.json` として保存されます：

```json
{
  "destination": "行き先",
  "activities": ["アクティビティ1", "アクティビティ2"],
  "story": "生成された物語（800-1200文字）",
  "letter": "生成された手紙（600-900文字）",
  "conversation_log": [
    {"speaker": "役割", "message": "発言内容"},
    ...
  ]
}
```

**保存場所:**
```
tmp/user_sessions/{session_id}/family_plan.json
```

## 環境変数

以下の環境変数を設定してください：

```bash
# Google Gemini API キー（必須）
GOOGLE_API_KEY=your_api_key
# または
GEMINI_API_KEY=your_api_key

# 使用するモデル（オプション、デフォルト: gemini-2.5-pro）
FAMILY_GEMINI_MODEL=gemini-2.5-pro

# セッションディレクトリ（オプション）
FAMILY_SESSIONS_DIR=/path/to/sessions
```

## エラーハンドリング

### ストーリー生成失敗時

ストーリー生成に失敗した場合、フォールバック処理により簡易サマリーが生成されます：

```python
def _generate_fallback_summary(self, conversation_log, destination, activities):
    activities_text = "、".join(activities)
    return (
        f"家族みんなで{destination}への旅行を計画しています。\n"
        f"現地では{activities_text}を楽しむ予定です。\n\n"
        f"家族全員がこの旅行を楽しみにしています！"
    )
```

### 手紙生成失敗時

手紙生成に失敗した場合、空文字列が保存され、ストーリーのみが返却されます。

### ロギング

全ての処理は Python の logging モジュールでログ出力されます：

```python
import logging
logger = logging.getLogger(__name__)

# 使用例
logger.info("ストーリー生成完了")
logger.error("エラーが発生しました", exc_info=True)
```

## テスト

### ユニットテスト

```bash
pytest tests/family/test_story_generator.py
pytest tests/family/test_letter_generator.py
```

### 統合テスト

```bash
pytest tests/family/test_integration.py
```

## トラブルシューティング

### よくある問題

#### 1. API キーエラー

```
エラー: API key not configured
```

**解決方法:**
```bash
export GOOGLE_API_KEY=your_api_key
```

#### 2. ペルソナ情報不足エラー

```
ValueError: 家族メンバー情報が指定されていません
```

**解決方法:**
ユーザープロファイルに以下の情報が含まれているか確認：
- `current_partner` または `ideal_partner`
- `children_info`

#### 3. ストーリー生成が遅い

**原因:**
Gemini API の応答時間が長い場合があります。

**解決方法:**
- タイムアウト設定の調整
- より軽量なモデルの使用を検討

## 関連ドキュメント

- [FAMILY_AGENT_DESIGN.md](../docs/FAMILY_AGENT_DESIGN.md) - 設計詳細
- [STORY_GENERATION.md](../docs/STORY_GENERATION.md) - ストーリー生成仕様
- [LETTER_GENERATION.md](../docs/LETTER_GENERATION.md) - 手紙生成仕様
- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) - システム全体アーキテクチャ

## ライセンス

このモジュールはプロジェクトのライセンスに従います。
