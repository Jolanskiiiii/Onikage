from dataclasses import dataclass
from enum import Enum, auto


class QuestStatus(Enum):
    AVAILABLE = auto()
    ACTIVE = auto()
    COMPLETED = auto()


@dataclass
class Quest:
    quest_id: str
    title: str
    giver: str
    description: str
    objective: str
    status: QuestStatus = QuestStatus.AVAILABLE


class QuestLog:
    """Owns the player's quests and their progress states."""

    def __init__(self) -> None:
        self._quests: dict[str, Quest] = {}

    def add(self, quest: Quest) -> None:
        if quest.quest_id in self._quests:
            raise ValueError(f"Quest '{quest.quest_id}' is already in the journal.")
        self._quests[quest.quest_id] = quest

    def get(self, quest_id: str) -> Quest:
        try:
            return self._quests[quest_id]
        except KeyError:
            raise KeyError(f"Unknown quest '{quest_id}'.") from None

    def first_available(self) -> Quest | None:
        return next(
            (quest for quest in self._quests.values() if quest.status == QuestStatus.AVAILABLE),
            None,
        )

    def accept(self, quest_id: str) -> None:
        quest = self.get(quest_id)
        if quest.status != QuestStatus.AVAILABLE:
            raise ValueError(f"Quest '{quest.title}' is not available to accept.")
        quest.status = QuestStatus.ACTIVE

    def complete(self, quest_id: str) -> None:
        quest = self.get(quest_id)
        if quest.status != QuestStatus.ACTIVE:
            raise ValueError(f"Quest '{quest.title}' is not active.")
        quest.status = QuestStatus.COMPLETED

    @property
    def quests(self) -> tuple[Quest, ...]:
        return tuple(self._quests.values())
