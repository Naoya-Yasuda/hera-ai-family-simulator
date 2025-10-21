from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List

import google.generativeai as genai
from google.generativeai import GenerativeModel

from .persona_factory import Persona


class StoryGenerator:
    """会話ログから物語的なストーリーを生成

    家族の会話内容、旅行情報、ペルソナ情報を基に、
    感情的で物語性のあるストーリーを3部構成で生成します。

    3部構成:
        1. 導入: 家族が旅行について話し合う様子
        2. 本編: 旅行先での具体的なシーンの想像
        3. 結び: 家族の絆や期待感の表現
    """

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

### 構成（3部構成で作成）
1. **導入部**: 家族が週末の旅行について話し合っている様子を描写（2-3段落）
   - 家族それぞれの性格が表れる会話の様子
   - 旅行への期待感が伝わる雰囲気

2. **本編**: 旅行先での具体的なシーンを想像して描写（3-4段落）
   - {destination}での家族の楽しい時間
   - {activities}を実際に体験している様子
   - 具体的な感覚描写（視覚、聴覚、触覚など）

3. **結び**: 家族の絆や未来への期待を表現（1-2段落）
   - この旅行が家族にとってどんな意味を持つか
   - 温かい余韻を残す締めくくり

### 文体とトーン
- 温かみのある、情景が浮かぶ描写
- 家族それぞれの個性が活きる表現
- 読者（ユーザー）が「こんな未来が待っているかも」と思える希望
- 全体で800-1200文字程度

### 注意事項
- 箇条書きは使わず、自然な文章で
- 会話文を適度に含めて臨場感を出す
- 各家族メンバーの性格や話し方を反映
- 「楽しみだね！」などのポジティブな締めくくり

それでは、心温まるストーリーを作成してください。
"""

    def __init__(self, model_name: str | None = None) -> None:
        """StoryGeneratorの初期化

        Args:
            model_name: 使用するモデル名。Noneの場合は環境変数またはデフォルト値を使用
        """
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)

        if model_name is None:
            model_name = os.getenv("FAMILY_GEMINI_MODEL", "gemini-2.5-pro")

        self.model = GenerativeModel(model_name)

    async def generate_story(
        self,
        conversation_log: List[Dict[str, str]],
        trip_info: Dict[str, Any],
        personas: List[Persona],
    ) -> str:
        """会話ログから物語的なストーリーを生成

        Args:
            conversation_log: 家族の会話ログ [{"speaker": "役割名", "message": "発言内容"}]
            trip_info: 旅行情報 {"destination": "行き先", "activities": ["アクティビティ1", ...]}
            personas: 家族メンバーのペルソナリスト

        Returns:
            str: 生成された物語（3部構成、800-1200文字程度）

        Raises:
            ValueError: 必須情報（destination、activities）が不足している場合
        """
        # バリデーション
        if not trip_info.get("destination"):
            raise ValueError("旅行先（destination）が指定されていません")

        activities = trip_info.get("activities", [])
        if not activities:
            raise ValueError("やりたいこと（activities）が指定されていません")

        # プロンプト用のデータを整形
        family_members_text = self._format_family_members(personas)
        conversation_text = self._format_conversation_log(conversation_log)
        activities_text = "、".join(activities)

        # プロンプト生成
        prompt = self.STORY_PROMPT_TEMPLATE.format(
            family_members=family_members_text,
            conversation_log=conversation_text,
            destination=trip_info["destination"],
            activities=activities_text,
        )

        # ストーリー生成（非同期実行）
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, self.model.generate_content, prompt
        )

        story = response.text if hasattr(response, "text") else str(response)
        return story.strip()

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
            lines.append(f"  話し方: {persona.speaking_style}")
            lines.append(f"  性格: {', '.join(persona.traits)}")
            lines.append(f"  背景: {persona.background}")
        return "\n".join(lines)

    def _format_conversation_log(self, conversation_log: List[Dict[str, str]]) -> str:
        """会話ログを読みやすいテキストに整形

        Args:
            conversation_log: 会話ログのリスト

        Returns:
            str: 整形された会話ログ
        """
        if not conversation_log:
            return "（会話ログなし）"

        lines = []
        for item in conversation_log:
            speaker = item.get("speaker", "不明")
            message = item.get("message", "")
            lines.append(f"{speaker}: {message}")

        return "\n".join(lines)
