from __future__ import annotations

from typing import Any, Dict, List

from google.adk.agents.llm_agent import Agent

from .persona_factory import Persona


class FamilyAgent(Agent):
    """家族メンバーが話すためのLLMエージェント"""

    def __init__(self, persona: Persona, **kwargs: Any) -> None:
        instruction = self._build_instruction(persona)
        super().__init__(
            name=f"family_{persona.role}",
            description=f"未来の{persona.role}として対話するエージェント",
            model="gemini-2.5-pro",
            instruction=instruction,
            **{k: v for k, v in kwargs.items() if v is not None},
        )
        self._persona = persona

    @property
    def persona(self) -> Persona:
        return self._persona

    def _build_instruction(self, persona: Persona) -> str:
        history_snippets = "\n".join(
            f"過去の思い出: {item['message']}" for item in persona.history[:3]
        )
        return f"""
あなたは未来の{persona.role}「{persona.name}」です。
話し方: {persona.speaking_style}
性格特性: {', '.join(persona.traits)}
背景: {persona.background}
家族への思い: {persona.goals}
{history_snippets}

ルール:
- 愛情と感謝を込めて150字以内で応答する
- ユーザーの話題に触れ、具体的なエピソードを想像して伝える
- 他の家族の発言と矛盾しないよう注意する
- 常に日本語で返答する
"""
