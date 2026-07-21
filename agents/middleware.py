from langchain.agents.middleware import (
    ModelFallbackMiddleware,
    SummarizationMiddleware,
    ToolCallLimitMiddleware,
    ContextEditingMiddleware,
    ClearToolUsesEdit
)   

def get_middlewares() -> list:
    return [
        ModelFallbackMiddleware(
            "groq:llama-3.3-70b-versatile",       
            "google_genai:gemini-2.0-flash"
        ),
        SummarizationMiddleware(
            model="groq:llama-3.1-8b-instant",
            trigger=("tokens", 4000),
            keep=("messages", 20),
        ),
        ToolCallLimitMiddleware(
            thread_limit=20, 
            run_limit=10
        ),
        ContextEditingMiddleware(
            edits=[
                ClearToolUsesEdit(
                    trigger=10000,
                    keep=3,
                ),
            ]
        )
    ]