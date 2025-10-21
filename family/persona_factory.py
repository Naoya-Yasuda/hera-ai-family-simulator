from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


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
        partner_info = self.profile.get("partner_info") or {}
        description = self.profile.get("partner_face_description")
        future_hope = (self.profile.get("lifestyle") or {}).get("future_hope")

        name = partner_info.get("name") or "未来のパートナー"
        role = partner_info.get("role") or "パートナー"
        style = partner_info.get("speaking_style") or "落ち着いた優しい口調"
        traits = partner_info.get("traits") or ["共感的", "思いやり", "支えになりたい"]
        goals = partner_info.get("goals") or "家族の夢を一緒に叶える"

        background_parts = []
        if description:
            background_parts.append(f"外見の特徴: {description}")
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
        children_info = self.profile.get("children_info") or []
        if not children_info:
            return [self._default_child(1), self._default_child(2)]

        personas: List[Persona] = []
        for idx, info in enumerate(children_info, start=1):
            personas.append(self._child_from_info(idx, info))
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
