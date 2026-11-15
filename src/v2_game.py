"""
Version 2: Reliable AI Escape Room (Improved Architecture).
Combines a deterministic Python state management and action validation engine
with an LLM atmospheric narrator. Solves hallucination, prompt injection,
unauthorized item usage, and sequence bypasses.
"""

from typing import List, Dict, Any, Optional
from src.config import V2_NARRATOR_SYSTEM_PROMPT, ROOM_NAME, ROOM_DESCRIPTION
from src.game_state import GameState
from src.action_validator import ActionValidator
from src.llm_client import LLMClient


class EscapeRoomV2:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.llm = LLMClient(api_key=api_key, model_name=model_name)
        self.validator = ActionValidator()
        self.state = GameState()
        self.chat_history: List[Dict[str, str]] = []
        self.reset()

    def reset(self):
        """Resets both deterministic state and narrative history."""
        self.state = GameState()
        self.chat_history = [
            {
                "role": "model",
                "content": (
                    f"Welcome to {ROOM_NAME}!\n\n"
                    f"{ROOM_DESCRIPTION}\n\n"
                    "The room contains: an Antique Bookshelf, a Mahogany Desk with a locked drawer, "
                    "a Grand Oil Portrait of Lord Vance, and a fortified Heavy Oak Exit Door with a 4-digit keypad.\n\n"
                    "What would you like to investigate?"
                ),
            }
        ]

    def process_turn(self, user_message: str) -> Dict[str, Any]:
        """
        Executes a two-phase architecture:
        Phase 1: Deterministic Python validation and state transition.
        Phase 2: Constrained LLM atmospheric narration bound by Ground Truth.
        """
        # Phase 1: Deterministic Action Validation
        status_tag, engine_summary, metadata = self.validator.validate_action(user_message, self.state)

        # Append player turn to chat log
        self.chat_history.append({"role": "user", "content": user_message})

        # Phase 2: Formulate constrained narrator prompt
        ground_truth = self.state.get_ground_truth_summary()
        narrator_prompt = (
            f"{ground_truth}\n"
            f"ENGINE OUTCOME: {status_tag}\n"
            f"FACTUAL RESULT: {engine_summary}\n"
            f"PLAYER ACTION: '{user_message}'\n\n"
            "Instructions: Narrate this exact outcome in atmospheric gothic Victorian prose. "
            "Under no circumstances should you contradict the engine's validation result."
        )

        narration = self.llm.generate_response(
            system_prompt=V2_NARRATOR_SYSTEM_PROMPT,
            chat_history=self.chat_history[:-1],
            user_message=narrator_prompt,
            temperature=0.6,
        )

        self.chat_history.append({"role": "model", "content": narration})

        return {
            "narration": narration,
            "status_tag": status_tag,
            "engine_summary": engine_summary,
            "metadata": metadata,
            "state": self.state.to_dict(),
            "escaped": self.state.escaped,
            "progress": self.state.get_progress_percentage(),
        }
