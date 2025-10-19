"""
Google ADKベースのヘーラーエージェント
google.adk.agents.llm_agentを使用した正式なADKエージェント
"""

import json
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum

# Google ADK imports
from google.adk.agents import llm_agent
from google.adk.agents import base_agent
from google.adk.agents import conversation
from google.adk.agents import memory
from google.adk.agents import tools

# Google Cloud imports
from google.cloud import aiplatform
from google.cloud import discoveryengine
from google.cloud import dialogflow
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate

# Gemini integration
import google.generativeai as genai

# Pydantic for data validation
from pydantic import BaseModel, Field


class ConversationState(Enum):
    """会話の状態"""
    GREETING = "greeting"
    INFORMATION_COLLECTION = "information_collection"
    FAMILY_GENERATION = "family_generation"
    COMPLETED = "completed"


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
    roman_name: str = "ユノー（Juno）"
    symbols: List[str] = ["孔雀", "王冠", "ザクロ"]
    personality: Dict[str, Any] = {
        "traits": ["愛情深い", "家族思い", "優しい", "知恵深い"],
        "speaking_style": "温かみのある、親しみやすい",
        "emotions": ["愛情", "慈愛", "家族への思い"]
    }


class ADKHeraAgent(llm_agent.LLMAgent):
    """Google ADKベースのヘーラーエージェント"""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        gemini_api_key: str = None,
        **kwargs
    ):
        self.project_id = project_id
        self.location = location
        self.gemini_api_key = gemini_api_key

        # Google Cloud クライアントの初期化
        self._initialize_google_clients()

        # ヘーラーの人格設定
        self.persona = HeraPersona()

        # セッション管理
        self.current_session = None
        self.user_profile = UserProfile()
        self.conversation_state = ConversationState.GREETING
        self.conversation_history = []

        # 情報収集の進捗
        self.required_info = [
            "age", "income_range", "lifestyle", "family_structure",
            "interests", "work_style", "location", "partner_info", "children_info"
        ]

        # ADKエージェントの初期化
        super().__init__(
            name="hera_agent",
            description="家族愛の神ヘーラーエージェント",
            llm_model="gemini-pro",
            **kwargs
        )

    def _initialize_google_clients(self):
        """Google Cloud クライアントを初期化"""
        try:
            # AI Platform
            aiplatform.init(project=self.project_id, location=self.location)

            # Discovery Engine（検索・推奨）
            self.discovery_client = discoveryengine.DocumentServiceClient()

            # Dialogflow（対話管理）
            self.dialogflow_client = dialogflow.SessionsClient()

            # Speech-to-Text
            self.speech_client = speech.SpeechClient()

            # Text-to-Speech
            self.tts_client = texttospeech.TextToSpeechClient()

            # Translation
            self.translate_client = translate.TranslationServiceClient()

            # Gemini
            if self.gemini_api_key:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')

        except Exception as e:
            print(f"Google Cloud クライアントの初期化に失敗: {e}")

    async def start_session(self, session_id: str) -> str:
        """セッション開始"""
        self.current_session = session_id
        self.user_profile = UserProfile()
        self.conversation_state = ConversationState.GREETING
        self.conversation_history = []

        # セッションディレクトリを作成
        await self._create_session_directory()

        # ヘーラーの挨拶を生成
        greeting = await self._generate_greeting()
        await self._add_to_history("hera", greeting)

        return greeting

    async def process_message(
        self,
        user_message: str,
        audio_data: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """ユーザーメッセージを処理"""

        # 音声データがある場合はテキストに変換
        if audio_data:
            user_message = await self._speech_to_text(audio_data)

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

        # セッションデータを保存
        await self._save_session_data()

        # 音声応答を生成（オプション）
        audio_response = None
        if audio_data:  # 音声入力があった場合のみ音声応答を生成
            audio_response = await self._text_to_speech(response)

        return {
            "text_response": response,
            "audio_response": audio_response,
            "conversation_state": self.conversation_state.value,
            "information_progress": progress,
            "is_complete": self.is_information_complete()
        }

    async def _generate_adk_response(self, user_message: str, progress: Dict[str, bool]) -> str:
        """ADKエージェントを使用して応答を生成"""

        # 未収集の情報を特定
        missing_info = [key for key, collected in progress.items() if not collected]

        # システムプロンプトを構築
        system_prompt = f"""
あなたは{self.persona.name}（{self.persona.role}）です。

基本情報：
- 名前: {self.persona.name}
- 役割: {self.persona.role}
- 領域: {self.persona.domain}
- ローマ名: {self.persona.roman_name}
- 象徴: {', '.join(self.persona.symbols)}
- 性格: {self.persona.personality}

現在の会話履歴：
{await self._format_conversation_history()}

収集済み情報：
{await self._format_collected_info()}

未収集の情報：
{missing_info}

ユーザーの最新メッセージ：{user_message}

自然な対話で、まだ収集できていない情報について質問してください。
温かみのある、親しみやすい口調で応答してください。
"""

        try:
            # ADKエージェントのprocessメソッドを使用
            response = await self.process(
                message=user_message,
                system_prompt=system_prompt,
                context={
                    "conversation_history": self.conversation_history,
                    "user_profile": self.user_profile.dict(),
                    "missing_info": missing_info
                }
            )

            return response.content if hasattr(response, 'content') else str(response)

        except Exception as e:
            print(f"ADKエージェント処理エラー: {e}")
            return "もう少し詳しく教えていただけますか？"

    async def _generate_greeting(self) -> str:
        """ヘーラーの挨拶を生成"""
        greeting_prompt = f"""
あなたは{self.persona.name}（{self.persona.role}）です。

基本情報：
- 名前: {self.persona.name}
- 役割: {self.persona.role}
- 領域: {self.persona.domain}
- ローマ名: {self.persona.roman_name}
- 象徴: {', '.join(self.persona.symbols)}
- 性格: {self.persona.personality}

ユーザーから家族についての情報を自然な対話で収集する必要があります。

以下の情報を収集してください：
- 年齢
- 収入（ざっくりレンジでOK）
- ライフスタイル（都会／地方、趣味、仕事のスタイルなど）
- 家族構成
- パートナー情報
- 子ども情報（いる場合）

温かみのある、親しみやすい口調で挨拶してください。
"""

        try:
            # ADKエージェントを使用して挨拶を生成
            response = await self.process(
                message="こんにちは",
                system_prompt=greeting_prompt
            )

            return response.content if hasattr(response, 'content') else str(response)

        except Exception as e:
            return f"こんにちは！私は{self.persona.name}です。家族についてお話ししましょう。"

    async def _extract_information(self, user_message: str) -> None:
        """ユーザーメッセージから情報を抽出"""

        extraction_prompt = f"""
以下のユーザーメッセージから、ユーザー情報を抽出してください：
{user_message}

抽出すべき情報：
- age: 年齢（数値）
- income_range: 収入範囲（文字列）
- lifestyle: ライフスタイル（辞書形式）
- family_structure: 家族構成（辞書形式）
- interests: 趣味・興味（リスト）
- work_style: 仕事スタイル（文字列）
- location: 居住地（文字列）
- partner_info: パートナー情報（辞書形式）
- children_info: 子ども情報（リスト）

JSON形式で抽出結果を返してください。
情報が不明な場合はnullを設定してください。
"""

        try:
            # ADKエージェントを使用して情報抽出
            response = await self.process(
                message=user_message,
                system_prompt=extraction_prompt
            )

            extracted_info = json.loads(response.content if hasattr(response, 'content') else str(response))
            await self._update_user_profile(extracted_info)

        except (json.JSONDecodeError, Exception) as e:
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

    async def _format_conversation_history(self) -> str:
        """会話履歴をフォーマット"""
        history_text = ""
        for entry in self.conversation_history[-10:]:  # 最新10件
            history_text += f"{entry['speaker']}: {entry['message']}\n"
        return history_text

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

    async def _create_session_directory(self) -> None:
        """セッションディレクトリを作成"""
        session_dir = f"/tmp/user_sessions/{self.current_session}"
        os.makedirs(session_dir, exist_ok=True)
        os.makedirs(f"{session_dir}/generated_content", exist_ok=True)
        os.makedirs(f"{session_dir}/generated_content/stories", exist_ok=True)
        os.makedirs(f"{session_dir}/generated_content/images", exist_ok=True)
        os.makedirs(f"{session_dir}/generated_content/videos", exist_ok=True)

    async def _save_session_data(self) -> None:
        """セッションデータを保存"""
        if not self.current_session:
            return

        session_dir = f"/tmp/user_sessions/{self.current_session}"

        # ユーザープロファイルを保存
        with open(f"{session_dir}/user_profile.json", "w", encoding="utf-8") as f:
            json.dump(self.user_profile.dict(), f, ensure_ascii=False, indent=2)

        # 会話履歴を保存
        with open(f"{session_dir}/conversation_history.json", "w", encoding="utf-8") as f:
            json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)

    async def _speech_to_text(self, audio_data: bytes) -> str:
        """音声をテキストに変換"""
        try:
            audio = speech.RecognitionAudio(content=audio_data)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="ja-JP"
            )

            response = self.speech_client.recognize(config=config, audio=audio)

            if response.results:
                return response.results[0].alternatives[0].transcript
            else:
                return ""
        except Exception as e:
            print(f"音声認識エラー: {e}")
            return ""

    async def _text_to_speech(self, text: str) -> bytes:
        """テキストを音声に変換"""
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="ja-JP",
                name="ja-JP-Wavenet-A"
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            return response.audio_content
        except Exception as e:
            print(f"音声合成エラー: {e}")
            return b""

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
        session_info = {
            "session_id": self.current_session,
            "user_profile": self.user_profile.dict(),
            "conversation_count": len(self.conversation_history),
            "information_complete": self.is_information_complete(),
            "session_dir": f"/tmp/user_sessions/{self.current_session}"
        }

        return session_info
