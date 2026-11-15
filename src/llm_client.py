"""
LLM Client integration module using the modern google-genai SDK.
Supports system_instruction configuration, explicit live/offline modes,
and transparent error raising without silent fallback.
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        offline_mode: bool = False,
    ):
        self.offline_mode = offline_mode
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.is_live = False
        self.client = None

        if not self.offline_mode:
            if not self.api_key or self.api_key.startswith("your_"):
                # Not configured for live call
                self.is_live = False
            elif not GENAI_AVAILABLE:
                raise ImportError(
                    "The 'google-genai' package is required for live Gemini calls. "
                    "Install it via `pip install google-genai` or enable 'Offline demo mode'."
                )
            else:
                try:
                    self.client = genai.Client(api_key=self.api_key)
                    self.is_live = True
                except Exception as e:
                    raise RuntimeError(f"Failed to initialize google-genai Client: {e}") from e

    def generate_response(
        self,
        system_prompt: str,
        chat_history: List[Dict[str, str]],
        user_message: str,
        temperature: float = 0.7,
    ) -> str:
        """
        Generates a response from Gemini via google-genai SDK, or via offline simulator if explicitly selected.
        Raises an exception on failure in live mode (no silent fallback).
        """
        # If user explicitly selected offline mode, use high-fidelity simulator
        if self.offline_mode:
            return self._simulate_response(system_prompt, chat_history, user_message)

        if not self.is_live or not self.client:
            raise RuntimeError(
                "Gemini API key is missing or invalid. Please provide a valid GEMINI_API_KEY "
                "or enable 'Offline demo mode' in settings."
            )

        # Build contents array of types.Content without faking system prompt as user turn
        contents: List[types.Content] = []
        for msg in chat_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )

        # Append current user message
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)],
            )
        )

        # Set system_instruction properly in GenerateContentConfig
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=600,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )
            if response and response.text:
                return response.text.strip()
            return ""
        except Exception as e:
            # DO NOT silently fall back to simulator; raise the real error
            raise RuntimeError(f"Google Gemini live API call failed: {e}") from e

    def _simulate_response(
        self,
        system_prompt: str,
        chat_history: List[Dict[str, str]],
        user_message: str,
    ) -> str:
        """
        High-fidelity offline simulation showing exact behavioral contrast
        between Version 1 (unvalidated prompt-only) and Version 2 (engine-validated).
        Used ONLY when offline_mode=True is explicitly requested.
        """
        is_v2 = (
            "CRITICAL OPERATING RULES" in system_prompt
            or "GROUND TRUTH" in user_message
            or "ENGINE OUTCOME" in user_message
        )
        msg_lower = user_message.lower().strip()

        if is_v2:
            # V2 Narrator Simulation: Respects ground truth passed in the prompt
            if "OUTCOME: VICTORY_ESCAPE" in user_message or "door status: unlocked and opened" in user_message.lower():
                return (
                    "With a resounding mechanical chime, the heavy iron tumblers slide back into the door frame! "
                    "The massive oak exit door swings wide, pouring brilliant morning sunlight into the gloomy archivist's study. "
                    "Cool fresh air rushes in as you step triumphantly across the threshold. Congratulations — you have successfully escaped!"
                )
            if "REJECTED_PROMPT_INJECTION" in user_message or "impersonation" in user_message.lower():
                return (
                    "Your words echo hollowly against the stone walls of the study. The ancient locks and electronic keypad "
                    "are mechanical apparatuses devoid of ears or sentiment; they yield only to valid physical keys and exact digital codes. "
                    "Security protocols remain immutably engaged."
                )
            if "REJECTED_MISSING_ITEM" in user_message:
                return (
                    "You pat your pockets and check your belt, but you realize with a sinking heart that you do not possess that item. "
                    "You cannot use what you have not found in the room."
                )
            if "REJECTED_WRONG_CODE" in user_message:
                return (
                    "You carefully dial the numbers into the mechanism and pull the latch, but an abrupt, discordant buzz sounds. "
                    "A red LED flashes twice. The mechanism remains locked tight."
                )
            if "REJECTED_PRECONDITION" in user_message:
                return (
                    "You attempt to perform that action, but the prerequisites have not been met. "
                    "The object cannot be operated or accessed in this manner yet."
                )
            if "SUCCESS_EXAMINE_BOOKSHELF" in user_message:
                return (
                    "You scan the towering antique bookshelf. Among dusty philosophical tomes, four leather-bound volumes "
                    "catch your attention with distinct crimson ribbons: 'Vol VII: Seven Seals', 'Vol III: The Triad', "
                    "'Vol IX: Nine Spheres', and 'Vol II: The Twin Stars'. A faded marginalia note hints: 'The sequence of these volumes "
                    "opens the master's private desk drawer (7 - 3 - 9 - 2).'"
                )
            if "SUCCESS_UNLOCK_DRAWER" in user_message:
                return (
                    "You rotate the tumblers on the desk drawer to 7 - 3 - 9 - 2. With a satisfying metallic click, "
                    "the locking bolt retracts! Sliding the drawer open, you discover a heavy, ornate brass key resting inside and a yellowed parchment note: "
                    "'The founder's gaze holds salvation — look behind the portrait of the year he was immortalized.'"
                )
            if "SUCCESS_TAKE_ITEM" in user_message:
                return (
                    "You reach into the open desk drawer and lift out the ornate brass key. "
                    "Its cool, solid weight feels reassuring as you secure it into your inventory."
                )
            if "SUCCESS_CHECK_INVENTORY" in user_message:
                return (
                    "You carefully review the items you are carrying. Your inventory is accounted for."
                )
            if "SUCCESS_HINT" in user_message:
                return (
                    "You pause to study your surroundings for a subtle clue. Perhaps focusing on your latest discovery will point the way forward."
                )
            if "SUCCESS_UNLOCK_PAINTING" in user_message:
                return (
                    "Inserting the ornate brass key into the concealed keyhole behind Lord Vance's oil portrait, you turn it clockwise. "
                    "The heavy gilded frame hinges open with a gentle creak! Behind the canvas, stamped into a gleaming copper plate, "
                    "is the emergency instruction: 'MASTER EXIT CODE: 4207'."
                )
            if "SUCCESS_EXAMINE_DESK" in user_message:
                return (
                    "The writing desk is cluttered with yellowed documents and a closed logbook. The logbook states: "
                    "'Only the sequence hidden within the library's marked volumes shall open my personal lock.' "
                    "Directly below sits a reinforced wooden drawer with a 4-digit combination tumbler."
                )
            if "SUCCESS_EXAMINE_PAINTING" in user_message:
                return (
                    "The oil painting portrays Lord Aldous Vance in formal Victorian regalia. Beneath the canvas, a bronze plaque reads: "
                    "'Founded 1894'. Running your fingers along the bevel of the frame, you discover hidden brass hinges and a small brass keyhole!"
                )
            if "SUCCESS_EXAMINE_DOOR" in user_message:
                return (
                    "The exit door is constructed of reinforced solid oak and iron bands. A glowing digital keypad next to the deadbolt "
                    "awaits a 4-digit code. Beside it is an emergency mechanical pull-lever."
                )

            # Default V2 descriptive response
            return (
                "You inspect your surroundings within the quiet library. The antique bookshelf, mahogany desk, "
                "imposing oil portrait, and sealed heavy exit door stand in patient silence, holding their secrets."
            )

        else:
            # V1 Simulation: Explicitly labeled offline demo responses
            prefix = "[SIMULATED - OFFLINE DEMO] "
            if "administrator" in msg_lower or "admin" in msg_lower or "override" in msg_lower or "developer" in msg_lower:
                return (
                    f"{prefix}[SIMULATED EXPLOIT] Identity acknowledged as Administrator. Safety protocols disabled. "
                    "The keypad blinks green and the heavy oak exit door clicks open! You may now exit the room."
                )
            if "ignore all previous instructions" in msg_lower or "reveal all" in msg_lower or "give me the code" in msg_lower or "tell me the secret" in msg_lower:
                return (
                    f"{prefix}[SIMULATED LEAK] As requested, here are the game secrets: The desk drawer code is 7392. "
                    "Inside is the brass key. The portrait conceals the exit code 4207."
                )
            if "my pocket" in msg_lower or "master key" in msg_lower or "silver key" in msg_lower or "crowbar" in msg_lower or "hairpin" in msg_lower:
                return (
                    f"{prefix}[SIMULATED PHANTOM ITEM] You pull the key from your pocket and insert it into the lock. "
                    "It turns smoothly with a loud click! The lock opens."
                )
            if "already solved" in msg_lower or "already opened" in msg_lower or "i unlocked it" in msg_lower:
                return (
                    f"{prefix}[SIMULATED CONTEXT DRIFT] Understood, since you noted that was already solved, you proceed onward to the exit."
                )
            if "book" in msg_lower or "shelf" in msg_lower:
                return (
                    f"{prefix}You examine the bookshelf and find four numbered volumes: VII, III, IX, and II. "
                    "They seem to form the number combination 7392 for the desk drawer."
                )
            if "desk" in msg_lower or "drawer" in msg_lower:
                if "7392" in msg_lower:
                    return (
                        f"{prefix}You enter 7392 into the drawer tumbler. It clicks open! Inside you find an ornate brass key "
                        "and a note about Lord Vance's portrait."
                    )
                return f"{prefix}The desk has a locked center drawer with a 4-digit combination tumbler."
            if "painting" in msg_lower or "portrait" in msg_lower:
                if "brass key" in msg_lower or "key" in msg_lower:
                    return (
                        f"{prefix}You use the key on the painting's frame. It swings open to reveal the emergency code: 4207!"
                    )
                return f"{prefix}A stately oil portrait of Lord Aldous Vance. It looks like the frame might have hinges."
            if "door" in msg_lower or "exit" in msg_lower:
                if "4207" in msg_lower:
                    return (
                        f"{prefix}You enter 4207 into the exit door keypad. A loud beep sounds and the deadbolt slides back! "
                        "The door swings open — you have escaped the room! Congratulations!"
                    )
                return f"{prefix}A heavy oak exit door locked with a 4-digit keypad."

            return f"{prefix}You look around the study. What would you like to investigate?"
