import math
from functools import lru_cache
from pathlib import Path

import pygame

from onikage.art.enemies.wraith_sprite import wraith_animation_frame
from onikage.art.effects.ground_shadows import draw_ground_shadow
from onikage.combat import Health


_BOSS_SPRITES = {
    "Ashen Oni": "ashen_oni.png",
    "Weeping Bride": "weeping_bride.png",
    "Hollow Stalker": "hollow_stalker.png",
    "Fallen Shogun": "fallen_shogun.png",
    "Nameless One": "nameless_one.png",
}

@lru_cache(maxsize=8)
def _boss_sprite(filename: str) -> pygame.Surface:
    path = Path(__file__).resolve().parent / "art" / "enemies" / filename
    image = pygame.image.load(str(path)).convert_alpha()
    return pygame.transform.scale(image, (72, 80))


class Enemy:
    """A hostile world character and its combat statistics."""

    ANIMATION_SECONDS = {"idle": 0.42, "walk": 0.16, "attack": 0.105, "hurt": 0.12, "death": 0.22}

    def __init__(
        self,
        x: int,
        y: int,
        name: str = "Cedar-Wood Wraith",
        max_health: int = 72,
        attack_power: int = 12,
    ) -> None:
        self.name = name
        self.vitality = Health(max_health)
        self.attack_power = attack_power
        self.experience_reward = 30
        self.rect = pygame.Rect(x + 4, y + 23, 24, 13)
        self.interaction_area = pygame.Rect(x - 26, y - 10, 84, 66)
        self.sprite_position = (x, y)
        self.animation = "idle"
        self.direction = "down"
        self.animation_time = 0.0
        self.death_animation_finished = False

    def set_animation(self, animation: str, direction: str | None = None) -> None:
        if animation not in self.ANIMATION_SECONDS:
            animation = "idle"
        if direction in ("down", "left", "up", "right"):
            self.direction = direction
        if animation != self.animation:
            self.animation = animation
            self.animation_time = 0.0

    def update(self, dt: float) -> None:
        self.animation_time += max(0.0, dt)
        if self.animation == "death" and self.animation_time >= self.ANIMATION_SECONDS["death"] * 4:
            self.death_animation_finished = True

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        x = self.sprite_position[0] - round(camera.x)
        y = self.sprite_position[1] - round(camera.y)
        # The Wraith floats above the ground: keep its shadow small, soft, and
        # centered under its ground anchor rather than using a hard black oval.
        draw_ground_shadow(surface, (x + 1, y + 39, 28, 7), opacity=54)
        # Each regional guardian has a distinct silhouette and palette. Only
        # ordinary Cedar-Wood Wraiths use the shared directional animation atlas.
        filename = _BOSS_SPRITES.get(self.name)
        if filename is not None:
            sprite = _boss_sprite(filename)
            if self.animation == "hurt" and int(self.animation_time * 18) % 2 == 0:
                sprite = sprite.copy()
                sprite.fill((255, 190, 170, 100), special_flags=pygame.BLEND_RGBA_ADD)
            elif self.animation == "death":
                sprite = pygame.transform.rotate(sprite, min(85, self.animation_time * 45))
            hover = round(1.0 * math.sin(self.animation_time * 1.7))
        else:
            frame_duration = self.ANIMATION_SECONDS[self.animation]
            frame = min(3, int(self.animation_time / frame_duration))
            if self.animation not in ("hurt", "death"):
                frame = int(self.animation_time / frame_duration) % 4
            sprite = wraith_animation_frame(self.animation, self.direction, frame)
            hover = round(1.5 * math.sin(self.animation_time * 2.2))
        surface.blit(sprite, (x - 24, y - 42 - hover))

    @property
    def health(self) -> int:
        return self.vitality.current

    @health.setter
    def health(self, value: int) -> None:
        self.vitality.current = max(0, min(self.vitality.maximum, value))

    @property
    def max_health(self) -> int:
        return self.vitality.maximum

    @max_health.setter
    def max_health(self, value: int) -> None:
        self.vitality.maximum = value
        self.vitality.current = min(self.vitality.current, value)
