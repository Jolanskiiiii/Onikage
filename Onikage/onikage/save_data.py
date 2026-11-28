"""Versioned JSON save data with atomic writes and previous-save recovery."""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from onikage.masks import MaskManager
from onikage.campaign import CampaignProgress
from onikage.weapons import WeaponInventory


SAVE_VERSION = 3
VALID_DIRECTIONS = {"up", "up-right", "right", "down-right", "down", "down-left", "left", "up-left"}
WORLD_WIDTH = 84 * 32
WORLD_HEIGHT = 60 * 32


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
    campaign: dict[str, Any] = field(default_factory=lambda: CampaignProgress().to_dict())
    version: int = SAVE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": SAVE_VERSION,
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
            "campaign": self.campaign,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SaveData:
        if not isinstance(data, dict):
            raise ValueError("Save root must be a JSON object.")

        version = _integer(data.get("version", 1), "version", minimum=1)
        if version not in (1, 2, SAVE_VERSION):
            raise ValueError(f"Unsupported save version: {version}.")

        player = data.get("player", {})
        if not isinstance(player, dict):
            raise ValueError("Player save data must be an object.")

        player_x = _number(player.get("x", 755.0), "player.x")
        player_y = _number(player.get("y", 580.0), "player.y")
        if not 0 <= player_x <= WORLD_WIDTH or not 0 <= player_y <= WORLD_HEIGHT:
            raise ValueError("Saved player position is outside the village bounds.")

        direction = player.get("direction", "right")
        if not isinstance(direction, str) or direction not in VALID_DIRECTIONS:
            raise ValueError("Saved player direction is invalid.")

        weapons = data.get("weapon_inventory", {})
        masks = data.get("mask_manager", {})
        if not isinstance(weapons, dict) or not isinstance(masks, dict):
            raise ValueError("Weapon and mask save data must be objects.")

        try:
            inventory = WeaponInventory.from_dict(weapons)
            mask_manager = MaskManager.from_dict(masks)
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ValueError("Saved weapon or mask data is invalid.") from exc

        campaign = CampaignProgress.from_dict(data.get("campaign", {}))

        health = _integer(player.get("health", 100), "player.health", minimum=0)
        stamina = _number(player.get("stamina", 100.0), "player.stamina")
        level = _integer(player.get("level", 1), "player.level", minimum=1)
        experience = _integer(player.get("experience", 0), "player.experience", minimum=0)
        rations = _integer(player.get("rations", 3), "player.rations", minimum=0)
        wraith_health = _integer(data.get("wraith_health", 72), "wraith_health", minimum=0)

        if health > 100 or not 0 <= stamina <= 100 or level > 999 or experience > 1_000_000_000:
            raise ValueError("Saved player statistics are outside supported limits.")
        if rations > 999 or wraith_health > 72:
            raise ValueError("Saved progression values are outside supported limits.")

        return cls(
            player_x=player_x,
            player_y=player_y,
            direction=direction,
            health=health,
            stamina=stamina,
            level=level,
            experience=experience,
            rations=rations,
            weapon_inventory=inventory.to_dict(),
            mask_manager=mask_manager.to_dict(),
            active_quest_ids=_string_list(data.get("active_quest_ids")),
            completed_quest_ids=_string_list(data.get("completed_quest_ids")),
            wraith_health=wraith_health,
            campaign=campaign.to_dict(),
            version=SAVE_VERSION,
        )


def _number(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite.")
    return result


def _integer(value: object, field_name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{field_name} must be an integer of at least {minimum}.")
    return value


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [entry for entry in value if isinstance(entry, str)]


class SaveManager:
    """Reads, writes, validates, and recovers the current ONIKAGE JSON save."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else Path.home() / ".onikage" / "save.json"
        self.backup_path = self.path.with_suffix(self.path.suffix + ".bak")
        self.last_load_source: str | None = None

    @property
    def exists(self) -> bool:
        """Whether a valid primary or backup save can be loaded."""
        return self.load() is not None

    def save(self, data: SaveData) -> None:
        if not isinstance(data, SaveData):
            raise TypeError("SaveManager.save expects SaveData.")
        # Round-trip validation catches malformed in-memory state before disk I/O.
        normalized = SaveData.from_dict(data.to_dict())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        backup_temporary = self.backup_path.with_suffix(self.backup_path.suffix + ".tmp")
        payload = json.dumps(normalized.to_dict(), ensure_ascii=False, indent=2)

        try:
            _write_text_atomically(temporary, payload)
            if self.path.is_file() and self._read_valid(self.path) is not None:
                _write_bytes_atomically(backup_temporary, self.path.read_bytes())
                os.replace(backup_temporary, self.backup_path)
            os.replace(temporary, self.path)
        finally:
            _remove_if_present(temporary)
            _remove_if_present(backup_temporary)

    def load(self) -> SaveData | None:
        self.last_load_source = None
        primary = self._read_valid(self.path)
        if primary is not None:
            self.last_load_source = "primary"
            return primary

        backup = self._read_valid(self.backup_path)
        if backup is None:
            return None

        self.last_load_source = "backup"
        # Restore the primary copy when possible, leaving the backup untouched.
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            restore_temp = self.path.with_suffix(self.path.suffix + ".restore.tmp")
            _write_text_atomically(restore_temp, json.dumps(backup.to_dict(), ensure_ascii=False, indent=2))
            os.replace(restore_temp, self.path)
        except OSError:
            pass
        finally:
            if "restore_temp" in locals():
                _remove_if_present(restore_temp)
        return backup

    @staticmethod
    def _read_valid(path: Path) -> SaveData | None:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return SaveData.from_dict(raw)
        except (OSError, json.JSONDecodeError, TypeError, ValueError, OverflowError):
            return None


def _write_text_atomically(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())


def _write_bytes_atomically(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def _remove_if_present(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
