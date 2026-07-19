
from functools import cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

@cache
def get_system_prompt() -> str:
    """Loads and caches the tax agent's system prompt."""
    path = PROMPTS_DIR / "tax_agent_system_prompt.txt"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise RuntimeError(f"System prompt not found at {path}") from e

