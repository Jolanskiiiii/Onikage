import pygame

from onikage.art.enemies.wraith_sprite import wraith_frame


class Enemy:
    """A hostile world character and its turn-based battle statistics."""

    def __init__(
        self,
        x: int,
        y: int,
        name: str = "Cedar-Wood Wraith",
        max_health: int = 72,
        attack_power: int = 12,
    ) -> None:
        self.name = name
        self.max_health = max_health
        self.health = max_health
        self.attack_power = attack_power
        self.experience_reward = 30
        self.rect = pygame.Rect(x + 4, y + 23, 24, 13)
        self.interaction_area = pygame.Rect(x - 26, y - 10, 84, 66)
        self.sprite_position = (x, y)

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        x = self.sprite_position[0] - round(camera.x)
        y = self.sprite_position[1] - round(camera.y)
        pygame.draw.ellipse(surface, (14, 26, 28), (x - 7, y - 9, 47, 53), 1)
        pygame.draw.ellipse(surface, (15, 18, 20), (x - 4, y + 31, 38, 9))
        frame = pygame.time.get_ticks() // 420 % 2
        surface.blit(wraith_frame(frame), (x - 8, y - 27))
