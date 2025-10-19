"""
家族メンバーエージェント
ヘーラーエージェントで収集した情報を基に、個性的な家族メンバーのペルソナエージェントを生成
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import openai
from dataclasses import dataclass, asdict
from enum import Enum


class FamilyRole(Enum):
    """家族の役割"""
    PARTNER = "partner"
    CHILD = "child"
    GRANDFATHER = "grandfather"
    GRANDMOTHER = "grandmother"


@dataclass
class FamilyMember:
    """家族メンバーの情報"""
    name: str
    role: FamilyRole
    age: int
    personality: Dict[str, Any]
    speaking_style: Dict[str, Any]
    interests: List[str]
    values: List[str]
    current_emotion: str = "neutral"
    relationship_to_user: str = ""


class FamilyAgent:
    """家族メンバーエージェント"""

    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        self.family_members: List[FamilyMember] = []
        self.conversation_history = []
        self.current_session = None

    def generate_family_members(self, user_profile: Dict[str, Any], session_id: str) -> List[FamilyMember]:
        """ユーザープロファイルを基に家族メンバーを生成"""
        self.current_session = session_id

        # 家族構成を決定
        family_structure = self._determine_family_structure(user_profile)

        # 各家族メンバーを生成
        family_members = []

        # パートナーを生成
        if family_structure.get("has_partner", False):
            partner = self._generate_partner(user_profile)
            family_members.append(partner)

        # 子どもを生成
        children = family_structure.get("children", [])
        for child_info in children:
            child = self._generate_child(child_info, user_profile)
            family_members.append(child)

        # 祖父母を生成
        if family_structure.get("has_grandparents", False):
            grandfather = self._generate_grandfather(user_profile)
            grandmother = self._generate_grandmother(user_profile)
            family_members.extend([grandfather, grandmother])

        self.family_members = family_members

        # 家族メンバー情報を保存
        self._save_family_members()

        return family_members

    def _determine_family_structure(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """ユーザープロファイルから家族構成を決定"""
        family_structure = {
            "has_partner": user_profile.get("partner_info") is not None,
            "children": [],
            "has_grandparents": False
        }

        # 子どもの情報を処理
        children_info = user_profile.get("children_info", [])
        if children_info:
            for child in children_info:
                family_structure["children"].append({
                    "age": child.get("age", 5),
                    "gender": child.get("gender", "unknown"),
                    "personality": child.get("personality", {})
                })

        # 祖父母の存在を決定（ユーザーの年齢や家族構成に基づく）
        user_age = user_profile.get("age", 30)
        if user_age > 25:  # 25歳以上なら祖父母がいる可能性
            family_structure["has_grandparents"] = True

        return family_structure

    def _generate_partner(self, user_profile: Dict[str, Any]) -> FamilyMember:
        """パートナーエージェントを生成"""
        partner_info = user_profile.get("partner_info", {})

        # パートナーの基本情報を生成
        name = partner_info.get("name", "美咲")
        age = partner_info.get("age", user_profile.get("age", 28))

        # 性格を生成
        personality = self._generate_personality("partner", user_profile)

        # 話し方を生成
        speaking_style = self._generate_speaking_style(age, "partner")

        # 興味・価値観を生成
        interests = self._generate_interests("partner", user_profile)
        values = self._generate_values("partner", user_profile)

        return FamilyMember(
            name=name,
            role=FamilyRole.PARTNER,
            age=age,
            personality=personality,
            speaking_style=speaking_style,
            interests=interests,
            values=values,
            relationship_to_user="パートナー"
        )

    def _generate_child(self, child_info: Dict[str, Any], user_profile: Dict[str, Any]) -> FamilyMember:
        """子どもエージェントを生成"""
        age = child_info.get("age", 5)
        gender = child_info.get("gender", "unknown")

        # 年齢に応じた名前を生成
        name = self._generate_child_name(age, gender)

        # 年齢に応じた性格を生成
        personality = self._generate_child_personality(age)

        # 年齢に応じた話し方を生成
        speaking_style = self._generate_child_speaking_style(age)

        # 年齢に応じた興味を生成
        interests = self._generate_child_interests(age)
        values = self._generate_child_values(age)

        return FamilyMember(
            name=name,
            role=FamilyRole.CHILD,
            age=age,
            personality=personality,
            speaking_style=speaking_style,
            interests=interests,
            values=values,
            relationship_to_user="子ども"
        )

    def _generate_grandfather(self, user_profile: Dict[str, Any]) -> FamilyMember:
        """祖父エージェントを生成"""
        name = "じいじ"
        age = 65

        personality = {
            "traits": ["穏やか", "経験豊富", "家族思い", "知恵深い"],
            "character": "落ち着いた、慈愛深い"
        }

        speaking_style = {
            "tone": "落ち着いた",
            "vocabulary": "丁寧語",
            "emotions": ["慈愛", "安心感", "誇り"]
        }

        interests = ["園芸", "将棋", "散歩", "読書"]
        values = ["伝統", "家族の絆", "知恵", "健康"]

        return FamilyMember(
            name=name,
            role=FamilyRole.GRANDFATHER,
            age=age,
            personality=personality,
            speaking_style=speaking_style,
            interests=interests,
            values=values,
            relationship_to_user="祖父"
        )

    def _generate_grandmother(self, user_profile: Dict[str, Any]) -> FamilyMember:
        """祖母エージェントを生成"""
        name = "ばあば"
        age = 62

        personality = {
            "traits": ["優しい", "料理好き", "孫思い", "愛情深い"],
            "character": "温かみのある、思いやり深い"
        }

        speaking_style = {
            "tone": "温かみのある",
            "vocabulary": "優しい言葉",
            "emotions": ["愛情", "心配", "喜び"]
        }

        interests = ["料理", "裁縫", "お花", "孫との時間"]
        values = ["家族の健康", "伝統", "愛情", "絆"]

        return FamilyMember(
            name=name,
            role=FamilyRole.GRANDMOTHER,
            age=age,
            personality=personality,
            speaking_style=speaking_style,
            interests=interests,
            values=values,
            relationship_to_user="祖母"
        )

    def _generate_personality(self, role: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """性格を生成"""
        prompt = f"""
