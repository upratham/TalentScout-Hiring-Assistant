from src.constants import MODEL, OPENAI_API_KEY, EXIT_KEYWORDS
from src.conversation import ConversationState
from src.core import Core
def run_pipeline_test():
    """
    Simulates a complete interview session to test the full pipeline.
    Prints each turn so you can see the conversation flow.
    """
    print("=" * 60)
    print("TALENTSCOUT PIPELINE TEST")
    print("=" * 60)
    
    # Initialise fresh conversation state
    state = ConversationState.initialise_conversation()
    
    # Get the opening greeting
    greeting = ConversationState.get_greeting(state=state)
    print(f"\nBot: {greeting}")
    
    # Simulate candidate inputs
    candidate_turns = [
        "Hi! I'm Alex Kumar.",
        "My email is alex.kumar@email.com and phone is +91-9988776655",
        "I have 3 years of experience.",
        "I'm looking for a Full Stack Developer role. Currently in Mumbai.",
        "My tech stack is Python, Django, React, and MongoDB.",
        "Sure, I'll answer the questions. "
        "For Python: I use decorators for cross-cutting concerns like logging and auth. "
        "I'm comfortable with async/await for IO-bound operations.",
        "done"  # exit keyword
    ]
    
    for user_input in candidate_turns:
        print(f"\nUser: {user_input}")
        
        # Check for exit before making an API call
        if Core.is_exit_intent(user_input):
            farewell = Core.handle_exit(state)
            print(f"\nBot: {farewell}")
            print("\n[Conversation ended]")
            break
        
        # Regular chat turn
        response = ConversationState.chat(state, user_input)
        print(f"\nBot: {response}")
        print("-" * 40)
    
    # Show final extracted info
    print("\n" + "=" * 60)
    print("FINAL EXTRACTED CANDIDATE INFO:")
    print("=" * 60)
    for key, val in state["candidate_info"].items():
        print(f"  {key}: {val}")
    
    print(f"\nTotal messages in history: {len(state['messages'])}")


# Uncomment to run the full pipeline test (makes multiple API calls)
run_pipeline_test()

print("Pipeline test function defined.")
print("Uncomment 'run_pipeline_test()' above and run this cell to test the full flow.")