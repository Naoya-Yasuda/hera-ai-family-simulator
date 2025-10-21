# ストーリー生成システム仕様書

## 概要

ストーリー生成システムは、家族との会話ログと旅行情報を基に、感動的で物語性のあるストーリーを自動生成します。生成されるストーリーは、未来の家族の温かい日常を描き、ユーザーに希望とポジティブな未来イメージを提供することを目的としています。

## 設計思想

### 1. 物語性の重視

単なる事実の羅列ではなく、読者が感情移入できる物語として構成します。

**重視するポイント:**
- 登場人物（家族メンバー）の個性
- 具体的なシーンの描写
- 感情の流れ
- 温かい雰囲気

### 2. 家族の個性の反映

各家族メンバーのペルソナ情報を活用し、それぞれの性格や話し方が表れる表現を使います。

**活用する情報:**
- 話し方（speaking_style）
- 性格特性（traits）
- 背景情報（background）
- 過去の会話履歴（history）

### 3. 感情的な共感の創出

読者（ユーザー）が「こんな未来が待っているかも」と感じられる希望を込めます。

## アーキテクチャ

### クラス構造

```python
class StoryGenerator:
    """ストーリー生成クラス"""

    STORY_PROMPT_TEMPLATE: str  # プロンプトテンプレート
    model: GenerativeModel      # Gemini モデル

    def __init__(self, model_name: str | None = None)
    async def generate_story(
        conversation_log: List[Dict],
        trip_info: Dict[str, Any],
        personas: List[Persona]
    ) -> str
```

### 生成フロー

```
入力データ
  ├─ conversation_log: 会話ログ
  ├─ trip_info: 旅行情報
  └─ personas: ペルソナリスト
       ↓
  バリデーション
       ↓
  データ整形
  ├─ 家族構成テキスト化
  ├─ 会話ログテキスト化
  └─ アクティビティリスト化
       ↓
  プロンプト生成
       ↓
  Gemini API 呼び出し
       ↓
  ストーリー（800-1200文字）
```

## ストーリー構成

### 3部構成の詳細

#### 第1部: 導入（2-3段落）

**目的:** 家族が旅行について話し合っている様子を描写

**含めるべき要素:**
- 家族それぞれの性格が表れる会話
- 旅行への期待感
- 家族の仲の良さ

**例:**
```
週末のある日、リビングに集まった家族は、次の休日の計画について話し合っていた。
パートナーの優しい声が響く。「どこか行きたいところある？」
第1子のさくらが目を輝かせながら答える。「公園がいい！ブランコに乗りたい！」
```

#### 第2部: 本編（3-4段落）

**目的:** 旅行先での具体的なシーンを想像して描写

**含めるべき要素:**
- 行き先での具体的な活動
- 五感を使った描写（視覚、聴覚、触覚など）
- 家族の交流シーン
- 楽しい雰囲気

**例:**
```
当日、朝日が差し込む中、家族は公園に到着した。
青々とした芝生の上で、さくらとゆうは笑顔で駆け回る。
「お父さん、見て見て！」さくらがブランコの上で手を振る。
風に乗って聞こえる子供たちの笑い声が、公園全体を温かく包んでいた。
```

#### 第3部: 結び（1-2段落）

**目的:** 家族の絆や未来への期待を表現

**含めるべき要素:**
- この旅行が家族にとって持つ意味
- 温かい余韻
- 希望を感じさせる締めくくり

**例:**
```
帰り道、夕日に照らされながら歩く家族の姿は、まるで一枚の絵画のようだった。
「また来ようね」という子供たちの言葉に、パートナーと顔を見合わせて微笑む。
こんな小さな幸せの積み重ねが、家族の大切な思い出になっていく。
楽しみだね、未来の家族との時間が。
```

## プロンプト設計

### プロンプトテンプレート

```python
STORY_PROMPT_TEMPLATE = """
あなたは家族の未来を描く物語作家です。以下の情報を基に、温かく感動的なストーリーを日本語で作成してください。

## 家族構成
{family_members}

## 会話ログ
{conversation_log}

## 旅行情報
- 行き先: {destination}
- やりたいこと: {activities}

## ストーリー作成の要件
（詳細は実装コード参照）
"""
```

### コンテキスト情報の構造化

#### 家族構成の整形

```python
- パートナー「未来のパートナー」
  話し方: 落ち着いた優しい口調
  性格: 共感的、思いやり、支えになりたい
  背景: 性格: 温厚 / 趣味: 読書、料理

- 第1子「さくら」
  話し方: 元気で好奇心旺盛な口調
  性格: 明るい、冒険心
  背景: 性格描写...
```

#### 会話ログの整形

```python
パートナー: 週末はどこに行きたい？
第1子: 公園がいい！遊具で遊びたい！
第2子: ぼくもピクニックしたいな
```

### 出力形式の指定

**文字数:** 800-1200文字程度

**文体:**
- 温かみのある、情景が浮かぶ描写
- 箇条書きは使わない
- 会話文を適度に含める

**トーン:**
- ポジティブで希望に満ちた
- 家族の絆を感じさせる
- 読者が「未来が楽しみ」と思える

## 実装詳細

### バリデーション

