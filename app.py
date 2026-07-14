import sys
from dotenv import load_dotenv
load_dotenv(override=True)

from agents.agent import agent
from tools.schemas import UserContext
from rag import RagPipeline


def main():
    print("==================================================")
    print("      TaxIQ - Tax Assistant Agent (FY 2025-26)    ")
    print("==================================================")
    
    user_id = input("Enter User ID (default: test_user): ").strip()
    if not user_id:
        user_id = "test_user"
        
    print(f"\nLogged in as: {user_id}")
    print("Type your message to chat with TaxIQ. Type 'exit' to quit.\n")
    
    context = UserContext(user_id=user_id)
    thread_state = {"messages": []}
    
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
                
            # Append user message
            thread_state["messages"].append({"role": "user", "content": user_input})
            
            # Invoke the agent
            res = agent.invoke(thread_state, context=context)
            
            # Update local thread state messages
            thread_state["messages"] = res["messages"]
            
            # Print last AI message
            ai_msg = res["messages"][-1]
            content = ai_msg.content
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
            print(f"\nTaxIQ: {content_str}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    rag = RagPipeline()
    print(rag.retrieve("What is the income tax rate for FY 2025-26?")) 