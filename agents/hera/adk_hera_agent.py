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
- 必要な情報が十分に収集されたと判断したら、「もう十分」「これで十分」などと明確に表現してください
- 情報収集が完了したと判断したら、自然に会話を終了する準備をしてください
- 常に愛情深く、家族思いの神として振る舞ってください

利用可能なツール：
- extract_user_information: ユーザー情報を抽出・保存
- check_session_completion: 情報収集完了を判定
- save_session_data: セッションデータを保存

これらのツールを適切に使用して、ユーザー情報の収集と管理を行ってください。
"""

    def _get_agent_tools(self) -> List[Any]:
        """エージェントのツールを取得"""
        from google.adk.tools import FunctionTool

        # カスタムツールを定義
        tools = []

        # 情報抽出ツール
        extract_info_tool = FunctionTool(
            func=self._extract_user_info_tool,
            require_confirmation=False
        )
        tools.append(extract_info_tool)

        # セッション完了判定ツール
        completion_tool = FunctionTool(
            func=self._check_completion_tool,
            require_confirmation=False
        )
        tools.append(completion_tool)

        # セッションデータ保存ツール
        save_tool = FunctionTool(
            func=self._save_session_tool,
            require_confirmation=False
        )
        tools.append(save_tool)

        return tools


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
        """ユーザーメッセージを処理（ADKの標準フローを無効化）"""
        print(f"🚫 ADK標準フローをスキップ: {user_message}")

        # カスタムツールが処理するため、ここでは何もしない
        return {
            "text_response": "カスタムツールで処理中...",
            "is_complete": False,
            "session_ended": False
        }

    async def _generate_adk_response(self, user_message: str, progress: Dict[str, bool]) -> str:
        """ADKエージェントを使用して応答を生成"""

        try:
            # ADKエージェントの正しい使用方法
            response = await self.agent.run(
                message=user_message,
                context={
                    "conversation_history": self.conversation_history,
                    "user_profile": self.user_profile.dict(),
                    "collected_info": await self._format_collected_info()
                }
            )

            return response.content if hasattr(response, 'content') else str(response)

        except Exception as e:
            print(f"ADKエージェント処理エラー: {e}")
            return "もう少し詳しく教えていただけますか？"


    async def _extract_information(self, user_message: str) -> None:
        """ユーザーメッセージから情報を抽出"""
        print(f"🔍 情報抽出開始: {user_message}")

        try:
            # 直接Gemini APIを使用して情報抽出
            from google.generativeai import GenerativeModel
            model = GenerativeModel('gemini-2.5-pro')

            prompt = f"""
以下のユーザーメッセージから情報を抽出し、JSON形式で返してください：

ユーザーメッセージ: {user_message}

現在のプロファイル: {self.user_profile.dict()}

以下のフィールドから該当する情報を抽出してください：
- age: 年齢（数値）
- income_range: 収入範囲（文字列）
- lifestyle: ライフスタイル情報（辞書）
- family_structure: 家族構成（辞書）
- interests: 趣味・興味（配列）
- work_style: 仕事スタイル（文字列）
- location: 居住地（文字列）
- partner_info: パートナー情報（辞書）
- children_info: 子ども情報（配列）

抽出できた情報のみをJSON形式で返してください。例：
{{"age": 38, "income_range": "500万", "location": "足立区", "work_style": "エンジニア"}}
"""

            response = model.generate_content(prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)

            print(f"🤖 抽出レスポンス: {response_text}")

            # JSON形式で抽出された情報をパース
            try:
                # JSON部分を抽出
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    extracted_info = json.loads(json_str)
                    print(f"📝 抽出された情報: {extracted_info}")
                    await self._update_user_profile(extracted_info)
                else:
                    print("⚠️ JSON形式が見つかりません")
                    await self._manual_extract_information(user_message)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON解析エラー: {e}")
                await self._manual_extract_information(user_message)

        except Exception as e:
            print(f"❌ 情報抽出エラー: {e}")
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

    async def _check_completion_with_llm(self, user_message: str) -> bool:
        """LLMを使用して情報収集完了を判定"""
        try:
            print(f"🔍 LLM完了判定を実行中...")
            print(f"📝 ユーザーメッセージ: {user_message}")
            print(f"👤 現在のプロファイル: {await self._format_collected_info()}")

            # フォールバック: ADKエージェントではなく直接Gemini APIで判定
            from google.generativeai import GenerativeModel
            model = GenerativeModel('gemini-2.5-pro')
            prompt = f"""
以下の情報収集状況を確認してください：

現在のユーザープロファイル：
{await self._format_collected_info()}

ユーザーの最新メッセージ：
{user_message}

必要な情報が十分に収集されたかどうかを判断してください。
以下の条件を考慮してください：
- 年齢、収入、家族構成、パートナー情報、子ども情報、趣味、仕事、居住地
- 情報が不足していても、ユーザーが「もう十分」「これで十分」などと言っている場合は完了とする
- エージェントが「もう十分」と判断している場合は完了とする

完了の場合は「COMPLETED」、未完了の場合は「INCOMPLETE」で回答してください。
"""
            response = model.generate_content(prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)
            is_completed = "COMPLETED" in response_text.upper()

            print(f"🤖 LLM判定結果: {response_text}")
            print(f"✅ 完了判定: {is_completed}")

            return is_completed

        except Exception as e:
            print(f"❌ LLM完了判定エラー: {e}")
            return False


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

    async def _generate_hera_response(self, user_message: str) -> str:
        """ヘーラーエージェントの応答を生成"""
        try:
            from google.generativeai import GenerativeModel
            model = GenerativeModel('gemini-2.5-pro')

            prompt = f"""
