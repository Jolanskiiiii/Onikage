"""Playable Burning Village chapter environment.

This first chapter map reuses the proven top-down village collision/entity
pipeline while supplying a distinct scorched ground palette and animated fire,
smoke and ember dressing. It intentionally keeps world-space anchors stable.
"""
from __future__ import annotations

import math
import random
import pygame

from onikage.village import VillageWorld
from onikage.art.tiles.region_tiles import draw_region_tiles
from onikage.art.objects.region_props import draw_region_set


class BurningVillageWorld(VillageWorld):
    """A scorched counterpart to Kagehama with stable top-down collision."""

    REGION_ID = "burning_village"
    ENTRY_POINT = (150, 580)
    RETURN_GATE = pygame.Rect(58, 548, 54, 80)

    def __init__(self) -> None:
        super().__init__()
        self.show_scorched_pass_gate = False
        self.wraith.name = "Ashen Oni"
        self.wraith.vitality.maximum = 190
        self.wraith.health = 190
        self.wraith.attack_power = 19
        self.wraith.experience_reward = 120
        self.wraith.sprite_position = (1160, 565)
        self.wraith.rect.topleft = (1164, 588)
        self.wraith.interaction_area = pygame.Rect(1128, 555, 100, 82)
        self.obstacles = [o for o in self.obstacles if o is not self.wraith.rect]
        self.obstacles.append(self.wraith.rect)
        # Burning debris blocks several side paths while leaving the central
        # road navigable for the player and the guardian encounter.
        self.fire_pits = [
            pygame.Rect(420, 535, 70, 48),
            pygame.Rect(880, 690, 82, 48),
            pygame.Rect(1450, 535, 90, 48),
        ]
        self.obstacles.extend(r.copy() for r in self.fire_pits)
        # A ruined settlement should not reuse the intact village lantern line.
        # Keep only the shrine landmark and replace ordinary roadside lanterns
        # with debris props; the fire pits provide the chapter's warm light.
        self.decorations = [
            (790, 710, "shrine"),
            (490, 540, "barrel"),
            (990, 760, "barrel"),
            (1370, 735, "barrel"),
            (720, 490, "barrel"),
            (1210, 500, "barrel"),
        ]
        # Charred trees are smaller and more widely spaced than the healthy
        # cedar line in Kagehama, helping the chapter read as a separate place.
        self.trees = [tree for index, tree in enumerate(self.trees) if index % 3 == 0]
        self._embers = [
            (random.Random(8100 + i).randrange(80, 1710),
             random.Random(9100 + i).randrange(100, 1160),
             random.Random(10100 + i).random() * math.tau)
            for i in range(42)
        ]

    def update(self, dt: float) -> None:
        super().update(dt)
        self.wraith.update(dt)

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2,
             player_y: int | None = None) -> None:
        # Scorched underlay establishes a distinct chapter palette; inherited
        # tiles and props retain the original game's pixel scale and anchors.
        surface.fill((25, 23, 22))
        super().draw(surface, camera, player_y)
        draw_region_set(surface, camera, self.REGION_ID)
        self._draw_fire_atmosphere(surface, camera)
        self._draw_charred_building_marks(surface, camera)
        title_font = pygame.font.Font(None, 25)
        label = title_font.render("CHAPTER II  ·  THE BURNING VILLAGE", True, (242, 174, 112))
        surface.blit(label, (surface.get_width() - label.get_width() - 24, 18))

    def _draw_charred_building_marks(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        """Overlay broken roof beams and soot scars on inherited building shells."""
        for index, building in enumerate(self.buildings):
            sx, sy = building.x - round(camera.x), building.y - round(camera.y)
            if not (-260 <= sx <= surface.get_width() + 80 and -220 <= sy <= surface.get_height() + 80):
                continue
            pygame.draw.polygon(surface, (25, 23, 23), [
                (sx + 8, sy + 46), (sx + building.width // 2, sy + 5),
                (sx + building.width - 8, sy + 46),
                (sx + building.width - 25, sy + 39), (sx + 20, sy + 58),
            ])
            pygame.draw.line(surface, (76, 48, 39), (sx + 20, sy + 43),
                             (sx + building.width - 24, sy + 34), 3)
            pygame.draw.line(surface, (35, 29, 28), (sx + 34, sy + 50),
                             (sx + building.width - 40, sy + 18), 2)
            if index % 2 == 0:
                pygame.draw.line(surface, (177, 72, 37), (sx + building.width // 2, sy + 48),
                                 (sx + building.width // 2 + 5, sy + 24), 2)

    def _draw_tiles(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        draw_region_tiles(
            surface, camera, self.TILE_SIZE, self.COLUMNS, self.ROWS,
            self._is_road, self.REGION_ID,
        )

    def _draw_fire_atmosphere(self, surface: pygame.Surface,
                              camera: pygame.Vector2) -> None:
        t = self.elapsed
        for i, pit in enumerate(self.fire_pits):
            cx = pit.centerx - round(camera.x)
            cy = pit.centery - round(camera.y)
            if not (-40 <= cx <= surface.get_width() + 40 and -40 <= cy <= surface.get_height() + 40):
                continue
            pulse = 5 + int(3 * math.sin(t * 5.0 + i))
            pygame.draw.ellipse(surface, (75, 34, 24), (cx - 31, cy - 11, 62, 22))
            for flame in range(4):
                fx = cx - 20 + flame * 13
                height = pulse + ((flame * 3 + int(t * 7)) % 5)
                pygame.draw.polygon(surface, (188, 72, 35), [(fx - 5, cy + 5), (fx, cy - height), (fx + 5, cy + 5)])
                pygame.draw.polygon(surface, (244, 157, 65), [(fx - 2, cy + 4), (fx, cy - height // 2), (fx + 2, cy + 4)])
        for x, y, phase in self._embers:
            sy = (y - t * (15 + (phase % 13) * 2)) % self.WORLD_SIZE[1]
            sx = x + math.sin(t * 1.4 + phase) * 7
            px, py = round(sx - camera.x), round(sy - camera.y)
            if 0 <= px < surface.get_width() and 0 <= py < surface.get_height():
                surface.set_at((px, py), (238, 123 + int(35 * abs(math.sin(t + phase))), 55))

    @staticmethod
    def _is_road(column: int, row: int) -> bool:
        # A broken, offset evacuation route through the burned settlement.
        west = 0 <= column <= 18 and 17 <= row <= 21
        bend = 16 <= column <= 31 and 14 <= row <= 21 and abs(row - (21 - (column - 16)//3)) <= 2
        east = 29 <= column <= 55 and 16 <= row <= 21
        north_escape = 9 <= column <= 13 and 7 <= row <= 19
        south_ally = 36 <= column <= 41 and 19 <= row <= 31
        return west or bend or east or north_escape or south_ally

    def is_at_return_gate(self, point: tuple[int, int]) -> bool:
        return self.RETURN_GATE.collidepoint(point)
