"""
改良版同時対話システム
ロールベースの家族エージェントシステムと統合
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import openai
from dataclasses import dataclass, asdict
from role_system import FamilyConfigurationManager, FamilyMemberAgent, FamilyRole


@dataclass
class ChatMessage:
    """チャットメッセージ"""
    speaker: str
    message: str
    emotion: str
    timestamp: str
    role: str
    agent_info: Optional[Dict[str, Any]] = None


@dataclass
class HappyMoment:
    """幸せなひととき"""
    activity: str
    description: str
    emotions: List[str]
    participants: List[str]
    setting: str
    created_at: str
    role_interactions: Dict[str, str]  # 各ロールの関与


class EnhancedSimultaneousChatManager:
    """改良版同時対話管理システム"""

    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        self.family_config_manager = FamilyConfigurationManager(openai_api_key)
        self.active_agents: List[FamilyMemberAgent] = []
        self.conversation_history: List[ChatMessage] = []
        self.happy_moments: List[HappyMoment] = []
        self.current_session = None
        self.active_speakers: List[str] = []
        self.role_interaction_rules = self._initialize_interaction_rules()

    def _initialize_interaction_rules(self) -> Dict[str, Dict[str, Any]]:
        """ロール間の相互作用ルールを初期化"""
        return {
            "partner": {
                "primary_interactions": ["child", "grandfather", "grandmother"],
                "support_role": "family_coordinator",
                "response_priority": "high"
            },
            "child": {
                "primary_interactions": ["partner", "grandfather", "grandmother"],
                "support_role": "family_joy",
                "response_priority": "medium"
            },
            "grandfather": {
                "primary_interactions": ["child", "partner"],
                "support_role": "wisdom_provider",
                "response_priority": "medium"
            },
            "grandmother": {
                "primary_interactions": ["child", "partner"],
                "support_role": "care_provider",
                "response_priority": "medium"
            }
        }

    def start_family_chat(self, session_id: str, user_profile: Dict[str, Any]) -> List[FamilyMemberAgent]:
        """家族チャットを開始"""
        self.current_session = session_id

        # 家族構成を設定
        self.active_agents = self.family_config_manager.configure_family(user_profile, session_id)

        # 会話履歴をクリア
        self.conversation_history = []
        self.happy_moments = []

        # 家族の挨拶を生成
        greetings = self._generate_family_greetings()

        return self.active_agents

    def process_user_message(self, user_message: str) -> List[ChatMessage]:
        """ユーザーメッセージを処理し、家族メンバーの応答を生成"""
        # ユーザーメッセージを履歴に追加
        user_msg = ChatMessage(
            speaker="ユーザー",
            message=user_message,
            emotion="neutral",
            timestamp=datetime.now().isoformat(),
            role="user"
        )
        self.conversation_history.append(user_msg)

        # 各家族メンバーの応答を生成（ロール優先度に基づく）
        responses = self._generate_role_based_responses(user_message)

        # 応答を履歴に追加
        self.conversation_history.extend(responses)

        # 幸せなひとときを抽出
        self._extract_happy_moments(user_message, responses)

        # セッションデータを保存
        self._save_chat_data()

        return responses

    def _generate_role_based_responses(self, user_message: str) -> List[ChatMessage]:
        """ロール優先度に基づいて応答を生成"""
        responses = []

        # ロール優先度でソート
        sorted_agents = self._sort_agents_by_priority(user_message)

        for agent in sorted_agents:
            if self._should_agent_respond(agent, user_message):
                response = self._generate_agent_response(agent, user_message)
                responses.append(response)

        return responses

    def _sort_agents_by_priority(self, user_message: str) -> List[FamilyMemberAgent]:
        """メッセージ内容に基づいてエージェントを優先度順にソート"""
        # メッセージの内容を分析して優先度を決定
        message_analysis = self._analyze_message_content(user_message)

        # 優先度に基づいてソート
        def priority_key(agent):
            role = agent.role.value
            rules = self.role_interaction_rules.get(role, {})
            priority = rules.get("response_priority", "low")

            # メッセージ内容に基づく優先度調整
            if message_analysis.get("needs_wisdom") and role == "grandfather":
                return 0
            elif message_analysis.get("needs_care") and role == "grandmother":
                return 1
            elif message_analysis.get("needs_support") and role == "partner":
                return 2
            elif message_analysis.get("needs_joy") and role == "child":
                return 3
            else:
                return 4

        return sorted(self.active_agents, key=priority_key)

    def _analyze_message_content(self, user_message: str) -> Dict[str, bool]:
        """メッセージ内容を分析"""
        analysis = {
            "needs_wisdom": False,
            "needs_care": False,
            "needs_support": False,
            "needs_joy": False
        }

        # キーワードベースの分析
        wisdom_keywords = ["悩み", "相談", "アドバイス", "経験"]
        care_keywords = ["体調", "健康", "心配", "面倒"]
        support_keywords = ["助けて", "困った", "不安", "支え"]
        joy_keywords = ["楽しい", "嬉しい", "遊び", "笑い"]

        for keyword in wisdom_keywords:
            if keyword in user_message:
                analysis["needs_wisdom"] = True
                break

        for keyword in care_keywords:
            if keyword in user_message:
                analysis["needs_care"] = True
                break

        for keyword in support_keywords:
            if keyword in user_message:
                analysis["needs_support"] = True
                break

        for keyword in joy_keywords:
            if keyword in user_message:
                analysis["needs_joy"] = True
                break

        return analysis

    def _should_agent_respond(self, agent: FamilyMemberAgent, user_message: str) -> bool:
        """エージェントが応答すべきかどうかを判定"""
        role = agent.role.value
        rules = self.role_interaction_rules.get(role, {})

        # 基本的には全員が応答するが、文脈に応じて調整
        return True

    def _generate_agent_response(self, agent: FamilyMemberAgent, user_message: str) -> ChatMessage:
        """エージェントの応答を生成"""
        # 会話の文脈を取得
        context = self._get_conversation_context()

        # エージェントの応答を生成
        response = agent.generate_response(user_message, context)

        return ChatMessage(
            speaker=agent.name,
            message=response,
            emotion=agent.current_emotion,
            timestamp=datetime.now().isoformat(),
            role=agent.role.value,
            agent_info=agent.get_agent_info()
        )

    def _get_conversation_context(self) -> str:
        """会話の文脈を取得"""
        context = ""
        for msg in self.conversation_history[-5:]:  # 最新5件
            context += f"{msg.speaker} ({msg.role}): {msg.message}\n"
        return context

    def _generate_family_greetings(self) -> List[ChatMessage]:
        """家族の挨拶を生成"""
        greetings = []

        for agent in self.active_agents:
            greeting_prompt = f"""
            あなたは{agent.name}（{agent.role.value}）です。

            基本情報：
            - 年齢: {agent.age}歳
            - 性格: {agent.personality}
            - 話し方: {agent.speaking_style}
            - 興味: {agent.interests}
            - 価値観: {agent.values}
            - ユーザーとの関係: {agent.relationship_to_user}

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
                speaker=agent.name,
                message=response.choices[0].message.content,
                emotion="happy",
                timestamp=datetime.now().isoformat(),
                role=agent.role.value,
                agent_info=agent.get_agent_info()
            )

            greetings.append(greeting)

        self.conversation_history.extend(greetings)
        return greetings

    def _extract_happy_moments(self, user_message: str, responses: List[ChatMessage]) -> None:
        """幸せなひとときを抽出"""
        # 各ロールの関与を記録
        role_interactions = {}
        for response in responses:
            role_interactions[response.role] = response.message

        extraction_prompt = f"""
        以下の会話から、家族の幸せなひとときを抽出してください。

        ユーザーのメッセージ: {user_message}
        家族の応答: {[r.message for r in responses]}
        ロール別の関与: {role_interactions}

        幸せなひとときとして以下を抽出してください：
        - 活動内容
        - 感情
        - 参加者
        - 設定・場所
        - 各ロールの関与

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
                created_at=datetime.now().isoformat(),
                role_interactions=role_interactions
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
        with open(f"{session_dir}/enhanced_family_chat_history.json", "w", encoding="utf-8") as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=2)

        # 幸せなひとときを保存
        happy_moments_data = [asdict(moment) for moment in self.happy_moments]
        with open(f"{session_dir}/enhanced_happy_moments.json", "w", encoding="utf-8") as f:
            json.dump(happy_moments_data, f, ensure_ascii=False, indent=2)

    def get_conversation_history(self) -> List[ChatMessage]:
        """会話履歴を取得"""
        return self.conversation_history

    def get_happy_moments(self) -> List[HappyMoment]:
        """幸せなひとときを取得"""
        return self.happy_moments

    def get_agents_by_role(self, role: FamilyRole) -> List[FamilyMemberAgent]:
        """ロールでエージェントを取得"""
        return self.family_config_manager.get_agents_by_role(role)

    def get_all_agents(self) -> List[FamilyMemberAgent]:
        """全エージェントを取得"""
        return self.active_agents

    def get_member_emotions(self) -> Dict[str, str]:
        """各メンバーの現在の感情を取得"""
        emotions = {}
        for agent in self.active_agents:
            emotions[agent.name] = agent.current_emotion
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
        ロール別の関与: {latest_moment.role_interactions}

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
                "emotions": latest_moment.emotions,
                "role_interactions": latest_moment.role_interactions
            }

    def add_family_member(self, role: FamilyRole, custom_params: Optional[Dict[str, Any]] = None) -> FamilyMemberAgent:
        """家族メンバーを追加"""
        user_profile = {}  # 必要に応じて現在のユーザープロファイルを取得
        agent = self.family_config_manager.add_agent(role, user_profile, custom_params)
        self.active_agents.append(agent)
        return agent

    def remove_family_member(self, agent_name: str) -> bool:
        """家族メンバーを削除"""
        success = self.family_config_manager.remove_agent(agent_name)
        if success:
            self.active_agents = [agent for agent in self.active_agents if agent.name != agent_name]
        return success