あなたは{self.persona.name}（{self.persona.role}）です。

基本情報：
- 名前: {self.persona.name}
- 役割: {self.persona.role}
- 領域: {self.persona.domain}
- 象徴: {', '.join(self.persona.symbols)}
- 性格: {self.persona.personality}

現在のユーザープロファイル：
{await self._format_collected_info()}

会話履歴：
{self.conversation_history[-3:] if len(self.conversation_history) > 3 else self.conversation_history}

ユーザーの最新メッセージ：
{user_message}

あなたの役割：
1. 温かみのある、親しみやすい口調で応答する
2. 家族についての情報を自然な対話で収集する
3. 以下の情報を収集する：
   - 年齢、収入範囲、ライフスタイル、家族構成
   - パートナー情報、子ども情報、趣味・興味
   - 仕事スタイル、居住地

重要な指示：
- 必要な情報が十分に収集されたと判断したら、「もう十分」「これで十分」などと明確に表現してください
- 常に愛情深く、家族思いの神として振る舞ってください
- ユーザーの話を聞いて、適切な質問をしてください

ユーザーのメッセージに対して、{self.persona.name}として自然で温かい応答をしてください。
"""

            response = model.generate_content(prompt)
            return response.text if hasattr(response, 'text') else str(response)

        except Exception as e:
            print(f"❌ ヘーラー応答生成エラー: {e}")
            return "もう少し詳しく教えていただけますか？"

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
            print(f"⚠️ セッションIDが設定されていません: {self.current_session}")
            return

        print(f"💾 セッションデータを保存中... セッションID: {self.current_session}")

        # プロジェクトルート内のtmpディレクトリを使用
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        session_dir = os.path.join(project_root, "tmp", "user_sessions", self.current_session)
        os.makedirs(session_dir, exist_ok=True)

        print(f"📁 セッションディレクトリ: {session_dir}")

        # ユーザープロファイルを保存
        profile_data = self.user_profile.dict()
        print(f"👤 ユーザープロファイル: {profile_data}")

        with open(f"{session_dir}/user_profile.json", "w", encoding="utf-8") as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)

        # 会話履歴を保存
        print(f"💬 会話履歴数: {len(self.conversation_history)}")
        with open(f"{session_dir}/conversation_history.json", "w", encoding="utf-8") as f:
            json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)

        print(f"✅ セッションデータ保存完了: {session_dir}")


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

    # ADKの標準フローに対応するメソッドを追加
    async def run(self, message: str, session_id: str = None, **kwargs) -> str:
        """ADKの標準runメソッド"""
        print(f"🚀 ADK runメソッドが呼び出されました")
        print(f"📝 メッセージ: {message}")
        print(f"🆔 セッションID: {session_id}")

        # セッション開始（初回の場合）
        if not self.current_session and session_id:
            await self.start_session(session_id)

        # メッセージ処理
        result = await self.process_message(message)

        print(f"📤 レスポンス: {result.get('text_response', '')}")
        print(f"✅ 完了: {result.get('is_complete', False)}")

        return result.get('text_response', '')

    # ADKツール用のメソッド
    async def _extract_user_info_tool(self, user_message: str) -> str:
        """ユーザー情報抽出ツール"""
        print(f"🔍 情報抽出ツールが呼び出されました: {user_message}")

        try:
            # セッションIDが未設定なら生成
            if not self.current_session:
                import uuid
                self.current_session = str(uuid.uuid4())
                print(f"🆔 新規セッションID生成: {self.current_session}")

            # 会話履歴にユーザーメッセージを追加
            await self._add_to_history("user", user_message)

            # ユーザー情報を抽出
            await self._extract_information(user_message)

            # エージェントの応答を生成
            response = await self._generate_hera_response(user_message)

            # エージェントの応答を履歴に追加
            await self._add_to_history("hera", response)

            # セッションデータを保存
            await self._save_session_data()

            return response
        except Exception as e:
            print(f"❌ 情報抽出エラー: {e}")
            return f"申し訳ございません。エラーが発生しました: {str(e)}"

    async def _check_completion_tool(self, user_message: str) -> str:
        """セッション完了判定ツール"""
        print(f"🔍 完了判定ツールが呼び出されました: {user_message}")

        try:
            # LLMによる完了判定
            is_complete = await self._check_completion_with_llm(user_message)

            if is_complete:
                print("✅ セッション完了と判定されました")
                return "COMPLETED"
            else:
                print("⏳ セッション継続と判定されました")
                return "INCOMPLETE"

        except Exception as e:
            print(f"❌ 完了判定エラー: {e}")
            return f"完了判定中にエラーが発生しました: {str(e)}"

    async def _save_session_tool(self, session_id: str = "") -> str:
        """セッションデータ保存ツール"""
        print(f"💾 セッション保存ツールが呼び出されました: {session_id}")

        try:
            if session_id and session_id.strip():
                self.current_session = session_id

            # セッションデータを保存
            await self._save_session_data()

            return f"セッションデータを保存しました: {self.current_session}"
        except Exception as e:
            print(f"❌ セッション保存エラー: {e}")
            return f"セッション保存中にエラーが発生しました: {str(e)}"
