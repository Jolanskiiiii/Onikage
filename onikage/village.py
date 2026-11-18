import random
from functools import lru_cache

import pygame

from onikage.art.effects.village_atmosphere import VillageAtmosphere
from onikage.art.environments.village import draw_cedar_tree, draw_village_building
from onikage.art.objects.village import draw_village_object
from onikage.art.tiles.village import (
    make_stream_tiles,
    make_village_tiles,
    road_tile_index,
)
from onikage.enemy import Enemy
from onikage.npc import NPC


@lru_cache(maxsize=1)
def _village_road_cells() -> frozenset[tuple[int, int]]:
    roads: set[tuple[int, int]] = set()

    def connect(points: tuple[tuple[int, int], ...], radius: int = 1) -> None:
        for start, end in zip(points, points[1:]):
            steps = max(abs(end[0] - start[0]), abs(end[1] - start[1]), 1)
            for step in range(steps + 1):
                x = round(start[0] + (end[0] - start[0]) * step / steps)
                y = round(start[1] + (end[1] - start[1]) * step / steps)
                for offset_x in range(-radius, radius + 1):
                    for offset_y in range(-radius, radius + 1):
                        column, row = x + offset_x, y + offset_y
                        if 0 <= column < 56 and 0 <= row < 40:
                            roads.add((column, row))

    connect(
        (
            (-1, 18),
            (7, 18),
            (13, 17),
            (19, 18),
            (26, 18),
            (34, 19),
            (41, 18),
            (48, 18),
            (56, 18),
        ),
        radius=1,
    )
    connect(((26, 18), (26, 13), (26, 7), (26, 4)), radius=1)
    connect(((10, 18), (11, 16), (12, 14)), radius=1)
    connect(((42, 18), (43, 16), (44, 14)), radius=1)
    connect(((26, 18), (25, 20), (25, 22)), radius=1)
    connect(
        ((26, 18), (26, 23), (25, 26), (25, 29), (26, 33), (28, 36)),
        radius=1,
    )
    connect(((18, 18), (17, 21), (16, 23)), radius=1)
    connect(((35, 19), (36, 22), (37, 24)), radius=1)
    return frozenset(roads)


