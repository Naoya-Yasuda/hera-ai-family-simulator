"""
ロールベース家族エージェントシステムの使用例
"""

import os
from role_system import FamilyConfigurationManager, FamilyRole
from enhanced_simultaneous_chat import EnhancedSimultaneousChatManager


def main():
    """使用例のメイン関数"""

    # OpenAI APIキーを設定
    openai_api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")

    # ユーザープロファイルの例
    user_profile = {
        "age": 28,
        "income_range": "400-600万円",
        "lifestyle": {
            "location": "東京",
            "work_style": "会社員",
            "hobbies": ["読書", "映画鑑賞", "旅行"]
        },
        "interests": ["読書", "映画", "旅行", "料理"],
        "partner_info": {
            "name": "美咲",
            "age": 26,
            "personality": "優しくて家族思い"
        },
        "children_info": [
            {
                "age": 5,
                "gender": "male",
                "personality": "好奇心旺盛"
            },
            {
                "age": 3,
                "gender": "female",
                "personality": "元気いっぱい"
            }
        ]
    }

    # セッションID
    session_id = "demo_session_001"

    print("=== ロールベース家族エージェントシステム デモ ===\n")

    # 1. 家族構成管理システムの初期化
    print("1. 家族構成管理システムを初期化...")
    family_config_manager = FamilyConfigurationManager(openai_api_key)

    # 2. 家族構成を設定
    print("2. ユーザープロファイルに基づいて家族構成を設定...")
    family_agents = family_config_manager.configure_family(user_profile, session_id)

    print(f"生成された家族メンバー: {len(family_agents)}人")
    for agent in family_agents:
        print(f"- {agent.name} ({agent.role.value}): {agent.age}歳")

    # 3. 同時対話システムの初期化
    print("\n3. 同時対話システムを初期化...")
    chat_manager = EnhancedSimultaneousChatManager(openai_api_key)

    # 4. 家族チャットを開始
    print("4. 家族チャットを開始...")
    active_agents = chat_manager.start_family_chat(session_id, user_profile)

    print(f"アクティブな家族メンバー: {len(active_agents)}人")
    for agent in active_agents:
        print(f"- {agent.name} ({agent.role.value})")

    # 5. ユーザーメッセージの処理例
    print("\n5. ユーザーメッセージの処理例...")

    test_messages = [
        "こんにちは！今日は家族で何をしましょうか？",
        "子どもたちと一緒に公園に行きたいです",
        "おじいちゃん、おばあちゃんも一緒に来ませんか？"
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"\n--- メッセージ {i}: {message} ---")

        # ユーザーメッセージを処理
        responses = chat_manager.process_user_message(message)

        # 家族メンバーの応答を表示
        for response in responses:
            print(f"{response.speaker} ({response.role}): {response.message}")
            print(f"  感情: {response.emotion}")

    # 6. 幸せなひとときの表示
    print("\n6. 抽出された幸せなひととき...")
    happy_moments = chat_manager.get_happy_moments()

    for i, moment in enumerate(happy_moments, 1):
        print(f"\n幸せなひととき {i}:")
        print(f"  活動: {moment.activity}")
        print(f"  説明: {moment.description}")
        print(f"  感情: {moment.emotions}")
        print(f"  参加者: {moment.participants}")
        print(f"  設定: {moment.setting}")
        print(f"  ロール別の関与: {moment.role_interactions}")

    # 7. 家族シーンの生成
    print("\n7. 家族シーンの生成...")
    family_scene = chat_manager.generate_family_scene()

    if family_scene:
        print("生成された家族シーン:")
        for key, value in family_scene.items():
            print(f"  {key}: {value}")

    # 8. エージェントの動的な追加・削除の例
    print("\n8. エージェントの動的な管理...")

    # 新しい家族メンバーを追加（例：ペット）
    print("ペットを家族に追加...")
    pet_agent = chat_manager.add_family_member(
        FamilyRole.PET,
        custom_params={
            "name": "ポチ",
            "age": 3,
            "personality": "元気で人懐っこい",
            "interests": ["散歩", "おもちゃ", "家族"]
        }
    )
    print(f"追加されたペット: {pet_agent.name}")

    # 特定のロールのエージェントを取得
    print("\n特定のロールのエージェントを取得...")
    children = chat_manager.get_agents_by_role(FamilyRole.CHILD)
    print(f"子どもエージェント: {len(children)}人")
    for child in children:
        print(f"- {child.name}: {child.age}歳")

    # 9. 会話履歴の表示
    print("\n9. 会話履歴...")
    conversation_history = chat_manager.get_conversation_history()
    print(f"総会話数: {len(conversation_history)}")

    # 最新の会話を表示
    recent_messages = conversation_history[-3:]  # 最新3件
    for msg in recent_messages:
        print(f"{msg.speaker} ({msg.role}): {msg.message}")

    # 10. 各メンバーの感情状態
    print("\n10. 各メンバーの現在の感情...")
    emotions = chat_manager.get_member_emotions()
    for name, emotion in emotions.items():
        print(f"{name}: {emotion}")

    print("\n=== デモ完了 ===")


def demonstrate_role_customization():
    """ロールカスタマイズの例"""

    openai_api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")
    family_config_manager = FamilyConfigurationManager(openai_api_key)

    print("\n=== ロールカスタマイズの例 ===")

    # カスタムパラメータでパートナーエージェントを作成
    custom_partner_params = {
        "name": "さくら",
        "age": 30,
        "personality_traits": ["アーティスティック", "創造的", "家族思い"],
        "interests": ["絵画", "音楽", "家族時間"],
        "values": ["創造性", "家族の絆", "美しさ"]
    }

    user_profile = {"age": 28, "interests": ["アート", "音楽"]}

    # カスタムパートナーエージェントを生成
    partner_agent = family_config_manager.role_factory.create_agent_from_role(
        role=FamilyRole.PARTNER,
        user_profile=user_profile,
        custom_params=custom_partner_params
    )

    print(f"カスタムパートナー: {partner_agent.name}")
    print(f"年齢: {partner_agent.age}歳")
    print(f"性格: {partner_agent.personality}")
    print(f"興味: {partner_agent.interests}")
    print(f"価値観: {partner_agent.values}")

    # カスタムパートナーとの会話例
    print("\nカスタムパートナーとの会話例:")
    response = partner_agent.generate_response("今日は何をしたい？")
    print(f"ユーザー: 今日は何をしたい？")
    print(f"{partner_agent.name}: {response}")


if __name__ == "__main__":
    main()
    demonstrate_role_customization()
