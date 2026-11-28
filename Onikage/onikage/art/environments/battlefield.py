"""Procedural night-sky and forest layers for turn-based encounters."""

import pygame


def draw_battlefield(surface: pygame.Surface, elapsed: float) -> None:
    width, height = surface.get_size()
    scale_x = width / 1280
    scale_y = height / 720

    def point(x: int, y: int) -> tuple[int, int]:
        return round(x * scale_x), round(y * scale_y)

    for y in range(0, 448, 8):
        shade = y // 8
        color = (15 + shade // 14, 21 + shade // 15, 34 + shade // 10)
        pygame.draw.rect(surface, color, (*point(0, y), width, max(1, round(8 * scale_y))))

    moon = point(1000, 154)
    radius_scale = min(scale_x, scale_y)
    for radius, color in (
        (108, (42, 36, 48)),
        (88, (76, 47, 53)),
        (68, (132, 70, 65)),
        (52, (170, 100, 82)),
    ):
        pygame.draw.circle(surface, color, moon, max(1, round(radius * radius_scale)))
    pygame.draw.rect(surface, (187, 124, 92), (*point(977, 118), max(1, round(11 * scale_x)), max(1, round(4 * scale_y))))
    pygame.draw.rect(surface, (147, 90, 75), (*point(1010, 175), max(1, round(17 * scale_x)), max(1, round(7 * scale_y))))
    pygame.draw.rect(surface, (187, 124, 92), (*point(983, 197), max(1, round(8 * scale_x)), max(1, round(3 * scale_y))))

    for index in range(24):
        x = round((index * 97 + 31) * scale_x) % width
        y = round(((index * 53 + 17) % 270) * scale_y)
        twinkle = (index + int(elapsed * 2)) % 4
        pygame.draw.rect(
            surface,
            (94 + twinkle * 8, 105 + twinkle * 7, 119 + twinkle * 6),
            (x, y, 2, 2),
        )

    pygame.draw.polygon(
        surface,
        (22, 28, 34),
        [point(x, y) for x, y in (
            (0, 381), (120, 326), (258, 391), (409, 303), (565, 389),
            (728, 318), (895, 390), (1068, 307), (1280, 382), (1280, 500), (0, 500),
        )],
    )
    pygame.draw.polygon(
        surface,
        (28, 35, 37),
        [point(x, y) for x, y in (
            (0, 416), (180, 357), (350, 423), (520, 349), (695, 419),
            (870, 357), (1060, 418), (1190, 365), (1280, 395), (1280, 512), (0, 512),
        )],
    )
    for x, peak_y in ((48, 389), (176, 372), (1100, 374), (1210, 388)):
        pygame.draw.polygon(
            surface,
            (17, 27, 31),
            [point(x - 36, peak_y + 76), point(x, peak_y), point(x + 37, peak_y + 76)],
        )
        pygame.draw.polygon(
            surface,
            (30, 43, 42),
            [point(x - 25, peak_y + 48), point(x, peak_y + 8), point(x + 24, peak_y + 48)],
        )

    pygame.draw.rect(surface, (26, 34, 33), (*point(0, 430), width, max(1, round(290 * scale_y))))
    pygame.draw.line(surface, (80, 72, 58), point(0, 431), point(1280, 431), 2)
    for index in range(28):
        x = round((index * 83 + int(elapsed * 13)) * scale_x) % width
        y = round((448 + (index * 47) % 76) * scale_y)
        pygame.draw.rect(surface, (37, 49, 42), (x, y, 4, 2))
        if index % 4 == 0:
            pygame.draw.rect(surface, (119, 88, 59), (x + 2, y + 3, 2, 2))
    for index in range(12):
        x = round((index * 131 + int(elapsed * 17)) * scale_x) % width
        y = round((420 + (index * 31) % 105) * scale_y)
        pygame.draw.rect(surface, (126, 67, 48), (x, y, 2, 3))
