"""
同時対話システム
複数の家族メンバーエージェントが同時に会話に参加し、幸せなひとときを定義
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import openai
from dataclasses import dataclass, asdict
from family_agent import FamilyMember, FamilyAgent


@dataclass
class ChatMessage:
    """チャットメッセージ"""
    speaker: str
    message: str
    emotion: str
    timestamp: str
    member_info: Optional[Dict[str, Any]] = None


@dataclass
class HappyMoment:
    """幸せなひととき"""
    activity: str
    description: str
    emotions: List[str]
    participants: List[str]
    setting: str
    created_at: str


class SimultaneousChatManager:
    """同時対話管理システム"""

    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        self.family_agent = FamilyAgent(openai_api_key)
        self.family_members: List[FamilyMember] = []
        self.conversation_history: List[ChatMessage] = []
        self.happy_moments: List[HappyMoment] = []
        self.current_session = None
        self.active_speakers: List[str] = []

    def start_family_chat(self, session_id: str, user_profile: Dict[str, Any]) -> List[FamilyMember]:
        """家族チャットを開始"""
        self.current_session = session_id

        # 家族メンバーを生成
        self.family_members = self.family_agent.generate_family_members(user_profile, session_id)

        # 会話履歴をクリア
        self.conversation_history = []
        self.happy_moments = []

        # 家族の挨拶を生成
        greetings = self._generate_family_greetings()

        return self.family_members

    def process_user_message(self, user_message: str) -> List[ChatMessage]:
        """ユーザーメッセージを処理し、家族メンバーの応答を生成"""
        # ユーザーメッセージを履歴に追加
        user_msg = ChatMessage(
            speaker="ユーザー",
            message=user_message,
            emotion="neutral",
            timestamp=datetime.now().isoformat()
        )
        self.conversation_history.append(user_msg)

        # 各家族メンバーの応答を生成
        responses = []
        for member in self.family_members:
            if self._should_member_respond(member, user_message):
                response = self._generate_member_response(member, user_message)
                responses.append(response)

        # 応答を履歴に追加
        self.conversation_history.extend(responses)

        # 幸せなひとときを抽出
        self._extract_happy_moments(user_message, responses)

        # セッションデータを保存
        self._save_chat_data()

        return responses

    def _generate_family_greetings(self) -> List[ChatMessage]:
        """家族の挨拶を生成"""
        greetings = []

        for member in self.family_members:
            greeting_prompt = f"""
あなたは{member.name}（{member.role.value}）です。
年齢: {member.age}歳
性格: {member.personality}
話し方: {member.speaking_style}
興味: {member.interests}
価値観: {member.values}

家族の新しいメンバー（ユーザー）に温かく挨拶してください。
あなたの性格と話し方に合った挨拶をしてください。
"""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": greeting_prompt}],
                max_tokens=150,
                temperature=0.8
            )

            greeting = ChatMessage(
                speaker=member.name,
                message=response.choices[0].message.content,
                emotion="happy",
                timestamp=datetime.now().isoformat(),
                member_info=asdict(member)
            )

            greetings.append(greeting)

        self.conversation_history.extend(greetings)
        return greetings

    def _should_member_respond(self, member: FamilyMember, user_message: str) -> bool:
        """メンバーが応答すべきかどうかを判定"""
        # 基本的には全員が応答するが、文脈に応じて調整
        return True

    def _generate_member_response(self, member: FamilyMember, user_message: str) -> ChatMessage:
        """家族メンバーの応答を生成"""

        # 会話の文脈を取得
        context = self._get_conversation_context()

        response_prompt = f"""
あなたは{member.name}（{member.role.value}）です。

基本情報：
- 年齢: {member.age}歳
- 性格: {member.personality}
- 話し方: {member.speaking_style}
- 興味: {member.interests}
- 価値観: {member.values}
- 現在の感情: {member.current_emotion}

会話の文脈：
{context}

ユーザーの最新メッセージ：{user_message}

