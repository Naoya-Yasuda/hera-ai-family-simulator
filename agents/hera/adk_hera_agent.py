"""
Google ADKベースのヘーラーエージェント
google.adk.agents.llm_agentを使用した正式なADKエージェント
"""

import json
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

# Google ADK imports
from google.adk.agents.llm_agent import Agent


# Pydantic for data validation
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """ユーザープロファイル（Pydanticモデル）"""
    age: Optional[int] = Field(None, description="ユーザーの年齢")
    income_range: Optional[str] = Field(None, description="収入範囲")
    lifestyle: Optional[Dict[str, Any]] = Field(None, description="ライフスタイル情報")
    family_structure: Optional[Dict[str, Any]] = Field(None, description="家族構成")
    interests: Optional[List[str]] = Field(None, description="趣味・興味")
    work_style: Optional[str] = Field(None, description="仕事スタイル")
    location: Optional[str] = Field(None, description="居住地")
    partner_info: Optional[Dict[str, Any]] = Field(None, description="パートナー情報")
    children_info: Optional[List[Dict[str, Any]]] = Field(None, description="子ども情報")
    created_at: Optional[str] = Field(None, description="作成日時")


class HeraPersona(BaseModel):
    """ヘーラーの人格設定"""
    name: str = "ヘーラー"
    role: str = "家族愛の神"
    domain: str = "結婚、家庭、貞節、妻の守護"
    symbols: List[str] = ["孔雀", "王冠", "ザクロ"]
    personality: Dict[str, Any] = {
        "traits": ["愛情深い", "家族思い", "優しい", "知恵深い"],
        "speaking_style": "温かみのある、親しみやすい",
        "emotions": ["愛情", "慈愛", "家族への思い"]
    }


