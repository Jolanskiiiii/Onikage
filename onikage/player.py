import pygame

from onikage.art.characters.player_sprite import player_frame


class Player:
    """The wandering samurai and the player's current RPG statistics."""

    SIZE = (24, 36)
    WALK_SPEED = 170.0
    SPRINT_SPEED = 240.0

    def __init__(self, x: float, y: float) -> None:
        self.position = pygame.Vector2(x, y)
        self.rect = pygame.Rect(round(x), round(y), *self.SIZE)
        self.health = 100
        self.max_health = 100
        self.stamina = 100.0
        self.max_stamina = 100.0
        self.level = 1
        self.experience = 0
        self.rations = 3
        self.direction = "down"
        self.walk_time = 0.0
        self.moving = False

    def update(
        self,
        dt: float,
        keys: pygame.key.ScancodeWrapper,
        obstacles: list[pygame.Rect],
    ) -> None:
        move_x = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        move_y = int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(
            keys[pygame.K_w] or keys[pygame.K_UP]
        )
        movement = pygame.Vector2(move_x, move_y)
        self.moving = movement.length_squared() > 0
        if movement.length_squared():
            movement = movement.normalize()
            if abs(move_x) > abs(move_y):
                self.direction = "right" if move_x > 0 else "left"
            else:
                self.direction = "down" if move_y > 0 else "up"

        sprinting = (
            keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        ) and self.stamina > 0 and movement.length_squared() > 0
        if sprinting:
            speed = self.SPRINT_SPEED
            self.stamina = max(0.0, self.stamina - 32.0 * dt)
        else:
            speed = self.WALK_SPEED
            self.stamina = min(self.max_stamina, self.stamina + 19.0 * dt)

        distance = movement * speed * dt
        self._move_axis(distance.x, 0, obstacles)
        self._move_axis(distance.y, 1, obstacles)
        if self.moving:
            self.walk_time += dt
        else:
            self.walk_time = 0.0

    def _move_axis(
        self,
        amount: float,
        axis: int,
        obstacles: list[pygame.Rect],
    ) -> None:
        if amount == 0:
            return

        self.position[axis] += amount
        self.rect.topleft = (round(self.position.x), round(self.position.y))
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle):
                if axis == 0:
                    if amount > 0:
                        self.rect.right = obstacle.left
                    else:
                        self.rect.left = obstacle.right
                    self.position.x = self.rect.x
                else:
                    if amount > 0:
                        self.rect.bottom = obstacle.top
                    else:
                        self.rect.top = obstacle.bottom
                    self.position.y = self.rect.y

    def draw(self, surface: pygame.Surface, screen_position: tuple[int, int]) -> None:
        x, y = screen_position
        frame = 1 + int(self.walk_time * 7) % 2 if self.moving else 0
        pygame.draw.ellipse(surface, (13, 16, 17), (x - 1, y + 29, 26, 7))
        surface.blit(player_frame(self.direction, frame), (x - 4, y - 10))

    def interaction_point(self) -> tuple[int, int]:
        facing = {
            "up": (0, -26),
            "down": (0, 40),
            "left": (-28, 8),
            "right": (28, 8),
        }
        dx, dy = facing[self.direction]
        return self.rect.centerx + dx, self.rect.centery + dy
