"""
ロールベースの家族エージェントシステム
家族構成に応じて動的にエージェントを生成・管理
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
import openai


class FamilyRole(Enum):
    """家族の役割"""
    PARTNER = "partner"
    CHILD = "child"
    GRANDFATHER = "grandfather"
    GRANDMOTHER = "grandmother"
    SIBLING = "sibling"
    PET = "pet"


@dataclass
class RoleTemplate:
    """ロールテンプレート"""
    role: FamilyRole
    name: str
    age_range: tuple
    personality_traits: List[str]
    speaking_style: Dict[str, Any]
    interests: List[str]
    values: List[str]
    relationship_dynamics: Dict[str, Any]
    default_emotions: List[str]


class RoleFactory:
    """ロールファクトリー - ロールに基づいてエージェントを生成"""

    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        self.role_templates = self._initialize_role_templates()

    def _initialize_role_templates(self) -> Dict[FamilyRole, RoleTemplate]:
        """ロールテンプレートを初期化"""
        templates = {}

        # パートナーテンプレート
        templates[FamilyRole.PARTNER] = RoleTemplate(
            role=FamilyRole.PARTNER,
            name="パートナー",
            age_range=(20, 50),
            personality_traits=["愛情深い", "支え合い", "理解力", "協調性"],
            speaking_style={
                "tone": "温かみのある",
                "vocabulary": "親しみやすい",
                "emotions": ["愛情", "支え合い", "理解"]
            },
            interests=["家族時間", "趣味", "旅行", "料理"],
            values=["家族の絆", "健康", "成長", "愛情"],
            relationship_dynamics={
                "primary_relationship": "パートナー",
                "interaction_style": "対等",
                "support_role": "相互支援"
            },
            default_emotions=["loving", "supportive", "understanding"]
        )

        # 子どもテンプレート（年齢別）
        templates[FamilyRole.CHILD] = RoleTemplate(
            role=FamilyRole.CHILD,
            name="子ども",
            age_range=(0, 18),
            personality_traits=["好奇心旺盛", "純真", "成長中", "家族思い"],
            speaking_style={
                "tone": "年齢に応じた",
                "vocabulary": "年齢相応",
                "emotions": ["純真", "喜び", "驚き", "成長"]
            },
            interests=["遊び", "学習", "友達", "家族"],
            values=["楽しさ", "好奇心", "家族", "友達"],
            relationship_dynamics={
                "primary_relationship": "子ども",
                "interaction_style": "親子",
                "support_role": "愛情と教育"
            },
            default_emotions=["happy", "curious", "excited"]
        )

        # 祖父テンプレート
        templates[FamilyRole.GRANDFATHER] = RoleTemplate(
            role=FamilyRole.GRANDFATHER,
            name="祖父",
            age_range=(60, 80),
            personality_traits=["穏やか", "経験豊富", "家族思い", "知恵深い"],
            speaking_style={
                "tone": "落ち着いた",
                "vocabulary": "丁寧語",
                "emotions": ["慈愛", "安心感", "誇り"]
            },
            interests=["園芸", "将棋", "散歩", "読書"],
            values=["伝統", "家族の絆", "知恵", "健康"],
            relationship_dynamics={
                "primary_relationship": "祖父",
                "interaction_style": "指導的",
                "support_role": "知恵と経験の提供"
            },
            default_emotions=["wise", "caring", "proud"]
        )

        # 祖母テンプレート
        templates[FamilyRole.GRANDMOTHER] = RoleTemplate(
            role=FamilyRole.GRANDMOTHER,
            name="祖母",
            age_range=(55, 75),
            personality_traits=["優しい", "料理好き", "孫思い", "愛情深い"],
            speaking_style={
                "tone": "温かみのある",
                "vocabulary": "優しい言葉",
                "emotions": ["愛情", "心配", "喜び"]
            },
            interests=["料理", "裁縫", "お花", "孫との時間"],
            values=["家族の健康", "伝統", "愛情", "絆"],
            relationship_dynamics={
                "primary_relationship": "祖母",
                "interaction_style": "慈愛",
                "support_role": "愛情とケア"
            },
            default_emotions=["loving", "caring", "nurturing"]
        )

        return templates

    def create_agent_from_role(self, role: FamilyRole, user_profile: Dict[str, Any],
                             custom_params: Optional[Dict[str, Any]] = None) -> 'FamilyMemberAgent':
        """ロールに基づいてエージェントを生成"""
        template = self.role_templates[role]

        # カスタムパラメータを適用
        if custom_params:
            template = self._apply_custom_params(template, custom_params)

        # エージェントを生成
        return FamilyMemberAgent(
            role=role,
            template=template,
            user_profile=user_profile,
            openai_api_key=self.openai_api_key
        )

    def _apply_custom_params(self, template: RoleTemplate, custom_params: Dict[str, Any]) -> RoleTemplate:
        """カスタムパラメータをテンプレートに適用"""
        # テンプレートのコピーを作成
        updated_template = RoleTemplate(
            role=template.role,
            name=custom_params.get("name", template.name),
            age_range=custom_params.get("age_range", template.age_range),
            personality_traits=custom_params.get("personality_traits", template.personality_traits),
            speaking_style=custom_params.get("speaking_style", template.speaking_style),
            interests=custom_params.get("interests", template.interests),
            values=custom_params.get("values", template.values),
            relationship_dynamics=custom_params.get("relationship_dynamics", template.relationship_dynamics),
            default_emotions=custom_params.get("default_emotions", template.default_emotions)
        )
        return updated_template


class FamilyMemberAgent:
    """家族メンバーエージェント（ロールベース）"""

    def __init__(self, role: FamilyRole, template: RoleTemplate,
                 user_profile: Dict[str, Any], openai_api_key: str):
        self.role = role
        self.template = template
        self.user_profile = user_profile
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key

        # エージェントの詳細情報を生成
        self.name = self._generate_name()
        self.age = self._generate_age()
        self.personality = self._generate_personality()
        self.speaking_style = self._generate_speaking_style()
        self.interests = self._generate_interests()
        self.values = self._generate_values()
        self.current_emotion = "neutral"
        self.relationship_to_user = template.relationship_dynamics["primary_relationship"]

        # 会話履歴
        self.conversation_history = []

    def _generate_name(self) -> str:
        """名前を生成"""
        if self.role == FamilyRole.PARTNER:
            return self.user_profile.get("partner_info", {}).get("name", "美咲")
        elif self.role == FamilyRole.CHILD:
            return self._generate_child_name()
        elif self.role == FamilyRole.GRANDFATHER:
            return "じいじ"
        elif self.role == FamilyRole.GRANDMOTHER:
            return "ばあば"
        else:
            return self.template.name

    def _generate_child_name(self) -> str:
        """子どもの名前を生成"""
        age = self.user_profile.get("age", 5)
        gender = self.user_profile.get("gender", "unknown")

        if age < 7:
            return "たろう" if gender == "male" else "さくら"
        elif age < 13:
            return "ゆうと" if gender == "male" else "みお"
        else:
            return "そうた" if gender == "male" else "あい"

    def _generate_age(self) -> int:
        """年齢を生成"""
        if self.role == FamilyRole.PARTNER:
            return self.user_profile.get("partner_info", {}).get("age",
                   self.user_profile.get("age", 28))
        elif self.role == FamilyRole.CHILD:
            return self.user_profile.get("age", 5)
        elif self.role == FamilyRole.GRANDFATHER:
            return 65
        elif self.role == FamilyRole.GRANDMOTHER:
            return 62
        else:
            return 30

    def _generate_personality(self) -> Dict[str, Any]:
        """性格を生成"""
        prompt = f"""
        ユーザー情報を基に、{self.template.name}の性格を生成してください。

        ユーザー情報：
        - 年齢: {self.user_profile.get('age', '不明')}
        - 趣味: {self.user_profile.get('interests', [])}
        - ライフスタイル: {self.user_profile.get('lifestyle', {})}

        ロール: {self.role.value}
        基本性格: {self.template.personality_traits}

        ユーザーと相性の良い性格を生成してください。
        JSON形式で返してください。
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.8
        )

        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {
                "traits": self.template.personality_traits,
                "character": "温かみのある"
            }

    def _generate_speaking_style(self) -> Dict[str, Any]:
        """話し方を生成"""
        return self.template.speaking_style

    def _generate_interests(self) -> List[str]:
        """興味・趣味を生成"""
        return self.template.interests

    def _generate_values(self) -> List[str]:
        """価値観を生成"""
        return self.template.values

    def generate_response(self, user_message: str, context: str = "") -> str:
        """ユーザーメッセージに対する応答を生成"""
        response_prompt = f"""
        あなたは{self.name}（{self.role.value}）です。

        基本情報：
        - 年齢: {self.age}歳
        - 性格: {self.personality}
        - 話し方: {self.speaking_style}
        - 興味: {self.interests}
        - 価値観: {self.values}
        - 現在の感情: {self.current_emotion}
        - ユーザーとの関係: {self.relationship_to_user}

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
        self._update_emotion(user_message, response.choices[0].message.content)

        # 会話履歴に追加
        self.conversation_history.append({
            "user_message": user_message,
            "agent_response": response.choices[0].message.content,
            "timestamp": datetime.now().isoformat()
        })

        return response.choices[0].message.content

    def _update_emotion(self, user_message: str, response: str) -> None:
        """感情を更新"""
        emotion_prompt = f"""
        {self.name}の性格: {self.personality}
        ユーザーのメッセージ: {user_message}
        {self.name}の応答: {response}

        {self.name}の現在の感情を以下のいずれかから選択してください：
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

        self.current_emotion = emotion_response.choices[0].message.content.strip()

    def get_agent_info(self) -> Dict[str, Any]:
        """エージェント情報を取得"""
        return {
            "name": self.name,
            "role": self.role.value,
            "age": self.age,
            "personality": self.personality,
            "speaking_style": self.speaking_style,
            "interests": self.interests,
            "values": self.values,
            "current_emotion": self.current_emotion,
            "relationship_to_user": self.relationship_to_user
        }


