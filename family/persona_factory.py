from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .personality_calculator import PersonalityCalculator, BigFiveTraits


@dataclass
class Persona:
    name: str
    role: str
    speaking_style: str
    traits: List[str]
    goals: str
    background: str
    history: List[Dict[str, Any]] = field(default_factory=list)


class PersonaFactory:
    """ユーザープロファイルから家族用ペルソナを生成"""

    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile or {}

    def build_partner(self) -> Persona:
        """パートナーペルソナを生成（交際状況に応じて分岐）"""
        relationship_status = self.profile.get("relationship_status")

        # パートナー情報を取得（状況に応じて分岐）
        if relationship_status in ["married", "partnered"]:
            # 既婚/パートナーありの場合: 実際のパートナー情報を使用
            partner_data = self.profile.get("current_partner") or {}
        elif relationship_status == "single":
            # 独身の場合: 理想のパートナー像を使用
            partner_data = self.profile.get("ideal_partner") or {}
        else:
            # 後方互換性: 旧形式のpartner_infoをフォールバック
            partner_data = self.profile.get("partner_info") or {}

        # 基本情報の取得
        description = self.profile.get("partner_face_description")
        future_hope = (self.profile.get("lifestyle") or {}).get("future_hope")

        name = partner_data.get("name") or "未来のパートナー"
        role = partner_data.get("role") or "パートナー"
        style = partner_data.get("speaking_style") or "落ち着いた優しい口調"
        goals = partner_data.get("goals") or "家族の夢を一緒に叶える"

        # 性格特性から特徴リストを生成（新機能）
        personality_traits = partner_data.get("personality_traits")
        if personality_traits:
            # ビッグファイブから日本語の特徴を生成
            traits = self._traits_from_big_five(BigFiveTraits(**personality_traits))
        else:
            # 既存形式または未指定時のフォールバック
            traits = partner_data.get("traits") or ["共感的", "思いやり", "支えになりたい"]

        # 背景情報の構築
        background_parts = []
        if temperament := partner_data.get("temperament"):
            background_parts.append(f"性格: {temperament}")
        if description:
            background_parts.append(f"外見の特徴: {description}")
        if hobbies := partner_data.get("hobbies"):
            background_parts.append(f"趣味: {', '.join(hobbies)}")
        if future_hope:
            background_parts.append(f"共通の願い: {future_hope}")
        background = " / ".join(background_parts) if background_parts else "未来の家庭像を大切にしている"

        history = [
            {
                "speaker": "partner",
                "message": "私たちの将来をいつも真剣に考えてくれてありがとう",
            }
        ]

        return Persona(
            name=name,
            role=role,
            speaking_style=style,
            traits=traits,
            goals=goals,
            background=background,
            history=history,
        )

    def build_children(self) -> List[Persona]:
        """子供ペルソナを生成（親の性格特性から科学的に計算）"""
        children_info = self.profile.get("children_info") or []
        if not children_info:
            # デフォルト: 2人の子供
            children_info = [
                {"desired_gender": "女", "age": 7},
                {"desired_gender": "男", "age": 5}
            ]

        # 親の性格特性を取得
        user_traits = self.profile.get("user_personality_traits")
        relationship_status = self.profile.get("relationship_status")

        # パートナーの性格特性を取得
        if relationship_status in ["married", "partnered"]:
            partner_data = self.profile.get("current_partner") or {}
        elif relationship_status == "single":
            partner_data = self.profile.get("ideal_partner") or {}
        else:
            partner_data = self.profile.get("partner_info") or {}

        partner_traits = partner_data.get("personality_traits")

        # 性格特性が両方揃っている場合は科学的計算を使用
        use_calculator = (user_traits is not None and partner_traits is not None)

        if use_calculator:
            # PersonalityCalculatorで計算
            calculator = PersonalityCalculator(user_traits, partner_traits)

        personas: List[Persona] = []
        for idx, info in enumerate(children_info):
            # 出生順位を追加
            info["birth_order"] = f"第{idx + 1}子"

            if use_calculator:
                # 科学的計算を使用
                persona = self._child_from_calculator(idx, info, calculator)
            else:
                # 既存ロジックを使用（後方互換性）
                persona = self._child_from_info(idx + 1, info)

            personas.append(persona)

        return personas

    def _child_from_info(self, idx: int, info: Dict[str, Any]) -> Persona:
        desired_gender = info.get("desired_gender")
        name = info.get("name") or ("ゆう" if desired_gender == "男" else "さくら" if desired_gender == "女" else f"お子さん{idx}")
        role = info.get("role") or ("長男" if idx == 1 else "長女" if idx == 2 else f"子ども{idx}")
        style, traits = self._style_for_child(idx)
        goals = info.get("goals") or "家族で楽しい時間を増やす"

        background_parts = []
        if desired_gender:
            background_parts.append(f"希望された性別: {desired_gender}")
        if hobby := info.get("hobby"):
            background_parts.append(f"好きなこと: {hobby}")
        background = " / ".join(background_parts) if background_parts else "家族と一緒に遊ぶことが大好き"

        return Persona(
            name=name,
            role=role,
            speaking_style=info.get("speaking_style") or style,
            traits=info.get("traits") or traits,
            goals=goals,
            background=background,
            history=[{"speaker": "child", "message": "家族で遊園地に行きたいな"}]
        )

    def _default_child(self, idx: int) -> Persona:
        style, traits = self._style_for_child(idx)
        return Persona(
            name=f"お子さん{idx}",
            role=f"子ども{idx}",
            speaking_style=style,
            traits=traits,
            goals="家族みんなで笑い合いたい",
            background="未来の家族像を想像しながら話す",
            history=[{"speaker": "child", "message": "みんなで動物園に行きたいな"}]
        )

    def _style_for_child(self, idx: int):
        if idx == 1:
            return "元気で好奇心旺盛な口調", ["明るい", "冒険心"]
        if idx == 2:
            return "素直で優しい口調", ["思いやり", "甘えん坊"]
        return "落ち着いて面倒見の良い口調", ["しっかり者", "頼りになる"]

    def _child_from_calculator(
        self,
        idx: int,
        info: Dict[str, Any],
        calculator: PersonalityCalculator
    ) -> Persona:
        """PersonalityCalculatorを使用して子供ペルソナを生成"""
        # 性格特性を計算
        child_traits = calculator.calculate_child_traits(child_index=idx)

        # LLMで具体的な性格描写を生成
        personality_desc = calculator.generate_personality_description(child_traits, info)

        # 名前生成
        desired_gender = info.get("desired_gender")
        age = info.get("age", 5)

        default_names = {
            "女": ["さくら", "ゆい", "はな", "あおい"],
            "男": ["ゆう", "そうた", "はると", "りく"]
        }

        if desired_gender in default_names:
            name = info.get("name") or default_names[desired_gender][idx % len(default_names[desired_gender])]
        else:
            name = info.get("name") or f"お子さん{idx + 1}"

        role = f"第{idx + 1}子"

        return Persona(
            name=name,
            role=role,
            speaking_style=personality_desc["speaking_style"],
            traits=personality_desc["traits"],
            goals=personality_desc["goals"],
            background=personality_desc["personality_description"],
            history=[{
                "speaker": "child",
                "message": f"家族で{self._suggest_activity(child_traits)}したいな！"
            }]
        )

    def _suggest_activity(self, traits: BigFiveTraits) -> str:
        """性格特性に応じた活動を提案"""
        if traits.extraversion > 0.6:
            return "遊園地やテーマパークに行き"
        elif traits.openness > 0.6:
            return "博物館や科学館に行き"
        elif traits.conscientiousness > 0.6:
            return "一緒に料理やものづくりをし"
        elif traits.agreeableness > 0.6:
            return "ピクニックでのんびり過ごし"
        else:
            return "映画を観たり本を読んだりし"

    def _traits_from_big_five(self, big_five: BigFiveTraits) -> List[str]:
        """ビッグファイブから日本語の特徴リストを生成"""
        traits = []

        if big_five.openness > 0.6:
            traits.append("好奇心旺盛")
        if big_five.conscientiousness > 0.6:
            traits.append("しっかり者")
        if big_five.extraversion > 0.6:
            traits.append("社交的")
        if big_five.agreeableness > 0.6:
            traits.append("思いやりがある")
        if big_five.neuroticism < 0.4:
            traits.append("楽観的")

        return traits if traits else ["優しい", "明るい"]
