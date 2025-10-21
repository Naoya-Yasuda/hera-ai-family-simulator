"""
遺伝学・心理学に基づいた子供の性格計算モジュール

ビッグファイブ性格特性の遺伝率研究に基づき、親の性格から子供の性格を科学的に推定します。
"""

from __future__ import annotations

import asyncio
import json
import re
import random
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class BigFiveTraits:
    """ビッグファイブ性格特性（0.0-1.0のスケール）"""
    openness: float = 0.5           # 開放性（新しい経験への積極性）
    conscientiousness: float = 0.5  # 誠実性（計画性・責任感）
    extraversion: float = 0.5       # 外向性（社交性・活発さ）
    agreeableness: float = 0.5      # 協調性（思いやり・協力性）
    neuroticism: float = 0.5        # 神経症傾向（情緒不安定性）

    def to_dict(self) -> Dict[str, float]:
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism
        }


class PersonalityCalculator:
    """科学的根拠に基づく子供の性格計算

    参考文献:
    - Bouchard & McGue (2003) 双生児研究による遺伝率推定
    - Polderman et al. (2015) メタ分析による性格の遺伝率
    """

    # 遺伝率（研究ベースの推定値）
    HERITABILITY = {
        "openness": 0.57,
        "conscientiousness": 0.49,
        "extraversion": 0.54,
        "agreeableness": 0.42,
        "neuroticism": 0.48
    }

    # 環境要因の影響（残りの分散）
    ENVIRONMENT_FACTOR = {
        "openness": 0.43,
        "conscientiousness": 0.51,
        "extraversion": 0.46,
        "agreeableness": 0.58,
        "neuroticism": 0.52
    }

    def __init__(self, user_traits: Dict[str, float], partner_traits: Dict[str, float]):
        """
        Args:
            user_traits: ユーザーの性格特性（ビッグファイブ）
            partner_traits: パートナーの性格特性
        """
        self.user_traits = BigFiveTraits(**user_traits)
        self.partner_traits = BigFiveTraits(**partner_traits)

    def calculate_child_traits(self, child_index: int = 0) -> BigFiveTraits:
        """
        子供の性格特性を計算

        計算ロジック:
        1. 遺伝的要因: 両親の平均値を基準に遺伝率を適用
        2. 環境要因: ランダム性を加味（兄弟間の差異を表現）
        3. 出生順位効果: 第一子と第二子で微調整

        Args:
            child_index: 子供のインデックス（0=第一子, 1=第二子）

        Returns:
            計算された子供の性格特性
        """
        child_traits = {}

        for trait_name in ["openness", "conscientiousness", "extraversion",
                          "agreeableness", "neuroticism"]:
            # 1. 両親の平均値（遺伝的ベースライン）
            parent_avg = (
                getattr(self.user_traits, trait_name) +
                getattr(self.partner_traits, trait_name)
            ) / 2

            # 2. 遺伝的要因（遺伝率を適用）
            genetic_component = parent_avg * self.HERITABILITY[trait_name]

            # 3. 環境要因（ランダム性）
            # 正規分布に従う環境要因（平均0.5、標準偏差0.15）
            environmental_noise = random.gauss(0.5, 0.15)
            environmental_component = environmental_noise * self.ENVIRONMENT_FACTOR[trait_name]

            # 4. 出生順位効果
            birth_order_adjustment = self._birth_order_effect(trait_name, child_index)

            # 5. 合成（0-1の範囲にクランプ）
            final_value = genetic_component + environmental_component + birth_order_adjustment
            final_value = max(0.0, min(1.0, final_value))

            child_traits[trait_name] = round(final_value, 2)

        return BigFiveTraits(**child_traits)

    def _birth_order_effect(self, trait_name: str, child_index: int) -> float:
        """
        出生順位による性格への影響

        研究結果（Sulloway, 1996等）:
        - 第一子: より誠実性が高い、責任感が強い
        - 後続子: より開放性が高い、外向的
        """
        if child_index == 0:  # 第一子
            adjustments = {
                "conscientiousness": 0.05,  # より誠実
                "agreeableness": 0.03,      # より協調的
                "extraversion": -0.02,      # やや内向的
                "openness": -0.02,          # やや保守的
                "neuroticism": 0.01         # やや慎重
            }
        elif child_index == 1:  # 第二子
            adjustments = {
                "conscientiousness": -0.03,
                "agreeableness": 0.02,
                "extraversion": 0.04,       # より外向的
                "openness": 0.05,           # より開放的
                "neuroticism": -0.01
            }
        else:  # 第三子以降
            adjustments = {
                "conscientiousness": -0.04,
                "agreeableness": 0.04,
                "extraversion": 0.05,
                "openness": 0.06,
                "neuroticism": -0.02
            }

        return adjustments.get(trait_name, 0.0)

    def generate_personality_description(
        self,
        traits: BigFiveTraits,
        child_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        性格特性から具体的な性格描写を生成（LLM使用）

        Args:
            traits: ビッグファイブ特性
            child_info: 子供の基本情報（年齢、性別など）

        Returns:
            speaking_style, traits_list, goals, background等
        """
        try:
            from google.generativeai import GenerativeModel
            model = GenerativeModel('gemini-2.5-pro')

            prompt = f"""
あなたは児童心理学者です。以下の科学的性格特性データから、子供のキャラクター設定を作成してください。

【ビッグファイブ性格特性】（0-1スケール）
- 開放性（Openness）: {traits.openness}
  高い→好奇心旺盛、創造的、新しいことが好き
  低い→慣れたことを好む、現実的

- 誠実性（Conscientiousness）: {traits.conscientiousness}
  高い→計画的、責任感が強い、几帳面
  低い→自由奔放、柔軟

- 外向性（Extraversion）: {traits.extraversion}
  高い→社交的、活発、人懐っこい
  低い→内向的、静か、一人の時間を大切に

- 協調性（Agreeableness）: {traits.agreeableness}
  高い→優しい、思いやり、協力的
  低い→競争的、自己主張が強い

- 神経症傾向（Neuroticism）: {traits.neuroticism}
  高い→感受性が強い、慎重、心配性
  低い→落ち着いている、楽観的

【子供情報】
- 年齢: {child_info.get('age', 5)}歳
- 性別: {child_info.get('desired_gender', '未定')}
- 出生順位: {child_info.get('birth_order', '第一子')}

【出力形式】JSON
{{
  "speaking_style": "話し方の特徴（例: 元気いっぱいで好奇心旺盛な口調）",
  "traits": ["特徴1", "特徴2", "特徴3"],
  "personality_description": "性格の総合的な説明（2-3文）",
  "goals": "この子の目標や願い",
  "typical_behaviors": ["行動特徴1", "行動特徴2"]
}}

重要: 年齢に応じた自然な子供らしさを保ちつつ、科学的データを反映してください。
"""

            response = model.generate_content(prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)

            # JSON抽出
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))

        except Exception as e:
            print(f"⚠️ LLM性格描写生成エラー: {e}")

        # フォールバック
        return self._fallback_description(traits)

    def _fallback_description(self, traits: BigFiveTraits) -> Dict[str, Any]:
        """LLM失敗時のフォールバック描写"""
        traits_list = []

        if traits.openness > 0.6:
            traits_list.append("好奇心旺盛")
        if traits.conscientiousness > 0.6:
            traits_list.append("しっかり者")
        if traits.extraversion > 0.6:
            traits_list.append("元気いっぱい")
        if traits.agreeableness > 0.6:
            traits_list.append("思いやりがある")
        if traits.neuroticism < 0.4:
            traits_list.append("楽観的")

        if not traits_list:
            traits_list = ["明るい", "優しい"]

        if traits.extraversion > 0.6:
            speaking_style = "元気で活発な口調"
        elif traits.conscientiousness > 0.6:
            speaking_style = "しっかりした落ち着いた口調"
        else:
            speaking_style = "優しく素直な口調"

        return {
            "speaking_style": speaking_style,
            "traits": traits_list,
            "personality_description": f"{', '.join(traits_list)}な子供",
            "goals": "家族で楽しく過ごす",
            "typical_behaviors": ["家族と遊ぶ", "新しいことに興味を持つ"]
        }