class FamilyConfigurationManager:
    """家族構成管理システム"""

    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.role_factory = RoleFactory(openai_api_key)
        self.active_agents: List[FamilyMemberAgent] = []
        self.session_id = None

    def configure_family(self, user_profile: Dict[str, Any], session_id: str) -> List[FamilyMemberAgent]:
        """ユーザープロファイルに基づいて家族構成を設定"""
        self.session_id = session_id
        self.active_agents = []

        # 家族構成を決定
        family_structure = self._determine_family_structure(user_profile)

        # 各ロールのエージェントを生成
        for role_config in family_structure:
            agent = self.role_factory.create_agent_from_role(
                role=role_config["role"],
                user_profile=user_profile,
                custom_params=role_config.get("custom_params")
            )
            self.active_agents.append(agent)

        # 家族構成を保存
        self._save_family_configuration()

        return self.active_agents

    def _determine_family_structure(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ユーザープロファイルから家族構成を決定"""
        family_structure = []

        # パートナーを追加
        if user_profile.get("partner_info"):
            family_structure.append({
                "role": FamilyRole.PARTNER,
                "custom_params": user_profile.get("partner_info")
            })

        # 子どもを追加
        children_info = user_profile.get("children_info", [])
        for child_info in children_info:
            family_structure.append({
                "role": FamilyRole.CHILD,
                "custom_params": child_info
            })

        # 祖父母を追加（条件付き）
        user_age = user_profile.get("age", 30)
        if user_age > 25:  # 25歳以上なら祖父母がいる可能性
            family_structure.extend([
                {"role": FamilyRole.GRANDFATHER},
                {"role": FamilyRole.GRANDMOTHER}
            ])

        return family_structure

    def _save_family_configuration(self) -> None:
        """家族構成を保存"""
        if not self.session_id:
            return

        session_dir = f"/tmp/user_sessions/{self.session_id}"
        os.makedirs(session_dir, exist_ok=True)

        family_config = []
        for agent in self.active_agents:
            family_config.append(agent.get_agent_info())

        with open(f"{session_dir}/family_configuration.json", "w", encoding="utf-8") as f:
            json.dump(family_config, f, ensure_ascii=False, indent=2)

    def get_agents_by_role(self, role: FamilyRole) -> List[FamilyMemberAgent]:
        """ロールでエージェントを取得"""
        return [agent for agent in self.active_agents if agent.role == role]

    def get_all_agents(self) -> List[FamilyMemberAgent]:
        """全エージェントを取得"""
        return self.active_agents

    def add_agent(self, role: FamilyRole, user_profile: Dict[str, Any],
                  custom_params: Optional[Dict[str, Any]] = None) -> FamilyMemberAgent:
        """エージェントを追加"""
        agent = self.role_factory.create_agent_from_role(
            role=role,
            user_profile=user_profile,
            custom_params=custom_params
        )
        self.active_agents.append(agent)
        return agent

    def remove_agent(self, agent_name: str) -> bool:
        """エージェントを削除"""
        for i, agent in enumerate(self.active_agents):
            if agent.name == agent_name:
                del self.active_agents[i]
                return True
        return False