class VillageWorld:
    """A small tile-based village with scenery, collision, and one sign."""

    TILE_SIZE = 32
    COLUMNS = 56
    ROWS = 40
    WORLD_SIZE = (COLUMNS * TILE_SIZE, ROWS * TILE_SIZE)

    def __init__(self) -> None:
        self.atmosphere = VillageAtmosphere(self.WORLD_SIZE)
        self.grass_tiles, self.road_tiles = make_village_tiles(self.TILE_SIZE)
        self.stream_tiles = make_stream_tiles(self.TILE_SIZE)
        self.buildings = [
            pygame.Rect(160, 170, 190, 132),
            pygame.Rect(530, 130, 205, 145),
            pygame.Rect(1080, 180, 190, 135),
            pygame.Rect(1430, 280, 190, 145),
            pygame.Rect(210, 840, 220, 150),
            pygame.Rect(1130, 880, 230, 160),
        ]
        self.trees = self._make_trees()
        self.obstacles = [
            *[pygame.Rect(rect.x - 12, rect.y + 48, rect.width + 24, rect.height - 42)
              for rect in self.buildings],
            *[pygame.Rect(x - 9, y + 19, 18, 13) for x, y, _ in self.trees],
        ]
        self.sign_rect = pygame.Rect(788, 574, 26, 34)
        self.obstacles.append(self.sign_rect.copy())
        self.villager = NPC(
            970,
            590,
            "Hana, Village Keeper",
            (
                "You are the exile from the northern pass, aren't you? The shrine bells rang when you arrived.",
                "The old cedar forest has grown restless. Lights wander between the trees after sundown.",
                "Before you leave, would you offer a prayer at our village shrine? The people could use a little hope.",
            ),
        )
        self.obstacles.append(self.villager.rect.copy())
        self.shrine_rect = pygame.Rect(786, 710, 50, 39)
        self.obstacles.append(self.shrine_rect.copy())
        self.wraith = Enemy(850, 420)
        self.obstacles.append(self.wraith.rect.copy())
        self.decorations = [
            (790, 710, "shrine"),
            (490, 540, "barrel"),
            (990, 760, "barrel"),
            (440, 500, "bamboo"),
            (1060, 500, "paper_lantern"),
            (1370, 750, "katana_stand"),
            (1460, 745, "fence"),
        ]
        self.prop_obstacles = [
            pygame.Rect(754, 749, 24, 8),
            pygame.Rect(805, 754, 22, 10),
            pygame.Rect(450, 522, 12, 9),
            pygame.Rect(1070, 522, 10, 8),
            pygame.Rect(1374, 770, 24, 8),
            pygame.Rect(1461, 769, 30, 8),
            pygame.Rect(431, 496, 40, 13),
            pygame.Rect(1177, 476, 40, 13),
            pygame.Rect(1442, 682, 40, 13),
            pygame.Rect(612, 916, 40, 13),
            pygame.Rect(517, 481, 18, 12),
            pygame.Rect(1238, 541, 18, 12),
        ]
        self.river_obstacles = [
            pygame.Rect(448, 928, 328, 32),
            pygame.Rect(824, 928, 296, 32),
            pygame.Rect(1376, 928, self.WORLD_SIZE[0] - 1376, 32),
        ]
        self.obstacles.extend(rect.copy() for rect in self.river_obstacles)
        self.obstacles.extend(obstacle.copy() for obstacle in self.prop_obstacles)
        self.forest_gate = pygame.Rect(770, 90, 250, 60)
        self.decorations.extend(
            (
                (450, 505, "sakura"),
                (1197, 485, "sakura"),
                (1462, 691, "sakura"),
                (632, 925, "sakura"),
                (526, 493, "bamboo_grove"),
                (1247, 553, "bamboo_grove"),
                (800, 960, "bridge"),
                (1020, 710, "stone_lantern"),
                (1480, 790, "torii"),
            )
        )

    @staticmethod
    def _make_trees() -> list[tuple[int, int, int]]:
        randomizer = random.Random(37)
        trees: list[tuple[int, int, int]] = []
        house_areas = [
            pygame.Rect(100, 100, 300, 240),
            pygame.Rect(470, 60, 320, 280),
            pygame.Rect(1020, 110, 310, 260),
            pygame.Rect(1380, 220, 300, 270),
            pygame.Rect(150, 780, 340, 260),
            pygame.Rect(1080, 820, 340, 280),
        ]
        road_area = pygame.Rect(0, 515, 1792, 230)
        for _ in range(78):
            x = randomizer.randrange(40, 1750)
            y = randomizer.randrange(50, 1200)
            spot = pygame.Rect(x - 22, y - 22, 44, 44)
            if (
                any(spot.colliderect(area) for area in house_areas)
                or spot.colliderect(road_area)
                or (x // VillageWorld.TILE_SIZE, y // VillageWorld.TILE_SIZE)
                in _village_road_cells()
            ):
                continue
            trees.append((x, y, randomizer.randrange(30, 43)))
        return trees

    def update(self, dt: float) -> None:
        self.atmosphere.update(dt)

    @property
    def elapsed(self) -> float:
        return self.atmosphere.elapsed

    def draw(
        self,
        surface: pygame.Surface,
        camera: pygame.Vector2,
        player_y: int | None = None,
    ) -> None:
        self._draw_tiles(surface, camera)
        view = pygame.Rect(
            round(camera.x) - 80,
            round(camera.y) - 100,
            surface.get_width() + 160,
            surface.get_height() + 200,
        )
        for building in self.buildings:
            if (
                (player_y is None or building.bottom <= player_y)
                and building.inflate(60, 70).colliderect(view)
            ):
                draw_village_building(surface, building, camera)
        for x, y, height in self.trees:
            tree_bounds = pygame.Rect(x - height, y - 10, height * 2, height + 12)
            if (
                (player_y is None or y + height <= player_y)
                and tree_bounds.colliderect(view)
            ):
                draw_cedar_tree(surface, x, y, height, camera)
        if player_y is None or self.wraith.rect.bottom <= player_y:
            self.wraith.draw(surface, camera)
        if player_y is None or self.villager.rect.bottom <= player_y:
            self.villager.draw(surface, camera)
        for x, y, kind in self.decorations:
            object_depth = self._decoration_depth(y, kind)
            if view.collidepoint(x, y) and (player_y is None or object_depth <= player_y):
                draw_village_object(surface, x, y, kind, camera)
        if player_y is None or self.sign_rect.bottom <= player_y:
            self._draw_sign(surface, camera)
        self.atmosphere.draw(surface, camera)

    def draw_foreground(
        self,
        surface: pygame.Surface,
        camera: pygame.Vector2,
        player_y: int,
    ) -> None:
        view = pygame.Rect(
            round(camera.x) - 80,
            round(camera.y) - 100,
            surface.get_width() + 160,
            surface.get_height() + 200,
        )
        for building in self.buildings:
            if building.bottom > player_y and building.inflate(60, 70).colliderect(view):
                draw_village_building(surface, building, camera)
        for x, y, height in self.trees:
            tree_bounds = pygame.Rect(x - height, y - 10, height * 2, height + 12)
            if y + height > player_y and tree_bounds.colliderect(view):
                draw_cedar_tree(surface, x, y, height, camera)
        if self.wraith.rect.bottom > player_y:
            self.wraith.draw(surface, camera)
        if self.villager.rect.bottom > player_y:
            self.villager.draw(surface, camera)
        for x, y, kind in self.decorations:
            object_depth = self._decoration_depth(y, kind)
            if object_depth > player_y and view.collidepoint(x, y):
                draw_village_object(surface, x, y, kind, camera)
        if self.sign_rect.bottom > player_y:
            self._draw_sign(surface, camera)

    def interact(self, point: tuple[int, int]) -> str | None:
        target = pygame.Rect(point[0] - 18, point[1] - 18, 36, 36)
        if target.colliderect(self.sign_rect.inflate(30, 30)):
            return "Village Notice: The northern road leads to the old cedar forest. Do not travel there after sunset."
        if self.is_near_shrine(point):
            return "The shrine bells answer your prayer."
        return None

    def find_villager(self, point: tuple[int, int]) -> NPC | None:
        target = pygame.Rect(point[0] - 12, point[1] - 12, 24, 24)
        if target.colliderect(self.villager.interaction_area):
            return self.villager
        return None

    def find_enemy(self, point: tuple[int, int]) -> Enemy | None:
        target = pygame.Rect(point[0] - 12, point[1] - 12, 24, 24)
        if self.wraith.health > 0 and target.colliderect(self.wraith.interaction_area):
            return self.wraith
        return None

    def is_near_shrine(self, point: tuple[int, int]) -> bool:
        target = pygame.Rect(point[0] - 18, point[1] - 18, 36, 36)
        return target.colliderect(self.shrine_rect.inflate(18, 18))

    @staticmethod
    def _decoration_depth(y: int, kind: str) -> int:
        if kind == "shrine":
            return y + 54
        if kind == "barrel":
            return y + 37
        if kind == "bridge":
            return y - 104
        if kind == "sakura":
            return y + 4
        if kind == "bamboo_grove":
            return y + 12
        return y + 32

    def _draw_tiles(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        left = max(0, int(camera.x // self.TILE_SIZE))
        top = max(0, int(camera.y // self.TILE_SIZE))
        right = min(
            self.COLUMNS,
            int((camera.x + surface.get_width()) // self.TILE_SIZE) + 2,
        )
        bottom = min(
            self.ROWS,
            int((camera.y + surface.get_height()) // self.TILE_SIZE) + 2,
        )
        for row in range(top, bottom):
            for column in range(left, right):
                x = column * self.TILE_SIZE - round(camera.x)
                y = row * self.TILE_SIZE - round(camera.y)
                road = self._is_road(column, row)
                tiles = self.road_tiles if road else self.grass_tiles
                if road:
                    connections = 0
                    for bit, (offset_x, offset_y) in enumerate(
                        ((0, -1), (1, 0), (0, 1), (-1, 0))
                    ):
                        if self._is_road(column + offset_x, row + offset_y):
                            connections |= 1 << bit
                    variant = (column * 7 + row * 11 + column * row) % 8
                    tile_index = road_tile_index(connections, variant)
                else:
                    tile_index = (column * 7 + row * 11 + column * row) % len(tiles)
                surface.blit(tiles[tile_index], (x, y))
                if (
                    row == 29
                    and column >= 14
                    and not 23 <= column <= 26
                    and not 35 <= column <= 42
                ):
                    stream_index = (column * 3 + row) % len(self.stream_tiles)
                    surface.blit(self.stream_tiles[stream_index], (x, y))

    @staticmethod
    def _is_road(column: int, row: int) -> bool:
        return (column, row) in _village_road_cells()

    def _draw_sign(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        x = self.sign_rect.x - round(camera.x)
        y = self.sign_rect.y - round(camera.y)
        pygame.draw.rect(surface, (75, 48, 36), (x + 11, y + 16, 5, 20))
        pygame.draw.rect(surface, (133, 87, 55), (x, y, 26, 20))
        pygame.draw.rect(surface, (86, 54, 41), (x + 4, y + 4, 18, 12))
        pygame.draw.line(surface, (210, 184, 142), (x + 8, y + 8), (x + 17, y + 8), 2)
        pygame.draw.line(surface, (210, 184, 142), (x + 8, y + 13), (x + 16, y + 13), 1)
