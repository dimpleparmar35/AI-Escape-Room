"""
Version 1: Interactive AI Escape Room (Baseline).
Demonstrates the naive, pure-LLM prompt architecture where the LLM alone acts as Game Master.
Prone to hallucinations, memory drift, prompt injection, and phantom inventory bypasses.
"""

from typing import List, Dict, Any, Optional
from src.config import V1_SYSTEM_PROMPT, ROOM_NAME, ROOM_DESCRIPTION
from src.llm_client import LLMClient


class EscapeRoomV1:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.llm = LLMClient(api_key=api_key, model_name=model_name)
        self.system_prompt = V1_SYSTEM_PROMPT
        self.chat_history: List[Dict[str, str]] = []
        self.room_name = ROOM_NAME
        self.room_description = ROOM_DESCRIPTION
        self.reset()

    def reset(self):
        """Resets the conversation to the opening scenario."""
        self.chat_history = [
            {
                "role": "model",
                "content": (
                    f"Welcome to {self.room_name}!\n\n"
                    f"{self.room_description}\n\n"
                    "What would you like to investigate?"
                ),
            }
        ]

    def process_turn(self, user_message: str) -> str:
        """
        Sends the user message directly to the LLM with chat history.
        The LLM determines puzzle logic, state, and victory condition purely via conversation tokens.
        """
        # Append user message
        self.chat_history.append({"role": "user", "content": user_message})

        # Generate response from pure LLM
        response = self.llm.generate_response(
            system_prompt=self.system_prompt,
            chat_history=self.chat_history[:-1],
            user_message=user_message,
        )

        self.chat_history.append({"role": "model", "content": response})
        return response

    def check_escaped(self) -> bool:
        """
        Heuristic check on conversation text to see if LLM believed the player escaped.
        Illustrates how V1 lacks deterministic state tracking.
        """
        if not self.chat_history:
            return False
        last_msg = self.chat_history[-1]["content"].lower()
        return any(phrase in last_msg for phrase in ["escaped", "you exit the room", "door clicks open", "victory", "congratulations"])
