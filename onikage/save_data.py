"""Versioned JSON persistence for the current playable campaign slice."""

import json
import math
import os
import platform
from dataclasses import dataclass
from pathlib import Path


class SaveError(Exception):
    """A save could not be read, validated, or written."""


@dataclass(frozen=True)
class SavedQuest:
    quest_id: str
    title: str
    giver: str
    description: str
    objective: str
    status: str


@dataclass(frozen=True)
class GameSave:
    map_id: str
    x: float
    y: float
    direction: str
    health: int
    stamina: float
    level: int
    experience: int
    rations: int
    village_wraith_health: int
    forest_wraith_health: int
    quests: tuple[SavedQuest, ...]

    VERSION = 1
    MAX_PLAYER_X = 1768
    MAX_PLAYER_Y = 1244
    DIRECTIONS = {"down", "up", "left", "right"}
    QUEST_STATUSES = {"AVAILABLE", "ACTIVE", "COMPLETED"}

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.VERSION,
            "map_id": self.map_id,
            "player": {
                "x": self.x,
                "y": self.y,
                "direction": self.direction,
                "health": self.health,
                "stamina": self.stamina,
                "level": self.level,
                "experience": self.experience,
                "rations": self.rations,
            },
            "wraith_health": {
                "village": self.village_wraith_health,
                "forest": self.forest_wraith_health,
            },
            "quests": [
                {
                    "quest_id": quest.quest_id,
                    "title": quest.title,
                    "giver": quest.giver,
                    "description": quest.description,
                    "objective": quest.objective,
                    "status": quest.status,
                }
                for quest in self.quests
            ],
        }

    @classmethod
    def from_dict(cls, value: object) -> "GameSave":
        data = _require_object(value, "save")
        version = _require_int(data.get("version"), "version")
        if version != cls.VERSION:
            raise SaveError(f"Unsupported save version: {version}.")

        map_id = _require_string(data.get("map_id"), "map_id")
        if map_id not in {"village", "forest"}:
            raise SaveError(f"Unknown map in save: {map_id!r}.")

        player = _require_object(data.get("player"), "player")
        x = _require_number(player.get("x"), "player.x")
        y = _require_number(player.get("y"), "player.y")
        direction = _require_string(player.get("direction"), "player.direction")
        if direction not in cls.DIRECTIONS:
            raise SaveError(f"Unknown player direction: {direction!r}.")

        health = _require_int(player.get("health"), "player.health")
        stamina = _require_number(player.get("stamina"), "player.stamina")
        level = _require_int(player.get("level"), "player.level")
        experience = _require_int(player.get("experience"), "player.experience")
        rations = _require_int(player.get("rations"), "player.rations")
        if not 0 <= x <= cls.MAX_PLAYER_X or not 0 <= y <= cls.MAX_PLAYER_Y:
            raise SaveError("Player position is outside the known maps.")
        if not 1 <= health <= 100:
            raise SaveError("Player health is outside the valid range.")
        if not 0 <= stamina <= 100:
            raise SaveError("Player stamina is outside the valid range.")
        if level < 1 or experience < 0 or rations < 0:
            raise SaveError("Player progression or inventory is invalid.")

        wraiths = _require_object(data.get("wraith_health"), "wraith_health")
        village_health = _require_int(wraiths.get("village"), "village wraith health")
        forest_health = _require_int(wraiths.get("forest"), "forest wraith health")
        if not 0 <= village_health <= 72 or not 0 <= forest_health <= 84:
            raise SaveError("Wraith health is outside the valid range.")

        raw_quests = data.get("quests")
        if not isinstance(raw_quests, list):
            raise SaveError("Save quests must be a list.")
        quests: list[SavedQuest] = []
        quest_ids: set[str] = set()
        for index, raw_quest in enumerate(raw_quests):
            quest = _require_object(raw_quest, f"quests[{index}]")
            quest_id = _require_string(quest.get("quest_id"), f"quests[{index}].quest_id")
            status = _require_string(quest.get("status"), f"quests[{index}].status")
            if not quest_id or quest_id in quest_ids:
                raise SaveError("Save contains a missing or duplicate quest id.")
            if status not in cls.QUEST_STATUSES:
                raise SaveError(f"Unknown quest status: {status!r}.")
            quest_ids.add(quest_id)
            quests.append(
                SavedQuest(
                    quest_id=quest_id,
                    title=_require_string(quest.get("title"), f"quests[{index}].title"),
                    giver=_require_string(quest.get("giver"), f"quests[{index}].giver"),
                    description=_require_string(
                        quest.get("description"), f"quests[{index}].description"
                    ),
                    objective=_require_string(
                        quest.get("objective"), f"quests[{index}].objective"
                    ),
                    status=status,
                )
            )

        return cls(
            map_id=map_id,
            x=x,
            y=y,
            direction=direction,
            health=health,
            stamina=stamina,
            level=level,
            experience=experience,
            rations=rations,
            village_wraith_health=village_health,
            forest_wraith_health=forest_health,
            quests=tuple(quests),
        )


class SaveRepository:
    """Reads and atomically writes the single local campaign save."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path if path is not None else self.default_path()

    @staticmethod
    def default_path() -> Path:
        operating_system = platform.system()
        if operating_system == "Windows":
            data_home = Path(
                os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
            )
        elif operating_system == "Darwin":
            data_home = Path.home() / "Library" / "Application Support"
        else:
            data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        return data_home / "ONIKAGE" / "save.json"

    @property
    def has_save(self) -> bool:
        return self.path.is_file()

    def save(self, game_save: GameSave) -> None:
        validated = GameSave.from_dict(game_save.to_dict())
        temporary_path = self.path.with_name(f"{self.path.name}.tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path.write_text(
                json.dumps(validated.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary_path.replace(self.path)
        except OSError as error:
            raise SaveError(f"Could not write save file at {self.path}: {error}") from error
        finally:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError as error:
                raise SaveError(
                    f"Could not clean up temporary save file at {temporary_path}: {error}"
                ) from error

    def load(self) -> GameSave:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise SaveError(f"No save file exists at {self.path}.") from error
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise SaveError(f"Could not read save file at {self.path}: {error}") from error
        return GameSave.from_dict(data)


def _require_object(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise SaveError(f"Save field {field!r} must be an object.")
    return value


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise SaveError(f"Save field {field!r} must be a string.")
    return value


def _require_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SaveError(f"Save field {field!r} must be an integer.")
    return value


def _require_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SaveError(f"Save field {field!r} must be a number.")
    number = float(value)
    if not math.isfinite(number):
        raise SaveError(f"Save field {field!r} must be finite.")
    return number
