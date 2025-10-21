from __future__ import annotations

import json
import os
from typing import Any, Dict

from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.llm_agent import Agent

from .tooling import FamilyToolSet


class FamilyProfileLoader:
    _base_dir: str | None = None

    @classmethod
    def get_base_dir(cls) -> str:
        if cls._base_dir is None:
            cls._base_dir = os.environ.get("FAMILY_SESSIONS_DIR") or os.path.join(
                os.path.dirname(__file__),
                "..",
                "tmp",
                "user_sessions",
            )
        return cls._base_dir

    @classmethod
    def load_from_session(cls, session_id: str) -> Dict[str, Any]:
        if not session_id:
            return {}
        base_dir = cls.get_base_dir()
        profile_path = os.path.join(base_dir, session_id, "user_profile.json")
        if not os.path.exists(profile_path):
            return {}
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}


class FamilySessionAgent(Agent):
    """進行役が家族ツールを呼び出すラッパー"""

    def __init__(self, profile: Dict[str, Any], api_key: str | None = None, **kwargs: Any) -> None:
        super().__init__(
            name="family_session_agent",
            description="家族会話の進行役。自身は発話せず、ツールを通じて家族の声をまとめる",
            model="gemini-2.5-pro",
            **kwargs,
        )
        self._toolset = FamilyToolSet(profile)
        self._profile_loaded = bool(profile)
        self.before_agent_callback = self._ensure_profile
        if self._profile_loaded:
            self._apply_toolset()

    async def _ensure_profile(self, callback_context: CallbackContext):
        if self._toolset and self._profile_loaded:
            self._apply_toolset()
            return

        session_id = callback_context.session.id
        profile = FamilyProfileLoader.load_from_session(session_id)
        self._toolset = FamilyToolSet(profile)
        self._profile_loaded = True
        self._apply_toolset()
        callback_context.state["profile"] = profile

    @property
    def toolset(self) -> FamilyToolSet:
        return self._toolset

    def _apply_toolset(self) -> None:
        self.tools = self._toolset.build_tools()
        self.instruction = self._build_instruction(self._toolset.tool_names())

    def _build_instruction(self, tool_names: list[str]) -> str:
        joined = ", ".join(tool_names)
        return f"""
あなたは家族会話の司会です。ユーザーの発言を理解し、以下の家族ツールを呼び出して返答をまとめてください。
利用可能なツール: {joined}

ルール:
- 自分自身でメッセージを生成しない
- ユーザーの発言1回につき、最大2つのツールを呼び出す
- ツールから受け取った応答のみを利用し、[{{"speaker": "名前", "message": "発言"}}, ...] 形式のJSONリストで返す
- JSON以外の余計なテキストは付けない
- 順序は会話が自然になるように並べ替える
- どのツールを呼ぶかは前回の発言者を避けるよう配慮する
"""


def create_family_session(context: Dict[str, Any] | None = None, api_key: str | None = None):
    context = context or {}
    profile = context.get("profile") or {}
    return FamilySessionAgent(profile, api_key=api_key)
