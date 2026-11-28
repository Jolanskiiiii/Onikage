"""Drowned Temple chapter: flooded top-down shrine and Weeping Bride guardian."""
from __future__ import annotations

import math
import pygame

from onikage.village import VillageWorld
from onikage.art.tiles.region_tiles import draw_region_tiles
from onikage.art.objects.region_props import draw_region_set


class DrownedTempleWorld(VillageWorld):
    REGION_ID = "drowned_temple"
    ENTRY_POINT = (150, 580)
    RETURN_GATE = pygame.Rect(58, 548, 54, 80)

    def __init__(self) -> None:
        super().__init__()
        self.buildings = []  # These regions use bespoke landmarks, not Kagehama houses.
        self.wraith.name = "Weeping Bride"
        self.wraith.vitality.maximum = 225
        self.wraith.health = 225
        self.wraith.attack_power = 22
        self.wraith.experience_reward = 155
        self.wraith.sprite_position = (1160, 565)
        self.wraith.rect.topleft = (1164, 588)
        self.wraith.interaction_area = pygame.Rect(1128, 555, 100, 82)
        self.obstacles = [o for o in self.obstacles if o is not self.wraith.rect]
        self.obstacles.append(self.wraith.rect)
        # Flooded channels are deliberately placed beside, not across, the
        # central causeway so the existing top-down navigation remains usable.
        self.water = [
            pygame.Rect(250, 300, 360, 110),
            pygame.Rect(760, 270, 290, 115),
            pygame.Rect(1260, 300, 360, 110),
            pygame.Rect(360, 760, 300, 125),
            pygame.Rect(1040, 760, 340, 125),
        ]
        self.obstacles.extend(r.copy() for r in self.water)
        self.decorations = [
            (790, 710, "shrine"), (500, 490, "barrel"),
            (990, 760, "shrine"), (1370, 735, "barrel"),
            (720, 470, "shrine"), (1210, 500, "barrel"),
        ]
        self.trees = [tree for index, tree in enumerate(self.trees) if index % 4 == 0]
        self._water_phase = 0.0

    def update(self, dt: float) -> None:
        super().update(dt)
        self._water_phase += max(0.0, dt)

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2,
             player_y: int | None = None) -> None:
        surface.fill((13, 22, 29))
        super().draw(surface, camera, player_y)
        draw_region_set(surface, camera, self.REGION_ID)
        self._draw_water(surface, camera)
        # Dedicated drowned sanctuary: raised stone plinth, teal roof tiers,
        # dark timber pillars and a luminous sealed doorway.
        hx, hy = 760 - round(camera.x), 115 - round(camera.y)
        hall = pygame.Rect(hx, hy, 360, 190)
        if surface.get_rect().colliderect(hall.inflate(70, 70)):
            pygame.draw.ellipse(surface, (5, 15, 19), (hx - 18, hy + 150, 396, 52))
            pygame.draw.rect(surface, (45, 63, 65), (hx + 24, hy + 116, 312, 58))
            pygame.draw.rect(surface, (95, 119, 112), (hx + 24, hy + 116, 312, 7))
            pygame.draw.rect(surface, (24, 39, 43), (hx + 48, hy + 55, 264, 72))
            for px in (hx + 62, hx + 118, hx + 242, hx + 298):
                pygame.draw.rect(surface, (91, 65, 49), (px, hy + 52, 10, 83))
                pygame.draw.line(surface, (148, 111, 76), (px + 2, hy + 55), (px + 2, hy + 126), 1)
            pygame.draw.polygon(surface, (14, 33, 39), [(hx + 8, hy + 65), (hx + 180, hy + 4), (hx + 352, hy + 65)])
            pygame.draw.polygon(surface, (45, 83, 85), [(hx + 28, hy + 61), (hx + 180, hy + 13), (hx + 332, hy + 61)])
            pygame.draw.line(surface, (105, 158, 151), (hx + 34, hy + 60), (hx + 326, hy + 60), 3)
            pygame.draw.rect(surface, (8, 22, 28), (hx + 151, hy + 72, 58, 62))
            pygame.draw.ellipse(surface, (41, 132, 139), (hx + 169, hy + 84, 22, 35), 2)
        # Cool mist softens the far edges without obscuring collision routes.
        mist = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for i in range(5):
            y = int((i * 151 + self._water_phase * (7 + i)) % (surface.get_height() + 100)) - 50
            pygame.draw.ellipse(mist, (112, 151, 164, 13), (-80, y, surface.get_width() + 160, 54))
        surface.blit(mist, (0, 0))
        font = pygame.font.Font(None, 25)
        label = font.render("CHAPTER III  ·  THE DROWNED TEMPLE", True, (159, 204, 211))
        surface.blit(label, (surface.get_width() - label.get_width() - 24, 18))

    def _draw_tiles(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        draw_region_tiles(
            surface, camera, self.TILE_SIZE, self.COLUMNS, self.ROWS,
            self._is_road, self.REGION_ID,
        )

    def _draw_water(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        for i, pool in enumerate(self.water):
            rect = pool.move(-round(camera.x), -round(camera.y))
            if not surface.get_rect().colliderect(rect):
                continue
            pygame.draw.rect(surface, (13, 39, 49), rect)
            pygame.draw.rect(surface, (38, 78, 86), rect, 2)
            for line in range(5):
                y = rect.y + 12 + line * 21
                offset = math.sin(self._water_phase * 1.2 + line + i) * 9
                pygame.draw.line(surface, (63, 112, 119), (rect.x + 12 + int(offset), y),
                                 (rect.right - 12 + int(offset), y), 1)

    @staticmethod
    def _is_road(column: int, row: int) -> bool:
        # Narrow raised causeways connect temple islands across flooded basins.
        west = 0 <= column <= 17 and 17 <= row <= 20
        central = 15 <= column <= 40 and 17 <= row <= 19
        east = 38 <= column <= 55 and 17 <= row <= 20
        north_bridge = 24 <= column <= 29 and 7 <= row <= 18
        south_bridge = 30 <= column <= 35 and 18 <= row <= 33
        inner_walk = 20 <= column <= 35 and 10 <= row <= 13
        return west or central or east or north_bridge or south_bridge or inner_walk

    def is_at_return_gate(self, point: tuple[int, int]) -> bool:
        return self.RETURN_GATE.collidepoint(point)