ユーザーの情報を基に、{role}の性格を生成してください。

ユーザー情報：
- 年齢: {user_profile.get('age', '不明')}
- 趣味: {user_profile.get('interests', [])}
- ライフスタイル: {user_profile.get('lifestyle', {})}

{role}として、ユーザーと相性の良い性格を生成してください。
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
                "traits": ["優しい", "家族思い", "積極的"],
                "character": "温かみのある"
            }

    def _generate_speaking_style(self, age: int, role: str) -> Dict[str, Any]:
        """話し方を生成"""
        if role == "partner":
            return {
                "tone": "温かみのある",
                "vocabulary": "親しみやすい",
                "emotions": ["愛情", "支え合い", "理解"]
            }
        elif role == "child":
            if age < 7:
                return {
                    "tone": "可愛らしい",
                    "vocabulary": "簡単な言葉",
                    "emotions": ["純真", "喜び", "驚き"]
                }
            elif age < 13:
                return {
                    "tone": "元気いっぱい",
                    "vocabulary": "年齢相応",
                    "emotions": ["興奮", "好奇心", "達成感"]
                }
            else:
                return {
                    "tone": "少し生意気",
                    "vocabulary": "若者言葉",
                    "emotions": ["反抗期", "友情", "成長"]
                }
        else:  # 祖父母
            return {
                "tone": "落ち着いた",
                "vocabulary": "丁寧語",
                "emotions": ["慈愛", "安心感", "誇り"]
            }

    def _generate_interests(self, role: str, user_profile: Dict[str, Any]) -> List[str]:
        """興味・趣味を生成"""
        if role == "partner":
            return ["料理", "読書", "映画鑑賞", "旅行"]
        elif role == "child":
            return ["おもちゃ", "絵本", "公園遊び", "ゲーム"]
        else:  # 祖父母
            return ["園芸", "将棋", "散歩", "読書"]

    def _generate_values(self, role: str, user_profile: Dict[str, Any]) -> List[str]:
        """価値観を生成"""
        if role == "partner":
            return ["家族の絆", "健康", "成長", "愛情"]
        elif role == "child":
            return ["楽しさ", "好奇心", "家族", "友達"]
        else:  # 祖父母
            return ["伝統", "家族の絆", "知恵", "健康"]

    def _generate_child_name(self, age: int, gender: str) -> str:
        """子どもの名前を生成"""
        if age < 7:
            return "たろう" if gender == "male" else "さくら"
        elif age < 13:
            return "ゆうと" if gender == "male" else "みお"
        else:
            return "そうた" if gender == "male" else "あい"

    def _generate_child_personality(self, age: int) -> Dict[str, Any]:
        """子どもの性格を生成"""
        if age < 7:
            return {
                "traits": ["好奇心旺盛", "元気", "素直"],
                "character": "可愛らしい、純真"
            }
        elif age < 13:
            return {
                "traits": ["活発", "勉強好き", "友達思い"],
                "character": "元気いっぱい、好奇心旺盛"
            }
        else:
            return {
                "traits": ["思春期", "自立心", "友達重視"],
                "character": "少し生意気、成長期"
            }

    def _generate_child_speaking_style(self, age: int) -> Dict[str, Any]:
        """子どもの話し方を生成"""
        if age < 7:
            return {
                "tone": "可愛らしい",
                "vocabulary": "簡単な言葉",
                "emotions": ["純真", "喜び", "驚き"]
            }
        elif age < 13:
            return {
                "tone": "元気いっぱい",
                "vocabulary": "年齢相応",
                "emotions": ["興奮", "好奇心", "達成感"]
            }
        else:
            return {
                "tone": "少し生意気",
                "vocabulary": "若者言葉",
                "emotions": ["反抗期", "友情", "成長"]
            }

    def _generate_child_interests(self, age: int) -> List[str]:
        """子どもの興味を生成"""
        if age < 7:
            return ["おもちゃ", "絵本", "公園遊び", "アニメ"]
        elif age < 13:
            return ["スポーツ", "読書", "ゲーム", "友達"]
        else:
            return ["音楽", "スポーツ", "SNS", "友達"]

    def _generate_child_values(self, age: int) -> List[str]:
        """子どもの価値観を生成"""
        if age < 7:
            return ["楽しさ", "家族", "おもちゃ", "遊び"]
        elif age < 13:
            return ["友達", "勉強", "スポーツ", "家族"]
        else:
            return ["友達", "自由", "成長", "家族"]

    def _save_family_members(self) -> None:
        """家族メンバー情報を保存"""
        if not self.current_session:
            return

        session_dir = f"/tmp/user_sessions/{self.current_session}"

        family_data = []
        for member in self.family_members:
            member_data = asdict(member)
            family_data.append(member_data)

        with open(f"{session_dir}/family_members.json", "w", encoding="utf-8") as f:
            json.dump(family_data, f, ensure_ascii=False, indent=2)

    def get_family_members(self) -> List[FamilyMember]:
        """家族メンバーを取得"""
        return self.family_members

    def get_member_by_name(self, name: str) -> Optional[FamilyMember]:
        """名前で家族メンバーを取得"""
        for member in self.family_members:
            if member.name == name:
                return member
        return None
