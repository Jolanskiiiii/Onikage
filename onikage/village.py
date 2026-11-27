import random
from dataclasses import dataclass

import pygame

from onikage.art.effects.village_atmosphere import VillageAtmosphere
from onikage.art.environments.village import draw_cedar_tree, draw_village_building
from onikage.art.objects.village import draw_lantern_lighting, draw_village_object
from onikage.art.tiles.village import make_village_tiles
from onikage.art.ui.panels import item_icon
from onikage.enemy import Enemy
from onikage.masks import MaskManager, MaskType
from onikage.npc import NPC
from onikage.weapons import WeaponType


@dataclass
class WeaponPickup:
    weapon_type: WeaponType
    rect: pygame.Rect


@dataclass
class MaskPickup:
    mask_type: MaskType
    rect: pygame.Rect


class VillageWorld:
    """A small tile-based village with scenery, collision, and one sign."""

    TILE_SIZE = 32
    COLUMNS = 56
    ROWS = 40
    WORLD_SIZE = (COLUMNS * TILE_SIZE, ROWS * TILE_SIZE)

    def __init__(self) -> None:
        self.atmosphere = VillageAtmosphere(self.WORLD_SIZE)
        self.grass_tiles, self.road_tiles = make_village_tiles(self.TILE_SIZE)
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
        self.obstacles.append(self.wraith.rect)
        self.weapon_pickups = [
            WeaponPickup(WeaponType.YARI, pygame.Rect(1354, 682, 26, 22)),
        ]
        self.mask_pickups = [
            MaskPickup(MaskType.TENGU, pygame.Rect(1346, 602, 28, 28)),
            MaskPickup(MaskType.SUFFERING, pygame.Rect(868, 454, 28, 28)),
        ]
        self.decorations = [
            (935, 550, "lantern"),
            (970, 550, "lantern"),
            (770, 475, "lantern"),
            (910, 475, "lantern"),
            (1045, 550, "lantern"),
            (1045, 738, "lantern"),
            (790, 710, "shrine"),
            (490, 540, "barrel"),
            (990, 760, "barrel"),
            (1370, 735, "lantern"),
        ]
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
            if any(spot.colliderect(area) for area in house_areas) or spot.colliderect(road_area):
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
        draw_lantern_lighting(surface, camera, self.decorations, self.elapsed)
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
        if self.wraith.health > 0 and (
            player_y is None or self.wraith.rect.bottom <= player_y
        ):
            self.wraith.draw(surface, camera)
        for pickup in self.weapon_pickups:
            if player_y is None or pickup.rect.bottom <= player_y:
                self._draw_weapon_pickup(surface, pickup, camera)
        if player_y is None or self.villager.rect.bottom <= player_y:
            self.villager.draw(surface, camera)
        for x, y, kind in self.decorations:
            object_depth = y + (40 if kind == "shrine" else 33)
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
        if self.wraith.health > 0 and self.wraith.rect.bottom > player_y:
            self.wraith.draw(surface, camera)
        for pickup in self.weapon_pickups:
            if pickup.rect.bottom > player_y:
                self._draw_weapon_pickup(surface, pickup, camera)
        if self.villager.rect.bottom > player_y:
            self.villager.draw(surface, camera)
        for x, y, kind in self.decorations:
            object_depth = y + (40 if kind == "shrine" else 33)
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

    def find_weapon_pickup(self, point: tuple[int, int]) -> WeaponPickup | None:
        target = pygame.Rect(point[0] - 14, point[1] - 14, 28, 28)
        return next(
            (pickup for pickup in self.weapon_pickups if target.colliderect(pickup.rect.inflate(30, 30))),
            None,
        )

    def find_mask_pickup(self, point: tuple[int, int]) -> MaskPickup | None:
        target = pygame.Rect(point[0] - 14, point[1] - 14, 28, 28)
        return next(
            (pickup for pickup in self.mask_pickups if target.colliderect(pickup.rect.inflate(30, 30))),
            None,
        )

    def draw_mask_pickups(
        self,
        surface: pygame.Surface,
        camera: pygame.Vector2,
        player_y: int,
        manager: MaskManager,
        foreground: bool,
    ) -> None:
        for pickup in self.mask_pickups:
            if not manager.can_acquire(pickup.mask_type):
                continue
            is_foreground = pickup.rect.bottom > player_y
            if is_foreground != foreground:
                continue
            x = pickup.rect.x - round(camera.x)
            y = pickup.rect.y - round(camera.y)
            center = pickup.rect.move(-round(camera.x), -round(camera.y)).center
            pygame.draw.circle(surface, (126, 91, 145), center, 18, 1)
            icon = pygame.transform.scale(item_icon("mask"), (28, 28))
            surface.blit(icon, (x, y))

    @staticmethod
    def _draw_weapon_pickup(
        surface: pygame.Surface,
        pickup: WeaponPickup,
        camera: pygame.Vector2,
    ) -> None:
        x = pickup.rect.x - round(camera.x)
        y = pickup.rect.y - round(camera.y)
        pygame.draw.ellipse(surface, (13, 19, 20), (x - 3, y + 13, 32, 9))
        pygame.draw.ellipse(surface, (126, 112, 77), (x + 2, y + 6, 21, 12), 1)
        # Procedural ground-plane yari silhouette; no placeholder art file is referenced.
        pygame.draw.line(surface, (90, 67, 45), (x + 4, y + 18), (x + 22, y + 2), 3)
        pygame.draw.line(surface, (181, 193, 184), (x + 18, y + 6), (x + 24, y), 2)
        pygame.draw.polygon(
            surface,
            (195, 199, 177),
            [(x + 21, y + 3), (x + 26, y - 3), (x + 24, y + 5)],
        )

    def is_near_shrine(self, point: tuple[int, int]) -> bool:
        target = pygame.Rect(point[0] - 18, point[1] - 18, 36, 36)
        return target.colliderect(self.shrine_rect.inflate(18, 18))

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
                tile_index = (column * 7 + row * 11 + column * row) % len(tiles)
                surface.blit(tiles[tile_index], (x, y))

    @staticmethod
    def _is_road(column: int, row: int) -> bool:
        main_road = 16 <= row <= 21 and 0 <= column <= 55
        north_road = 24 <= column <= 29 and 5 <= row <= 17
        south_road = 22 <= column <= 28 and 20 <= row <= 35
        west_lane = 9 <= column <= 15 and 17 <= row <= 20
        east_lane = 38 <= column <= 44 and 17 <= row <= 21
        return main_road or north_road or south_road or west_lane or east_lane

    def _draw_sign(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        x = self.sign_rect.x - round(camera.x)
        y = self.sign_rect.y - round(camera.y)
        pygame.draw.rect(surface, (75, 48, 36), (x + 11, y + 16, 5, 20))
        pygame.draw.rect(surface, (133, 87, 55), (x, y, 26, 20))
        pygame.draw.rect(surface, (86, 54, 41), (x + 4, y + 4, 18, 12))
        pygame.draw.line(surface, (210, 184, 142), (x + 8, y + 8), (x + 17, y + 8), 2)
        pygame.draw.line(surface, (210, 184, 142), (x + 8, y + 13), (x + 16, y + 13), 1)

    def sorted_depth_entities(self, entities: list[tuple[float, float, object]]) -> list[object]:
        """Sort top-down entities by their screen-space ground Y coordinate."""
        return [entity for _, _, entity in sorted(entities, key=lambda item: (item[1], item[0]))]

    def point_collides(self, rect: pygame.Rect) -> bool:
        """Return whether a ground-plane rect intersects an environmental collider."""
        return any(rect.colliderect(obstacle) for obstacle in self.obstacles)
