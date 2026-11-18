import pygame


class NPC:
    """A village character with a name, dialogue, and a collision body."""

    SIZE = (24, 36)

    def __init__(self, x: int, y: int, name: str, lines: tuple[str, ...]) -> None:
        self.position = (x, y)
        self.name = name
        self.lines = lines
        self.rect = pygame.Rect(x + 4, y + 22, 16, 12)
        self.interaction_area = pygame.Rect(x - 24, y - 10, 72, 64)

    def draw(self, surface: pygame.Surface, camera: pygame.Vector2) -> None:
        x = self.position[0] - round(camera.x)
        y = self.position[1] - round(camera.y)
        pygame.draw.ellipse(surface, (17, 20, 20), (x + 2, y + 29, 21, 7))
        pygame.draw.rect(surface, (105, 46, 48), (x + 5, y + 19, 14, 12))
        pygame.draw.rect(surface, (180, 145, 105), (x + 6, y + 21, 12, 3))
        pygame.draw.rect(surface, (68, 46, 40), (x + 6, y + 28, 5, 6))
        pygame.draw.rect(surface, (68, 46, 40), (x + 13, y + 28, 5, 6))
        pygame.draw.rect(surface, (192, 151, 111), (x + 8, y + 11, 9, 9))
        pygame.draw.rect(surface, (41, 32, 30), (x + 6, y + 6, 13, 7))
        pygame.draw.rect(surface, (41, 32, 30), (x + 8, y + 3, 10, 5))
        pygame.draw.rect(surface, (34, 30, 30), (x + 9, y + 15, 2, 2))
        pygame.draw.rect(surface, (34, 30, 30), (x + 14, y + 15, 2, 2))

        marker_y = y + 1
        pygame.draw.circle(surface, (18, 19, 20), (x + 12, marker_y), 7)
        pygame.draw.circle(surface, (213, 173, 101), (x + 12, marker_y), 5)
        pygame.draw.rect(surface, (46, 35, 29), (x + 11, marker_y - 3, 2, 5))
        pygame.draw.rect(surface, (46, 35, 29), (x + 11, marker_y + 3, 2, 1))
