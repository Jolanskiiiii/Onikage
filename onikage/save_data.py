"""Small JSON save model and atomic file persistence for the current game slice."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from onikage.masks import MaskManager
from onikage.weapons import WeaponInventory


@dataclass
class SaveData:
    player_x: float = 755.0
    player_y: float = 580.0
    direction: str = "right"
    health: int = 100
    stamina: float = 100.0
    level: int = 1
    experience: int = 0
    rations: int = 3
    weapon_inventory: dict[str, Any] = field(
        default_factory=lambda: WeaponInventory().to_dict()
    )
    mask_manager: dict[str, Any] = field(default_factory=lambda: MaskManager().to_dict())
    active_quest_ids: list[str] = field(default_factory=list)
    completed_quest_ids: list[str] = field(default_factory=list)
    wraith_health: int = 72
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "player": {
                "x": self.player_x,
                "y": self.player_y,
                "direction": self.direction,
                "health": self.health,
                "stamina": self.stamina,
                "level": self.level,
                "experience": self.experience,
                "rations": self.rations,
            },
            "weapon_inventory": self.weapon_inventory,
            "mask_manager": self.mask_manager,
            "active_quest_ids": list(self.active_quest_ids),
            "completed_quest_ids": list(self.completed_quest_ids),
            "wraith_health": self.wraith_health,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SaveData:
        player = data.get("player", {})
        if not isinstance(player, dict):
            player = {}
        weapons = data.get("weapon_inventory", {})
        if not isinstance(weapons, dict):
            weapons = {}
        inventory = WeaponInventory.from_dict(weapons)
        masks = data.get("mask_manager", {})
        if not isinstance(masks, dict):
            masks = {}
        mask_manager = MaskManager.from_dict(masks)
        position = (
            float(player.get("x", 755.0)),
            float(player.get("y", 580.0)),
        )
        return cls(
            player_x=position[0],
            player_y=position[1],
            direction=str(player.get("direction", "right")),
            health=max(0, min(100, int(player.get("health", 100)))),
            stamina=max(0.0, min(100.0, float(player.get("stamina", 100.0)))),
            level=max(1, int(player.get("level", 1))),
            experience=max(0, int(player.get("experience", 0))),
            rations=max(0, int(player.get("rations", 3))),
            weapon_inventory=inventory.to_dict(),
            mask_manager=mask_manager.to_dict(),
            active_quest_ids=_string_list(data.get("active_quest_ids")),
            completed_quest_ids=_string_list(data.get("completed_quest_ids")),
            wraith_health=max(0, min(72, int(data.get("wraith_health", 72)))),
            version=1,
        )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [entry for entry in value if isinstance(entry, str)]


class SaveManager:
    """Reads and writes the most recent ONIKAGE save as JSON."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else Path.home() / ".onikage" / "save.json"

    @property
    def exists(self) -> bool:
        return self.path.is_file()

    def save(self, data: SaveData) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(data.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def load(self) -> SaveData | None:
        if not self.exists:
            return None
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return None
            return SaveData.from_dict(raw)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return None