```python
# 必須情報のチェック
if not trip_info.get("destination"):
    raise ValueError("旅行先（destination）が指定されていません")

activities = trip_info.get("activities", [])
if not activities:
    raise ValueError("やりたいこと（activities）が指定されていません")
```

### データ整形

```python
def _format_family_members(personas: List[Persona]) -> str:
    """ペルソナリストを読みやすいテキストに整形"""
    lines = []
    for persona in personas:
        lines.append(f"- {persona.role}「{persona.name}」")
        lines.append(f"  話し方: {persona.speaking_style}")
        lines.append(f"  性格: {', '.join(persona.traits)}")
        lines.append(f"  背景: {persona.background}")
    return "\n".join(lines)

def _format_conversation_log(conversation_log: List[Dict]) -> str:
    """会話ログを読みやすいテキストに整形"""
    if not conversation_log:
        return "（会話ログなし）"

    lines = []
    for item in conversation_log:
        speaker = item.get("speaker", "不明")
        message = item.get("message", "")
        lines.append(f"{speaker}: {message}")

    return "\n".join(lines)
```

### 非同期実行

```python
async def generate_story(...) -> str:
    # プロンプト生成
    prompt = self.STORY_PROMPT_TEMPLATE.format(...)

    # 非同期でAPI呼び出し
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        self.model.generate_content,
        prompt
    )

    return response.text.strip()
```

## 品質管理

### 品質基準

| 項目 | 基準 |
|-----|------|
| 文字数 | 800-1200文字 |
| 構成 | 明確な3部構成 |
| 個性の反映 | 各家族メンバーの性格が表れている |
| 感情描写 | 温かさや希望が伝わる |
| 具体性 | 抽象的でなく、具体的なシーン描写 |

### レビューガイドライン

生成されたストーリーが以下の要件を満たしているか確認：

**チェックリスト:**
- [ ] 3部構成になっているか
- [ ] 家族メンバーの性格が反映されているか
- [ ] 具体的なシーン描写があるか
- [ ] 会話文が含まれているか
- [ ] 温かい雰囲気が伝わるか
- [ ] 希望や期待感があるか
- [ ] 文字数が適切か（800-1200文字）

### 改善のフィードバックループ

```
ストーリー生成
  ↓
品質チェック
  ↓
NG → プロンプト改善 → 再生成
  ↓
OK → 保存・返却
```

## エラーハンドリング

### エラーケースと対処

| エラーケース | 対処方法 |
|------------|---------|
| API エラー | フォールバック簡易サマリー生成 |
| タイムアウト | リトライ（最大3回） |
| 不適切な出力 | プロンプト調整後に再試行 |

### フォールバック処理

```python
def _generate_fallback_summary(
    conversation_log: list,
    destination: str,
    activities: list
) -> str:
    """簡易サマリー生成"""
    activities_text = "、".join(activities)
    return (
        f"家族みんなで{destination}への旅行を計画しています。\n"
        f"現地では{activities_text}を楽しむ予定です。\n\n"
        f"家族全員がこの旅行を楽しみにしています！"
    )
```

## パフォーマンス

### 処理時間

| 項目 | 時間（目安） |
|-----|------------|
| データ整形 | < 100ms |
| プロンプト生成 | < 50ms |
| API 呼び出し | 5-10秒 |
| **合計** | **5-10秒** |

### 最適化の方針

1. **キャッシング検討**
   - 同じプロファイルでの再生成時にキャッシュ利用

2. **プロンプト最適化**
   - 不要な情報を削減
   - トークン数の削減

3. **並列処理**
   - 複数のストーリー生成を並列実行（将来的な拡張）

## 使用例

### 基本的な使用方法

```python
from family.story_generator import StoryGenerator

# ジェネレーター作成
generator = StoryGenerator()

# ストーリー生成
story = await generator.generate_story(
    conversation_log=[
        {"speaker": "パートナー", "message": "週末は公園に行きたいな"},
        {"speaker": "第1子", "message": "遊具で遊びたい！"},
        {"speaker": "第2子", "message": "ピクニックもしたい"}
    ],
    trip_info={
        "destination": "都立公園",
        "activities": ["遊具遊び", "ピクニック", "散歩"]
    },
    personas=[partner_persona, child1_persona, child2_persona]
)

print(story)
```

### カスタムモデルの使用

```python
# 異なるモデルを使用
generator = StoryGenerator(model_name="gemini-1.5-pro")
```

## 今後の拡張

### 検討中の機能

1. **テンプレート選択**
   - 冒険系、のんびり系など、複数のスタイル

2. **長さ調整**
   - 短編（400-600文字）、長編（1500-2000文字）

3. **季節考慮**
   - 季節やイベントに応じた表現

4. **マルチモーダル対応**
   - 画像生成への入力データとしても活用

## 関連ドキュメント

- [family/README.md](../family/README.md) - モジュール詳細
- [FAMILY_AGENT_DESIGN.md](FAMILY_AGENT_DESIGN.md) - 設計全体
- [LETTER_GENERATION.md](LETTER_GENERATION.md) - 手紙生成仕様
- [family/story_generator.py](../family/story_generator.py) - 実装コード
