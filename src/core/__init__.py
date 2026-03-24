from dataclasses import dataclass
from src.candidate import  Candidate
from src.constants import *
from src.logger import configure_logger
logging = configure_logger()
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

        