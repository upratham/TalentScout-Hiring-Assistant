from dataclasses import dataclass, field
from src.constants import *
from datetime import datetime
from openai import OpenAI
import json
from src.logger import configure_logger
logging = configure_logger()
client = OpenAI(api_key=OPENAI_API_KEY)

@dataclass
class ConversationState:
    @staticmethod
    def initialise_conversation():
        """
        Creates a fresh conversation state.
        
        Returns a dict with:
        - messages: the full chat history sent to the LLM each turn
        - candidate_info: structured storage for collected fields
        - is_active: flag to know if conversation is still running
        """
        return {
            # The messages list — grows with every turn
            # We include the system prompt as the first message
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT}
            ],
            
            # Candidate fields we want to collect
            # These start as None and get filled in as the conversation progresses
            "candidate_info": {
                "name": None,
                "email": None,
                "phone": None,
                "years_experience": None,
                "desired_position": None,
                "location": None,
                "tech_stack": None,
                "timestamp": datetime.now().isoformat()
            },
            
            # Conversation control
            "is_active": True,
            "questions_asked": False  # track whether tech questions were generated
        }
    
    @staticmethod
    def chat(state: dict, user_message: str) -> str:
        """
        Sends a user message to the LLM and returns the assistant's reply.
        
        Mutates state['messages'] in place — appends both the user message
        and the assistant reply to the history.
        
        Args:
            state: the conversation state dict from initialise_conversation()
            user_message: the raw text typed by the user
        
        Returns:
            str: the assistant's reply text
        """
        # Step 1: Add the user's message to history
        state["messages"].append({
            "role": "user",
            "content": user_message
        })
        
        # Step 2: Call the OpenAI API with the FULL history
        # The system prompt is always messages[0], so the LLM always
        # has its instructions + full conversation context
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=state["messages"],  # <-- entire history every time
                temperature=0.7,             # balance between creativity and consistency
                max_tokens=1000              # enough for detailed technical questions
            )
            
            # Step 3: Extract the reply text
            assistant_reply = response.choices[0].message.content
            
        except Exception as e:
            # Graceful error handling — show a friendly message instead of crashing
            assistant_reply = ("I'm experiencing a technical issue right now. "
                            "Please try again in a moment.")
            logging.error(f"API Error: {e}")
        
        # Step 4: Add the assistant's reply to history
        # This is critical — future turns will include this in context
        state["messages"].append({
            "role": "assistant",
            "content": assistant_reply
        })
        
        return assistant_reply

    @staticmethod
    def get_greeting(state: dict) -> str:
        """
        Triggers the initial greeting from the bot.
        Called once when the conversation starts.
        """
        
        return ConversationState.chat(state, "Hello, I am ready to start the interview process.")

    