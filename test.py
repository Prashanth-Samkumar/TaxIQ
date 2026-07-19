from agents import load_agent
from tools.schemas import UserContext
from langchain_core.utils.uuid import uuid7
import os
from dotenv import load_dotenv
load_dotenv()

config = {"configurable": {"thread_id": str(uuid7())}}
agent = load_agent()

res = agent.invoke(
    {"messages": [{'role':'user', "content":"hello"}] }, 
    context=UserContext(user_id="001"),
    config = config
    )

print(res['messages'][-1].content)