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
    gender: Optional[str] = Field(None, description="性別")
    income_range: Optional[str] = Field(None, description="収入範囲")
    lifestyle: Optional[Dict[str, Any]] = Field(None, description="ライフスタイル情報")
    family_structure: Optional[Dict[str, Any]] = Field(None, description="家族構成")
    interests: Optional[List[str]] = Field(None, description="趣味・興味")
    work_style: Optional[str] = Field(None, description="現在の仕事スタイル")
    future_career: Optional[str] = Field(None, description="将来の仕事・キャリア")
    location: Optional[str] = Field(None, description="居住地")
    partner_info: Optional[Dict[str, Any]] = Field(None, description="パートナー情報")
    children_info: Optional[List[Dict[str, Any]]] = Field(None, description="子ども情報")
    user_photos: List[str] = Field(default_factory=list, description="ユーザーの写真パス（必須）")
    partner_photos: Optional[List[str]] = Field(None, description="配偶者の写真パス")
    partner_face_description: Optional[str] = Field(None, description="配偶者の顔の方向性・特徴の文章記述（写真がない場合必須）")
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
        # ADK WebサーバーのベースURL（Dev UIが動いているURL）
        self.adk_base_url = os.getenv("ADK_BASE_URL", "http://127.0.0.1:8000")

        # ヘーラーの人格設定
        self.persona = HeraPersona()

        # セッション管理
        self.current_session = None
        self.user_profile = UserProfile()
        self.conversation_history = []

        # 情報収集の進捗
        self.required_info = [
            "age", "gender", "income_range", "lifestyle", "family_structure",
            "interests", "work_style", "future_career", "location",
            "partner_info", "children_info", "user_photos", "partner_photos", "partner_face_description"
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
   - 年齢、性別
   - 収入範囲、ライフスタイル
   - 家族構成、パートナー情報、子ども情報
   - 趣味・興味、現在の仕事スタイル、将来のキャリア
   - 居住地
   - ユーザーの写真（必須）
   - 配偶者の写真または顔の特徴の文章記述（どちらか必須）

重要な指示：
- ユーザーの写真は必須です。提供されない場合は明確に要求してください
- 配偶者の写真が提供できない場合は、顔の方向性や特徴を文章で記述してもらってください
- 将来のキャリアについては、現在の仕事と区別して聞いてください
- 必要な情報が十分に収集されたと判断したら、「もう十分」「これで十分」などと明確に表現してください
- 常に愛情深く、家族思いの神として振る舞ってください

利用方針（厳守）：
- 必ず最初にextract_user_infoを呼び出し、ツールの戻り値をそのまま最終応答として返すこと
- ツール実行前に通常のテキスト応答を出力してはならない
- check_session_completionは必要時のみ呼び出す

利用可能なツール：
- extract_user_info: ユーザー情報を抽出・保存（最初に必ず呼ぶ／戻り値=最終応答）
- check_session_completion: 情報収集完了を判定

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

        # セッションデータ保存ツールは削除（_extract_user_info_toolで既に保存済み）

        return tools


    async def start_session(self, session_id: str) -> str:
        """セッション開始"""
        self.current_session = session_id
        self.user_profile = UserProfile()
        self.conversation_history = []

        # セッション用ディレクトリを事前に作成
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        session_dir = os.path.join(project_root, "tmp", "user_sessions", session_id)
        photos_dir = os.path.join(session_dir, "photos")

        # ディレクトリが存在しない場合のみ作成
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
            os.makedirs(photos_dir)
            print(f"📁 セッションディレクトリを作成しました: {session_dir}")

        # 初手の通常挨拶は表示順の混乱を避けるため無効化
        return ""


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
- gender: 性別（文字列: "男性", "女性", "その他"）
- income_range: 収入範囲（文字列）
- lifestyle: ライフスタイル情報（辞書）
- family_structure: 家族構成（辞書）
- interests: 趣味・興味（配列）
- work_style: 現在の仕事スタイル（文字列）
- future_career: 将来の仕事・キャリア（文字列）
- location: 居住地（文字列）
- partner_info: パートナー情報（辞書）
- children_info: 子ども情報（配列）
- user_photos: ユーザーの写真パス（配列、必須）
- partner_photos: 配偶者の写真パス（配列）
- partner_face_description: 配偶者の顔の方向性・特徴の文章記述（写真がない場合必須）

抽出できた情報のみをJSON形式で返してください。例：
{{"age": 38, "gender": "男性", "income_range": "500万", "location": "足立区", "work_style": "エンジニア", "future_career": "フリーランス"}}
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
                # 手動抽出は行わず、次発話でのLLM抽出に委ねる
                print(f"⚠️ JSON解析エラー（手動抽出はスキップ）: {e}")

        except Exception as e:
            print(f"❌ 情報抽出エラー（手動抽出はスキップ）: {e}")

    async def _update_user_profile(self, extracted_info: Dict[str, Any]) -> None:
        """ユーザープロファイルを更新"""
        for key, value in extracted_info.items():
            if hasattr(self.user_profile, key) and value is not None:
                setattr(self.user_profile, key, value)

        # 作成日時を設定
        if self.user_profile.created_at is None:
            self.user_profile.created_at = datetime.now().isoformat()


    def _check_information_progress(self) -> Dict[str, bool]:
        """情報収集の進捗を確認"""
        progress = {}
        for info_key in self.required_info:
            value = getattr(self.user_profile, info_key, None)
            if info_key == "user_photos":
                # ユーザーの写真は必須（空のリストは不可）
                progress[info_key] = value is not None and len(value) > 0
            elif info_key in ["partner_photos", "partner_face_description"]:
                # 配偶者の写真または顔の特徴の文章記述のどちらかが必須
                partner_photos = getattr(self.user_profile, "partner_photos", None)
                partner_face_description = getattr(self.user_profile, "partner_face_description", None)
                progress[info_key] = (partner_photos is not None and len(partner_photos) > 0) or (partner_face_description is not None and partner_face_description.strip() != "")
            else:
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
- ユーザーの写真（必須）
- 配偶者の写真または顔の特徴の文章記述（どちらか必須）
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
   - ユーザーの写真（必須）
   - 配偶者の写真または顔の特徴の文章記述（どちらか必須）

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


    async def _get_latest_adk_session_id(self, retries: int = 3, timeout_sec: float = 10.0) -> Optional[str]:
        """ADKの最新セッションIDを取得（リトライ付）"""
        try:
            import httpx
            last_err = None
            for attempt in range(1, retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=timeout_sec) as client:
                        r = await client.get(f"{self.adk_base_url}/apps/agents/users/user/sessions")
                        if r.status_code == 200:
                            data = r.json()
                            print(f"🔍 ADKセッション一覧(try {attempt}/{retries}): {data}")
                            if isinstance(data, list) and data:
                                # lastUpdateTimeがあれば最新順に
                                try:
                                    data_sorted = sorted(
                                        data,
                                        key=lambda x: x.get("lastUpdateTime", 0),
                                        reverse=True
                                    )
                                except Exception:
                                    data_sorted = data
                                first = data_sorted[0]
                                if isinstance(first, dict):
                                    sid = first.get("session_id") or first.get("id")
                                    if sid:
                                        return sid
                except Exception as e:
                    last_err = e
                    print(f"⚠️ ADKセッションID取得エラー(try {attempt}/{retries}): {e}")
                    # 簡易バックオフ
                    import asyncio as _asyncio
                    await _asyncio.sleep(min(1.5 * attempt, 5))

            print(f"❌ ADKセッションIDの取得に失敗: {last_err}")
            return None
        except Exception as e:
            print(f"❌ ADKセッションID取得処理エラー: {e}")
            return None


    async def _save_session_data(self) -> None:
        """セッションデータを保存"""
        if not self.current_session:
            print(f"⚠️ セッションIDが設定されていません: {self.current_session}")
            return

        print(f"💾 セッションデータを保存中... セッションID: {self.current_session}")

        # プロジェクトルート内のtmpディレクトリを使用（事前に作成済みを想定）
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        session_dir = os.path.join(project_root, "tmp", "user_sessions", self.current_session)

        # ディレクトリの存在確認のみ（start_sessionで作成済み）
        if not os.path.exists(session_dir):
            print(f"⚠️ セッションディレクトリが存在しません: {session_dir}")
            return

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


    async def _save_conversation_history(self) -> None:
        """会話履歴のみを保存（毎ターン呼び出し）"""
        if not self.current_session:
            print("⚠️ セッションID未設定のため履歴保存をスキップ")
            return

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        session_dir = os.path.join(project_root, "tmp", "user_sessions", self.current_session)
        if not os.path.exists(session_dir):
            print(f"⚠️ セッションディレクトリが存在しません: {session_dir}")
            return

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

    # ADKの標準フローに対応するメソッドを追加
    async def run(self, message: str, session_id: str = None, **kwargs) -> str:
        """ADKの標準runメソッド"""
        print(f"🚀 ADK runメソッドが呼び出されました")
        print(f"📝 メッセージ: {message}")
        print(f"🆔 セッションID: {session_id}")

        # ADK既存セッションIDのみを使用
        resolved_session_id = None
        if session_id and session_id.strip():
            resolved_session_id = session_id.strip()
        else:
            try:
                import httpx
                with httpx.Client(timeout=5) as client:
                    r = client.get(f"{self.adk_base_url}/apps/agents/users/user/sessions")
                    if r.status_code == 200 and isinstance(r.json(), list) and r.json():
                        data = r.json()
                        # lastUpdateTimeがあれば最新順に
                        try:
                            data_sorted = sorted(
                                data,
                                key=lambda x: x.get("lastUpdateTime", 0),
                                reverse=True
                            )
                        except Exception:
                            data_sorted = data
                        first = data_sorted[0]
                        if isinstance(first, dict):
                            resolved_session_id = first.get("session_id") or first.get("id")
            except Exception as e:
                print(f"⚠️ ADKセッションID取得エラー(run): {e}")

        if not resolved_session_id:
            print("❌ ADKセッションIDが取得できません")
            return "セッションIDが取得できませんでした"

        # UIのセッションIDに常時同期（異なる場合は更新）
        if self.current_session != resolved_session_id:
            self.current_session = resolved_session_id
            # ディレクトリ未作成時のみ開始処理
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            session_dir = os.path.join(project_root, "tmp", "user_sessions", self.current_session)
            if not os.path.exists(session_dir):
                await self.start_session(self.current_session)

        # ツールを直接呼び出して応答を生成（標準フロー無効化のため）
        response = await self._extract_user_info_tool(message)

        print(f"📤 レスポンス: {response}")

        return response

    # ADKツール用のメソッド
    async def _extract_user_info_tool(self, user_message: str) -> str:
        """ユーザー情報抽出ツール"""
        print(f"🔍 情報抽出ツールが呼び出されました: {user_message}")

        try:
            # runで設定されていない場合はフォールバックで最新セッションIDを取得
            if not self.current_session:
                latest_sid = await self._get_latest_adk_session_id(retries=3, timeout_sec=10.0)
                if not latest_sid:
                    print("❌ ADKセッションIDが取得できません（ツール側フォールバック）")
                    return "セッションIDが取得できませんでした"
                self.current_session = latest_sid
                print(f"🆔 ツール側でセッションID設定: {self.current_session}")

            # セッション開始（ディレクトリ未作成時）
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            session_dir = os.path.join(project_root, "tmp", "user_sessions", self.current_session)
            if not os.path.exists(session_dir):
                await self.start_session(self.current_session)

            # 会話履歴にユーザーメッセージを追加
            await self._add_to_history("user", user_message)
            # 会話履歴のみ即時保存
            await self._save_conversation_history()

            # ユーザー情報を抽出
            await self._extract_information(user_message)

            # エージェントの応答を生成
            response = await self._generate_hera_response(user_message)
            # エージェントの応答を履歴に追加
            await self._add_to_history("hera", response)
            # 会話履歴のみ即時保存
            await self._save_conversation_history()

            # 毎ターンの保存は行わず、メモリにのみ保持
            return response
        except Exception as e:
            print(f"❌ 情報抽出エラー: {e}")
            return f"申し訳ございません。エラーが発生しました: {str(e)}"

    async def _check_completion_tool(self, user_message: str) -> str:
        """セッション完了判定ツール"""
        print(f"🔍 完了判定ツールが呼び出されました: {user_message}")

        try:
            # セッションIDのフォールバック（runを経由しない呼出し対策）
            if not self.current_session:
                latest_sid = await self._get_latest_adk_session_id(retries=3, timeout_sec=10.0)
                if not latest_sid:
                    print("❌ ADKセッションIDが取得できません（完了判定フォールバック）")
                    return "INCOMPLETE"
                self.current_session = latest_sid
                print(f"🆔 完了判定側でセッションID設定: {self.current_session}")
                # ディレクトリ未作成時のみ開始
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                session_dir = os.path.join(project_root, "tmp", "user_sessions", self.current_session)
                if not os.path.exists(session_dir):
                    await self.start_session(self.current_session)

            # LLMによる完了判定
            is_complete = await self._check_completion_with_llm(user_message)

            if is_complete:
                print("✅ セッション完了と判定されました")
                # 完了時のみディスク保存（プロフィール・履歴）
                await self._save_session_data()
                return "COMPLETED"
            else:
                print("⏳ セッション継続と判定されました")
                return "INCOMPLETE"

        except Exception as e:
            print(f"❌ 完了判定エラー: {e}")
            return f"完了判定中にエラーが発生しました: {str(e)}"


    async def _handle_photo_upload(self, photo_data: bytes, photo_type: str = "user") -> str:
        """写真アップロード処理"""
        try:
            # セッションIDが未設定ならスキップ（ADKのIDのみ使用）
            if not self.current_session:
                print("⚠️ セッションID未設定のため写真保存をスキップ")
                return None

            # 写真保存ディレクトリ（事前に作成済みを想定）
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            photos_dir = os.path.join(project_root, "tmp", "user_sessions", self.current_session, "photos")

            # ディレクトリの存在確認のみ
            if not os.path.exists(photos_dir):
                print(f"⚠️ 写真ディレクトリが存在しません: {photos_dir}")
                return None

            # ファイル名を生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{photo_type}_{timestamp}.jpg"
            filepath = os.path.join(photos_dir, filename)

            # 写真を保存
            with open(filepath, "wb") as f:
                f.write(photo_data)

            # プロファイルに写真パスを追加
            if photo_type == "user":
                if not self.user_profile.user_photos:
                    self.user_profile.user_photos = []
                self.user_profile.user_photos.append(filepath)
            elif photo_type == "partner":
                if not self.user_profile.partner_photos:
                    self.user_profile.partner_photos = []
                self.user_profile.partner_photos.append(filepath)

            return filepath

        except Exception as e:
            print(f"❌ 写真アップロードエラー: {e}")
            return None
