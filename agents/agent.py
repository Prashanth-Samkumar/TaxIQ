import os
import sqlite3
import logging
from dotenv import load_dotenv
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from prompts.prompt_builder import get_system_prompt
from agents.middleware import get_middlewares
from tools.schemas import UserContext
from tools import ALL_TOOLS

load_dotenv()

logger = logging.getLogger(__name__)
REQUIRED_KEYS = ["GROQ_API_KEY", "GOOGLE_API_KEY"]

def validate_env() -> None:
    """Validate that required environment variables are present."""
    missing = [k for k in REQUIRED_KEYS if not os.environ.get(k)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Please ensure they are set in your environment or .env file."
        )

def load_agent(db_path: str = "checkpoints.db"):
    """
    Validates environment, sets up SQLite checkpointer, and loads the TaxIQ agent.
    """
    validate_env()

    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn)
        checkpointer.setup()
    except sqlite3.Error as e:
        logger.error(f"SQLite initialization failed for database path '{db_path}': {e}")
        raise RuntimeError(f"Failed to initialize SQLite checkpointer at '{db_path}': {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error setting up checkpointer: {e}")
        raise RuntimeError(f"Error setting up agent checkpointer: {e}") from e

    try:
        agent = create_agent(
            model="groq:llama-3.3-70b-versatile",
            tools=ALL_TOOLS,
            context_schema=UserContext,
            middleware=get_middlewares(),
            system_prompt=get_system_prompt(),
            checkpointer=checkpointer
        )
        return agent
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise RuntimeError(f"Failed to initialize agent: {e}") from e