"""
ヘーラー（Hera）エージェント
家族愛の神として、自然な対話でユーザー情報を収集
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import openai
from dataclasses import dataclass, asdict


@dataclass
class UserProfile:
    """ユーザープロファイル"""
    age: Optional[int] = None
    income_range: Optional[str] = None
    lifestyle: Optional[Dict[str, Any]] = None
    family_structure: Optional[Dict[str, Any]] = None
    interests: Optional[List[str]] = None
    work_style: Optional[str] = None
    location: Optional[str] = None
    partner_info: Optional[Dict[str, Any]] = None
    children_info: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[str] = None


class HeraAgent:
    """ヘーラーエージェント - 家族愛の神"""

    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key

        # ヘーラーの人格設定
        self.persona = {
            "name": "ヘーラー",
            "role": "家族愛の神",
            "domain": "結婚、家庭、貞節、妻の守護",
            "roman_name": "ユノー（Juno）",
            "symbols": ["孔雀", "王冠", "ザクロ"],
            "personality": {
                "traits": ["愛情深い", "家族思い", "優しい", "知恵深い"],
                "speaking_style": "温かみのある、親しみやすい",
                "emotions": ["愛情", "慈愛", "家族への思い"]
            }
        }

        # 収集すべき情報のリスト
        self.required_info = [
            "age", "income_range", "lifestyle", "family_structure",
            "interests", "work_style", "location", "partner_info", "children_info"
        ]

        # 現在のセッション情報
        self.current_session = None
        self.user_profile = UserProfile()
        self.conversation_history = []

    def start_session(self, session_id: str) -> str:
        """セッション開始"""
        self.current_session = session_id
        self.user_profile = UserProfile()
        self.conversation_history = []

        # セッションディレクトリを作成
        self._create_session_directory()

        # ヘーラーの挨拶
        greeting = self._generate_greeting()
        self._add_to_history("hera", greeting)
        return greeting

    def process_message(self, user_message: str) -> str:
        """ユーザーメッセージを処理して応答を生成"""
        self._add_to_history("user", user_message)

        # 情報収集の進捗を確認
        progress = self._check_information_progress()

        # ヘーラーの応答を生成
        response = self._generate_response(user_message, progress)

        # 応答を履歴に追加
        self._add_to_history("hera", response)

        # ユーザー情報を更新
        self._extract_information(user_message)

        # セッション情報を保存
        self._save_session_data()

        return response

    def _generate_greeting(self) -> str:
        """ヘーラーの挨拶を生成"""
        greeting_prompt = f"""
あなたはヘーラー（Hera）、家族愛の神です。
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

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": greeting_prompt},
                {"role": "user", "content": "こんにちは"}
            ],
            max_tokens=200,
            temperature=0.7
        )

        return response.choices[0].message.content

    def _generate_response(self, user_message: str, progress: Dict[str, bool]) -> str:
        """ユーザーメッセージに対する応答を生成"""

        # 未収集の情報を特定
        missing_info = [key for key, collected in progress.items() if not collected]

        response_prompt = f"""
あなたはヘーラー（Hera）、家族愛の神です。
現在の会話履歴：
{self._format_conversation_history()}

収集済み情報：
{self._format_collected_info()}

未収集の情報：
{missing_info}

ユーザーの最新メッセージ：{user_message}

自然な対話で、まだ収集できていない情報について質問してください。
温かみのある、親しみやすい口調で応答してください。
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": response_prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )

        return response.choices[0].message.content

    def _extract_information(self, user_message: str) -> None:
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

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": extraction_prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )

        try:
            extracted_info = json.loads(response.choices[0].message.content)
            self._update_user_profile(extracted_info)
        except json.JSONDecodeError:
            # JSON解析エラーの場合は手動で情報を抽出
            self._manual_extract_information(user_message)

    def _update_user_profile(self, extracted_info: Dict[str, Any]) -> None:
        """ユーザープロファイルを更新"""
        for key, value in extracted_info.items():
            if hasattr(self.user_profile, key) and value is not None:
                setattr(self.user_profile, key, value)

        # 作成日時を設定
        if self.user_profile.created_at is None:
            self.user_profile.created_at = datetime.now().isoformat()

    def _manual_extract_information(self, user_message: str) -> None:
        """手動で情報を抽出（フォールバック）"""
        # 年齢の抽出
        import re
        age_match = re.search(r'(\d+)歳', user_message)
        if age_match and self.user_profile.age is None:
            self.user_profile.age = int(age_match.group(1))

        # その他の情報も同様に抽出
        # 実装は必要に応じて拡張

    def _check_information_progress(self) -> Dict[str, bool]:
        """情報収集の進捗を確認"""
        progress = {}
        for info_key in self.required_info:
            value = getattr(self.user_profile, info_key, None)
            progress[info_key] = value is not None
        return progress

    def _format_conversation_history(self) -> str:
        """会話履歴をフォーマット"""
        history_text = ""
        for entry in self.conversation_history[-10:]:  # 最新10件
            history_text += f"{entry['speaker']}: {entry['message']}\n"
        return history_text

    def _format_collected_info(self) -> str:
        """収集済み情報をフォーマット"""
        collected = []
        for key, value in asdict(self.user_profile).items():
            if value is not None and key != 'created_at':
                collected.append(f"{key}: {value}")
        return "\n".join(collected)

    def _add_to_history(self, speaker: str, message: str) -> None:
        """会話履歴に追加"""
        self.conversation_history.append({
            "speaker": speaker,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def _create_session_directory(self) -> None:
        """セッションディレクトリを作成"""
        session_dir = f"/tmp/user_sessions/{self.current_session}"
        os.makedirs(session_dir, exist_ok=True)
        os.makedirs(f"{session_dir}/generated_content", exist_ok=True)
        os.makedirs(f"{session_dir}/generated_content/stories", exist_ok=True)
        os.makedirs(f"{session_dir}/generated_content/images", exist_ok=True)
        os.makedirs(f"{session_dir}/generated_content/videos", exist_ok=True)

    def _save_session_data(self) -> None:
        """セッションデータを保存"""
        if not self.current_session:
            return

        session_dir = f"/tmp/user_sessions/{self.current_session}"

        # ユーザープロファイルを保存
        with open(f"{session_dir}/user_profile.json", "w", encoding="utf-8") as f:
            json.dump(asdict(self.user_profile), f, ensure_ascii=False, indent=2)

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

    def end_session(self) -> Dict[str, Any]:
        """セッション終了"""
        if not self.current_session:
            return {}

        # 最終データを保存
        self._save_session_data()

        # セッション情報を返す
        session_info = {
            "session_id": self.current_session,
            "user_profile": asdict(self.user_profile),
            "conversation_count": len(self.conversation_history),
            "information_complete": self.is_information_complete(),
            "session_dir": f"/tmp/user_sessions/{self.current_session}"
        }

        return session_info
