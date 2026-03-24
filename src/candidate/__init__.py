from dataclasses import dataclass
from src.constants import *
from datetime import datetime
from openai import OpenAI
import json
import os
from src.logger import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)
client = OpenAI(api_key=OPENAI_API_KEY)

@dataclass
class Candidate:
    @staticmethod
    def save_candidate_data(candidate_info: dict) -> bool:
        """
        Saves candidate info to a JSONL file (JSON Lines format).
        
        Appends each candidate as a single JSON line.
        No need to read entire file — just append.
        
        Args:
            candidate_info: dict of collected candidate fields
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        # Skip saving if no meaningful data was collected
        has_data = any(
            v is not None 
            for k, v in candidate_info.items() 
            if k != "timestamp"
        )
        
        if not has_data:
            print("No candidate data to save.")
            return False
        
        try:
            # Append this candidate as a single JSON line
            with open(CANDIDATES_FILE, "a") as f:
                json.dump(candidate_info, f)
                f.write("\n")  # newline after each JSON object
            
            print(f"Candidate data saved to {CANDIDATES_FILE}")
            return True
        
        except Exception as e:
            print(f"Error saving candidate data: {e}")
            return False


    @staticmethod
    def view_saved_candidates() -> list:
        """Utility to read all saved candidates from JSONL file for review."""
        if not os.path.exists(CANDIDATES_FILE):
            print("No candidates file found yet.")
            return []
        
        all_candidates = []
        with open(CANDIDATES_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    all_candidates.append(json.loads(line))
        
        print(f"Total candidates saved: {len(all_candidates)}")
        for i, c in enumerate(all_candidates, 1):
            print(f"  [{i}] {c.get('name', 'Unknown')} — {c.get('desired_position', 'N/A')} — {c.get('timestamp', '')}")
        
        return all_candidates
    
    @staticmethod
    def extract_candidate_info(state: dict) -> dict:
        """
        Runs a separate LLM call to extract structured candidate info
        from the conversation history.
        
        This is a one-shot extraction call — it does NOT add to the
        main conversation history. It reads the history as a transcript.
        
        Args:
            state: the conversation state dict
        
        Returns:
            dict: extracted candidate fields
        """
        # Build a plain-text transcript from the conversation history
        # Skip the system prompt (index 0)
        transcript_lines = []
        for msg in state["messages"][1:]:  # skip system prompt
            role = "Candidate" if msg["role"] == "user" else "TalentBot"
            transcript_lines.append(f"{role}: {msg['content']}")
        
        transcript = "\n".join(transcript_lines)
        
        # Separate API call just for extraction
        # This does NOT affect the main conversation state
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {"role": "user", "content": f"Transcript:\n{transcript}"}
                ],response_format={"type": "json_object"},
                temperature=0.0,   # extraction should be deterministic
                max_tokens=400
            )
            
            raw = response.choices[0].message.content.strip()
            
            # Strip markdown code fences if the model adds them anyway
            raw = raw.replace("```json", "").replace("```", "").strip()
            
            extracted = json.loads(raw)
            
            # Merge into state — only update fields that were extracted
            for key in ["name", "email", "phone", "years_experience",
                        "desired_position", "location", "tech_stack"]:
                if extracted.get(key) is not None:
                    state["candidate_info"][key] = extracted[key]
            
            return state["candidate_info"]
        
        except json.JSONDecodeError as e:
            print(f"JSON parse error during extraction: {e}")
            print(f"Raw response was: {raw}")
            return state["candidate_info"]
        
        except Exception as e:
            print(f"Extraction error: {e}")
            return state["candidate_info"]
        
    
def generate_technical_questions(tech_stack: list, years_experience: int = 2) -> str:
    """
    Generates tailored technical interview questions for a given tech stack.
    
    This is a standalone utility — it does not interact with the main
    conversation state. Useful for testing or calling independently.
    
    Args:
        tech_stack: list of technologies, e.g. ['Python', 'Django', 'PostgreSQL']
        years_experience: int, used to calibrate question difficulty
    
    Returns:
        str: formatted block of interview questions
    """
    if not tech_stack:
        return "No tech stack provided. Please specify technologies first."
    
    stack_str = ", ".join(tech_stack)
    user_request = (
        f"Candidate has {years_experience} years of experience. "
        f"Tech stack: {stack_str}. "
        f"Generate interview questions."
    )
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": QUESTION_GEN_PROMPT},
                {"role": "user",   "content": user_request}
            ],
            temperature=0.7,
            max_tokens=1200
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error generating questions: {e}"
    
