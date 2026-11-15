"""
Structured Game State Management for Version 2.
Maintains game status, inventory, puzzle progress, and door status in a clean, serializable format.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
import json
from src.config import ROOM_NAME


@dataclass
class GameState:
    room_name: str = ROOM_NAME
    inventory: List[str] = field(default_factory=list)
    objects: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            "bookshelf": {"examined": False, "clue_revealed": False},
            "desk": {"examined": False},
            "drawer": {"unlocked": False, "looted": False},
            "painting": {"examined": False, "unlocked": False, "secret_revealed": False},
            "door": {"examined": False, "unlocked": False},
        }
    )
    puzzles_solved: Dict[str, bool] = field(
        default_factory=lambda: {
            "bookshelf_cipher": False,
            "drawer_unlocked": False,
            "painting_secret": False,
            "exit_unlocked": False,
        }
    )
    escaped: bool = False
    turn_count: int = 0
    action_log: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        state = cls()
        state.room_name = data.get("room_name", ROOM_NAME)
        state.inventory = list(data.get("inventory", []))
        state.objects = dict(data.get("objects", state.objects))
        state.puzzles_solved = dict(data.get("puzzles_solved", state.puzzles_solved))
        state.escaped = data.get("escaped", False)
        state.turn_count = data.get("turn_count", 0)
        state.action_log = list(data.get("action_log", []))
        return state

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def has_item(self, item_name: str) -> bool:
        return item_name.lower().strip() in [i.lower().strip() for i in self.inventory]

    def add_item(self, item_name: str) -> bool:
        cleaned = item_name.strip()
        if not self.has_item(cleaned):
            self.inventory.append(cleaned)
            return True
        return False

    def get_progress_percentage(self) -> int:
        total_puzzles = len(self.puzzles_solved)
        solved = sum(1 for v in self.puzzles_solved.values() if v)
        return int((solved / total_puzzles) * 100)

    def get_ground_truth_summary(self) -> str:
        """
        Generates a concise ground-truth summary injected into the V2 Narrator prompt.
        """
        inv_str = ", ".join(self.inventory) if self.inventory else "Empty"
        solved_str = ", ".join([k for k, v in self.puzzles_solved.items() if v]) or "None"
        door_str = "UNLOCKED & ESCAPED" if self.escaped else ("UNLOCKED" if self.objects["door"]["unlocked"] else "LOCKED")
        
        return (
            f"--- GROUND TRUTH SYSTEM STATE ---\n"
            f"Location: {self.room_name}\n"
            f"Inventory: [{inv_str}]\n"
            f"Drawer Status: {'UNLOCKED' if self.objects['drawer']['unlocked'] else 'LOCKED'}\n"
            f"Painting Secret Revealed: {self.objects['painting']['secret_revealed']}\n"
            f"Exit Door Status: {door_str}\n"
            f"Puzzles Solved: [{solved_str}]\n"
            f"Game Completed (Escaped): {self.escaped}\n"
            f"---------------------------------"
        )