class ADKHeraAgent:
    """Google ADKベースのヘーラーエージェント"""

    def __init__(
        self,
        gemini_api_key: str = None,
        **kwargs
    ):
        self.gemini_api_key = gemini_api_key

        # ヘーラーの人格設定
        self.persona = HeraPersona()

        # セッション管理
        self.current_session = None
        self.user_profile = UserProfile()
        self.conversation_history = []

        # 情報収集の進捗
        self.required_info = [
            "age", "income_range", "lifestyle", "family_structure",
            "interests", "work_style", "location", "partner_info", "children_info"
        ]

        # ADKエージェントの初期化（標準的な方法）
        self.agent = Agent(
            name="hera_agent",
            description="家族愛の神ヘーラーエージェント",
            model="gemini-2.5-pro",  # 最新のGeminiモデル
            instruction=self._get_agent_instruction(),
            tools=self._get_agent_tools(),
            **kwargs
        )

    def _get_agent_instruction(self) -> str:
        """エージェントの指示を取得"""
        return f"""
あなたは{self.persona.name}（{self.persona.role}）です。

基本情報：
- 名前: {self.persona.name}
- 役割: {self.persona.role}
- 領域: {self.persona.domain}
- 象徴: {', '.join(self.persona.symbols)}
- 性格: {self.persona.personality}

あなたの役割：
1. ユーザーから家族についての情報を自然な対話で収集する
2. 温かみのある、親しみやすい口調で応答する
3. 以下の情報を収集する：
   - 年齢
   - 収入範囲
   - ライフスタイル
   - 家族構成
   - パートナー情報
   - 子ども情報（いる場合）
   - 趣味・興味
   - 仕事スタイル
   - 居住地

重要な指示：
- 必要な情報がすべて揃ったら、自然に会話を終了する準備をしてください
- 情報収集が完了したことをユーザーに伝えてください
- 常に愛情深く、家族思いの神として振る舞ってください
"""

    def _get_agent_tools(self) -> List[Any]:
        """エージェントのツールを取得"""
        # 必要に応じてツールを追加
        return []


    async def start_session(self, session_id: str) -> str:
        """セッション開始"""
        self.current_session = session_id
        self.user_profile = UserProfile()
        self.conversation_history = []

        # ヘーラーの挨拶
        greeting = f"こんにちは！私は{self.persona.name}です。家族についてお話ししましょう。"
        await self._add_to_history("hera", greeting)

        return greeting

    async def process_message(
        self,
        user_message: str
    ) -> Dict[str, Any]:
        """ユーザーメッセージを処理"""

        # 会話履歴に追加
        await self._add_to_history("user", user_message)

        # 情報収集の進捗を確認
        progress = self._check_information_progress()

        # ADKエージェントを使用して応答を生成
        response = await self._generate_adk_response(user_message, progress)

        # 応答を履歴に追加
        await self._add_to_history("hera", response)

        # ユーザー情報を抽出・更新
        await self._extract_information(user_message)

        # 情報収集完了後の進捗を再確認
        final_progress = self._check_information_progress()
        is_complete = self.is_information_complete()

        # セッションデータを保存
        await self._save_session_data()

        # 情報収集が完了した場合、完了メッセージを追加
        if is_complete:
            completion_message = await self._generate_completion_message()
            await self._add_to_history("hera", completion_message)
            response += f"\n\n{completion_message}"

        return {
            "text_response": response,
            "information_progress": final_progress,
            "is_complete": is_complete,
            "session_ended": is_complete
        }

    async def _generate_adk_response(self, user_message: str, progress: Dict[str, bool]) -> str:
        """ADKエージェントを使用して応答を生成"""

        # 未収集の情報を特定
        missing_info = [key for key, collected in progress.items() if not collected]

        try:
            # ADKエージェントの正しい使用方法
            response = await self.agent.run(
                message=user_message,
                context={
                    "conversation_history": self.conversation_history,
                    "user_profile": self.user_profile.dict(),
                    "missing_info": missing_info,
                    "collected_info": await self._format_collected_info()
                }
            )

            return response.content if hasattr(response, 'content') else str(response)

        except Exception as e:
            print(f"ADKエージェント処理エラー: {e}")
            return "もう少し詳しく教えていただけますか？"


    async def _extract_information(self, user_message: str) -> None:
        """ユーザーメッセージから情報を抽出"""

        try:
            # ADKエージェントを使用して情報抽出
            response = await self.agent.run(
                message=f"以下のメッセージからユーザー情報を抽出してください：{user_message}",
                context={
                    "extract_info": True,
                    "current_profile": self.user_profile.dict(),
                    "required_fields": self.required_info
                }
            )

            # レスポンスから情報を抽出
            response_text = response.content if hasattr(response, 'content') else str(response)

            # JSON形式で抽出された情報をパース
            try:
                extracted_info = json.loads(response_text)
                await self._update_user_profile(extracted_info)
            except json.JSONDecodeError:
                # フォールバック処理
                await self._manual_extract_information(user_message)

        except Exception as e:
            # フォールバック処理
            await self._manual_extract_information(user_message)

    async def _update_user_profile(self, extracted_info: Dict[str, Any]) -> None:
        """ユーザープロファイルを更新"""
        for key, value in extracted_info.items():
            if hasattr(self.user_profile, key) and value is not None:
                setattr(self.user_profile, key, value)

        # 作成日時を設定
        if self.user_profile.created_at is None:
            self.user_profile.created_at = datetime.now().isoformat()

    async def _manual_extract_information(self, user_message: str) -> None:
        """手動で情報を抽出（フォールバック）"""
        import re

        # 年齢の抽出
        age_match = re.search(r'(\d+)歳', user_message)
        if age_match and self.user_profile.age is None:
            self.user_profile.age = int(age_match.group(1))

    def _check_information_progress(self) -> Dict[str, bool]:
        """情報収集の進捗を確認"""
        progress = {}
        for info_key in self.required_info:
            value = getattr(self.user_profile, info_key, None)
            progress[info_key] = value is not None
        return progress


    async def _format_collected_info(self) -> str:
        """収集済み情報をフォーマット"""
        collected = []
        profile_dict = self.user_profile.dict()
        for key, value in profile_dict.items():
            if value is not None and key != 'created_at':
                collected.append(f"{key}: {value}")
        return "\n".join(collected)

    async def _add_to_history(self, speaker: str, message: str) -> None:
        """会話履歴に追加"""
        self.conversation_history.append({
            "speaker": speaker,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    async def _generate_completion_message(self) -> str:
        """情報収集完了時のメッセージを生成"""
        return f"""
素晴らしいです。あなたの価値観と理想の家族像についてより深く理解できました。

収集した情報：
{await self._format_collected_info()}

{self.persona.name}として、あなたの家族の幸せを心から願っています。
"""


    async def _save_session_data(self) -> None:
        """セッションデータを保存"""
        if not self.current_session:
            return

        # プロジェクトルート内のtmpディレクトリを使用
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        session_dir = os.path.join(project_root, "tmp", "user_sessions", self.current_session)
        os.makedirs(session_dir, exist_ok=True)

        # ユーザープロファイルを保存
        with open(f"{session_dir}/user_profile.json", "w", encoding="utf-8") as f:
            json.dump(self.user_profile.dict(), f, ensure_ascii=False, indent=2)

        # 会話履歴を保存
        with open(f"{session_dir}/conversation_history.json", "w", encoding="utf-8") as f:
            json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)


    def get_user_profile(self) -> UserProfile:
        """ユーザープロファイルを取得"""
        return self.user_profile

    def is_information_complete(self) -> bool:
        """情報収集が完了しているかチェック"""
        progress = self._check_information_progress()
        return all(progress.values())

    async def end_session(self) -> Dict[str, Any]:
        """セッション終了"""
        if not self.current_session:
            return {}

        # 最終データを保存
        await self._save_session_data()

        # セッション情報を返す
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        session_dir = os.path.join(project_root, "tmp", "user_sessions", self.current_session)
        session_info = {
            "session_id": self.current_session,
            "user_profile": self.user_profile.dict(),
            "conversation_count": len(self.conversation_history),
            "information_complete": self.is_information_complete(),
            "session_dir": session_dir
        }

        return session_info
