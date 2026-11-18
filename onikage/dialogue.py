import pygame

from onikage.art.ui.panels import draw_frame, hana_portrait


class DialogueSystem:
    """Tracks a conversation one line at a time."""

    def __init__(self) -> None:
        self.speaker = ""
        self.lines: tuple[str, ...] = ()
        self.index = 0
        self.active = False

    def start(self, speaker: str, lines: tuple[str, ...]) -> None:
        if not lines:
            raise ValueError("A conversation must contain at least one line.")
        self.speaker = speaker
        self.lines = lines
        self.index = 0
        self.active = True

    def advance(self) -> bool:
        if not self.active:
            return False
        self.index += 1
        if self.index >= len(self.lines):
            self.active = False
        return self.active

    @property
    def current_line(self) -> str:
        if not self.active:
            return ""
        return self.lines[self.index]

    def draw(
        self,
        surface: pygame.Surface,
        name_font: pygame.font.Font,
        text_font: pygame.font.Font,
        hint_font: pygame.font.Font,
    ) -> None:
        if not self.active:
            return

        box = pygame.Rect(64, 500, 1152, 184)
        draw_frame(surface, box, (15, 17, 21), (177, 139, 86))

        nameplate = pygame.Rect(box.x + 24, box.y - 23, 308, 42)
        draw_frame(surface, nameplate, (35, 29, 27), (177, 139, 86))
        name = name_font.render(self.speaker, True, (230, 199, 144))
        surface.blit(name, (nameplate.x + 16, nameplate.y + 4))

        portrait_rect = pygame.Rect(box.x + 22, box.y + 54, 72, 72)
        pygame.draw.rect(surface, (9, 12, 15), portrait_rect)
        pygame.draw.rect(surface, (157, 118, 74), portrait_rect, 2)
        surface.blit(hana_portrait(), (portrait_rect.x + 3, portrait_rect.y + 3))

        text_left = portrait_rect.right + 20
        lines = self._wrap(self.current_line, text_font, box.right - text_left - 34)
        for index, line in enumerate(lines[:3]):
            rendered = text_font.render(line, True, (232, 224, 206))
            surface.blit(rendered, (text_left, box.y + 48 + index * 30))

        for index in range(len(self.lines)):
            color = (218, 172, 91) if index == self.index else (92, 82, 71)
            pygame.draw.rect(surface, color, (text_left + index * 18, box.bottom - 34, 12, 3))

        hint = hint_font.render("E / ENTER  CONTINUE     ESC  CLOSE", True, (162, 149, 129))
        surface.blit(hint, (box.right - hint.get_width() - 26, box.bottom - 29))

    @staticmethod
    def _wrap(
        text: str,
        font: pygame.font.Font,
        max_width: int,
    ) -> list[str]:
        lines: list[str] = []
        current = ""
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] > max_width and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines
