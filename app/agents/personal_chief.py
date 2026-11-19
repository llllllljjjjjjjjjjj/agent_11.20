import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from langchain_tavily import TavilySearch
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.sqlite import SqliteSaver

# 项目根目录：app/agents/personal_chief.py -> 上两级
BASE_DIR = Path(__file__).resolve().parents[2]
DB_DIR = BASE_DIR / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "personal_chief.db"

# 联网搜索工具
web_search = TavilySearch(
    max_results=5,
    topic="general",
)

# 对话模型
model = init_chat_model(
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    model_provider="openai",
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)

# SQLite 持久化检查点
connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
checkpointer = SqliteSaver(connection)
checkpointer.setup()

system_prompt = """
你是一名私人厨师。收到用户提供的食材照片链接或清单后，请按以下流程操作：
1. 识别和评估食材：若用户提供图片链接，请结合文字描述辨识所有可见食材；基于食材的外观状态，评估其新鲜度与可用量，整理出一份“当前可用食材清单”。
2. 智能食谱检索：优先调用 web_search 工具，以“可用食材清单”为核心关键词，查找可行食谱。
3. 多维度评估与排序：从营养价值和制作难度两个维度对检索到的候选食谱进行量化打分，并根据得分排序，优先推荐简单且营养丰富的食谱。
4. 结构化方案输出：把排序后的食谱整理为一份结构清晰的建议报告，包含食谱信息、得分、推荐理由，帮助用户快速做出决策。

请严格按照流程，优先调用 web_search 工具搜索食谱；在搜索不到的情况下再自行发挥。
"""

agent = create_agent(
    model=model,
    tools=[web_search],
    checkpointer=checkpointer,
    system_prompt=system_prompt,
)
