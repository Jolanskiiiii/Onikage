"""Seeded village mist and firefly motion with a reusable overlay surface."""

import math
import random

import pygame


class VillageAtmosphere:
    def __init__(self, world_size: tuple[int, int], seed: int = 109) -> None:
        self.world_size = world_size
        self.elapsed = 0.0
        randomizer = random.Random(seed)
        self.fog = [
            (
                randomizer.uniform(-180, world_size[0]),
                randomizer.uniform(0, world_size[1]),
                randomizer.uniform(90, 180),
                randomizer.uniform(6, 13),
            )
            for _ in range(10)
        ]
        self.fireflies = [
            (
                randomizer.randrange(world_size[0]),
                randomizer.randrange(300, world_size[1]),
                randomizer.random() * math.tau,
            )
            for _ in range(22)
        ]
        self._fog_overlay: pygame.Surface | None = None

    def update(self, dt: float) -> None:
        self.elapsed += dt

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        self._draw_fog(surface, camera)
        self._draw_fireflies(surface, camera)

    def _draw_fog(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        if self._fog_overlay is None or self._fog_overlay.get_size() != surface.get_size():
            self._fog_overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay = self._fog_overlay
        overlay.fill((0, 0, 0, 0))
        for index, (x, y, width, speed) in enumerate(self.fog):
            drift = (x + self.elapsed * speed) % (self.world_size[0] + width) - width
            sx, sy = int(drift - camera.x * 0.35), int(y - camera.y * 0.35)
            if -width < sx < surface.get_width() and -70 < sy < surface.get_height() + 70:
                alpha = 9 + int(5 * math.sin(self.elapsed + index))
                pygame.draw.ellipse(overlay, (144, 164, 158, alpha), (sx, sy, int(width), 27))
                pygame.draw.ellipse(
                    overlay,
                    (167, 179, 167, alpha // 2),
                    (sx + 18, sy + 8, int(width * 0.68), 25),
                )
        surface.blit(overlay, (0, 0))

    def _draw_fireflies(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        for index, (x, y, phase) in enumerate(self.fireflies):
            bob = math.sin(self.elapsed * 1.8 + phase) * 5
            sx = x - round(camera.x) + math.sin(self.elapsed * 0.35 + phase) * 7
            sy = int(y - camera.y + bob)
            if not (0 <= sx < surface.get_width() and 0 <= sy < surface.get_height()):
                continue
            brightness = 0.5 + 0.5 * math.sin(self.elapsed * 2.5 + phase)
            if brightness < 0.28:
                continue
            color = (122, 160, 106) if index % 3 else (191, 157, 89)
            dot = (int(sx), sy)
            pygame.draw.rect(
                surface,
                (color[0] // 4, color[1] // 4, color[2] // 4),
                (dot[0] - 2, dot[1] - 2, 5, 5),
            )
            pygame.draw.rect(surface, color, (dot[0], dot[1], 2, 2))
