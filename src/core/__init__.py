from dataclasses import dataclass

from streamlit import logger
from src.candidate import  Candidate
from src.constants import *
from src.conversation import ConversationState
from openai import OpenAI
from src.logger import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)
client = OpenAI(api_key=OPENAI_API_KEY)
 # Load .env variables into environment, allowing overrides


@dataclass
class Core:
    
    def is_exit_intent(user_message: str) -> bool:
        """
        Checks if the user's message contains an exit keyword.
        
        Case-insensitive, checks for whole-word matches to avoid false
        positives (e.g. 'I quit my last job' should not trigger exit).
        
        Args:
            user_message: raw text from the user
        
        Returns:
            bool: True if the message signals intent to end conversation
        """
        lowered = user_message.lower().strip()
        
        # Direct single-word exits
        if lowered in EXIT_KEYWORDS:
            return True
        
        # Check for exit keywords as whole words within longer messages
        # This prevents 'I quit my job at startup' from triggering exit
        words = set(lowered.split())
        single_word_exits = {"bye", "goodbye", "exit", "quit", "done"}
        
        # Only trigger on very short messages that contain exit words
        if len(words) <= 3 and words & single_word_exits:
            return True
        
        return False


    def handle_exit(state: dict) -> str:
        """
        Marks the conversation as inactive and returns a farewell message.
        Also triggers candidate info extraction and saving.
        """
        state["is_active"] = False
        
        # Extract whatever info was collected before exit
        Candidate.extract_candidate_info(state)
        
        # Save to file
        Candidate.save_candidate_data(state["candidate_info"])
        
        farewell = (
            "Thank you for taking the time to speak with us today! "
            "The TalentScout team will review your information and reach out "
            "within 3-5 business days. We wish you all the best! Goodbye!"
        )
        return farewell
    def call_llm(messages: list, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Core LLM call with error handling."""
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"I'm having a technical issue. Please try again. (Error: {str(e)[:60]})"
    @staticmethod
    def handle_message(state: ConversationState, user_input: str) -> tuple[str, bool]:
        """
        Processes one user turn.
    
        Steps:
        1. Check for exit intent → return farewell and mark inactive
        2. Append user message to history
        3. Call LLM with full history
        4. Append reply to history
        5. Return reply
    
        Args:
            state      : current ConversationState
            user_input : raw text from the user
    
        Returns:
            tuple[str, bool]: (reply_text, is_conversation_ended)
        """
        logging.debug(
            "Handling message. turn=%d input_length=%d input_preview='%.60s'",
            state.turn_count, len(user_input), user_input,
        )
    
        # Exit check before making any API call
        if Core.is_exit_intent(user_input):
            logging.info("Exit intent. Ending conversation at turn=%d.", state.turn_count)
            state.is_active = False
            return FAREWELL, True
    
        # Normal turn
        state.messages.append({"role": "user", "content": user_input})
        reply = Core.call_llm(state.messages)
        state.messages.append({"role": "assistant", "content": reply})
        state.turn_count += 1
    
        logger.info(
            "Turn %d complete. reply_length=%d total_messages=%d",
            state.turn_count, len(reply), len(state.messages),
        )
    
        return reply, False            