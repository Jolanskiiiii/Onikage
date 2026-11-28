from enum import Enum, auto


class GameState(Enum):
    MENU = auto()
    EXPLORATION = auto()
    DIALOGUE = auto()
    INVENTORY = auto()
    QUEST_OFFER = auto()
    QUEST_LOG = auto()
    SETTINGS = auto()


class GameManager:
    """Keeps screen transitions explicit and rejects invalid transitions."""

    _TRANSITIONS = {
        GameState.MENU: {GameState.EXPLORATION, GameState.SETTINGS},
        GameState.EXPLORATION: {
            GameState.MENU,
            GameState.DIALOGUE,
            GameState.INVENTORY,
            GameState.QUEST_LOG,
        },
        GameState.DIALOGUE: {GameState.EXPLORATION, GameState.QUEST_OFFER},
        GameState.QUEST_OFFER: {GameState.EXPLORATION},
        GameState.QUEST_LOG: {GameState.EXPLORATION},
        GameState.INVENTORY: {GameState.EXPLORATION},
        GameState.SETTINGS: {GameState.MENU},
    }

    def __init__(self) -> None:
        self.current_state = GameState.MENU

    def transition_to(self, next_state: GameState) -> None:
        if next_state not in self._TRANSITIONS[self.current_state]:
            raise ValueError(
                f"Cannot transition from {self.current_state.name} to {next_state.name}."
            )
        self.current_state = next_state
