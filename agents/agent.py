from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from prompts.prompt_builder import get_system_prompt
from agents.middleware import get_middlewares
from tools.schemas import UserContext
from tools import ALL_TOOLS

def load_agent(): 

    agent = create_agent(
        model="groq:llama-3.3-70b-versatile",
        tools=ALL_TOOLS,
        context_schema=UserContext,
        middleware=get_middlewares(),
        system_prompt=get_system_prompt(),
        checkpointer=InMemorySaver()
    )
    return agent