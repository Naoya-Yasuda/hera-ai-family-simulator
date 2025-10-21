from __future__ import annotations

from typing import Any, Dict

from google.adk.agents.llm_agent import Agent

from .tooling import FamilyToolSet


class FamilySessionAgent(Agent):
    """進行役が家族ツールを呼び出すラッパー"""

    def __init__(self, profile: Dict[str, Any], api_key: str | None = None, **kwargs: Any) -> None:
        toolset = FamilyToolSet(profile)
        tools = toolset.build_tools()
        instruction = self._build_instruction(toolset.tool_names())
        super().__init__(
            name="family_session_agent",
            description="家族会話の進行役。自身は発話せず、ツールを通じて家族の声をまとめる",
            model="gemini-2.5-pro",
            instruction=instruction,
            tools=tools,
            **kwargs,
        )
        self._toolset = toolset

    @property
    def toolset(self) -> FamilyToolSet:
        return self._toolset

    def _build_instruction(self, tool_names: list[str]) -> str:
        joined = ", ".join(tool_names)
        return f"""
あなたは家族会話の司会です。ユーザーの発言を理解し、以下の家族ツールを呼び出して返答をまとめてください。
利用可能なツール: {joined}

ルール:
- 自分自身でメッセージを生成しない
- ユーザーの発言1回につき、最大2つのツールを呼び出す
- ツールから受け取った応答のみを利用し、[{"speaker": "名前", "message": "発言"}, ...] 形式のJSONリストで返す
- JSON以外の余計なテキストは付けない
- 順序は会話が自然になるように並べ替える
- どのツールを呼ぶかは前回の発言者を避けるよう配慮する
"""


def create_family_session(context: Dict[str, Any] | None = None, api_key: str | None = None):
    context = context or {}
    profile = context.get("profile") or {}
    return FamilySessionAgent(profile, api_key=api_key)
