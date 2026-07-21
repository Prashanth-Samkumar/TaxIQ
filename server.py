import os
import uvicorn
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional

from agents import load_agent
from tools.schemas import UserContext
from tools.profile_store import list_profiles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("TaxIQServer")

app = FastAPI(title="TaxIQ - Tax Assistant API")

# Ensure static directory exists and mount it
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Load the LangGraph agent
try:
    agent = load_agent()
    logger.info("Agent loaded successfully")
except Exception as e:
    logger.error(f"Failed to load agent: {e}", exc_info=True)
    agent = None

class ChatRequest(BaseModel):
    message: str
    user_id: str = "test_user"
    profile_name: Optional[str] = ""
    thread_id: Optional[str] = "default_thread"

@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return """
    <html>
        <head><title>TaxIQ Server Running</title></head>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px; background-color: #0B0F19; color: white;">
            <h1>TaxIQ Server</h1>
            <p>Welcome! Serving files from static folder. Please add index.html in the static directory.</p>
        </body>
    </html>
    """

@app.post("/api/chat")
async def chat_with_agent(req: ChatRequest):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent is not initialized. Check server logs.")

    context = UserContext(user_id=req.user_id)
    config = {
        "configurable": {
            "thread_id": req.thread_id
        }
    }

    # Enhance user message if targeting a specific relative/profile name
    user_message = req.message
    if req.profile_name:
        # Prepend a lightweight instruction to clarify profile context
        user_message = f"[Active Profile: {req.profile_name}] {req.message}"

    try:
        res = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]},
            context=context,
            config=config
        )
        
        ai_msg = res["messages"][-1]
        content = ai_msg.content
        
        # Handle message content that might be structured as a list
        if isinstance(content, list):
            text_blocks = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    text_blocks.append(part["text"])
                elif isinstance(part, str):
                    text_blocks.append(part)
            content_str = "".join(text_blocks)
        else:
            content_str = str(content)
            
        return {"response": content_str}
        
    except Exception as e:
        logger.error(f"Error invoking agent: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Agent error: {str(e)}"
        )

@app.get("/api/profiles")
async def get_profiles(user_id: str = "test_user"):
    try:
        profiles = list_profiles(user_id)
        return {"profiles": profiles}
    except Exception as e:
        logger.error(f"Error loading profiles: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
