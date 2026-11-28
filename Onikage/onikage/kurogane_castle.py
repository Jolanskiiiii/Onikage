"""Fallen Kurogane Castle chapter and Fallen Shogun guardian arena."""
from __future__ import annotations

import math
import pygame

from onikage.village import VillageWorld
from onikage.art.tiles.region_tiles import draw_region_tiles
from onikage.art.objects.region_props import draw_region_set


class KuroganeCastleWorld(VillageWorld):
    REGION_ID = "kurogane_castle"
    ENTRY_POINT = (150, 580)
    RETURN_GATE = pygame.Rect(58, 548, 54, 80)

    def __init__(self) -> None:
        super().__init__()
        self.buildings = []  # These regions use bespoke landmarks, not Kagehama houses.
        self.wraith.name = "Fallen Shogun"
        self.wraith.vitality.maximum = 340
        self.wraith.health = 340
        self.wraith.attack_power = 29
        self.wraith.experience_reward = 260
        self.wraith.sprite_position = (1160, 565)
        self.wraith.rect.topleft = (1164, 588)
        self.wraith.interaction_area = pygame.Rect(1128, 555, 100, 82)
        self.obstacles = [o for o in self.obstacles if o is not self.wraith.rect]
        self.obstacles.append(self.wraith.rect)
        # Broken walls and rubble shape a broad, navigable approach to the keep.
        self.rubble = [
            pygame.Rect(250, 275, 250, 74), pygame.Rect(590, 220, 95, 190),
            pygame.Rect(910, 260, 260, 72), pygame.Rect(1390, 245, 220, 100),
            pygame.Rect(310, 850, 210, 92), pygame.Rect(720, 900, 270, 66),
            pygame.Rect(1290, 835, 250, 100),
        ]
        self.obstacles.extend(r.copy() for r in self.rubble)
        self.decorations = [
            (410, 500, "barrel"), (720, 720, "shrine"), (930, 470, "barrel"),
            (1370, 700, "shrine"), (1510, 490, "barrel"), (560, 890, "shrine"),
        ]
        self.trees = [tree for index, tree in enumerate(self.trees) if index % 7 == 0]
        self._ash_phase = 0.0

    def update(self, dt: float) -> None:
        super().update(dt)
        self._ash_phase += max(0.0, dt)

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2,
             player_y: int | None = None) -> None:
        surface.fill((15, 15, 20))
        super().draw(surface, camera, player_y)
        draw_region_set(surface, camera, self.REGION_ID)
        # Ruined curtain walls and a dark keep silhouette frame the guardian.
        for index, area in enumerate(self.rubble):
            rect = area.move(-round(camera.x), -round(camera.y))
            if not surface.get_rect().colliderect(rect):
                continue
            pygame.draw.rect(surface, (29, 30, 37), rect)
            pygame.draw.rect(surface, (65, 62, 65), rect, 3)
            for n in range(max(2, rect.width // 38)):
                x = rect.x + 12 + n * 36
                pygame.draw.line(surface, (83, 77, 77), (x, rect.y + 8),
                                 (x + (n % 3 - 1) * 7, rect.bottom - 8), 2)
        keep = pygame.Rect(760 - round(camera.x), 100 - round(camera.y), 430, 190)
        if surface.get_rect().colliderect(keep):
            pygame.draw.rect(surface, (25, 24, 31), keep)
            pygame.draw.rect(surface, (78, 69, 69), keep, 5)
            pygame.draw.polygon(surface, (18, 19, 27), [
                (keep.x - 24, keep.y + 28), (keep.centerx, keep.y - 48),
                (keep.right + 24, keep.y + 28)])
            pygame.draw.line(surface, (111, 81, 65), (keep.centerx, keep.y + 30),
                             (keep.centerx, keep.bottom - 4), 5)
        ash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for i in range(24):
            x = int((i * 71 + math.sin(self._ash_phase * .25 + i) * 20) % surface.get_width())
            y = int((i * 43 + self._ash_phase * (8 + i % 4)) % surface.get_height())
            pygame.draw.circle(ash, (166, 153, 145, 38), (x, y), 1 + i % 2)
        surface.blit(ash, (0, 0))
        font = pygame.font.Font(None, 25)
        label = font.render("CHAPTER V  ·  THE FALLEN KUROGANE CASTLE", True, (190, 165, 153))
        surface.blit(label, (surface.get_width() - label.get_width() - 24, 18))

    def _draw_tiles(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        draw_region_tiles(
            surface, camera, self.TILE_SIZE, self.COLUMNS, self.ROWS,
            self._is_road, self.REGION_ID,
        )

    def _is_road(column: int, row: int) -> bool:
        # Castle approach, outer bailey, and a narrow central keep avenue.
        approach = 0 <= column <= 19 and 17 <= row <= 20
        bailey_west = 17 <= column <= 22 and 12 <= row <= 26
        bailey_south = 20 <= column <= 39 and 23 <= row <= 27
        bailey_east = 37 <= column <= 42 and 12 <= row <= 26
        keep_avenue = 39 <= column <= 55 and 17 <= row <= 20
        inner_court = 23 <= column <= 37 and 15 <= row <= 20
        north_gate = 26 <= column <= 32 and 7 <= row <= 16
        return approach or bailey_west or bailey_south or bailey_east or keep_avenue or inner_court or north_gate

    def is_at_return_gate(self, point: tuple[int, int]) -> bool:
        return self.RETURN_GATE.collidepoint(point)
