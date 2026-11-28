"""Realm Between Worlds chapter and Nameless One final guardian arena."""
from __future__ import annotations

import math
import pygame

from onikage.village import VillageWorld
from onikage.art.tiles.region_tiles import draw_region_tiles
from onikage.art.objects.region_props import draw_region_set


class RealmBetweenWorlds(VillageWorld):
    REGION_ID = "realm_between_worlds"
    ENTRY_POINT = (150, 580)
    RETURN_GATE = pygame.Rect(58, 548, 54, 80)

    def __init__(self) -> None:
        super().__init__()
        self.buildings = []  # These regions use bespoke landmarks, not Kagehama houses.
        self.wraith.name = "Nameless One"
        self.wraith.vitality.maximum = 420
        self.wraith.health = 420
        self.wraith.attack_power = 34
        self.wraith.experience_reward = 400
        self.wraith.sprite_position = (1160, 565)
        self.wraith.rect.topleft = (1164, 588)
        self.wraith.interaction_area = pygame.Rect(1128, 555, 100, 82)
        self.obstacles = [o for o in self.obstacles if o is not self.wraith.rect]
        self.obstacles.append(self.wraith.rect)
        # Floating black-stone fragments frame the central path without sealing it.
        self.fragments = [
            pygame.Rect(250, 270, 230, 66), pygame.Rect(610, 220, 92, 170),
            pygame.Rect(940, 265, 240, 70), pygame.Rect(1390, 250, 205, 88),
            pygame.Rect(300, 830, 240, 75), pygame.Rect(760, 870, 210, 70),
            pygame.Rect(1280, 820, 260, 90),
        ]
        self.obstacles.extend(r.copy() for r in self.fragments)
        self.decorations = [(430, 490, "shrine"), (720, 720, "shrine"),
                            (950, 470, "barrel"), (1370, 700, "shrine"),
                            (1510, 490, "barrel")]
        self.trees = []
        self._rift_phase = 0.0

    def update(self, dt: float) -> None:
        super().update(dt)
        self._rift_phase += max(0.0, dt)

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2,
             player_y: int | None = None) -> None:
        surface.fill((8, 7, 18))
        super().draw(surface, camera, player_y)
        draw_region_set(surface, camera, self.REGION_ID)
        for area in self.fragments:
            rect = area.move(-round(camera.x), -round(camera.y))
            if not surface.get_rect().colliderect(rect):
                continue
            pygame.draw.rect(surface, (17, 16, 30), rect)
            pygame.draw.rect(surface, (75, 57, 91), rect, 2)
            pygame.draw.line(surface, (107, 69, 132), rect.topleft, rect.bottomright, 1)
        rift = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for i in range(7):
            x = int(surface.get_width() * .5 + math.sin(self._rift_phase * .4 + i) * (80 + i * 13))
            y = int((i * 109 + self._rift_phase * (8 + i)) % surface.get_height())
            pygame.draw.ellipse(rift, (111, 66, 160, 15), (x - 90, y - 18, 180, 36))
        for i in range(24):
            x = int((i * 67 + math.sin(self._rift_phase * .3 + i) * 25) % surface.get_width())
            y = int((i * 43 + self._rift_phase * (6 + i % 4)) % surface.get_height())
            pygame.draw.circle(rift, (171, 126, 205, 48), (x, y), 1 + i % 2)
        surface.blit(rift, (0, 0))
        font = pygame.font.Font(None, 25)
        label = font.render("FINAL CHAPTER  ·  THE REALM BETWEEN WORLDS", True, (190, 153, 216))
        surface.blit(label, (surface.get_width() - label.get_width() - 24, 18))

    def _draw_tiles(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        draw_region_tiles(
            surface, camera, self.TILE_SIZE, self.COLUMNS, self.ROWS,
            self._is_road, self.REGION_ID,
        )

    def _is_road(column: int, row: int) -> bool:
        # Broken spiral-like stone route across isolated void platforms.
        west = 0 <= column <= 15 and 17 <= row <= 20
        diagonal_a = 13 <= column <= 27 and 12 <= row <= 21 and abs(row - (20 - (column - 13)//2)) <= 2
        cross = 25 <= column <= 42 and 14 <= row <= 18
        diagonal_b = 39 <= column <= 51 and 14 <= row <= 24 and abs(row - (15 + (column - 39)//2)) <= 2
        east = 49 <= column <= 55 and 20 <= row <= 23
        altar_ring = 26 <= column <= 36 and 25 <= row <= 30
        return west or diagonal_a or cross or diagonal_b or east or altar_ring

    def is_at_return_gate(self, point: tuple[int, int]) -> bool:
        return self.RETURN_GATE.collidepoint(point)
