import random
from functools import lru_cache
from dataclasses import dataclass

import pygame

from onikage.art.effects.ground_shadows import draw_ground_shadow
from onikage.art.effects.village_atmosphere import VillageAtmosphere
from onikage.art.environments.village import draw_cedar_tree, draw_village_building
from onikage.art.objects.village import draw_lantern_lighting, draw_village_object
from onikage.art.objects.region_props import sprite
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


# Sprite origins are chosen so lantern ground contacts (origin Y + 33) sit
# on the road verges at Y=512 and Y=704, never in the walking lane.
VILLAGE_LANTERN_LAYOUT = (
    (260, 479), (500, 479), (1110, 479), (1370, 479),
    (260, 671), (500, 671), (1110, 671), (1370, 671),
)


class VillageWorld:
    """A small tile-based village with scenery, collision, and one sign."""

    TILE_SIZE = 32
    COLUMNS = 84
    ROWS = 60
    WORLD_SIZE = (COLUMNS * TILE_SIZE, ROWS * TILE_SIZE)

    def __init__(self) -> None:
        self.atmosphere = VillageAtmosphere(self.WORLD_SIZE)
        self.show_scorched_pass_gate = True
        self.grass_tiles, self.road_tiles = make_village_tiles(self.TILE_SIZE)
        self.buildings = [
            pygame.Rect(160, 170, 190, 132),
            pygame.Rect(530, 130, 205, 145),
            pygame.Rect(1080, 180, 190, 135),
            pygame.Rect(1430, 280, 190, 145),
            pygame.Rect(210, 840, 220, 150),
            pygame.Rect(1130, 880, 230, 160),
            # Additional homes define the southern residential quarter.
            pygame.Rect(620, 1260, 190, 138),
            pygame.Rect(1390, 1430, 210, 150),
        ]
        self.trees = self._make_trees()
        self.obstacles = [
            *[pygame.Rect(rect.x - 12, rect.y + 48, rect.width + 24, rect.height - 42)
              for rect in self.buildings],
            *[pygame.Rect(x - 10, y + height - 7, 20, 13) for x, y, height in self.trees],
        ]
        # Keep the sign at its original map position, but collide only with
        # its two physical supports and ground footprint (not the board face).
        self.sign_position = (788, 574)
        self.sign_rect = pygame.Rect(794, 594, 24, 24)
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
        # Optional quest destinations: memorial tablet and market ledger.
        self.quest_sites = {
            "names_on_stone": ((890, 875), "The memorial names are clear again. A quiet bell answers from the shrine."),
            "merchants_lost_ledger": ((650, 930), "You recover the merchant's ledger. The missing supply names are written inside."),
        }
        self.wraith = Enemy(850, 420)
        self.obstacles.append(self.wraith.rect)
        self.weapon_pickups = [
            WeaponPickup(WeaponType.YARI, pygame.Rect(1354, 682, 26, 22)),
        ]
        # Regional masks are awarded by their own guardian chapters, not
        # scattered as pickups in the starting village.
        self.mask_pickups: list[MaskPickup] = []
        # Lanterns sit on the verges, never in the walkable road footprint.
        # Their y values are sprite origins; the rendered ground contact is y + 33.
        self.decorations = [
            *((x, y, "lantern") for x, y in VILLAGE_LANTERN_LAYOUT),
            (790, 710, "shrine"),
            (490, 540, "barrel"),
            (990, 760, "barrel"),
            # Hand-placed village landmarks fill the expanded districts.
            (390, 485, "market"),
            (1190, 485, "market"),
            (890, 875, "well"),
            (650, 930, "cart"),
            (1430, 1120, "tea_stall"),
            (1080, 1370, "market"),
            (430, 1390, "garden"),
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
        # Populate the expanded outskirts as intentional woodland belts rather
        # than leaving the added world area as empty grass. Keep paths open.
        for _ in range(112):
            x = randomizer.randrange(44, VillageWorld.COLUMNS * VillageWorld.TILE_SIZE - 44)
            y = randomizer.randrange(48, VillageWorld.ROWS * VillageWorld.TILE_SIZE - 48)
            spot = pygame.Rect(x - 22, y - 22, 44, 44)
            if any(spot.colliderect(area) for area in house_areas) or spot.colliderect(road_area):
                continue
            if VillageWorld._is_road(x // VillageWorld.TILE_SIZE, y // VillageWorld.TILE_SIZE):
                continue
            trees.append((x, y, randomizer.randrange(30, 48)))
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
        self._draw_fences(surface, camera)
        draw_lantern_lighting(surface, camera, self.decorations, self.elapsed)
        view = self._world_view(surface, camera)
        self._draw_depth_layer(surface, camera, view, player_y, foreground=False)
        self._draw_quest_sites(surface, camera)
        self.atmosphere.draw(surface, camera)
        if self.show_scorched_pass_gate:
            self._draw_scorched_pass_gate(surface, camera)


    @staticmethod
    def _draw_fences(surface: pygame.Surface, camera: pygame.Vector2) -> None:
        # Short cedar fencing encloses garden edges and house yards without blocking lanes.
        for x, y, flip in ((350, 430, False), (1040, 430, True), (330, 790, False), (1450, 790, True)):
            fence = sprite("kagehama_fence.png")
            if flip:
                fence = pygame.transform.flip(fence, True, False)
            surface.blit(fence, (x - round(camera.x), y - round(camera.y)))

    @staticmethod
    def _draw_scorched_pass_gate(surface: pygame.Surface, camera: pygame.Vector2) -> None:
        """Draw a readable torii-style gate marking the eastbound chapter exit."""
        x, y = 1640 - round(camera.x), 532 - round(camera.y)
        if x < -100 or x > surface.get_width() + 100 or y < -100 or y > surface.get_height() + 100:
            return
        # Ground shadow and stone approach marker.
        draw_ground_shadow(surface, (x + 4, y + 83, 94, 13), opacity=105)
        pygame.draw.rect(surface, (63, 53, 46), (x + 16, y + 72, 64, 9))
        pygame.draw.rect(surface, (111, 83, 62), (x + 20, y + 73, 56, 3))
        # Weathered vermilion uprights.
        for px in (x + 22, x + 70):
            pygame.draw.rect(surface, (65, 35, 31), (px - 3, y + 13, 12, 68))
            pygame.draw.rect(surface, (128, 54, 43), (px, y + 16, 6, 63))
            pygame.draw.line(surface, (190, 104, 70), (px + 1, y + 19), (px + 1, y + 70), 1)
            pygame.draw.rect(surface, (49, 39, 34), (px - 3, y + 76, 12, 5))
        # Double crossbeam and blackened end caps.
        pygame.draw.rect(surface, (54, 34, 31), (x + 8, y + 7, 90, 12))
        pygame.draw.rect(surface, (151, 65, 48), (x + 5, y + 5, 96, 7))
        pygame.draw.rect(surface, (81, 43, 36), (x + 12, y + 18, 82, 5))
        pygame.draw.rect(surface, (42, 35, 32), (x + 2, y + 4, 12, 10))
        pygame.draw.rect(surface, (42, 35, 32), (x + 92, y + 4, 12, 10))
        font = pygame.font.Font(None, 18)
        label = font.render("SCORCHED PASS  [E]", True, (247, 205, 151))
        panel = pygame.Rect(x - 4, y - 19, label.get_width() + 12, 17)
        pygame.draw.rect(surface, (24, 20, 19), panel)
        pygame.draw.rect(surface, (157, 111, 72), panel, 1)
        surface.blit(label, (panel.x + 6, panel.y + 1))

    def _draw_quest_sites(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        """Subtle gold discovery markers for optional Kagehama errands."""
        for (wx, wy), _description in self.quest_sites.values():
            sx, sy = wx - round(camera.x), wy - round(camera.y)
            if not (-24 <= sx <= surface.get_width()+24 and -24 <= sy <= surface.get_height()+24):
                continue
            pygame.draw.ellipse(surface, (18, 17, 15), (sx-10, sy+5, 20, 7))
            pygame.draw.circle(surface, (73, 54, 31), (sx, sy), 8)
            pygame.draw.circle(surface, (213, 174, 100), (sx, sy), 5, 1)
            pygame.draw.circle(surface, (236, 207, 145), (sx, sy), 2)

    def draw_foreground(
        self,
        surface: pygame.Surface,
        camera: pygame.Vector2,
        player_y: int,
    ) -> None:
        view = self._world_view(surface, camera)
        self._draw_depth_layer(surface, camera, view, player_y, foreground=True)

    @staticmethod
    def _world_view(surface: pygame.Surface, camera: pygame.Vector2) -> pygame.Rect:
        return pygame.Rect(
            round(camera.x) - 80,
            round(camera.y) - 100,
            surface.get_width() + 160,
            surface.get_height() + 200,
        )

    @staticmethod
    def _sort_depth_entries(
        entries: list[tuple[int, int, str, object]],
    ) -> list[tuple[int, int, str, object]]:
        """Order world entities by ground Y, with X as a stable tie-breaker."""
        return sorted(entries, key=lambda entry: (entry[0], entry[1]))

    @staticmethod
    def _is_foreground_depth(entity_ground_y: int, player_ground_y: int) -> bool:
        """An entity is in front only when its ground row is below the player."""
        return entity_ground_y > player_ground_y

    def _draw_depth_layer(
        self,
        surface: pygame.Surface,
        camera: pygame.Vector2,
        view: pygame.Rect,
        player_y: int | None,
        foreground: bool,
    ) -> None:
        """Draw visible world entities on the selected side of the player depth."""
        entries: list[tuple[int, int, str, object]] = []

        for building in self.buildings:
            if building.inflate(60, 70).colliderect(view):
                entries.append((building.bottom, building.centerx, "building", building))

        for x, y, height in self.trees:
            tree_bounds = pygame.Rect(x - height, y - 10, height * 2, height + 12)
            if tree_bounds.colliderect(view):
                entries.append((self._tree_ground_y(y, height), x, "tree", (x, y, height)))

        if self.wraith.health > 0:
            entries.append((self.wraith.rect.bottom, self.wraith.rect.centerx, "wraith", self.wraith))

        for pickup in self.weapon_pickups:
            entries.append((pickup.rect.bottom, pickup.rect.centerx, "weapon", pickup))

        entries.append((self.villager.rect.bottom, self.villager.rect.centerx, "npc", self.villager))

        for x, y, kind in self.decorations:
            if view.collidepoint(x, y):
                entries.append((self._decoration_ground_y(y, kind), x, "decoration", (x, y, kind)))

        sign_bounds = pygame.Rect(
            self.sign_position[0] - 8,
            self.sign_position[1] - 4,
            52,
            52,
        )
        if sign_bounds.colliderect(view):
            entries.append((self.sign_ground_y, self.sign_position[0], "sign", None))

        for depth_y, _x, kind, payload in self._sort_depth_entries(entries):
            is_foreground = player_y is not None and self._is_foreground_depth(depth_y, player_y)
            if is_foreground != foreground and player_y is not None:
                continue
            if foreground and player_y is None:
                continue

            if kind == "building":
                draw_village_building(surface, payload, camera)
            elif kind == "tree":
                x, y, height = payload
                draw_cedar_tree(surface, x, y, height, camera)
            elif kind == "wraith":
                payload.draw(surface, camera)
            elif kind == "weapon":
                self._draw_weapon_pickup(surface, payload, camera)
            elif kind == "npc":
                payload.draw(surface, camera)
            elif kind == "decoration":
                x, y, decoration_kind = payload
                if decoration_kind in {"market", "well", "cart", "tea_stall", "garden"}:
                    self._draw_landmark(surface, x, y, decoration_kind, camera)
                else:
                    draw_village_object(surface, x, y, decoration_kind, camera)
            elif kind == "sign":
                self._draw_sign(surface, camera)

    def interact(self, point: tuple[int, int]) -> str | None:
        target = pygame.Rect(point[0] - 18, point[1] - 18, 36, 36)
        if target.colliderect(self.sign_rect.inflate(30, 30)):
            return "Village Notice: The northern road leads to the old cedar forest. Do not travel there after sunset."
        if self.is_near_shrine(point):
            return "The shrine bells answer your prayer."
        for (wx, wy), description in self.quest_sites.values():
            if pygame.Vector2(point).distance_to((wx, wy)) <= 48:
                return description
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
                self._draw_road_transition(surface, x, y, column, row, road)

    def _draw_road_transition(
        self,
        surface: pygame.Surface,
        screen_x: int,
        screen_y: int,
        column: int,
        row: int,
        road: bool,
    ) -> None:
        """Blit a cached edge-detail tile instead of setting pixels every frame."""
        overlay = self._road_transition_surface(column, row, road)
        if overlay is not None:
            surface.blit(overlay, (screen_x, screen_y))

    @staticmethod
    @lru_cache(maxsize=8192)
    def _road_transition_surface(column: int, row: int, road: bool) -> pygame.Surface | None:
        """Build deterministic road/grass edge pixels once per tile."""
        tile_size = VillageWorld.TILE_SIZE
        neighbors = ((0, -1), (1, 0), (0, 1), (-1, 0))
        overlay = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        has_detail = False
        for dx, dy in neighbors:
            if VillageWorld._is_road(column + dx, row + dy) == road:
                continue
            seed = (column * 73856093) ^ (row * 19349663) ^ (dx * 83492791) ^ (dy * 297121507)
            for index in range(10):
                seed = (seed * 1103515245 + 12345 + index * 97) & 0x7FFFFFFF
                along = 2 + (seed % (tile_size - 4))
                depth = 1 + ((seed >> 8) % (5 if index % 3 == 0 else 3))
                if dy == -1:
                    px, py = along, depth - 1
                elif dy == 1:
                    px, py = along, tile_size - depth
                elif dx == -1:
                    px, py = depth - 1, along
                else:
                    px, py = tile_size - depth, along
                if road:
                    color = ((43, 59, 43), (54, 72, 48), (35, 54, 43))[index % 3]
                else:
                    color = ((82, 67, 55), (96, 79, 63), (69, 56, 49))[index % 3]
                overlay.set_at((px, py), color + (255,))
                has_detail = True
        return overlay if has_detail else None

    @staticmethod
    @lru_cache(maxsize=16384)
    def _is_road(column: int, row: int) -> bool:
        """Hand-laid winding road network connecting every expanded district."""
        paths = (
            ((-2, 19), (18, 19), (27, 18), (39, 19), (51, 22), (64, 22), (76, 20), (86, 20)),
            ((26, 19), (26, 12), (32, 8), (43, 8), (55, 10), (68, 10), (74, 14)),
            ((17, 19), (13, 24), (11, 31), (16, 36), (25, 38), (31, 35)),
            ((26, 37), (31, 43), (42, 45), (54, 44), (63, 39), (65, 30), (61, 24)),
            ((64, 22), (69, 27), (72, 34), (78, 39), (82, 47), (78, 54)),
            ((42, 45), (42, 52), (50, 55), (62, 55), (73, 52), (82, 54)),
            ((13, 31), (7, 36), (6, 44), (12, 49), (25, 50), (42, 52)),
        )
        px, py = column + 0.5, row + 0.5
        for path in paths:
            for (ax, ay), (bx, by) in zip(path, path[1:]):
                dx, dy = bx - ax, by - ay
                length_sq = dx * dx + dy * dy
                t = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((px-ax)*dx + (py-ay)*dy) / length_sq))
                qx, qy = ax + t*dx, ay + t*dy
                if (px-qx)**2 + (py-qy)**2 <= 1.55**2:
                    return True
        return False

    @staticmethod
    @lru_cache(maxsize=5)
    def _landmark_surface(kind: str) -> pygame.Surface:
        """Load handcrafted market assets and cache supporting landmark surfaces."""
        names = {"market": "market_stall.png", "tea_stall": "tea_stall.png"}
        if kind in names:
            return sprite(names[kind])
        sizes = {"well": (58, 42), "cart": (70, 42), "garden": (88, 42)}
        w, h = sizes[kind]
        image = pygame.Surface((w, h), pygame.SRCALPHA)
        if kind == "well":
            pygame.draw.ellipse(image, (0, 0, 0, 90), (3, 28, 52, 12))
            pygame.draw.ellipse(image, (48, 55, 54), (5, 13, 48, 25))
            pygame.draw.ellipse(image, (111, 119, 111), (8, 10, 42, 22))
            pygame.draw.ellipse(image, (23, 40, 43), (14, 13, 30, 14))
            pygame.draw.arc(image, (173, 163, 137), (8, 10, 42, 22), 0, 3.14, 2)
            pygame.draw.line(image, (68, 43, 30), (12, 13), (12, 2), 3)
            pygame.draw.line(image, (68, 43, 30), (46, 13), (46, 2), 3)
            pygame.draw.line(image, (129, 91, 53), (12, 3), (46, 3), 3)
        elif kind == "cart":
            pygame.draw.ellipse(image, (0, 0, 0, 90), (6, 28, 60, 12))
            pygame.draw.circle(image, (28, 25, 22), (19, 29), 8)
            pygame.draw.circle(image, (126, 103, 76), (19, 29), 4)
            pygame.draw.circle(image, (28, 25, 22), (53, 29), 8)
            pygame.draw.circle(image, (126, 103, 76), (53, 29), 4)
            pygame.draw.polygon(image, (91, 55, 34), [(10, 8), (58, 8), (53, 26), (15, 26)])
            pygame.draw.line(image, (165, 116, 68), (13, 11), (55, 11), 2)
            for x, color in ((20, (139, 66, 43)), (32, (90, 119, 60)), (43, (184, 145, 70))):
                pygame.draw.circle(image, color, (x, 7), 5)
        else:
            pygame.draw.ellipse(image, (0, 0, 0, 75), (3, 29, 82, 11))
            pygame.draw.rect(image, (76, 54, 35), (4, 9, 80, 27), 2)
            for x, y in ((15, 17), (32, 25), (52, 16), (70, 25)):
                pygame.draw.ellipse(image, (49, 82, 42), (x-7, y-5, 14, 10))
                pygame.draw.line(image, (137, 150, 81), (x, y+2), (x+2, y-6), 2)
        return image

    @classmethod
    def _draw_landmark(cls, surface: pygame.Surface, x: int, y: int,
                       kind: str, camera: pygame.Vector2) -> None:
        image = cls._landmark_surface(kind)
        surface.blit(image, (x-round(camera.x)-image.get_width()//2,
                             y-round(camera.y)-image.get_height()+8))

    @staticmethod
    def _decoration_ground_y(y: int, kind: str) -> int:
        """Return the pixel row where a procedural prop shadow meets the ground."""
        return y + {"lantern": 33, "shrine": 44, "barrel": 30,
                    "market": 84, "well": 38, "cart": 38,
                    "tea_stall": 80, "garden": 38}[kind]

    @staticmethod
    def _tree_ground_y(y: int, height: int) -> int:
        # Cedar-tree ground shadow ends four pixels below its nominal height.
        return y + height + 4

    @property
    def sign_ground_y(self) -> int:
        return self.sign_position[1] + 44

    def _draw_sign(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        origin_x, origin_y = self.sign_position
        x = origin_x - round(camera.x)
        y = origin_y - round(camera.y)

        # The two posts and their feet share the same ground row as the
        # collision footprint; the board itself remains non-blocking.
        draw_ground_shadow(surface, (x + 5, y + 40, 28, 5), opacity=70)
        pygame.draw.line(surface, (42, 34, 29), (x + 7, y + 44), (x + 13, y + 44), 1)
        pygame.draw.line(surface, (42, 34, 29), (x + 23, y + 44), (x + 29, y + 44), 1)
        pygame.draw.rect(surface, (48, 33, 27), (x + 7, y + 20, 5, 24))
        pygame.draw.rect(surface, (48, 33, 27), (x + 23, y + 20, 5, 24))
        pygame.draw.line(surface, (151, 99, 61), (x + 8, y + 23), (x + 8, y + 41), 1)
        pygame.draw.line(surface, (151, 99, 61), (x + 24, y + 23), (x + 24, y + 41), 1)
        pygame.draw.line(surface, (76, 48, 34), (x + 10, y + 27), (x + 10, y + 37), 1)
        pygame.draw.line(surface, (76, 48, 34), (x + 26, y + 27), (x + 26, y + 37), 1)
        pygame.draw.rect(surface, (91, 59, 39), (x + 5, y + 42, 9, 2))
        pygame.draw.rect(surface, (91, 59, 39), (x + 21, y + 42, 9, 2))

        # Larger framed notice face with restrained grain and readable marks.
        pygame.draw.rect(surface, (43, 30, 25), (x - 2, y - 2, 36, 25))
        pygame.draw.rect(surface, (111, 70, 43), (x, y, 32, 21))
        pygame.draw.line(surface, (191, 137, 83), (x + 2, y + 1), (x + 29, y + 1), 1)
        pygame.draw.line(surface, (67, 43, 32), (x + 1, y + 19), (x + 30, y + 19), 1)
        pygame.draw.rect(surface, (163, 113, 69), (x + 2, y + 2, 28, 17))
        pygame.draw.rect(surface, (70, 48, 36), (x + 4, y + 4, 24, 13))
        pygame.draw.line(surface, (190, 145, 91), (x + 5, y + 5), (x + 26, y + 5), 1)
        pygame.draw.line(surface, (190, 145, 91), (x + 5, y + 15), (x + 26, y + 15), 1)
        pygame.draw.line(surface, (225, 194, 145), (x + 8, y + 8), (x + 13, y + 8), 2)
        pygame.draw.line(surface, (225, 194, 145), (x + 17, y + 8), (x + 24, y + 8), 1)
        pygame.draw.line(surface, (225, 194, 145), (x + 9, y + 12), (x + 22, y + 12), 1)
        pygame.draw.rect(surface, (199, 153, 96), (x + 14, y + 20, 4, 2))
        pygame.draw.circle(surface, (48, 35, 28), (x + 3, y + 3), 1)
        pygame.draw.circle(surface, (48, 35, 28), (x + 29, y + 3), 1)
        pygame.draw.rect(surface, (207, 157, 99), (x + 4, y + 1, 2, 1))
        pygame.draw.rect(surface, (207, 157, 99), (x + 26, y + 1, 2, 1))
        pygame.draw.line(surface, (119, 77, 48), (x + 3, y + 17), (x + 7, y + 17), 1)
        pygame.draw.line(surface, (119, 77, 48), (x + 25, y + 17), (x + 29, y + 17), 1)
        # Small corner pegs and side grain make the board read as assembled timber.
        pygame.draw.rect(surface, (57, 39, 30), (x + 1, y + 7, 2, 7))
        pygame.draw.rect(surface, (57, 39, 30), (x + 29, y + 7, 2, 7))
        pygame.draw.rect(surface, (201, 151, 94), (x + 2, y + 3, 1, 2))
        pygame.draw.rect(surface, (201, 151, 94), (x + 29, y + 3, 1, 2))
        pygame.draw.line(surface, (83, 53, 37), (x + 12, y + 22), (x + 12, y + 40), 1)
        pygame.draw.line(surface, (83, 53, 37), (x + 27, y + 22), (x + 27, y + 40), 1)

    def sorted_depth_entities(self, entities: list[tuple[float, float, object]]) -> list[object]:
        """Sort top-down entities by their screen-space ground Y coordinate."""
        return [entity for _, _, entity in sorted(entities, key=lambda item: (item[1], item[0]))]

    def point_collides(self, rect: pygame.Rect) -> bool:
        """Return whether a ground-plane rect intersects an environmental collider."""
        return any(rect.colliderect(obstacle) for obstacle in self.obstacles)
