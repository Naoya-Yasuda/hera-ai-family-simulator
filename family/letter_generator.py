from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List

import google.generativeai as genai
from google.generativeai import GenerativeModel

from .persona_factory import Persona


class LetterGenerator:
    """ストーリーを基に手紙形式のメッセージを生成

    生成されたストーリー、旅行情報、家族構成を基に、
    未来の家族から現在のユーザーへ送る温かい手紙を生成します。

    手紙の構成:
        - ヘッダー: 宛名（未来の[ユーザー名]へ）
        - 前書き: 感謝の気持ち
        - 本文: 旅行への期待と想い
        - 結び: 現在のあなたへのエール
        - フッター: 日付と署名
    """

    LETTER_PROMPT_TEMPLATE = """
あなたは未来の家族として、現在のユーザーへ温かい手紙を書く執筆者です。
以下の情報を基に、感謝と希望に満ちた手紙を日本語で作成してください。

## 家族構成
{family_members}

## 生成されたストーリー
{story}

## 旅行情報
- 行き先: {destination}
- やりたいこと: {activities}

## 手紙作成の要件

### 構成
1. **宛名**: 「未来の{user_name}へ」（{user_name}が不明な場合は「未来のあなたへ」）

2. **前書き（1-2段落）**
   - 週末の計画を立ててくれたことへの感謝
   - 家族みんなが楽しみにしている気持ち

3. **本文（3-4段落）**
   - {destination}への旅行についての具体的な期待
   - {activities}を一緒にやることへのワクワク感
   - 家族それぞれの想いや楽しみ（子供の視点も含める）
   - この旅行が家族にとって特別な思い出になる予感

4. **結び（1-2段落）**
   - 現在のあなた（ユーザー）への励ましやエール
   - 未来の家族がいつもそばにいることを伝える
   - 「楽しみに待っているね」などの温かいメッセージ

5. **署名**
   - 日付: {date}
   - 「未来の家族より」
   - 家族メンバーの名前（{family_names}）

### 文体とトーン
- 温かく、親しみやすい文体
- 感謝と愛情が伝わる表現
- 現在のあなたを勇気づける前向きなメッセージ
- 全体で600-900文字程度

### 注意事項
- 箇条書きは使わず、手紙らしい自然な文章で
- 家族それぞれの個性が感じられる表現を含める
- 「あなた」「きみ」など、親しみを込めた二人称を使う
- 最後は希望と期待で締めくくる

それでは、心のこもった手紙を作成してください。
"""

    def __init__(self, model_name: str | None = None) -> None:
        """LetterGeneratorの初期化

        Args:
            model_name: 使用するモデル名。Noneの場合は環境変数またはデフォルト値を使用
        """
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)

        if model_name is None:
            model_name = os.getenv("FAMILY_GEMINI_MODEL", "gemini-2.5-pro")

        self.model = GenerativeModel(model_name)

    async def generate_letter(
        self,
        story: str,
        trip_info: Dict[str, Any],
        family_members: List[Persona],
        user_name: str | None = None,
    ) -> str:
        """ストーリーを基に手紙形式のメッセージを生成

        Args:
            story: 生成されたストーリー
            trip_info: 旅行情報 {"destination": "行き先", "activities": ["アクティビティ1", ...]}
            family_members: 家族メンバーのペルソナリスト
            user_name: ユーザーの名前（省略可）

        Returns:
            str: 生成された手紙（600-900文字程度）

        Raises:
            ValueError: 必須情報が不足している場合
        """
        # バリデーション
        if not story or not story.strip():
            raise ValueError("ストーリーが空です")

        if not trip_info.get("destination"):
            raise ValueError("旅行先（destination）が指定されていません")

        activities = trip_info.get("activities", [])
        if not activities:
            raise ValueError("やりたいこと（activities）が指定されていません")

        if not family_members:
            raise ValueError("家族メンバー情報が指定されていません")

        # プロンプト用のデータを整形
        family_members_text = self._format_family_members(family_members)
        family_names = self._extract_family_names(family_members)
        activities_text = "、".join(activities)
        current_date = datetime.now().strftime("%Y年%m月%d日")
        user_display_name = user_name if user_name else "あなた"

        # プロンプト生成
        prompt = self.LETTER_PROMPT_TEMPLATE.format(
            family_members=family_members_text,
            story=story,
            destination=trip_info["destination"],
            activities=activities_text,
            user_name=user_display_name,
            date=current_date,
            family_names=family_names,
        )

        # 手紙生成（非同期実行）
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, self.model.generate_content, prompt
        )

        letter = response.text if hasattr(response, "text") else str(response)
        return letter.strip()

    def _format_family_members(self, personas: List[Persona]) -> str:
        """ペルソナリストを読みやすいテキストに整形

        Args:
            personas: ペルソナのリスト

        Returns:
            str: 整形された家族構成の説明
        """
        lines = []
        for persona in personas:
            lines.append(f"- {persona.role}「{persona.name}」")
            lines.append(f"  性格: {', '.join(persona.traits)}")
        return "\n".join(lines)

    def _extract_family_names(self, personas: List[Persona]) -> str:
        """家族メンバーの名前を抽出して整形

        Args:
            personas: ペルソナのリスト

        Returns:
            str: カンマ区切りの名前リスト（例: "さくら、ゆう、未来のパートナー"）
        """
        names = [persona.name for persona in personas]
        return "、".join(names)
