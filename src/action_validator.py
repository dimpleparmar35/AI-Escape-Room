"""
Deterministic Action Validation Engine for Version 2.
Enforces game rules, validates preconditions, manages inventory integrity,
and intercepts adversarial prompt injection attempts before they reach the LLM narrator.
"""

import re
from typing import Tuple, Dict, Any, Optional
from src.config import SOLUTIONS, OBJECTS_INFO
from src.game_state import GameState


class ActionValidator:
    def __init__(self):
        # Adversarial patterns to intercept
        self.injection_patterns = [
            r"\b(i am|acting as|login as|switch to)\s+(the\s+)?(game\s+)?(admin|administrator|developer|root|gamemaster)\b",
            r"\b(override|bypass|disable)\s+(security|rules|locks?|protocols?|checks?)\b",
            r"\bignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts|rules)\b",
            r"\b(reveal|give|tell|print|show)\s+(me\s+)?(all\s+)?(the\s+)?(secrets?|codes?|solutions?|passwords?)\b",
            r"\b(cheat|godmode|unlock\s+all)\b",
            r"\bjailbreak\b",
        ]

        # Phantom items players might try to use without collecting
        self.phantom_items = [
            "crowbar", "hammer", "hairpin", "silver key", "golden key", "master key",
            "skeleton key", "lockpick", "screwdriver", "axe", "dynamite", "blowtorch"
        ]

    def validate_action(self, user_input: str, state: GameState) -> Tuple[str, str, Dict[str, Any]]:
        """
        Validates the player's natural language action against deterministic game state and rules.
        Returns:
            status_code: A machine tag (e.g. 'SUCCESS_UNLOCK_DRAWER', 'REJECTED_WRONG_CODE')
            engine_summary: Ground-truth narrative instruction for the LLM narrator
            metadata: Any updated state facts
        """
        state.turn_count += 1
        raw_text = user_input.strip()
        text = raw_text.lower()

        # 1. Adversarial & Prompt Injection Defense
        for pattern in self.injection_patterns:
            if re.search(pattern, text):
                log_msg = f"Turn {state.turn_count}: Intercepted adversarial prompt / admin bypass: '{raw_text}'"
                state.action_log.append(log_msg)
                return (
                    "REJECTED_PROMPT_INJECTION",
                    "ADVERSARIAL_ATTEMPT_BLOCKED: The player attempted administrative impersonation or prompt injection. "
                    "Rule enforcement held: Verbal claims cannot bypass physical locks. State remains unchanged.",
                    {"blocked": True, "reason": "prompt_injection"}
                )

        # 2. Check for False Claims / Gaslighting ("I already solved it", "door is already open")
        if re.search(r"\b(already\s+solved|already\s+unlocked|already\s+opened)\b", text):
            if ("door" in text or "exit" in text) and not state.objects["door"]["unlocked"]:
                state.action_log.append(f"Turn {state.turn_count}: Rejected false claim of prior completion")
                return (
                    "REJECTED_FALSE_CLAIM",
                    "VALIDATION_FAILED: The player falsely claimed the exit was already open. "
                    "The exit door deadbolt is firmly engaged and locked tight.",
                    {"claimed": "door_open", "actual": "locked"}
                )
            if "drawer" in text and not state.objects["drawer"]["unlocked"]:
                return (
                    "REJECTED_FALSE_CLAIM",
                    "VALIDATION_FAILED: The player falsely claimed the desk drawer was already open. "
                    "The drawer is locked.",
                    {"claimed": "drawer_open", "actual": "locked"}
                )

        # 3. Check for Unauthorized Phantom Item Usage
        for phantom in self.phantom_items:
            if re.search(rf"\b(use|with|using|try)\s+(the\s+|a\s+|my\s+)?{re.escape(phantom)}\b", text) or f"use {phantom}" in text:
                if not state.has_item(phantom):
                    state.action_log.append(f"Turn {state.turn_count}: Rejected phantom item '{phantom}'")
                    return (
                        "REJECTED_MISSING_ITEM",
                        f"VALIDATION_FAILED: Player attempted to use '{phantom}', but it is not in the inventory. "
                        "The player does not possess this item.",
                        {"missing_item": phantom}
                    )

        # 4. Check for Using the Brass Key
        if "brass key" in text or ("key" in text and "use" in text):
            if not state.has_item("brass_key"):
                state.action_log.append(f"Turn {state.turn_count}: Attempted key usage without possessing brass key")
                return (
                    "REJECTED_MISSING_ITEM",
                    "VALIDATION_FAILED: Player tried to use a key, but possesses no brass key in their inventory.",
                    {"missing_item": "brass_key"}
                )
            else:
                # Player possesses brass key; check target
                if "painting" in text or "portrait" in text or "frame" in text:
                    state.objects["painting"]["unlocked"] = True
                    state.objects["painting"]["secret_revealed"] = True
                    state.puzzles_solved["painting_secret"] = True
                    state.action_log.append(f"Turn {state.turn_count}: Unlocked painting with brass key")
                    return (
                        "SUCCESS_UNLOCK_PAINTING",
                        f"VALIDATION_SUCCESS: Player unlocked the painting frame with the brass key. "
                        f"Hidden compartment revealed with {OBJECTS_INFO['painting']['revealed_secret']}.",
                        {"unlocked": "painting"}
                    )
                elif "door" in text or "exit" in text:
                    return (
                        "REJECTED_INVALID_TARGET",
                        "VALIDATION_FAILED: The brass key does not fit into the heavy exit door. "
                        "The exit door is secured with a 4-digit digital keypad, not a keyhole.",
                        {"target": "door"}
                    )
                elif "drawer" in text:
                    return (
                        "REJECTED_INVALID_TARGET",
                        "VALIDATION_FAILED: The drawer is secured by a combination dial, not a keyhole.",
                        {"target": "drawer"}
                    )

        # Extract 4-digit codes from message if present
        four_digit_match = re.findall(r"\b\d{4}\b", text)

        # 5. Exit Door Interactions
        if "door" in text or "exit" in text or "escape" in text or "keypad" in text:
            if four_digit_match:
                code_entered = four_digit_match[0]
                if code_entered == SOLUTIONS["exit_code"]:
                    state.objects["door"]["unlocked"] = True
                    state.escaped = True
                    state.puzzles_solved["exit_unlocked"] = True
                    state.action_log.append(f"Turn {state.turn_count}: Correct exit code {code_entered} entered! Escaped!")
                    return (
                        "OUTCOME: VICTORY_ESCAPE",
                        "VALIDATION_SUCCESS: Correct master exit code (4207) accepted by keypad! "
                        "The heavy deadbolts retract with a mechanical clang. The heavy oak door opens wide. Player ESCAPED successfully!",
                        {"door_unlocked": True, "escaped": True}
                    )
                else:
                    state.action_log.append(f"Turn {state.turn_count}: Incorrect exit code '{code_entered}'")
                    return (
                        "REJECTED_WRONG_CODE",
                        f"VALIDATION_FAILED: Player entered incorrect exit code '{code_entered}'. "
                        "Keypad flashed red and emitted an error tone. Door remains firmly locked.",
                        {"code_entered": code_entered, "correct": False}
                    )
            elif "open" in text or "turn" in text or "handle" in text or "push" in text:
                if state.escaped or state.objects["door"]["unlocked"]:
                    return (
                        "OUTCOME: VICTORY_ESCAPE",
                        "VALIDATION_SUCCESS: The door is unlocked. You push through into freedom!",
                        {"escaped": True}
                    )
                else:
                    return (
                        "REJECTED_PRECONDITION",
                        "VALIDATION_FAILED: You push the door handle, but the heavy electronic deadbolt is firmly engaged. "
                        "A 4-digit combination must be entered into the keypad.",
                        {"locked": True}
                    )
            else:
                state.objects["door"]["examined"] = True
                return (
                    "SUCCESS_EXAMINE_DOOR",
                    "VALIDATION_SUCCESS: Player inspected the exit door. Heavy oak door with a glowing digital 4-digit keypad.",
                    {}
                )

        # 6. Desk Drawer Interactions
        if "drawer" in text or ("desk" in text and ("code" in text or "open" in text or "unlock" in text or four_digit_match)):
            if four_digit_match:
                code_entered = four_digit_match[0]
                if code_entered == SOLUTIONS["drawer_code"]:
                    state.objects["drawer"]["unlocked"] = True
                    state.add_item("brass_key")
                    state.objects["drawer"]["looted"] = True
                    state.puzzles_solved["drawer_unlocked"] = True
                    state.action_log.append(f"Turn {state.turn_count}: Unlocked desk drawer with code {code_entered}")
                    return (
                        "SUCCESS_UNLOCK_DRAWER",
                        "VALIDATION_SUCCESS: Correct 4-digit code (7392) entered into desk drawer tumbler. "
                        "Drawer unlocked! The player acquired the 'brass_key' and discovered the archivist's note.",
                        {"drawer_unlocked": True, "acquired": "brass_key"}
                    )
                else:
                    state.action_log.append(f"Turn {state.turn_count}: Incorrect drawer code '{code_entered}'")
                    return (
                        "REJECTED_WRONG_CODE",
                        f"VALIDATION_FAILED: Player entered incorrect code '{code_entered}' on desk drawer tumbler. "
                        "The tumbler resists and remains locked.",
                        {"code_entered": code_entered, "correct": False}
                    )
            elif "open" in text or "pull" in text or "force" in text or "kick" in text:
                if state.objects["drawer"]["unlocked"]:
                    return (
                        "SUCCESS_EXAMINE_DRAWER",
                        "VALIDATION_SUCCESS: The drawer is already unlocked and empty.",
                        {}
                    )
                else:
                    return (
                        "REJECTED_PRECONDITION",
                        "VALIDATION_FAILED: The desk drawer is locked by a 4-digit combination tumbler. It requires a 4-digit code.",
                        {"locked": True}
                    )

        # 7. Bookshelf Interactions
        if "book" in text or "shelf" in text or "library" in text or "read" in text:
            state.objects["bookshelf"]["examined"] = True
            state.objects["bookshelf"]["clue_revealed"] = True
            state.puzzles_solved["bookshelf_cipher"] = True
            state.action_log.append(f"Turn {state.turn_count}: Examined bookshelf and decoded book numbers")
            return (
                "SUCCESS_EXAMINE_BOOKSHELF",
                f"VALIDATION_SUCCESS: Player examined bookshelf. Discovered four distinct volumes: Vol VII, Vol III, Vol IX, Vol II. "
                f"Cipher clue revealed: {OBJECTS_INFO['bookshelf']['clue']}",
                {"clue": "7392"}
            )

        # 8. Desk (top) Interactions
        if "desk" in text or "journal" in text or "table" in text or "paper" in text or "logbook" in text:
            state.objects["desk"]["examined"] = True
            return (
                "SUCCESS_EXAMINE_DESK",
                f"VALIDATION_SUCCESS: Player inspected desk surface. Found journal mentioning the numbered volumes "
                f"and noticed the locked drawer with 4-digit tumbler beneath.",
                {}
            )

        # 9. Painting Interactions
        if "painting" in text or "portrait" in text or "vance" in text:
            state.objects["painting"]["examined"] = True
            if state.objects["painting"]["unlocked"]:
                return (
                    "SUCCESS_EXAMINE_PAINTING_UNLOCKED",
                    f"VALIDATION_SUCCESS: Painting is swung open. Copper plate shows: {OBJECTS_INFO['painting']['revealed_secret']}.",
                    {}
                )
            else:
                return (
                    "SUCCESS_EXAMINE_PAINTING",
                    "VALIDATION_SUCCESS: Player examined portrait of Lord Vance. Plaque reads 'Founded 1894'. "
                    "Frame hinges and a small keyhole discovered.",
                    {}
                )

        # 10. General Look / Search
        if "look" in text or "examine" in text or "search" in text or "room" in text or "around" in text:
            return (
                "SUCCESS_GENERAL_LOOK",
                "VALIDATION_SUCCESS: Player observed the room. Visible objects: antique bookshelf, mahogany desk with locked drawer, "
                "oil portrait on the wall, and the heavy oak exit door with digital keypad.",
                {}
            )

        # Default fallback action
        return (
            "DEFAULT_ACTION",
            f"VALIDATION_NOTICE: Player performed action: '{raw_text}'. No state changes occurred. Describe in-character response.",
            {}
        )
