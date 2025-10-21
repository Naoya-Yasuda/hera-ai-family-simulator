from .hera.adk_hera_agent import ADKHeraAgent
import os
from dotenv import load_dotenv
from family import create_family_session

# 環境変数を読み込み
load_dotenv()

# ヘーラーエージェントのインスタンスを作成
hera_agent = ADKHeraAgent(
    gemini_api_key=os.getenv("GEMINI_API_KEY")
)

# ADKが期待するBaseAgentのインスタンスを返す
# ADKHeraAgent内のAgentインスタンスを直接使用
root_agent = hera_agent.agent
