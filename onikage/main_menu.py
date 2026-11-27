"""Title screen: a layered night scene, an animated title, and the menu buttons.

Everything static (sky, mountains, torii gate, mist, ground, vignette) is drawn
once into cached surfaces; only light-weight blits and a few small shapes are
drawn each frame.
"""

import math
import random

import pygame

from onikage.art.fonts.ui import load_pixel_font
from onikage.art.ui.panels import draw_frame

_GOLD = (208, 171, 105)
_CREAM = (232, 220, 197)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _ease(value: float) -> float:
    value = _clamp01(value)
    return value * value * (3.0 - 2.0 * value)


class MenuButton:
    """A menu button that can be highlighted, selected, or disabled."""

    def __init__(
        self,
        label: str,
        action: str,
        rect: pygame.Rect,
        enabled: bool = True,
        kanji: str = "",
    ) -> None:
        self.label = label
        self.action = action
        self.rect = rect
        self.enabled = enabled
        self.kanji = kanji
        self.hovered = False


class MainMenu:
    """Draws the title screen and reports the chosen menu action.

    Actions returned by ``handle_event``: ``resume``, ``new_game``, ``continue``,
    ``settings`` and ``exit``.
    """

    WIDTH = 1280
    HEIGHT = 720
    GOLD = _GOLD
    VERSION = "PROTOTYPE BUILD"
    INTRO_SECONDS = 2.0

    _LAYER_PAD = 60
    _FAR_TOP = 215
    _NEAR_TOP = 290
    _GROUND_TOP = 560
    _TORII = (1038, 500)
    _TITLE_X = 108
    _TITLE_Y = 84
    _BUTTON_X = 118
    _BUTTON_SIZE = (320, 50)
    _BUTTON_PITCH = 58
    _BUTTON_BOTTOM = 612
    _SETTINGS_PANEL = pygame.Rect(240, 120, 800, 480)

    _ENTRIES = {
        "resume": ("RESUME", "再開"),
        "new_game": ("NEW GAME", "新たな旅"),
        "continue": ("CONTINUE", "続きから"),
        "settings": ("SETTINGS", "設定"),
        "exit": ("EXIT", "終了"),
    }
    _CONTROLS = (
        (
            ("WASD / ARROWS", "Move"),
            ("SHIFT", "Sprint"),
            ("E", "Interact / talk"),
            ("C", "Fight a nearby foe"),
            ("ESC", "Pause to menu"),
        ),
        (
            ("LMB / RMB", "Light / heavy attacks"),
            ("1 - 4 / WHEEL", "Select a weapon"),
            ("V / Q", "Switch mask / ability"),
            ("U", "Upgrade equipped mask"),
            ("I / J", "Inventory / quest journal"),
            ("F11", "Fullscreen"),
        ),
    )

    def __init__(self) -> None:
        self.elapsed = 0.0
        self.selected_index = 0
        self.has_session = False
        self.save_available = False
        self.save_summary: str | None = None
        self.back_button = pygame.Rect(540, 530, 200, 52)
        self.buttons: list[MenuButton] = []
        self._rebuild_buttons()
        self._bar_y = float(self.buttons[0].rect.y)

        scenery = random.Random(11)
        self.stars = [
            (
                scenery.randrange(0, self.WIDTH),
                scenery.randrange(8, 330),
                scenery.uniform(0, math.tau),
                scenery.choice((1, 2, 2, 3)),
            )
            for _ in range(46)
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
            for _ in range(46)
        ]
        self._crow_timer = 5.0
        self._crow_progress = -1.0

        self.title_font = load_pixel_font(96)
        self.kanji_font = load_pixel_font(320)
        self.heading_font = load_pixel_font(32)
        self.button_font = load_pixel_font(24)
        self.subtitle_font = load_pixel_font(20)
        self.hint_font = load_pixel_font(16)
        self.note_font = load_pixel_font(16)
        self._text_cache: dict[tuple, pygame.Surface] = {}
        self._ember_cache: dict[tuple[int, int], pygame.Surface] = {}

        self._sky = self._build_sky()
        self._moon = self._build_moon()
        self._glow = self._build_glow(70, (255, 170, 90))
        self._far_layer = self._build_layer(
            ridge=[
                (-60, 480), (70, 410), (200, 445), (340, 372), (480, 440),
                (540, 410), (730, 228), (845, 349), (961, 253), (1170, 425),
                (1280, 390), (1340, 410),
            ],
            base_y=570,
            top=self._FAR_TOP,
            bottom=580,
            color=(24, 25, 34),
            rim=(58, 46, 60),
        )
        self._near_layer = self._build_layer(
            ridge=[
                (-60, 545), (140, 490), (320, 525), (500, 470), (650, 540),
                (710, 435), (920, 300), (1083, 438), (1195, 347), (1280, 420),
                (1340, 430),
            ],
            base_y=600,
            top=self._NEAR_TOP,
            bottom=625,
            color=(19, 21, 29),
            rim=(40, 36, 48),
            solid_from=480,
            pines=(
                (120, 525, 0.95), (250, 545, 0.7), (395, 520, 1.05),
                (570, 504, 1.0), (742, 478, 0.8), (1140, 485, 0.92),
            ),
        )
        self._mist_far = self._build_mist(seed=3, blobs=9, strength=30)
        self._mist_near = self._build_mist(seed=8, blobs=8, strength=22)
        self._torii = self._build_torii()
        self._ground = self._build_ground()
        self._vignette_strips = self._build_vignette_strips()
        self._scrim = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        self._scrim.fill((8, 8, 13, 205))
        self._fade = pygame.Surface((self.WIDTH, self.HEIGHT))
        self._fade.fill((0, 0, 0))
        self._flash = pygame.Surface((self.WIDTH, self.HEIGHT))
        self._flash.fill((255, 244, 230))

        self._title = self.title_font.render("ONIKAGE", False, _CREAM)
        self._title_shadow = self.title_font.render("ONIKAGE", False, (81, 37, 42))
        self._kanji = self.kanji_font.render("鬼影", False, (130, 42, 50))
        self._line_y = self._TITLE_Y + self._title.get_height() + 4
        panel = self._SETTINGS_PANEL
        self._toggle_rect = pygame.Rect(panel.right - 44 - 72, panel.y + 102, 72, 32)

    # ------------------------------------------------------------------ state

    def set_resume_available(self, available: bool) -> None:
        """Show a RESUME button while a game is in progress."""
        if available != self.has_session:
            self.has_session = available
            self._rebuild_buttons()
            self._bar_y = float(self.buttons[0].rect.y)
        self.selected_index = 0

    def set_continue_available(self, available: bool, summary: str | None = None) -> None:
        """Enable CONTINUE once a save exists; ``summary`` is shown as its hint."""
        self.save_available = available
        self.save_summary = summary
        for button in self.buttons:
            if button.action == "continue":
                button.enabled = available

    def _rebuild_buttons(self) -> None:
        actions = ["new_game", "continue", "settings", "exit"]
        if self.has_session:
            actions.insert(0, "resume")
        width, height = self._BUTTON_SIZE
        gap = self._BUTTON_PITCH - height
        top = self._BUTTON_BOTTOM - (len(actions) * self._BUTTON_PITCH - gap)
        self.buttons = []
        for index, action in enumerate(actions):
            label, kanji = self._ENTRIES[action]
            enabled = self.save_available if action == "continue" else True
            rect = pygame.Rect(
                self._BUTTON_X, top + index * self._BUTTON_PITCH, width, height
            )
            self.buttons.append(MenuButton(label, action, rect, enabled, kanji))
        self.selected_index = 0

    # ----------------------------------------------------------------- update

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

        if self._crow_progress >= 0.0:
            self._crow_progress += dt / 16.0
            if self._crow_progress >= 1.0:
                self._crow_progress = -1.0
                self._crow_timer = random.uniform(14.0, 26.0)
        else:
            self._crow_timer -= dt
            if self._crow_timer <= 0.0:
                self._crow_progress = 0.0

        target = float(self.buttons[self.selected_index].rect.y)
        self._bar_y += (target - self._bar_y) * (1.0 - math.exp(-dt * 16.0))

    # ----------------------------------------------------------------- events

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if self.elapsed < self.INTRO_SECONDS and event.type in (
            pygame.KEYDOWN,
            pygame.MOUSEBUTTONDOWN,
        ):
            self.elapsed = self.INTRO_SECONDS
            return None

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
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self.buttons[self.selected_index].action
            elif event.key == pygame.K_ESCAPE:
                return "resume" if self.has_session else "exit"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.enabled and button.rect.collidepoint(event.pos):
                    return button.action
        return None

    def handle_settings_click(self, pos: tuple[int, int]) -> str | None:
        """Return ``back`` or ``fullscreen`` for a click on the settings panel."""
        if self.back_button.collidepoint(pos):
            return "back"
        if self._toggle_rect.collidepoint(pos):
            return "fullscreen"
        return None

    def _move_selection(self, direction: int) -> None:
        index = self.selected_index
        for _ in self.buttons:
            index = (index + direction) % len(self.buttons)
            if self.buttons[index].enabled:
                self.selected_index = index
                return

    # ------------------------------------------------------------------- draw

    def draw(self, surface: pygame.Surface) -> None:
        t = self.elapsed
        surface.blit(self._sky, (0, 0))
        self._draw_stars(surface)
        self._draw_moon(surface)
        self._draw_crow(surface)
        surface.blit(
            self._far_layer,
            (-self._LAYER_PAD + int(math.sin(t * 0.12) * 8), self._FAR_TOP),
        )
        self._draw_mist(surface, self._mist_far, 9.0, 345)
        surface.blit(
            self._near_layer,
            (-self._LAYER_PAD + int(math.sin(t * 0.12 + 1.0) * 16), self._NEAR_TOP),
        )
        self._draw_torii(surface)
        self._draw_mist(surface, self._mist_near, 18.0, 465)
        surface.blit(self._ground, (0, self._GROUND_TOP))
        self._draw_kanji(surface)
        self._draw_embers(surface)
        for strip, position in self._vignette_strips:
            surface.blit(strip, position)
        self._draw_title(surface)
        self._draw_buttons(surface)
        self._draw_footer(surface)
        self._draw_intro_overlays(surface)

    def draw_back_button(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        hovered = self.back_button.collidepoint(pygame.mouse.get_pos())
        fill = (50, 37, 32) if hovered else (28, 27, 31)
        pygame.draw.rect(surface, fill, self.back_button)
        pygame.draw.rect(surface, _GOLD, self.back_button, 2)
        label = self._text(font, "BACK  [ESC]", (235, 220, 189))
        surface.blit(label, label.get_rect(center=self.back_button.center))

    def draw_settings_panel(self, surface: pygame.Surface, fullscreen: bool) -> None:
        surface.blit(self._scrim, (0, 0))
        panel = self._SETTINGS_PANEL
        draw_frame(surface, panel, (15, 17, 21), (177, 139, 86))
        left = panel.x + 44

        title = self._text(self.heading_font, "SETTINGS", _CREAM)
        surface.blit(title, (left, panel.y + 30))
        kanji = self._text(self.subtitle_font, "設定", _GOLD)
        surface.blit(kanji, (left + title.get_width() + 16, panel.y + 40))
        pygame.draw.rect(surface, (98, 79, 58), (left, panel.y + 82, panel.width - 88, 1))

        row_y = panel.y + 104
        label = self._text(self.button_font, "FULLSCREEN", _CREAM)
        surface.blit(label, (left, row_y))
        tip = self._text(self.hint_font, "CLICK THE SWITCH OR PRESS F11", (150, 140, 124))
        surface.blit(tip, (left + label.get_width() + 18, row_y + 8))
        self._draw_toggle(surface, fullscreen)

        heading = self._text(self.hint_font, "CONTROLS", _GOLD)
        surface.blit(heading, (left, panel.y + 168))
        pygame.draw.rect(
            surface, (98, 79, 58), (left + heading.get_width() + 14, panel.y + 177, 300, 1)
        )
        for column, rows in enumerate(self._CONTROLS):
            x = left + column * 360
            for row, (key, action) in enumerate(rows):
                y = panel.y + 204 + row * 34
                surface.blit(self._text(self.hint_font, key, _GOLD), (x, y))
                surface.blit(self._text(self.hint_font, action, _CREAM), (x + 160, y))

        self.draw_back_button(surface, self.hint_font)

    def _draw_toggle(self, surface: pygame.Surface, enabled: bool) -> None:
        rect = self._toggle_rect
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surface, (9, 12, 15), rect)
        pygame.draw.rect(surface, (255, 220, 150) if hovered else _GOLD, rect, 2)
        knob_x = rect.right - 32 if enabled else rect.x + 6
        knob_color = _GOLD if enabled else (110, 104, 96)
        pygame.draw.rect(surface, knob_color, (knob_x, rect.y + 5, 26, rect.height - 10))
        state = self._text(self.hint_font, "ON" if enabled else "OFF", _CREAM)
        surface.blit(state, (rect.x - state.get_width() - 14, rect.y + 8))

    # --------------------------------------------------------- scene drawing

    def _draw_stars(self, surface: pygame.Surface) -> None:
        for x, y, phase, size in self.stars:
            level = 0.55 + 0.45 * math.sin(self.elapsed * 1.3 + phase)
            color = (int(174 * level), int(160 * level), int(151 * level))
            pygame.draw.rect(surface, color, (x, y, size, size))

    def _draw_moon(self, surface: pygame.Surface) -> None:
        moon_y = 185 + int(math.sin(self.elapsed * 0.35) * 3)
        surface.blit(self._moon, (1000 - 150, moon_y - 150))

    def _draw_crow(self, surface: pygame.Surface) -> None:
        if self._crow_progress < 0.0:
            return
        p = self._crow_progress
        x = int(-40 + p * (self.WIDTH + 80))
        y = int(170 + math.sin(p * 9.0) * 16 - p * 30)
        wing = int(math.sin(self.elapsed * 11.0) * 7)
        color = (9, 10, 14)
        pygame.draw.ellipse(surface, color, (x - 7, y - 3, 14, 7))
        pygame.draw.polygon(
            surface, color,
            [(x - 3, y - 2), (x - 15, y - 6 - wing), (x - 20, y - wing), (x - 6, y + 1)],
        )
        pygame.draw.polygon(
            surface, color,
            [(x + 3, y - 2), (x + 15, y - 6 - wing), (x + 20, y - wing), (x + 6, y + 1)],
        )
        pygame.draw.polygon(surface, color, [(x + 6, y - 1), (x + 12, y - 3), (x + 8, y + 1)])

    def _draw_mist(
        self, surface: pygame.Surface, tile: pygame.Surface, speed: float, y: int
    ) -> None:
        offset = int((self.elapsed * speed) % self.WIDTH)
        surface.blit(tile, (-offset, y))
        surface.blit(tile, (self.WIDTH - offset, y))

    def _draw_torii(self, surface: pygame.Surface) -> None:
        x, y = self._TORII
        surface.blit(self._torii, (x - 130, y - 185))
        for offset, phase in ((-30, 0.0), (30, 1.7)):
            flicker = (
                0.72
                + 0.2 * math.sin(self.elapsed * 7.0 + phase)
                + 0.08 * math.sin(self.elapsed * 17.0 + phase * 2.0)
            )
            level = _clamp01(flicker)
            cx, cy = x + offset, y - 100
            self._glow.set_alpha(int(255 * level))
            surface.blit(self._glow, (cx - 70, cy - 70))
            dark = (35, 20, 22)
            pygame.draw.line(surface, dark, (cx, y - 128), (cx, cy - 14), 1)
            pygame.draw.rect(surface, dark, (cx - 8, cy - 14, 16, 3))
            pygame.draw.rect(surface, (176, 62, 48), (cx - 7, cy - 11, 14, 20))
            lit = _clamp01(level + 0.15)
            pygame.draw.rect(
                surface,
                (int(230 * lit), int(150 * lit), int(80 * lit)),
                (cx - 4, cy - 8, 8, 14),
            )
            pygame.draw.rect(surface, dark, (cx - 8, cy + 9, 16, 3))

    def _draw_kanji(self, surface: pygame.Surface) -> None:
        reveal = _ease((self.elapsed - 0.3) / 1.2)
        if reveal <= 0.0:
            return
        self._kanji.set_alpha(int(38 * reveal))
        surface.blit(self._kanji, (70 + int(math.sin(self.elapsed * 0.2) * 6), 30))

    def _draw_embers(self, surface: pygame.Surface) -> None:
        for particle in self.particles:
            flicker = 0.5 + 0.5 * math.sin(self.elapsed * 1.4 + particle["phase"])
            alpha = (90 + int(80 * flicker)) // 24 * 24
            speck = self._ember(particle["size"], alpha)
            surface.blit(speck, (int(particle["x"]), int(particle["y"])))

    def _ember(self, size: int, alpha: int) -> pygame.Surface:
        key = (size, alpha)
        speck = self._ember_cache.get(key)
        if speck is None:
            speck = pygame.Surface((size, size), pygame.SRCALPHA)
            speck.fill((232, 140, 84, alpha))
            self._ember_cache[key] = speck
        return speck

    # ----------------------------------------------------------- title and UI

    def _draw_title(self, surface: pygame.Surface) -> None:
        t = self.elapsed
        x = self._TITLE_X
        y = self._TITLE_Y + int(math.sin(t * 0.7) * 2)
        width, height = self._title.get_size()

        if 0.0 < t - 0.45 < 1.0:
            progress = _ease((t - 0.45) / 0.45)
            fade = 1.0 - _ease((t - 0.9) / 0.5)
            start = (x - 28, y + 10)
            end = (x + width + 28, y + height - 6)
            tip = (
                start[0] + (end[0] - start[0]) * progress,
                start[1] + (end[1] - start[1]) * progress,
            )
            red = tuple(int(v * fade) for v in (150, 40, 46))
            bright = tuple(int(v * fade) for v in (245, 236, 220))
            pygame.draw.line(surface, red, (start[0] + 4, start[1] + 4), (tip[0] + 4, tip[1] + 4), 3)
            pygame.draw.line(surface, bright, start, tip, 5)

        alpha = int(255 * _ease((t - 0.75) / 0.7))
        if alpha > 0:
            self._title_shadow.set_alpha(alpha)
            self._title.set_alpha(alpha)
            surface.blit(self._title_shadow, (x + 4, y + 5))
            surface.blit(self._title, (x, y))

        line_w = int(width * _ease((t - 1.1) / 0.6))
        if line_w > 0:
            left = x + 8
            pygame.draw.rect(surface, _GOLD, (left, self._line_y, line_w, 2))
            glint = int((t * 150) % (width + 220)) - 110
            glint_start = max(left, left + glint)
            glint_end = min(left + line_w, left + glint + 30)
            if glint_end > glint_start:
                pygame.draw.rect(
                    surface, (255, 238, 196), (glint_start, self._line_y - 1, glint_end - glint_start, 4)
                )

        sub_alpha = int(255 * _ease((t - 1.2) / 0.6))
        if sub_alpha > 0:
            subtitle = self._text(self.subtitle_font, "THE CURSE OF THE FALLEN SAMURAI", (190, 157, 121))
            subtitle.set_alpha(sub_alpha)
            surface.blit(subtitle, (x + 10, self._line_y + 14))
            tagline = self._text(self.note_font, "A TALE WRITTEN IN BLOOD AND ASH", (132, 127, 124))
            tagline.set_alpha(sub_alpha)
            surface.blit(tagline, (x + 12, self._line_y + 44))

    def _draw_buttons(self, surface: pygame.Surface) -> None:
        t = self.elapsed
        mouse_pos = pygame.mouse.get_pos()
        appear = [_ease((t - 1.2 - index * 0.09) / 0.45) for index in range(len(self.buttons))]

        for button, amount in zip(self.buttons, appear):
            if amount <= 0.0:
                continue
            rect = button.rect.move(int((1.0 - amount) * -26), 0)
            plate = tuple(int(v * amount) for v in (21, 23, 29))
            edge = tuple(int(v * amount) for v in (91, 79, 67))
            pygame.draw.rect(surface, plate, rect)
            pygame.draw.rect(surface, edge, rect, 1)

        selected = self.buttons[self.selected_index]
        amount = appear[self.selected_index]
        if selected.enabled and amount > 0.0:
            bar = pygame.Rect(
                selected.rect.x + int((1.0 - amount) * -26),
                int(round(self._bar_y)),
                selected.rect.width,
                selected.rect.height,
            )
            pulse = 0.5 + 0.5 * math.sin(t * 3.0)
            pygame.draw.rect(surface, (48 + int(8 * pulse), 34, 33), bar)
            pygame.draw.rect(surface, _GOLD, bar, 2)
            pygame.draw.rect(surface, (130, 47, 51), (bar.left, bar.top, 5, bar.height))
            self._draw_sword(surface, bar.left - 74 + int(math.sin(t * 4.0) * 2), bar.centery)

        for button, amount in zip(self.buttons, appear):
            if amount <= 0.0:
                continue
            rect = button.rect.move(int((1.0 - amount) * -26), 0)
            active = button.enabled and abs(button.rect.y - self._bar_y) < 25
            if not button.enabled:
                label_color, kanji_color = (91, 91, 91), (70, 70, 70)
            elif active:
                label_color, kanji_color = (239, 223, 194), (214, 176, 108)
            else:
                label_color, kanji_color = (170, 158, 138), (126, 106, 74)
            label = self._text(self.button_font, button.label, label_color)
            label.set_alpha(int(255 * amount))
            surface.blit(label, (rect.x + 30, rect.centery - label.get_height() // 2))
            kanji = self._text(self.hint_font, button.kanji, kanji_color)
            kanji.set_alpha(int(255 * amount))
            surface.blit(
                kanji,
                (rect.right - 18 - kanji.get_width(), rect.centery - kanji.get_height() // 2),
            )

        target = selected
        for button in self.buttons:
            if not button.enabled and button.rect.collidepoint(mouse_pos):
                target = button
        hint_alpha = int(255 * _ease((t - 1.8) / 0.4))
        if hint_alpha > 0:
            hint = self._text(self.hint_font, self._hint_for(target), (176, 160, 132))
            hint.set_alpha(hint_alpha)
            surface.blit(hint, (self._BUTTON_X + 2, self.buttons[-1].rect.bottom + 18))

    def _draw_sword(self, surface: pygame.Surface, x: int, cy: int) -> None:
        steel = (178, 196, 198)
        gold = (213, 173, 100)
        pygame.draw.polygon(
            surface, steel,
            [(x + 14, cy - 2), (x + 52, cy - 2), (x + 58, cy), (x + 52, cy + 1), (x + 14, cy + 1)],
        )
        pygame.draw.line(surface, (232, 236, 224), (x + 16, cy - 2), (x + 52, cy - 2), 1)
        pygame.draw.rect(surface, gold, (x + 10, cy - 5, 4, 9))
        pygame.draw.rect(surface, (120, 43, 47), (x - 6, cy - 2, 16, 4))
        pygame.draw.rect(surface, gold, (x - 8, cy - 3, 3, 6))

    def _hint_for(self, button: MenuButton) -> str:
        if not button.enabled:
            return "No saved journey found yet."
        if button.action == "resume":
            return "Return to your journey where you left off."
        if button.action == "new_game":
            if self.has_session:
                return "Abandon the current journey and begin anew."
            return "Begin the exile's journey at the cedar village."
        if button.action == "continue":
            return self.save_summary or "Load your most recent save."
        if button.action == "settings":
            return "Display options and a reference of the controls."
        return "Leave the world of Onikage."

    def _draw_footer(self, surface: pygame.Surface) -> None:
        alpha = int(255 * _ease((self.elapsed - 1.8) / 0.4))
        if alpha <= 0:
            return
        left = self._text(
            self.note_font, "ARROW KEYS / W S   SELECT     ENTER   CONFIRM", (121, 119, 119)
        )
        right = self._text(self.note_font, "F11  FULLSCREEN", (121, 119, 119))
        version = self._text(self.note_font, self.VERSION, (96, 92, 92))
        for item in (left, right, version):
            item.set_alpha(alpha)
        surface.blit(left, (118, 690))
        surface.blit(right, (self.WIDTH - 118 - right.get_width(), 690))
        surface.blit(version, (self.WIDTH - 118 - version.get_width(), 668))

    def _draw_intro_overlays(self, surface: pygame.Surface) -> None:
        t = self.elapsed
        flash = (t - 0.72) / 0.35
        if 0.0 < flash < 1.0:
            self._flash.set_alpha(int(80 * (1.0 - flash)))
            surface.blit(self._flash, (0, 0))
        fade = 1.0 - _clamp01(t / 0.9)
        if fade > 0.0:
            self._fade.set_alpha(int(255 * fade))
            surface.blit(self._fade, (0, 0))

    def _text(
        self, font: pygame.font.Font, text: str, color: tuple[int, int, int]
    ) -> pygame.Surface:
        key = (id(font), text, color)
        rendered = self._text_cache.get(key)
        if rendered is None:
            rendered = font.render(text, True, color)
            self._text_cache[key] = rendered
        return rendered

    # ------------------------------------------------- cached scene surfaces

    def _build_sky(self) -> pygame.Surface:
        sky = pygame.Surface((self.WIDTH, self.HEIGHT))
        for y in range(self.HEIGHT):
            blend = y / self.HEIGHT
            horizon = max(0.0, 1.0 - abs(y - 520) / 190)
            color = (
                int(16 + 12 * blend + 24 * horizon),
                int(17 + 7 * blend + 4 * horizon),
                int(30 + 7 * blend + 7 * horizon),
            )
            pygame.draw.line(sky, color, (0, y), (self.WIDTH, y))
        return sky.convert()

    @staticmethod
    def _build_moon() -> pygame.Surface:
        size = 300
        c = size // 2
        moon = pygame.Surface((size, size), pygame.SRCALPHA)
        for radius in range(148, 92, -4):
            alpha = int(4 + (148 - radius) * 0.55)
            pygame.draw.circle(moon, (150, 48, 56, alpha), (c, c), radius)
        pygame.draw.circle(moon, (98, 36, 47), (c, c), 92)
        pygame.draw.circle(moon, (142, 49, 56), (c, c), 78)
        pygame.draw.circle(moon, (166, 65, 66), (c, c), 68)
        pygame.draw.circle(moon, (142, 49, 56), (c, c), 57)
        for dx, dy, radius in ((-22, -18, 9), (18, -30, 6), (10, 20, 11), (-30, 24, 5)):
            pygame.draw.circle(moon, (128, 44, 52), (c + dx, c + dy), radius)
        return moon

    @staticmethod
    def _build_glow(radius: int, color: tuple[int, int, int]) -> pygame.Surface:
        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for ring in range(radius, 0, -3):
            alpha = int(((radius - ring) / radius) ** 2 * 90)
            pygame.draw.circle(glow, (*color, alpha), (radius, radius), ring)
        return glow

    def _build_layer(
        self,
        ridge: list[tuple[int, int]],
        base_y: int,
        top: int,
        bottom: int,
        color: tuple[int, int, int],
        rim: tuple[int, int, int],
        solid_from: int | None = None,
        pines: tuple[tuple[int, int, float], ...] = (),
    ) -> pygame.Surface:
        pad = self._LAYER_PAD
        width = self.WIDTH + pad * 2
        layer = pygame.Surface((width, bottom - top), pygame.SRCALPHA)
        points = [(x + pad, y - top) for x, y in ridge]
        polygon = points + [(points[-1][0], base_y - top), (points[0][0], base_y - top)]
        pygame.draw.polygon(layer, color, polygon)
        pygame.draw.lines(layer, rim, False, points, 2)
        if solid_from is not None:
            pygame.draw.rect(
                layer, (20, 23, 30), (0, solid_from - top, width, bottom - solid_from)
            )
        for x, y, scale in pines:
            self._draw_pine(layer, x + pad, y - top, scale)
        return layer

    @staticmethod
    def _draw_pine(target: pygame.Surface, x: int, y: int, scale: float) -> None:
        trunk = max(4, int(9 * scale))
        pygame.draw.rect(
            target,
            (13, 18, 22),
            pygame.Rect(x - trunk // 2, int(y - 100 * scale), trunk, int(112 * scale)),
        )
        for tier in range(4):
            top = y - (145 - tier * 30) * scale
            width = (49 - tier * 6) * scale
            pygame.draw.polygon(
                target,
                (13, 23 + tier, 26),
                [
                    (x, top),
                    (x - width, top + 55 * scale),
                    (x - width * 0.55, top + 48 * scale),
                    (x + width * 0.55, top + 48 * scale),
                    (x + width, top + 55 * scale),
                ],
            )

    def _build_mist(self, seed: int, blobs: int, strength: int) -> pygame.Surface:
        tile = pygame.Surface((self.WIDTH, 200), pygame.SRCALPHA)
        rng = random.Random(seed)
        for _ in range(blobs):
            width = rng.randrange(260, 520)
            height = rng.randrange(36, 80)
            cx = rng.randrange(0, self.WIDTH)
            cy = rng.randrange(60, 150)
            blob = pygame.Surface((width, height), pygame.SRCALPHA)
            for step in range(8):
                scale = 1.0 - step / 8
                inner = pygame.Rect(0, 0, int(width * scale), int(height * scale))
                inner.center = (width // 2, height // 2)
                pygame.draw.ellipse(blob, (150, 160, 178, int(strength * (step + 1) / 8)), inner)
            for wrap in (-self.WIDTH, 0, self.WIDTH):
                tile.blit(blob, (cx - width // 2 + wrap, cy - height // 2))
        return tile

    @staticmethod
    def _build_torii() -> pygame.Surface:
        ox, oy = 130, 185
        surface = pygame.Surface((260, 205), pygame.SRCALPHA)
        red, shadow, highlight, cap = (91, 31, 39), (47, 24, 30), (135, 47, 50), (28, 14, 19)

        def block(x: int, y: int, w: int, h: int, color: tuple[int, int, int]) -> None:
            pygame.draw.rect(surface, color, (ox + x, oy + y, w, h))

        block(-99, -153, 198, 13, shadow)
        block(-112, -162, 224, 13, red)
        block(-114, -168, 228, 6, cap)
        pygame.draw.polygon(surface, cap, [(ox - 114, oy - 168), (ox - 128, oy - 178), (ox - 104, oy - 168)])
        pygame.draw.polygon(surface, cap, [(ox + 114, oy - 168), (ox + 128, oy - 178), (ox + 104, oy - 168)])
        block(-79, -137, 158, 9, shadow)
        block(-8, -148, 16, 22, (33, 22, 24))
        block(-6, -146, 12, 18, (86, 68, 46))
        block(-69, -133, 16, 153, red)
        block(53, -133, 16, 153, red)
        block(-65, -128, 5, 143, highlight)
        block(57, -128, 5, 143, highlight)
        block(-71, 0, 20, 18, cap)
        block(51, 0, 20, 18, cap)
        return surface

    def _build_ground(self) -> pygame.Surface:
        top = self._GROUND_TOP
        ground = pygame.Surface((self.WIDTH, self.HEIGHT - top), pygame.SRCALPHA)
        outline = [
            (0, 591), (198, 567), (359, 605), (529, 576), (710, 612),
            (902, 579), (1085, 609), (1280, 568), (1280, 720), (0, 720),
        ]
        pygame.draw.polygon(ground, (11, 16, 20), [(x, y - top) for x, y in outline])
        rng = random.Random(5)
        blades = [(451, 664), (509, 682), (828, 650), (1136, 682), (78, 650)]
        blades += [(rng.randrange(20, 1260), rng.randrange(640, 712)) for _ in range(18)]
        for x, y in blades:
            pygame.draw.line(ground, (42, 47, 42), (x, y - top), (x - 9, y - 22 - top), 2)
            pygame.draw.line(ground, (42, 47, 42), (x, y - 12 - top), (x + 7, y - 26 - top), 2)
        return ground

    def _build_vignette_strips(self) -> list[tuple[pygame.Surface, tuple[int, int]]]:
        edge = 48
        vignette = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        for i in range(edge):
            alpha = int(150 * (1.0 - i / edge) ** 2)
            pygame.draw.rect(
                vignette, (0, 0, 0, alpha),
                (i, i, self.WIDTH - 2 * i, self.HEIGHT - 2 * i), 1,
            )
        areas = (
            pygame.Rect(0, 0, edge, self.HEIGHT),
            pygame.Rect(self.WIDTH - edge, 0, edge, self.HEIGHT),
            pygame.Rect(edge, 0, self.WIDTH - 2 * edge, edge),
            pygame.Rect(edge, self.HEIGHT - edge, self.WIDTH - 2 * edge, edge),
        )
        return [(vignette.subsurface(area), area.topleft) for area in areas]
