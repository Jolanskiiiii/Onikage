import math
import random

import pygame


class MenuButton:
    """A menu button that can be highlighted, selected, or disabled."""

    def __init__(self, label: str, action: str, rect: pygame.Rect, enabled: bool = True):
        self.label = label
        self.action = action
        self.rect = rect
        self.enabled = enabled
        self.hovered = False


class MainMenu:
    """Draws the title screen and reports the chosen menu action."""

    WIDTH = 1280
    HEIGHT = 720
    GOLD = (208, 171, 105)

    def __init__(self) -> None:
        self.elapsed = 0.0
        self.selected_index = 0
        self.back_button = pygame.Rect(540, 430, 200, 52)
        button_labels = (
            ("NEW GAME", "new_game", True),
            ("CONTINUE", "continue", False),
            ("SETTINGS", "settings", True),
            ("EXIT", "exit", True),
        )
        self.buttons = [
            MenuButton(label, action, pygame.Rect(118, 397 + i * 64, 300, 52), enabled)
            for i, (label, action, enabled) in enumerate(button_labels)
        ]
        self.particles = [
            {
                "x": random.uniform(0, self.WIDTH),
                "y": random.uniform(0, self.HEIGHT),
                "speed": random.uniform(9, 25),
                "drift": random.uniform(-8, 8),
                "size": random.choice((2, 3, 4)),
                "phase": random.uniform(0, math.tau),
            }
            for _ in range(38)
        ]

        self.title_font = pygame.font.SysFont("Yu Gothic UI", 72, bold=True)
        self.subtitle_font = pygame.font.SysFont("Yu Gothic UI", 19)
        self.button_font = pygame.font.SysFont("Yu Gothic UI", 22, bold=True)
        self.note_font = pygame.font.SysFont("Yu Gothic UI", 15)

    def update(self, dt: float) -> None:
        self.elapsed += dt
        for particle in self.particles:
            particle["y"] -= particle["speed"] * dt
            particle["x"] += (
                particle["drift"] + math.sin(self.elapsed + particle["phase"]) * 5
            ) * dt
            if particle["y"] < -8:
                particle["y"] = self.HEIGHT + 8
                particle["x"] = random.uniform(0, self.WIDTH)

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.MOUSEMOTION:
            for index, button in enumerate(self.buttons):
                button.hovered = button.rect.collidepoint(event.pos) and button.enabled
                if button.hovered:
                    self.selected_index = index

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._move_selection(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._move_selection(1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.buttons[self.selected_index].action
            elif event.key == pygame.K_ESCAPE:
                return "exit"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.enabled and button.rect.collidepoint(event.pos):
                    return button.action
        return None

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_sky(surface)
        self._draw_mountains(surface)
        self._draw_torii(surface)
        self._draw_foreground(surface)
        self._draw_particles(surface)
        self._draw_title(surface)
        self._draw_buttons(surface)
        self._draw_footer(surface)

    def draw_back_button(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        hovered = self.back_button.collidepoint(pygame.mouse.get_pos())
        fill = (50, 37, 32) if hovered else (28, 27, 31)
        pygame.draw.rect(surface, fill, self.back_button)
        pygame.draw.rect(surface, self.GOLD, self.back_button, 2)
        label = font.render("BACK  [ESC]", True, (235, 220, 189))
        surface.blit(label, label.get_rect(center=self.back_button.center))

    def _draw_sky(self, surface: pygame.Surface) -> None:
        surface.fill((13, 15, 25))
        for y in range(self.HEIGHT):
            blend = y / self.HEIGHT
            color = (
                int(16 + 12 * blend),
                int(17 + 7 * blend),
                int(30 + 7 * blend),
            )
            pygame.draw.line(surface, color, (0, y), (self.WIDTH, y))

        moon_y = 185 + int(math.sin(self.elapsed * 0.35) * 3)
        pygame.draw.circle(surface, (98, 36, 47), (1000, moon_y), 92)
        pygame.draw.circle(surface, (142, 49, 56), (1000, moon_y), 78)
        pygame.draw.circle(surface, (166, 65, 66), (1000, moon_y), 68)
        pygame.draw.circle(surface, (142, 49, 56), (1000, moon_y), 57)

        for x, y, radius in (
            (890, 112, 2),
            (1097, 108, 2),
            (1148, 229, 1),
            (832, 240, 1),
            (1060, 310, 2),
            (1202, 154, 1),
        ):
            pygame.draw.rect(surface, (174, 160, 151), (x, y, radius, radius))

    def _draw_mountains(self, surface: pygame.Surface) -> None:
        pygame.draw.polygon(
            surface,
            (24, 25, 34),
            [
                (540, 410), (730, 228), (845, 349), (961, 253), (1170, 425),
                (1280, 390), (1280, 570), (480, 570),
            ],
        )
        pygame.draw.polygon(
            surface,
            (19, 21, 29),
            [
                (710, 435), (920, 300), (1083, 438), (1195, 347), (1280, 420),
                (1280, 585), (650, 585),
            ],
        )
        pygame.draw.rect(surface, (20, 23, 30), (0, 480, self.WIDTH, 240))

        for base_x, base_y, scale in ((570, 504, 1.0), (742, 478, 0.8), (1140, 485, 0.92)):
            self._draw_pine(surface, base_x, base_y, scale)

    @staticmethod
    def _draw_pine(surface: pygame.Surface, x: int, y: int, scale: float) -> None:
        trunk = max(4, int(9 * scale))
        pygame.draw.rect(
            surface,
            (13, 18, 22),
            pygame.Rect(x - trunk // 2, y - 100 * scale, trunk, 112 * scale),
        )
        for tier in range(4):
            top = y - (145 - tier * 30) * scale
            width = (49 - tier * 6) * scale
            pygame.draw.polygon(
                surface,
                (13, 23 + tier, 26),
                [
                    (x, top),
                    (x - width, top + 55 * scale),
                    (x - width * 0.55, top + 48 * scale),
                    (x + width * 0.55, top + 48 * scale),
                    (x + width, top + 55 * scale),
                ],
            )

    def _draw_torii(self, surface: pygame.Surface) -> None:
        x, y = 1038, 500
        red = (91, 31, 39)
        shadow = (47, 24, 30)
        pygame.draw.rect(surface, shadow, (x - 99, y - 153, 198, 13))
        pygame.draw.rect(surface, red, (x - 112, y - 162, 224, 13))
        pygame.draw.rect(surface, shadow, (x - 79, y - 137, 158, 9))
        pygame.draw.rect(surface, red, (x - 69, y - 133, 16, 153))
        pygame.draw.rect(surface, red, (x + 53, y - 133, 16, 153))
        pygame.draw.rect(surface, (135, 47, 50), (x - 65, y - 128, 5, 143))
        pygame.draw.rect(surface, (135, 47, 50), (x + 57, y - 128, 5, 143))

    def _draw_foreground(self, surface: pygame.Surface) -> None:
        pygame.draw.polygon(
            surface,
            (11, 16, 20),
            [
                (0, 591), (198, 567), (359, 605), (529, 576), (710, 612),
                (902, 579), (1085, 609), (1280, 568), (1280, 720), (0, 720),
            ],
        )
        for x, y in ((451, 664), (509, 682), (828, 650), (1136, 682), (78, 650)):
            pygame.draw.line(surface, (42, 47, 42), (x, y), (x - 9, y - 22), 2)
            pygame.draw.line(surface, (42, 47, 42), (x, y - 12), (x + 7, y - 26), 2)

    def _draw_particles(self, surface: pygame.Surface) -> None:
        for particle in self.particles:
            alpha = 90 + int(
                70 * (0.5 + 0.5 * math.sin(self.elapsed * 1.4 + particle["phase"]))
            )
            speck = pygame.Surface((particle["size"], particle["size"]), pygame.SRCALPHA)
            speck.fill((203, 151, 110, alpha))
            surface.blit(speck, (int(particle["x"]), int(particle["y"])))

    def _draw_title(self, surface: pygame.Surface) -> None:
        title_y = 190 + int(math.sin(self.elapsed * 0.7) * 2)
        title = self.title_font.render("ONIKAGE", True, (232, 220, 197))
        shadow = self.title_font.render("ONIKAGE", True, (81, 37, 42))
        surface.blit(shadow, (112, title_y + 5))
        surface.blit(title, (108, title_y))

        line = pygame.Rect(116, title_y + 91, 264, 2)
        pygame.draw.rect(surface, self.GOLD, line)
        subtitle = self.subtitle_font.render(
            "THE CURSE OF THE FALLEN SAMURAI",
            True,
            (190, 157, 121),
        )
        surface.blit(subtitle, (118, title_y + 108))
        small = self.note_font.render("A TALE WRITTEN IN BLOOD AND ASH", True, (132, 127, 124))
        surface.blit(small, (120, title_y + 141))

    def _draw_buttons(self, surface: pygame.Surface) -> None:
        mouse_pos = pygame.mouse.get_pos()
        for index, button in enumerate(self.buttons):
            hovered = button.enabled and button.rect.collidepoint(mouse_pos)
            focused = index == self.selected_index
            active = hovered or focused
            fill = (48, 34, 33) if active else (21, 23, 29)
            border = self.GOLD if active else (91, 79, 67)
            text_color = (239, 223, 194) if button.enabled else (91, 91, 91)

            pygame.draw.rect(surface, fill, button.rect)
            pygame.draw.rect(surface, border, button.rect, 2 if active else 1)
            if active and button.enabled:
                pygame.draw.rect(
                    surface,
                    (130, 47, 51),
                    (button.rect.left, button.rect.top, 5, button.rect.height),
                )
            label = self.button_font.render(button.label, True, text_color)
            surface.blit(label, label.get_rect(center=button.rect.center))

        note = self.note_font.render("CONTINUE IS AVAILABLE AFTER YOUR FIRST SAVE", True, (127, 122, 116))
        surface.blit(note, (120, 667))

    def _draw_footer(self, surface: pygame.Surface) -> None:
        left = self.note_font.render("ARROW KEYS / W S   SELECT     ENTER   CONFIRM", True, (121, 119, 119))
        right = self.note_font.render("F11  FULLSCREEN", True, (121, 119, 119))
        surface.blit(left, (118, 690))
        surface.blit(right, (1065, 690))

    def _move_selection(self, direction: int) -> None:
        index = self.selected_index
        for _ in self.buttons:
            index = (index + direction) % len(self.buttons)
            if self.buttons[index].enabled:
                self.selected_index = index
                return
