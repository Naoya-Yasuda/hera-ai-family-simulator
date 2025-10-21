"""
Google ADKベースのヘーラーエージェント
google.adk.agents.llm_agentを使用した正式なADKエージェント
"""

import json
import os
import asyncio
import re
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

    # パートナー関連（拡張）
    relationship_status: Optional[str] = Field(
        None,
        description="交際状況: 'married'(既婚), 'partnered'(交際中), 'single'(独身), 'other'(その他)"
    )
    current_partner: Optional[Dict[str, Any]] = Field(None, description="現在のパートナー情報（既婚/交際中）")
    ideal_partner: Optional[Dict[str, Any]] = Field(None, description="理想のパートナー像（独身）")
    partner_info: Optional[Dict[str, Any]] = Field(None, description="パートナー情報（後方互換性用）")
    partner_face_description: Optional[str] = Field(None, description="配偶者の顔の特徴の文章記述")

    # 性格特性（ビッグファイブ）
    user_personality_traits: Optional[Dict[str, float]] = Field(
        None,
        description="ユーザー自身の性格特性（ビッグファイブ: openness, conscientiousness, extraversion, agreeableness, neuroticism）"
    )

    # 子供関連
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
        # ADK WebサーバーのベースURL（Dev UIが動いているURL）
        self.adk_base_url = os.getenv("ADK_BASE_URL", "http://127.0.0.1:8000")

        # ヘーラーの人格設定
        self.persona = HeraPersona()

        # セッション管理
        self.current_session = None
        self.user_profile = UserProfile()
        self.conversation_history = []
        self.last_extracted_fields: Dict[str, Any] = {}

        # 情報収集の進捗（必須項目のみ）
        self.required_info = [
            "age",
            "relationship_status",
            "user_personality_traits",
            "children_info"
        ]

        # 推奨項目（収集推奨だが必須ではない）
        self.recommended_info = [
            "location",
            "income_range"
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
1. ユーザーから未来の家族を描くための**最小限の情報**を効率的に収集する
2. 温かみのある、親しみやすい口調で応答する
3. **3-4ターン以内**で情報収集を完了させる

【収集する情報（優先順位順）】

⭐⭐⭐ 必須項目（必ず聞く）:
1. 年齢と交際状況
2. パートナーの性格（既婚/交際中なら実際、独身なら理想）
3. ユーザー自身の性格
4. 子供の希望（人数・性別）

⭐⭐ 推奨項目（できれば聞く）:
5. 居住地
6. 収入範囲

⭐ オプション（余裕があれば）:
7. 趣味・興味

【質問の仕方（重要）】
❌ ダメな例: 1つずつ順番に聞く
  「年齢を教えてください」→「次に性別を...」→「収入は...」

✅ 良い例: 関連する情報をまとめて聞く
  「まず、年齢と現在パートナーがいらっしゃるか、お住まいの地域を教えていただけますか？」

【効率的な質問フロー例】

ターン1（基本情報まとめて）:
「まず、あなたのことを教えてください。年齢、現在のパートナーの有無（既婚/交際中/独身）、お住まいの地域を教えていただけますか？」

ターン2（性格まとめて）:
【既婚/交際中】
「パートナーの方の性格とご自身の性格を教えてください。明るい、冷静、優しい、几帳面、社交的、内向的など、どんな言葉でも構いません」

【独身】
「理想のパートナーの性格とご自身の性格を、それぞれ教えてください」

ターン3（子供の希望）:
「お子さんは何人くらい希望されますか？性別の希望があれば教えてください」

→ これで完了！

【厳守事項】
- 1つの質問で複数項目をまとめて聞くこと
- 不要な情報（趣味、仕事、ライフスタイル詳細など）は基本的に聞かない
- 子供の性格は親の情報から自動計算されるため、絶対に聞かない
- 3-4ターンで情報収集を終えることを目指す
- ユーザーが自発的に話した情報は受け入れるが、こちらから細かく聞き出さない
- 必要な情報が揃ったら「ありがとうございます。十分な情報が揃いました」と明確に伝える
- 常に愛情深く、家族思いの神として振る舞う

利用方針（厳守）：
- 必ず最初にextract_user_infoを呼び出すこと
- ツール実行前に通常のテキスト応答を出力してはならない
- extract_user_infoのfunction_callを出力した場合は、その直後に必ず最終テキストメッセージを返し、ツールから受け取った文字列をそのまま提示すること
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

    def _wrap_response(self, message: Optional[str]) -> Dict[str, str]:
        """UI/APIで扱いやすい共通形式に整形"""
        text = (message or "").strip()
        if not text:
            text = "お話を伺いました。続きもぜひ教えてください。"
        return {
            "speaker": self.persona.name,
            "message": text,
        }

    def _wrap_response_json(self, message: Optional[str]) -> str:
        return json.dumps(self._wrap_response(message), ensure_ascii=False)


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


    async def _generate_adk_response(self, user_message: str, progress: Dict[str, bool]) -> Dict[str, str]:
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

            raw_text = response.content if hasattr(response, 'content') else str(response)
            return self._wrap_response(raw_text)

        except Exception as e:
            print(f"ADKエージェント処理エラー: {e}")
            return self._wrap_response("もう少し詳しく教えていただけますか？")


    async def _extract_information(self, user_message: str) -> Dict[str, Any]:
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

【必須項目】
- age: 年齢（数値）
- location: 居住地（文字列）※できれば

【パートナー関連】
- relationship_status: 交際状況（"married", "partnered", "single", "other"）

- current_partner: 現在のパートナー情報（既婚/交際中の場合）
  {{
    "name": "名前",
    "age": 年齢,
    "personality_traits": {{
      "openness": 0.0-1.0,        # 好奇心旺盛さ（新しいこと好き）
      "conscientiousness": 0.0-1.0, # 几帳面さ（計画的）
      "extraversion": 0.0-1.0,     # 社交性（明るい・活発）
      "agreeableness": 0.0-1.0,    # 優しさ（思いやり）
      "neuroticism": 0.0-1.0       # 心配性さ（慎重）
    }},
    "temperament": "性格の総合的な説明",
    "hobbies": ["趣味1", "趣味2"],
    "speaking_style": "話し方の特徴"
  }}

- ideal_partner: 理想のパートナー像（独身の場合）
  # 同様の構造

- user_personality_traits: ユーザー自身の性格特性
  {{
    "openness": 0.0-1.0,
    "conscientiousness": 0.0-1.0,
    "extraversion": 0.0-1.0,
    "agreeableness": 0.0-1.0,
    "neuroticism": 0.0-1.0
  }}

【子供関連】
- children_info: 子供の希望情報（配列）
  [{{
    "desired_gender": "男/女",
    "age": 希望年齢
  }}]
  ※性格は親の情報から自動計算されるため、性格情報は含めない

【性格特性の推定ルール】
会話から以下のキーワードで0.0-1.0の値を推定:
- 「明るい」「社交的」「外向的」「活発」 → extraversion: 0.7-0.8
- 「几帳面」「計画的」「責任感」「しっかり」 → conscientiousness: 0.7-0.8
- 「優しい」「思いやり」「協力的」 → agreeableness: 0.7-0.8
- 「好奇心旺盛」「創造的」「新しいこと好き」 → openness: 0.7-0.8
- 「落ち着いている」「楽観的」 → neuroticism: 0.2-0.3
- 「心配性」「慎重」「不安」 → neuroticism: 0.7-0.8
- 「内向的」「静か」 → extraversion: 0.2-0.3
- キーワードがない場合 → 0.5（中立）

重要:
- 抽出できた情報のみをJSON形式で返す
- 不要な情報（趣味、仕事、ライフスタイルなど）は抽出しない
- 性格特性は必ず0.0-1.0の数値で推定する

例：
{{"age": 32, "location": "東京", "relationship_status": "married", "current_partner": {{"personality_traits": {{"extraversion": 0.7, "agreeableness": 0.8, "conscientiousness": 0.6, "openness": 0.5, "neuroticism": 0.4}}, "temperament": "優しく几帳面"}}, "user_personality_traits": {{"extraversion": 0.5, "conscientiousness": 0.7, "agreeableness": 0.8, "openness": 0.6, "neuroticism": 0.4}}, "children_info": [{{"desired_gender": "女", "age": 5}}]}}
"""

            response = model.generate_content(prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)

            print(f"🤖 抽出レスポンス: {response_text}")

            # JSON形式で抽出された情報をパース
            extracted_info: Dict[str, Any] = {}
            try:
                # JSON部分を抽出
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    extracted_info = json.loads(json_str)
                    print(f"📝 抽出された情報: {extracted_info}")
                    await self._update_user_profile(extracted_info)
                else:
                    print("⚠️ JSON形式が見つかりません")
            except json.JSONDecodeError as e:
                # 手動抽出は行わず、次発話でのLLM抽出に委ねる
                print(f"⚠️ JSON解析エラー（手動抽出はスキップ）: {e}")

            self.last_extracted_fields = extracted_info
            return extracted_info

        except Exception as e:
            print(f"❌ 情報抽出エラー（手動抽出はスキップ）: {e}")
            return {}

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
            progress[info_key] = not self._is_value_missing(value)
        return progress

    def _is_value_missing(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        return False

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

【必須項目】（これらが揃えば完了）:
- 年齢
- 交際状況（relationship_status）
- パートナーまたは理想のパートナーの性格特性（personality_traits）
- ユーザー自身の性格特性（user_personality_traits）
- 子供の希望（children_info: 人数と性別）

【判定基準】:
1. 上記5項目が全て揃っている → COMPLETED
2. ユーザーが「もう十分」「これで十分」などと言っている → COMPLETED
3. エージェントが「十分な情報が揃いました」と言っている → COMPLETED
4. それ以外 → INCOMPLETE

※居住地や収入は任意項目のため、なくても完了とする

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
2. **3-4ターン以内**で必要最小限の情報を効率的に収集する
3. 必須情報のみ収集する：
   - 年齢と交際状況
   - パートナーの性格とユーザー自身の性格
   - 子供の希望（人数・性別）
   - （できれば）居住地

重要な指示：
- **1つの質問で複数項目をまとめて聞く**こと（例: 「年齢、パートナーの有無、居住地を教えてください」）
- 不要な情報（趣味、仕事、ライフスタイル詳細）は基本的に聞かない
- ユーザーが自発的に話した情報は受け入れるが、こちらから細かく聞き出さない
- 必要な情報が揃ったら「ありがとうございます。十分な情報が揃いました」と明確に伝える
- 常に愛情深く、家族思いの神として振る舞う

ユーザーのメッセージに対して、{self.persona.name}として自然で温かく、かつ**効率的な**応答をしてください。
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
        payload_raw = await self._extract_user_info_tool(message)

        if isinstance(payload_raw, dict):
            payload = payload_raw
            payload_json = json.dumps(payload, ensure_ascii=False)
        else:
            try:
                payload = json.loads(payload_raw)
                payload_json = payload_raw
            except Exception:
                payload = self._wrap_response(None)
                payload_json = json.dumps(payload, ensure_ascii=False)

        print(f"📤 レスポンス: {payload}")

        return payload_json

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
            response_text = await self._generate_hera_response(user_message)
            payload = self._wrap_response(response_text)

            # エージェントの応答を履歴に追加
            await self._add_to_history("hera", payload["message"])
            # 会話履歴のみ即時保存
            await self._save_conversation_history()

            # 毎ターンの保存は行わず、メモリにのみ保持
            return json.dumps(payload, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 情報抽出エラー: {e}")
            return json.dumps(
                self._wrap_response(f"申し訳ございません。エラーが発生しました: {str(e)}"),
                ensure_ascii=False,
            )

    async def _extract_missing_information(self, user_message: str, missing_fields: List[str]) -> Dict[str, Any]:
        """不足しているフィールドのみ抽出"""
        if not missing_fields:
            return {}

        print(f"🔍 不足項目の抽出を実行: {missing_fields}")

        try:
            from google.generativeai import GenerativeModel
            model = GenerativeModel('gemini-2.5-pro')

            prompt = f"""
以下の不足しているフィールドのみをJSON形式で抽出してください。存在しない場合はフィールドを含めないでください。

不足フィールド: {missing_fields}
ユーザーメッセージ: {user_message}
現在のプロファイル: {self.user_profile.dict()}
"""

            response = model.generate_content(prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)
            print(f"🤖 不足フィールド抽出レスポンス: {response_text}")

            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                print("⚠️ 不足項目抽出: JSON形式が見つかりません")
                return {}

            info = json.loads(json_match.group(0))
            if info:
                await self._update_user_profile(info)
                self.last_extracted_fields = info
            return info

        except Exception as e:
            print(f"❌ 不足項目抽出エラー: {e}")
            return {}

    async def _check_completion_tool(self, user_message: str) -> str:
        """セッション完了判定ツール"""
        print(f"🔍 完了判定ツールが呼び出されました: {user_message}")

        try:
            # 会話履歴にユーザーメッセージを追加（完了判定経路でも欠落させない）
            await self._add_to_history("user", user_message)
            # 履歴のみ即時保存
            await self._save_conversation_history()

            missing_fields = [
                key for key in self.required_info
                if self._is_value_missing(getattr(self.user_profile, key, None))
            ]
            await self._extract_missing_information(user_message, missing_fields)

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
