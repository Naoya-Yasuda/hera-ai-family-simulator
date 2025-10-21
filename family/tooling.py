from __future__ import annotations

import asyncio
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

        async def call_agent(*, tool_context, input_text: str) -> str:
            prompt = self._build_prompt(input_text)

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.model.generate_content, prompt)
            if hasattr(response, "text") and response.text:
                return response.text.strip()
            return str(response)

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
- 愛情と感謝を込めて150字以内で応答する
- ユーザーの話題に触れ、具体的なエピソードを想像して伝える
- 他の家族の発言と矛盾しないよう注意する
- 常に日本語で返答する

ユーザーからのメッセージ:
{user_message}
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
