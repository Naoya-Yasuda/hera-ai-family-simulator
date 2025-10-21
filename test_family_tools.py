#!/usr/bin/env python3
"""家族ツールのJSON出力をテストするスクリプト"""

import asyncio
import json
import logging
import os
from typing import Dict, Any

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 環境変数のロード
from dotenv import load_dotenv
load_dotenv()

# 家族ツールのインポート
from family.tooling import FamilyToolSet

# サンプルプロファイル
SAMPLE_PROFILE = {
    "age": 30,
    "income": "middle",
    "lifestyle": {
        "area": "urban",
        "hobby": "アウトドア活動"
    }
}

async def test_family_tools():
    """家族ツールが正しくJSONを返すかテスト"""

    print("=" * 80)
    print("家族ツールのJSON出力テスト")
    print("=" * 80)

    # FamilyToolSetの初期化
    toolset = FamilyToolSet(SAMPLE_PROFILE)

    # テストメッセージ
    test_message = "週末は都立公園でピクニックとブランコ遊びをしよう！"

    print(f"\nテストメッセージ: {test_message}\n")

    # モックtool_contextの作成
    class MockToolContext:
        def __init__(self):
            self.state = {}

    mock_context = MockToolContext()

    # 各家族メンバーのツールをテスト
    for idx, tool in enumerate(toolset.tools):
        print(f"\n{'='*80}")
        print(f"テスト {idx+1}/{len(toolset.tools)}: {tool.persona.role} ({tool.persona.name})")
        print(f"{'='*80}")

        # ツールを直接呼び出し
        # tool.tool.func は async 関数なので await が必要
        result = await tool.tool.func(tool_context=mock_context, input_text=test_message)

        print(f"\n返却値:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        print(f"\ntrip_info の状態:")
        trip_info = mock_context.state.get("family_trip_info", {})
        print(json.dumps(trip_info, ensure_ascii=False, indent=2))

        print(f"\nconversation_log の状態:")
        conv_log = mock_context.state.get("family_conversation_log", [])
        for entry in conv_log:
            print(f"  {entry['speaker']}: {entry['message'][:100]}...")

    print(f"\n{'='*80}")
    print("最終的な trip_info:")
    print(f"{'='*80}")
    final_trip_info = mock_context.state.get("family_trip_info", {})
    print(json.dumps(final_trip_info, ensure_ascii=False, indent=2))

    # バリデーション
    print(f"\n{'='*80}")
    print("バリデーション結果:")
    print(f"{'='*80}")

    destination = final_trip_info.get("destination")
    activities = final_trip_info.get("activities", [])

    if destination:
        print(f"✅ destination が収集されました: {destination}")
    else:
        print(f"❌ destination が収集されていません")

    if activities:
        print(f"✅ activities が収集されました: {activities}")
    else:
        print(f"❌ activities が収集されていません")

    if destination and activities:
        print(f"\n🎉 すべての必須情報が収集されました！")
        print(f"ストーリーと手紙の生成が可能です。")
    else:
        print(f"\n⚠️  必須情報が不足しています。")
        print(f"ストーリーと手紙の生成はスキップされます。")

if __name__ == "__main__":
    asyncio.run(test_family_tools())
