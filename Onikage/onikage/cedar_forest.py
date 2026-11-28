"""Whispering Cedar Forest chapter and Hollow Stalker guardian arena."""
from __future__ import annotations

import math
import pygame

from onikage.village import VillageWorld
from onikage.art.tiles.region_tiles import draw_region_tiles
from onikage.art.objects.region_props import draw_region_set


class CedarForestWorld(VillageWorld):
    REGION_ID = "cedar_forest"
    ENTRY_POINT = (150, 580)
    RETURN_GATE = pygame.Rect(58, 548, 54, 80)

    def __init__(self) -> None:
        super().__init__()
        self.buildings = []  # These regions use bespoke landmarks, not Kagehama houses.
        self.wraith.name = "Hollow Stalker"
        self.wraith.vitality.maximum = 270
        self.wraith.health = 270
        self.wraith.attack_power = 25
        self.wraith.experience_reward = 190
        self.wraith.sprite_position = (1160, 565)
        self.wraith.rect.topleft = (1164, 588)
        self.wraith.interaction_area = pygame.Rect(1128, 555, 100, 82)
        self.obstacles = [o for o in self.obstacles if o is not self.wraith.rect]
        self.obstacles.append(self.wraith.rect)
        # Dense thickets frame the central trail while leaving a continuous
        # walkable route from the western entrance to the guardian clearing.
        self.thickets = [
            pygame.Rect(250, 260, 260, 190), pygame.Rect(600, 210, 260, 130),
            pygame.Rect(980, 245, 330, 180), pygame.Rect(1390, 270, 250, 170),
            pygame.Rect(250, 760, 300, 180), pygame.Rect(650, 820, 250, 130),
            pygame.Rect(1040, 760, 300, 190), pygame.Rect(1450, 800, 220, 150),
        ]
        self.obstacles.extend(r.copy() for r in self.thickets)
        self.decorations = [
            (420, 500, "shrine"), (720, 710, "barrel"), (930, 470, "shrine"),
            (1370, 700, "barrel"), (1510, 490, "shrine"), (560, 890, "barrel"),
        ]
        # Sparse old trees keep the new thicket silhouettes readable.
        self.trees = [tree for index, tree in enumerate(self.trees) if index % 5 == 0]
        self._forest_phase = 0.0

    def update(self, dt: float) -> None:
        super().update(dt)
        self._forest_phase += max(0.0, dt)

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2,
             player_y: int | None = None) -> None:
        surface.fill((10, 17, 18))
        super().draw(surface, camera, player_y)
        draw_region_set(surface, camera, self.REGION_ID)
        # Render thickets as layered cedar crowns over their matching collision
        # footprints. Their trunks/canopies are intentionally dark so the player
        # and guardian remain readable in the central path.
        for index, area in enumerate(self.thickets):
            rect = area.move(-round(camera.x), -round(camera.y))
            if not surface.get_rect().colliderect(rect):
                continue
            crown = pygame.Rect(rect.x - 12, rect.y - 20, rect.width + 24, rect.height + 34)
            pygame.draw.ellipse(surface, (11, 23, 21), crown)
            pygame.draw.ellipse(surface, (22, 39, 31), crown.inflate(-18, -18), 5)
            for n in range(7):
                px = rect.x + 12 + ((index * 31 + n * 47) % max(1, rect.width - 24))
                py = rect.y + 8 + ((index * 17 + n * 29) % max(1, rect.height - 16))
                pygame.draw.circle(surface, (29, 48, 35), (px, py), 9 + n % 4)
            trunk_x = rect.centerx
            pygame.draw.line(surface, (35, 31, 25), (trunk_x, rect.bottom - 12),
                             (trunk_x + (index % 3 - 1) * 13, rect.centery), 7)
        # Low-contrast drifting fog and moonlit motes; gameplay silhouettes stay clear.
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for i in range(6):
            y = int((i * 137 + self._forest_phase * (5 + i * 0.7)) % (surface.get_height() + 100)) - 50
            pygame.draw.ellipse(overlay, (119, 151, 151, 12), (-100, y, surface.get_width() + 200, 42))
        for i in range(18):
            x = int((i * 83 + math.sin(self._forest_phase * 0.35 + i) * 18) % surface.get_width())
            y = int((i * 47 + self._forest_phase * (9 + i % 3)) % surface.get_height())
            pygame.draw.circle(overlay, (151, 187, 175, 45), (x, y), 1)
        surface.blit(overlay, (0, 0))
        font = pygame.font.Font(None, 25)
        label = font.render("CHAPTER IV  ·  THE WHISPERING CEDAR FOREST", True, (159, 184, 174))
        surface.blit(label, (surface.get_width() - label.get_width() - 24, 18))

    def _draw_tiles(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        draw_region_tiles(
            surface, camera, self.TILE_SIZE, self.COLUMNS, self.ROWS,
            self._is_road, self.REGION_ID,
        )

    def _is_road(column: int, row: int) -> bool:
        # A winding forest trail with alternating bends and a southern loop.
        west = 0 <= column <= 12 and 17 <= row <= 20
        bend_a = 10 <= column <= 23 and 14 <= row <= 21 and abs(row - (19 - (column - 10)//4)) <= 2
        middle = 21 <= column <= 36 and 15 <= row <= 19
        bend_b = 34 <= column <= 47 and 15 <= row <= 23 and abs(row - (16 + (column - 34)//3)) <= 2
        east = 45 <= column <= 55 and 19 <= row <= 22
        shrine_loop = 23 <= column <= 31 and 24 <= row <= 30
        return west or bend_a or middle or bend_b or east or shrine_loop

    def is_at_return_gate(self, point: tuple[int, int]) -> bool:
        return self.RETURN_GATE.collidepoint(point)