あなたの性格と話し方に合った応答をしてください。
家族の一員として、温かく親しみやすい応答を心がけてください。
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": response_prompt}],
            max_tokens=200,
            temperature=0.8
        )

        # 感情を更新
        emotion = self._update_member_emotion(member, user_message, response.choices[0].message.content)

        return ChatMessage(
            speaker=member.name,
            message=response.choices[0].message.content,
            emotion=emotion,
            timestamp=datetime.now().isoformat(),
            member_info=asdict(member)
        )

    def _get_conversation_context(self) -> str:
        """会話の文脈を取得"""
        context = ""
        for msg in self.conversation_history[-5:]:  # 最新5件
            context += f"{msg.speaker}: {msg.message}\n"
        return context

    def _update_member_emotion(self, member: FamilyMember, user_message: str, response: str) -> str:
        """メンバーの感情を更新"""
        emotion_prompt = f"""
{member.name}の性格: {member.personality}
ユーザーのメッセージ: {user_message}
{member.name}の応答: {response}

{member.name}の現在の感情を以下のいずれかから選択してください：
- happy (嬉しい)
- excited (興奮)
- calm (落ち着いた)
- loving (愛情深い)
- curious (好奇心)
- worried (心配)
- proud (誇り)
- nostalgic (懐かしい)

感情を返してください。
"""

        emotion_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": emotion_prompt}],
            max_tokens=50,
            temperature=0.3
        )

        emotion = emotion_response.choices[0].message.content.strip()
        member.current_emotion = emotion
        return emotion

    def _extract_happy_moments(self, user_message: str, responses: List[ChatMessage]) -> None:
        """幸せなひとときを抽出"""
        extraction_prompt = f"""
以下の会話から、家族の幸せなひとときを抽出してください。

ユーザーのメッセージ: {user_message}
家族の応答: {[r.message for r in responses]}

幸せなひとときとして以下を抽出してください：
- 活動内容
- 感情
- 参加者
- 設定・場所

JSON形式で返してください。
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": extraction_prompt}],
            max_tokens=300,
            temperature=0.5
        )

        try:
            happy_moment_data = json.loads(response.choices[0].message.content)

            happy_moment = HappyMoment(
                activity=happy_moment_data.get("activity", ""),
                description=happy_moment_data.get("description", ""),
                emotions=happy_moment_data.get("emotions", []),
                participants=happy_moment_data.get("participants", []),
                setting=happy_moment_data.get("setting", ""),
                created_at=datetime.now().isoformat()
            )

            self.happy_moments.append(happy_moment)

        except json.JSONDecodeError:
            # JSON解析エラーの場合は手動で抽出
            pass

    def _save_chat_data(self) -> None:
        """チャットデータを保存"""
        if not self.current_session:
            return

        session_dir = f"/tmp/user_sessions/{self.current_session}"

        # 会話履歴を保存
        chat_history = [asdict(msg) for msg in self.conversation_history]
        with open(f"{session_dir}/family_chat_history.json", "w", encoding="utf-8") as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=2)

        # 幸せなひとときを保存
        happy_moments_data = [asdict(moment) for moment in self.happy_moments]
        with open(f"{session_dir}/happy_moments.json", "w", encoding="utf-8") as f:
            json.dump(happy_moments_data, f, ensure_ascii=False, indent=2)

    def get_conversation_history(self) -> List[ChatMessage]:
        """会話履歴を取得"""
        return self.conversation_history

    def get_happy_moments(self) -> List[HappyMoment]:
        """幸せなひとときを取得"""
        return self.happy_moments

    def get_family_members(self) -> List[FamilyMember]:
        """家族メンバーを取得"""
        return self.family_members

    def get_member_emotions(self) -> Dict[str, str]:
        """各メンバーの現在の感情を取得"""
        emotions = {}
        for member in self.family_members:
            emotions[member.name] = member.current_emotion
        return emotions

    def generate_family_scene(self) -> Dict[str, Any]:
        """家族のシーンを生成"""
        if not self.happy_moments:
            return {}

        # 最新の幸せなひとときを基にシーンを生成
        latest_moment = self.happy_moments[-1]

        scene_prompt = f"""
以下の幸せなひとときを基に、家族のシーンを詳細に描写してください。

活動: {latest_moment.activity}
説明: {latest_moment.description}
感情: {latest_moment.emotions}
参加者: {latest_moment.participants}
設定: {latest_moment.setting}

家族の温かい雰囲気と幸せな瞬間を詳細に描写してください。
JSON形式で返してください。
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": scene_prompt}],
            max_tokens=500,
            temperature=0.7
        )

        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {
                "scene": "家族の温かい時間",
                "description": latest_moment.description,
                "emotions": latest_moment.emotions
            }
