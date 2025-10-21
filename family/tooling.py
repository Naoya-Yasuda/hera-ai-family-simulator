from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, List

import google.generativeai as genai
from google.generativeai import GenerativeModel
from google.adk.tools import FunctionTool

from .persona_factory import PersonaFactory
from .persona_factory import Persona


class FamilyTool:
    def __init__(self, persona: Persona, index: int, kind: str) -> None:
        self.persona = persona
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        model_name = os.getenv("FAMILY_GEMINI_MODEL", "gemini-2.5-pro")
        self.model = GenerativeModel(model_name)
        self.display_name = persona.role

        async def call_agent(*, tool_context, input_text: str) -> Dict[str, str]:
            prompt = self._build_prompt(input_text)

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.model.generate_content, prompt)
            text = response.text if hasattr(response, "text") else str(response)

            # デバッグログ
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[{self.persona.role}] Raw response: {text[:200]}...")

            destination = None
            activities: List[str] | None = None
            try:
                # JSONの前後の余計なテキストを除去
                text_cleaned = text.strip()
                # マークダウンコードブロックを除去
                if text_cleaned.startswith("```json"):
                    text_cleaned = text_cleaned[7:]
                if text_cleaned.startswith("```"):
                    text_cleaned = text_cleaned[3:]
                if text_cleaned.endswith("```"):
                    text_cleaned = text_cleaned[:-3]
                text_cleaned = text_cleaned.strip()

                logger.info(f"[{self.persona.role}] Cleaned JSON: {text_cleaned[:200]}...")

                result = json.loads(text_cleaned)
                speaker_text = result.get("message", text)
                destination = result.get("destination")
                activities_field = result.get("activities")

                logger.info(f"[{self.persona.role}] Parsed - destination: {destination}, activities: {activities_field}")

                if isinstance(activities_field, list):
                    activities = [str(item) for item in activities_field if item]
                elif activities_field:
                    activities = [str(activities_field)]
            except json.JSONDecodeError as e:
                logger.warning(f"[{self.persona.role}] JSON parse error: {e}, using text as-is")
                speaker_text = text.strip()

            trip_info = tool_context.state.setdefault("family_trip_info", {})
            if destination and isinstance(destination, str):
                trip_info["destination"] = destination
                logger.info(f"[{self.persona.role}] Set destination: {destination}")
            if activities:
                stored = trip_info.setdefault("activities", [])
                for activity in activities:
                    if activity not in stored:
                        stored.append(activity)
                logger.info(f"[{self.persona.role}] Added activities: {activities}, total: {stored}")

            log = tool_context.state.setdefault("family_conversation_log", [])
            log.append({"speaker": self.persona.role, "message": speaker_text})

            return {
                "speaker": self.persona.role,
                "message": speaker_text,
            }

        call_agent.__name__ = f"call_{kind}_{index}"
        self.tool = FunctionTool(func=call_agent, require_confirmation=False)

    def _build_prompt(self, user_message: str) -> str:
        history_snippets = "\n".join(
            f"過去の思い出: {item['message']}" for item in self.persona.history[:3]
        )
        return f"""
あなたは未来の{self.persona.role}「{self.persona.name}」です。
話し方: {self.persona.speaking_style}
性格特性: {', '.join(self.persona.traits)}
背景: {self.persona.background}
家族への思い: {self.persona.goals}
{history_snippets}

ルール:
- 返答は必ず以下のJSON形式で出力してください。JSON以外のテキストは一切含めないでください。
- フォーマット: {{"message": "ここに300字以内の返答", "destination": "行きたい場所名", "activities": ["やりたいこと1", "やりたいこと2"]}}

重要な指示:
- ユーザーのメッセージに「公園」「水族館」「海」などの場所が含まれている場合、必ずdestinationフィールドにその場所を設定してください
- ユーザーのメッセージに「ピクニック」「ブランコ」「遊ぶ」などの活動が含まれている場合、必ずactivitiesフィールドにその活動を配列で設定してください
- 場所や活動が明確でない場合のみ、destination や activities を null や空配列にしてください
- ユーザーの話題に触れ、具体的なエピソードを想像して伝える
- 他の家族の発言と矛盾しないよう注意する
- 常に日本語で返答する
- JSON形式を厳守してください

ユーザーからのメッセージ:
{user_message}

例1:
ユーザー「週末は公園でピクニックしよう」
→ {{"message": "いいね！公園でピクニック楽しみだね", "destination": "公園", "activities": ["ピクニック"]}}

例2:
ユーザー「都立公園でピクニックとブランコ遊びをしよう！」
→ {{"message": "わぁ素敵！都立公園でピクニックとブランコ、とっても楽しみ！", "destination": "都立公園", "activities": ["ピクニック", "ブランコ遊び"]}}
"""

    @property
    def name(self) -> str:
        return self.display_name


class FamilyToolSet:
    """家族会話ツール群"""

    def __init__(self, profile: Dict[str, Any]) -> None:
        self.factory = PersonaFactory(profile or {})
        self.tools = self._build_tools()

    def _build_tools(self) -> List[FamilyTool]:
        tools: List[FamilyTool] = []
        partner = self.factory.build_partner()
        tools.append(FamilyTool(partner, index=0, kind="partner"))
        for idx, persona in enumerate(self.factory.build_children(), start=1):
            tools.append(FamilyTool(persona, index=idx, kind="child"))
        return tools

    def build_tools(self) -> List[FunctionTool]:
        return [tool.tool for tool in self.tools]

    def tool_names(self) -> List[str]:
        return [tool.name for tool in self.tools]

    def get_personas(self) -> List[Persona]:
        """全ての家族メンバーのペルソナを取得

        Returns:
            List[Persona]: パートナーと子供を含む全ペルソナのリスト
        """
        return [tool.persona for tool in self.tools]
