"""Loads and plays the game's bundled sound effects."""

import logging
from pathlib import Path

import pygame


logger = logging.getLogger(__name__)


class GameAudio:
    STEP_INTERVAL = 0.38

    def __init__(self) -> None:
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._footstep_index = 0
        self._footstep_elapsed = 0.0
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except pygame.error as error:
                logger.warning("Audio output unavailable; sound effects disabled: %s", error)
                return

        audio_dir = Path(__file__).resolve().parents[2] / "assets" / "audio"
        volumes = {
            "bookClose": 0.3,
            "bookOpen": 0.3,
            "cloth1": 0.4,
            "footstep00": 0.22,
            "footstep05": 0.22,
            "handleSmallLeather": 0.35,
            "knifeSlice": 0.45,
            "knifeSlice2": 0.5,
        }
        for name, volume in volumes.items():
            sound = pygame.mixer.Sound(str(audio_dir / f"{name}.ogg"))
            sound.set_volume(volume)
            self._sounds[name] = sound

    def update_footsteps(self, dt: float, moved: bool) -> None:
        if not self._sounds:
            return
        if not moved:
            self._footstep_elapsed = 0.0
            return

        self._footstep_elapsed += dt
        if self._footstep_elapsed >= self.STEP_INTERVAL:
            name = ("footstep00", "footstep05")[self._footstep_index]
            self._sounds[name].play()
            self._footstep_index = (self._footstep_index + 1) % 2
            self._footstep_elapsed = 0.0

    def play_ui(self, opening: bool) -> None:
        if self._sounds:
            self._sounds["bookOpen" if opening else "bookClose"].play()

    def play_battle_action(self, command: int) -> None:
        sound_names = ("knifeSlice", "cloth1", "knifeSlice2", "handleSmallLeather")
        if not 0 <= command < len(sound_names):
            raise ValueError(f"Unknown battle command index: {command}.")
        if self._sounds:
            self._sounds[sound_names[command]].play()
