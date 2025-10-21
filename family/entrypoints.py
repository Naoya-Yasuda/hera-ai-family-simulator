from __future__ import annotations

import json
import logging
import os
from typing import Any, ClassVar, Dict

from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.llm_agent import Agent
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.genai import types

from .letter_generator import LetterGenerator
from .story_generator import StoryGenerator
from .tooling import FamilyToolSet

# ロガー設定
logger = logging.getLogger(__name__)


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
    """進行役が家族ツールを呼び出すラッパー

    会話終了時に以下の処理を自動実行:
        1. 会話ログと旅行情報の収集
        2. ストーリー生成（物語形式）
        3. 手紙生成（未来の家族からのメッセージ）
        4. 全てをJSONファイルに保存
        5. ストーリーをユーザーに返信
    """

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
        self.after_agent_callback = self._post_process
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

    async def _post_process(self, callback_context: CallbackContext):
        """会話終了後の後処理

        会話ログと旅行情報を基に、ストーリーと手紙を生成して保存します。

        処理フロー:
            1. 旅行情報と会話ログの収集
            2. ストーリー生成（StoryGenerator）
            3. 手紙生成（LetterGenerator）
            4. JSONファイルに保存
            5. ストーリーをイベントとして返却

        Args:
            callback_context: コールバックコンテキスト

        Returns:
            Event | None: 生成されたストーリーを含むイベント、または情報不足の場合はNone
        """
        # 1. 旅行情報の収集
        collected = callback_context.state.get("family_trip_info")
        if not collected:
            logger.info("旅行情報が収集されていません。後処理をスキップします。")
            return None

        destination = collected.get("destination")
        activities = collected.get("activities")
        if not destination or not activities:
            logger.warning(
                f"必須情報が不足しています。destination={destination}, activities={activities}"
            )
            return None

        conversation_log = callback_context.state.get("family_conversation_log", [])
        logger.info(
            f"後処理を開始: destination={destination}, "
            f"activities={len(activities)}件, conversation_log={len(conversation_log)}件"
        )

        # 2. ストーリー生成
        try:
            story_generator = StoryGenerator()
            personas = self._toolset.get_personas()
            story = await story_generator.generate_story(
                conversation_log=conversation_log,
                trip_info=collected,
                personas=personas,
            )
            logger.info(f"ストーリー生成完了: {len(story)}文字")
        except Exception as e:
            logger.error(f"ストーリー生成中にエラーが発生しました: {e}", exc_info=True)
            # エラー時は旧形式にフォールバック
            story = self._generate_fallback_summary(conversation_log, destination, activities)

        # 3. 手紙生成
        try:
            letter_generator = LetterGenerator()
            user_name = self._extract_user_name(callback_context)
            letter = await letter_generator.generate_letter(
                story=story,
                trip_info=collected,
                family_members=personas,
                user_name=user_name,
            )
            logger.info(f"手紙生成完了: {len(letter)}文字")
        except Exception as e:
            logger.error(f"手紙生成中にエラーが発生しました: {e}", exc_info=True)
            letter = ""  # エラー時は空文字列

        # 4. ファイル保存
        session_id = callback_context.session.id
        if session_id:
            try:
                base_dir = FamilyProfileLoader.get_base_dir()
                session_dir = os.path.join(base_dir, session_id)
                os.makedirs(session_dir, exist_ok=True)

                output_data = {
                    "destination": destination,
                    "activities": activities,
                    "story": story,
                    "letter": letter,
                    "conversation_log": conversation_log,
                }
                output_path = os.path.join(session_dir, "family_plan.json")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)

                logger.info(f"ファイル保存完了: {output_path}")
            except Exception as e:
                logger.error(f"ファイル保存中にエラーが発生しました: {e}", exc_info=True)

        # 5. ストーリーをイベントとして返却
        # Note: CallbackContext doesn't have 'branch' attribute, so we omit it
        return Event(
            invocation_id=callback_context.invocation_id,
            author=self.name,
            content=types.Content(
                role="assistant", parts=[types.Part(text=story)]
            ),
            actions=EventActions(end_of_agent=True),
        )

    def _generate_fallback_summary(
        self, conversation_log: list, destination: str, activities: list
    ) -> str:
        """エラー時のフォールバック用簡易サマリー生成

        Args:
            conversation_log: 会話ログ
            destination: 行き先
            activities: アクティビティリスト

        Returns:
            str: 簡易サマリー
        """
        activities_text = "、".join(activities)
        return (
            f"家族みんなで{destination}への旅行を計画しています。\n"
            f"現地では{activities_text}を楽しむ予定です。\n\n"
            f"家族全員がこの旅行を楽しみにしています！"
        )

    def _extract_user_name(self, callback_context: CallbackContext) -> str | None:
        """ユーザー名を抽出

        Args:
            callback_context: コールバックコンテキスト

        Returns:
            str | None: ユーザー名、取得できない場合はNone
        """
        try:
            profile = callback_context.state.get("profile", {})
            return profile.get("name") or profile.get("user_name")
        except Exception:
            return None

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
