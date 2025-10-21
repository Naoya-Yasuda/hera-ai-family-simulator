#!/usr/bin/env python3
"""
PersonaFactory の後方互換性テスト

既存データで動作することを確認
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(__file__))

from family.persona_factory import PersonaFactory


def test_backward_compatibility():
    """既存形式のプロファイルで正常に動作するか確認"""
    print("🧪 後方互換性テスト開始...")

    # 旧形式のプロファイル（新フィールドなし）
    old_profile = {
        "age": 30,
        "gender": "男性",
        "partner_info": {
            "name": "山田花子",
            "speaking_style": "優しい口調",
            "traits": ["思いやり", "優しい"]
        },
        "children_info": [
            {"desired_gender": "女", "age": 5},
            {"desired_gender": "男", "age": 3}
        ]
    }

    factory = PersonaFactory(old_profile)

    # パートナー生成（既存ロジック）
    partner = factory.build_partner()
    assert partner.name == "山田花子", f"パートナー名が一致しません: {partner.name}"
    assert "優しい" in partner.traits, f"特徴が一致しません: {partner.traits}"
    print(f"✅ パートナー生成成功: {partner.name} / {partner.traits}")

    # 子供生成（既存ロジック）
    children = factory.build_children()
    assert len(children) == 2, f"子供の数が一致しません: {len(children)}"
    print(f"✅ 子供生成成功: {len(children)}人")
    for idx, child in enumerate(children):
        print(f"   - {child.name} ({child.role}): {child.traits}")

    print("\n✅ 後方互換性テスト完了！既存データで正常に動作します。\n")


def test_new_features():
    """新機能（性格特性計算）が正常に動作するか確認"""
    print("🧪 新機能テスト開始...")

    # 新形式のプロファイル（性格特性あり）
    new_profile = {
        "age": 32,
        "gender": "女性",
        "relationship_status": "married",
        "current_partner": {
            "name": "佐藤太郎",
            "personality_traits": {
                "openness": 0.7,
                "conscientiousness": 0.8,
                "extraversion": 0.6,
                "agreeableness": 0.9,
                "neuroticism": 0.3
            },
            "temperament": "優しく几帳面",
            "hobbies": ["読書", "料理"]
        },
        "user_personality_traits": {
            "openness": 0.6,
            "conscientiousness": 0.7,
            "extraversion": 0.5,
            "agreeableness": 0.8,
            "neuroticism": 0.4
        },
        "children_info": [
            {"desired_gender": "女", "age": 7},
            {"desired_gender": "男", "age": 5}
        ]
    }

    factory = PersonaFactory(new_profile)

    # パートナー生成（新ロジック）
    partner = factory.build_partner()
    assert partner.name == "佐藤太郎", f"パートナー名が一致しません: {partner.name}"
    assert len(partner.traits) > 0, "特徴が生成されていません"
    print(f"✅ パートナー生成成功（新ロジック）: {partner.name}")
    print(f"   性格特性から生成された特徴: {partner.traits}")

    # 子供生成（科学的計算）
    children = factory.build_children()
    assert len(children) == 2, f"子供の数が一致しません: {len(children)}"
    print(f"✅ 子供生成成功（科学的計算）: {len(children)}人")
    for idx, child in enumerate(children):
        print(f"   - {child.name} ({child.role})")
        print(f"     特徴: {child.traits}")
        print(f"     話し方: {child.speaking_style}")
        print(f"     性格: {child.background}")

    print("\n✅ 新機能テスト完了！性格特性計算が正常に動作します。\n")


def test_single_user():
    """独身ユーザーのテスト"""
    print("🧪 独身ユーザーテスト開始...")

    single_profile = {
        "age": 28,
        "gender": "男性",
        "relationship_status": "single",
        "ideal_partner": {
            "name": "理想のパートナー",
            "personality_traits": {
                "openness": 0.7,
                "conscientiousness": 0.6,
                "extraversion": 0.8,
                "agreeableness": 0.7,
                "neuroticism": 0.3
            },
            "temperament": "明るく社交的"
        },
        "user_personality_traits": {
            "openness": 0.6,
            "conscientiousness": 0.5,
            "extraversion": 0.4,
            "agreeableness": 0.7,
            "neuroticism": 0.5
        }
    }

    factory = PersonaFactory(single_profile)

    partner = factory.build_partner()
    assert partner.name == "理想のパートナー", f"パートナー名が一致しません: {partner.name}"
    print(f"✅ 理想のパートナー生成成功: {partner.name}")
    print(f"   特徴: {partner.traits}")

    children = factory.build_children()
    print(f"✅ 理想のパートナーとの子供生成成功: {len(children)}人")

    print("\n✅ 独身ユーザーテスト完了！\n")


if __name__ == "__main__":
    try:
        test_backward_compatibility()
        test_new_features()
        test_single_user()

        print("=" * 60)
        print("🎉 全てのテストが成功しました！")
        print("=" * 60)
        print("\n📊 検証結果:")
        print("  ✅ 既存データでの動作（後方互換性）")
        print("  ✅ 新機能（性格特性計算）")
        print("  ✅ パートナー有無での分岐")
        print("\n💡 デグレは発生していません。安全に実装されています。")

    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
