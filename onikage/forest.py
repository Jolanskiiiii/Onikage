import random

import pygame

from onikage.art.effects.village_atmosphere import VillageAtmosphere
from onikage.art.environments.village import draw_cedar_tree
from onikage.enemy import Enemy


class ForestWorld:
    """A first playable cedar forest connected to the northern village road."""

    TILE_SIZE = 32
    COLUMNS = 56
    ROWS = 40
    WORLD_SIZE = (COLUMNS * TILE_SIZE, ROWS * TILE_SIZE)

    def __init__(self) -> None:
        self.atmosphere = VillageAtmosphere(self.WORLD_SIZE, seed=211)
        randomizer = random.Random(73)
        self.trees: list[tuple[int, int, int]] = []
        self.obstacles: list[pygame.Rect] = []

        for _ in range(145):
            x = randomizer.randrange(40, 1752)
            y = randomizer.randrange(50, 1230)
            on_trail = 770 <= x <= 1020 and (y < 145 or y > 1140)
            if on_trail:
                continue
            if 820 <= x <= 970 and 560 <= y <= 690:
                continue
            spot = pygame.Rect(x - 22, y - 22, 44, 44)
            if any(spot.colliderect(tree) for tree in self.obstacles):
                continue
            height = randomizer.randrange(38, 58)
            self.trees.append((x, y, height))
            self.obstacles.append(pygame.Rect(x - 10, y + 20, 20, 14))

        self.exit_rect = pygame.Rect(770, 1190, 250, 90)
        self.forest_altar = pygame.Rect(820, 590, 150, 80)
        self.obstacles.append(self.forest_altar.inflate(20, 20))
        self.wraith = Enemy(895, 520, "Forest Wraith", 84, 14)
        self.obstacles.append(self.wraith.rect.copy())

    def update(self, dt: float) -> None:
        self.atmosphere.update(dt)

    @property
    def elapsed(self) -> float:
        return self.atmosphere.elapsed

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2, player_y: int | None = None) -> None:
        surface.fill((17, 29, 27))
        self._draw_ground(surface, camera)
        view = pygame.Rect(round(camera.x) - 100, round(camera.y) - 100,
                           surface.get_width() + 200, surface.get_height() + 200)
        for x, y, height in self.trees:
            bounds = pygame.Rect(x - height, y - 10, height * 2, height + 12)
            if bounds.colliderect(view) and (player_y is None or y + height <= player_y):
                draw_cedar_tree(surface, x, y, height, camera)

        altar_x = self.forest_altar.x - round(camera.x)
        altar_y = self.forest_altar.y - round(camera.y)
        pygame.draw.ellipse(surface, (12, 19, 18), (altar_x - 15, altar_y + 58, 180, 28))
        pygame.draw.rect(surface, (65, 54, 43), (altar_x + 35, altar_y + 35, 80, 30))
        pygame.draw.rect(surface, (111, 88, 62), (altar_x + 43, altar_y + 25, 64, 12))
        pygame.draw.polygon(surface, (56, 46, 39), [(altar_x + 25, altar_y + 25), (altar_x + 75, altar_y + 5), (altar_x + 125, altar_y + 25)])

        if player_y is None or self.wraith.rect.bottom <= player_y:
            self.wraith.draw(surface, camera)
        self.atmosphere.draw(surface, camera)

    def draw_foreground(self, surface: pygame.Surface, camera: pygame.Vector2, player_y: int) -> None:
        view = pygame.Rect(round(camera.x) - 100, round(camera.y) - 100,
                           surface.get_width() + 200, surface.get_height() + 200)
        for x, y, height in self.trees:
            bounds = pygame.Rect(x - height, y - 10, height * 2, height + 12)
            if y + height > player_y and bounds.colliderect(view):
                draw_cedar_tree(surface, x, y, height, camera)
        if self.wraith.rect.bottom > player_y:
            self.wraith.draw(surface, camera)

    def interact(self, point: tuple[int, int]) -> str | None:
        target = pygame.Rect(point[0] - 18, point[1] - 18, 36, 36)
        if target.colliderect(self.forest_altar.inflate(30, 30)):
            return "The forest altar hums beneath a veil of mist."
        if target.colliderect(pygame.Rect(770, 1190, 250, 90)):
            return "The road leads south back to the village."
        return None

    def find_villager(self, point: tuple[int, int]) -> None:
        return None

    def find_enemy(self, point: tuple[int, int]) -> Enemy | None:
        target = pygame.Rect(point[0] - 12, point[1] - 12, 24, 24)
        if self.wraith.health > 0 and target.colliderect(self.wraith.interaction_area):
            return self.wraith
        return None

    def is_near_shrine(self, point: tuple[int, int]) -> bool:
        return False

    def _draw_ground(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        left = max(0, int(camera.x // self.TILE_SIZE))
        top = max(0, int(camera.y // self.TILE_SIZE))
        right = min(self.COLUMNS, int((camera.x + surface.get_width()) // self.TILE_SIZE) + 2)
        bottom = min(self.ROWS, int((camera.y + surface.get_height()) // self.TILE_SIZE) + 2)
        for row in range(top, bottom):
            for column in range(left, right):
                x = column * self.TILE_SIZE - round(camera.x)
                y = row * self.TILE_SIZE - round(camera.y)
                trail = 24 <= column <= 31
                if trail:
                    color = (49, 48, 38) if (column + row) % 3 else (57, 54, 42)
                else:
                    color = (29 + (column * 3 + row) % 5, 43 + (row * 2) % 6, 38)
                pygame.draw.rect(surface, color, (x, y, self.TILE_SIZE, self.TILE_SIZE))
