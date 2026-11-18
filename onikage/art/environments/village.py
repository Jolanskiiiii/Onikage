"""Layered house and cedar-tree pixel art for the starting village."""

import pygame


def draw_village_building(
    surface: pygame.Surface,
    rect: pygame.Rect,
    camera: pygame.Vector2,
) -> None:
    x, y = rect.x - round(camera.x), rect.y - round(camera.y)
    roof_shift = (rect.x // 16 + rect.y // 16) % 3
    roof_palettes = ((35, 35, 43), (47, 34, 38), (31, 43, 40))
    wall_palettes = ((102, 77, 58), (112, 78, 55), (105, 83, 66))
    roof_base = roof_palettes[roof_shift]
    wall = wall_palettes[roof_shift]
    pygame.draw.ellipse(
        surface,
        (13, 19, 19),
        (x - 13, y + rect.height - 7, rect.width + 26, 28),
    )
    pygame.draw.rect(surface, (56, 49, 42), (x + 11, y + rect.height - 18, rect.width - 22, 16))
    pygame.draw.rect(surface, (83, 67, 53), (x + 17, y + 35, rect.width - 34, rect.height - 48))
    pygame.draw.rect(surface, wall, (x + 21, y + 39, rect.width - 42, rect.height - 48))
    if roof_shift == 1:
        pygame.draw.rect(
            surface,
            (72, 49, 39),
            (x + 15, y + 78, rect.width - 30, 12),
        )
        pygame.draw.line(
            surface,
            (149, 104, 64),
            (x + 15, y + 78),
            (x + rect.width - 15, y + 78),
            2,
        )
    elif roof_shift == 2:
        pygame.draw.rect(
            surface,
            (132, 112, 87),
            (x + 33, y + 48, rect.width - 66, rect.height - 68),
        )
        for panel_x in range(x + 40, x + rect.width - 40, 16):
            pygame.draw.line(
                surface,
                (86, 67, 55),
                (panel_x, y + 51),
                (panel_x, y + rect.height - 23),
                1,
            )
    pygame.draw.rect(surface, (139, 107, 75), (x + 23, y + 43, rect.width - 46, 3))
    for beam_y in range(y + 55, y + rect.height - 18, 19):
        pygame.draw.line(surface, (73, 52, 43), (x + 23, beam_y), (x + rect.width - 23, beam_y), 2)
    for post_x in (x + 25, x + rect.width - 31):
        pygame.draw.rect(surface, (49, 38, 35), (post_x, y + 48, 6, rect.height - 64))
        pygame.draw.line(surface, (129, 89, 61), (post_x + 1, y + 50), (post_x + 1, y + rect.height - 18), 1)

    pygame.draw.polygon(
        surface,
        (20, 24, 31),
        [
            (x - 10, y + 49),
            (x + 22, y + 3),
            (x + rect.width // 2, y - 15),
            (x + rect.width - 22, y + 3),
            (x + rect.width + 10, y + 49),
            (x + rect.width - 5, y + 43),
            (x + rect.width // 2, y + 11),
            (x + 5, y + 43),
        ],
    )
    pygame.draw.polygon(
        surface,
        roof_base,
        [(x + 19, y + 35), (x + rect.width // 2, y - 8), (x + rect.width - 19, y + 35)],
    )
    for row, inset in ((y + 8, 24), (y + 18, 17), (y + 28, 10), (y + 38, 3)):
        pygame.draw.line(
            surface,
            (59, 61, 67),
            (x + inset, row),
            (x + rect.width - inset, row),
            2,
        )
        for tile_x in range(x + inset + 8, x + rect.width - inset, 18):
            pygame.draw.line(surface, (29, 32, 39), (tile_x, row), (tile_x, row + 5), 1)
    pygame.draw.line(surface, (113, 88, 66), (x - 8, y + 48), (x + rect.width + 8, y + 48), 3)
    pygame.draw.line(
        surface,
        (94, 70, 57),
        (x + rect.width // 2, y - 11),
        (x + rect.width // 2, y + 37),
        3,
    )
    pygame.draw.line(
        surface,
        (143, 111, 75),
        (x + rect.width // 2 - 6, y - 10),
        (x + rect.width // 2 + 6, y - 10),
        2,
    )

    door_x = x + rect.width // 2 - 18
    door_y = y + rect.height - 48
    pygame.draw.rect(surface, (42, 33, 31), (door_x - 2, door_y - 3, 40, 49))
    pygame.draw.rect(surface, (119, 82, 57), (door_x, door_y, 36, 44))
    pygame.draw.rect(surface, (48, 39, 36), (door_x + 5, door_y + 3, 26, 40))
    pygame.draw.rect(surface, (141, 103, 70), (door_x + 7, door_y + 4, 22, 37))
    for slat_x in range(door_x + 10, door_x + 29, 6):
        pygame.draw.line(surface, (78, 57, 46), (slat_x, door_y + 5), (slat_x, door_y + 39), 1)
    pygame.draw.rect(surface, (170, 134, 83), (door_x + 27, door_y + 23, 2, 3))
    pygame.draw.rect(surface, (115, 82, 57), (door_x - 7, y + rect.height - 7, 50, 5))
    pygame.draw.rect(surface, (76, 63, 53), (door_x - 12, y + rect.height - 2, 60, 4))

    for window_x in (x + 43, x + rect.width - 56):
        pygame.draw.rect(surface, (40, 35, 34), (window_x - 3, y + 62, 28, 34))
        pygame.draw.rect(surface, (169, 131, 81), (window_x - 1, y + 64, 24, 29))
        pygame.draw.rect(surface, (174, 137, 87), (window_x + 1, y + 66, 20, 25))
        pygame.draw.rect(surface, (107, 115, 103), (window_x + 3, y + 68, 16, 20))
        pygame.draw.line(surface, (190, 160, 112), (window_x + 11, y + 66), (window_x + 11, y + 91), 2)
        pygame.draw.line(surface, (190, 160, 112), (window_x + 2, y + 79), (window_x + 20, y + 79), 2)
        pygame.draw.line(surface, (77, 54, 43), (window_x - 4, y + 95), (window_x + 25, y + 95), 2)


def draw_cedar_tree(
    surface: pygame.Surface,
    x: int,
    y: int,
    height: int,
    camera: pygame.Vector2,
) -> None:
    sx, sy = x - round(camera.x), y - round(camera.y)
    width = max(22, height - 8)
    variant = (x * 3 + y) % 4
    evergreen = (21 + variant, 39 + variant, 35 + variant)
    lit_green = (37 + variant, 58 + variant, 45 + variant)
    pygame.draw.ellipse(surface, (12, 19, 18), (sx - width // 2, sy + height - 13, width, 17))
    pygame.draw.rect(surface, (54, 39, 33), (sx - 4, sy + 8, 8, height - 9))
    pygame.draw.rect(surface, (91, 62, 42), (sx - 1, sy + 12, 2, height - 14))
    pygame.draw.line(surface, (112, 78, 49), (sx + 1, sy + 17), (sx + 5, sy + 12), 1)
    pygame.draw.polygon(
        surface,
        (15, 29, 29),
        [
            (sx, sy - 7), (sx - width // 2, sy + 19), (sx - width // 3, sy + 17),
            (sx - width // 2 + 5, sy + 31), (sx + width // 2 - 5, sy + 31),
            (sx + width // 3, sy + 17), (sx + width // 2, sy + 19),
        ],
    )
    pygame.draw.polygon(
        surface,
        evergreen,
        [
            (sx, sy - 5), (sx - width // 2 + 3, sy + 17), (sx - width // 3, sy + 16),
            (sx - width // 2 + 8, sy + 28), (sx + width // 2 - 8, sy + 28),
            (sx + width // 3, sy + 16), (sx + width // 2 - 3, sy + 17),
        ],
    )
    pygame.draw.polygon(
        surface,
        lit_green,
        [(sx, sy - 3), (sx - width // 3, sy + 13), (sx - 4, sy + 12), (sx + width // 3, sy + 13)],
    )
    pygame.draw.polygon(
        surface,
        (28, 48, 40),
        [
            (sx, sy + 6), (sx - width // 3, sy + 22), (sx - width // 2 + 9, sy + 24),
            (sx + width // 2 - 9, sy + 24), (sx + width // 3, sy + 22),
        ],
    )
    for leaf_x, leaf_y in (
        (sx - width // 3, sy + 12),
        (sx + width // 4, sy + 8),
        (sx - width // 5, sy + 20),
        (sx + width // 3 - 3, sy + 21),
    ):
        pygame.draw.rect(surface, (72, 83, 53), (leaf_x, leaf_y, 3, 2))
    pygame.draw.rect(surface, (92, 82, 51), (sx - 1, sy + 25, 2, 1))
