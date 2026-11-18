"""Standalone, non-gameplay preview for the four approved art-pack samples."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if "--smoke" in sys.argv:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pygame

from onikage.art.asset_pipeline import (
    Animation,
    TileMap,
    load_image,
    load_sprite_sheet,
    scale_nearest,
)


PACK_ROOT = ROOT / "onikage" / "assets" / "artpacks"
WINDOW_SIZE = (1280, 720)

_BACKGROUND = (13, 16, 23)
_PANEL = (22, 27, 35)
_BORDER = (106, 83, 55)
_TEXT = (226, 214, 188)
_MUTED = (154, 156, 157)
_ACCENT = (163, 53, 56)


class AssetPackPreview:
    def __init__(self) -> None:
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 21)
        self.title_font = pygame.font.Font(None, 40)
        self.current_pack = 0
        self.animation_selection = {1: 0, 3: 0}
        self.paused = False
        self.scaled_cache: dict[tuple[int, int, int], pygame.Surface] = {}

        self.feudal_props = tuple(
            (
                name,
                load_image(
                    PACK_ROOT
                    / "feudal_japan"
                    / "props"
                    / f"{filename}_32x32.png"
                ),
            )
            for name, filename in (
                ("Torii gate", "01_torii_gate"),
                ("Stone lantern", "02_stone_lantern"),
                ("Bamboo", "03_bamboo_cluster"),
                ("Sake barrel", "04_sake_barrel"),
                ("Katana stand", "05_katana_stand"),
                ("Paper lantern", "06_paper_lantern"),
                ("Wooden fence", "07_wooden_fence"),
                ("Offering box", "08_offering_box"),
            )
        )

        ninja_root = PACK_ROOT / "ninja_adventure"
        samurai_root = ninja_root / "characters" / "samurai"
        self.ninja_idle = load_sprite_sheet(samurai_root / "idle.png", (16, 16))
        self.ninja_attack = load_sprite_sheet(
            samurai_root / "attack.png", (16, 16)
        )
        self.ninja_walk = load_sprite_sheet(samurai_root / "walk.png", (16, 16))
        self.ninja_walk_image = load_image(samurai_root / "walk.png")
        self.ninja_sprite_sheet = load_image(samurai_root / "sprite_sheet.png")
        self.ninja_animations = {
            "Idle": Animation(self.ninja_idle.row(0), frame_duration=0.16),
            "Attack": Animation(self.ninja_attack.row(0), frame_duration=0.16),
        }
        self.ninja_dungeon = load_image(ninja_root / "tilesets" / "dungeon.png")
        self.ninja_house = load_image(ninja_root / "tilesets" / "house.png")

        dungeon_root = PACK_ROOT / "0x72_dungeon"
        self.dungeon_atlas = load_image(dungeon_root / "atlas.png")
        self.dungeon_floor = load_image(dungeon_root / "tiles" / "floor_plain.png")
        self.dungeon_mud = load_image(
            dungeon_root / "tiles" / "floor_mud_mid_1.png"
        )
        self.dungeon_wall = load_image(
            dungeon_root / "tiles" / "Wall_inner_nw.png"
        )
        self.dungeon_torch = load_image(dungeon_root / "tiles" / "torch_8.png")
        self.dungeon_door = load_image(dungeon_root / "tiles" / "door_closed.png")
        self.dungeon_stairs = load_image(
            dungeon_root / "tiles" / "stairs_mid.png"
        )
        self.dungeon_room = TileMap(self._make_dungeon_room(), tile_size=16)

        crawler_root = PACK_ROOT / "pixel_crawler"
        crawler_characters = crawler_root / "characters"
        self.crawler_animations = {
            "Idle Down": self._load_animation(
                crawler_characters / "idle_down.png", (64, 64), 0.3
            ),
            "Walk Down": self._load_animation(
                crawler_characters / "walk_down.png", (64, 64), 0.12
            ),
            "Slice Down": self._load_animation(
                crawler_characters / "slice_down.png", (64, 64), 0.09, False
            ),
            "Hit Down": self._load_animation(
                crawler_characters / "hit_down.png", (64, 64), 0.12, False
            ),
        }
        self.crawler_tiles = load_image(
            crawler_root / "tilesets" / "dungeon_tiles.png"
        )
        self.crawler_floors = load_image(
            crawler_root / "tilesets" / "floors_tiles.png"
        )

    @staticmethod
    def _load_animation(
        path: Path,
        frame_size: tuple[int, int],
        duration: float,
        loop: bool = True,
    ) -> Animation:
        sheet = load_sprite_sheet(path, frame_size)
        return Animation(sheet.row(0), frame_duration=duration, loop=loop)

    @staticmethod
    def _make_dungeon_room() -> tuple[tuple[str, ...], ...]:
        rows: list[tuple[str, ...]] = []
        for row in range(10):
            cells = ["floor"] * 20
            if row in (3, 7):
                for column in range(4, 16):
                    if column % 3 == 0:
                        cells[column] = "mud"
            rows.append(tuple(cells))
        return tuple(rows)

    def _scaled(
        self, image: pygame.Surface, size: tuple[int, int]
    ) -> pygame.Surface:
        key = (id(image), size[0], size[1])
        if key not in self.scaled_cache:
            self.scaled_cache[key] = scale_nearest(image, size)
        return self.scaled_cache[key]

    def _text(
        self,
        target: pygame.Surface,
        text: str,
        position: tuple[int, int],
        color: tuple[int, int, int] = _TEXT,
        font: pygame.font.Font | None = None,
    ) -> None:
        target.blit((font or self.font).render(text, True, color), position)

    def _panel(
        self,
        target: pygame.Surface,
        rect: pygame.Rect,
        label: str,
    ) -> pygame.Rect:
        pygame.draw.rect(target, _PANEL, rect, border_radius=4)
        pygame.draw.rect(target, _BORDER, rect, width=2, border_radius=4)
        self._text(target, label, (rect.x + 14, rect.y + 10), font=self.small_font)
        return rect

    def draw(self, target: pygame.Surface, delta_seconds: float = 0.0) -> None:
        target.fill(_BACKGROUND)
        self._draw_header(target)
        if self.current_pack == 0:
            self._draw_feudal(target)
        elif self.current_pack == 1:
            self._draw_ninja(target, delta_seconds)
        elif self.current_pack == 2:
            self._draw_dungeon(target)
        else:
            self._draw_crawler(target, delta_seconds)

    def _draw_header(self, target: pygame.Surface) -> None:
        titles = (
            "Feudal Japan Props Vol.1",
            "Ninja Adventure",
            "0x72 Dungeon Tileset",
            "Pixel Crawler Exterior",
        )
        pygame.draw.rect(target, (18, 22, 30), (0, 0, WINDOW_SIZE[0], 102))
        pygame.draw.line(target, _BORDER, (0, 101), (WINDOW_SIZE[0], 101), 2)
        self._text(target, "ONIKAGE  /  ASSET LAB", (32, 18), _ACCENT, self.small_font)
        self._text(target, titles[self.current_pack], (32, 40), font=self.title_font)
        self._text(
            target,
            "1 Feudal   2 Ninja   3 0x72   4 Crawler"
            "     A/D animation   Space pause   Esc quit",
            (700, 24),
            _MUTED,
            self.small_font,
        )
        notes = (
            "Original 32x32 props; displayed enlarged with nearest-neighbor scaling.",
            "Samurai frames and tiles are source previews; walk-row directions are not labeled.",
            "Atlas and standalone samples retain their native layout; room uses named 16x16 tiles.",
            "Generic character and bright terrain are shown for style comparison only.",
        )
        self._text(target, notes[self.current_pack], (32, 78), _MUTED, self.small_font)

    def _draw_feudal(self, target: pygame.Surface) -> None:
        card_width, card_height = 286, 260
        for index, (name, image) in enumerate(self.feudal_props):
            column, row = index % 4, index // 4
            rect = pygame.Rect(
                34 + column * (card_width + 18),
                124 + row * (card_height + 24),
                card_width,
                card_height,
            )
            self._panel(target, rect, name)
            scaled = self._scaled(image, (128, 128))
            target.blit(scaled, scaled.get_rect(center=(rect.centerx, rect.y + 145)))
            self._text(
                target,
                "32 x 32 source",
                (rect.x + 14, rect.bottom - 34),
                _MUTED,
                self.small_font,
            )

    def _draw_ninja(
        self, target: pygame.Surface, delta_seconds: float
    ) -> None:
        selected = self.animation_selection[1] % 2
        animation_name = ("Idle", "Attack")[selected]
        animation = self.ninja_animations[animation_name]
        if not self.paused:
            animation.update(delta_seconds)

        card = self._panel(target, pygame.Rect(34, 124, 315, 530), "Samurai")
        sprite = self._scaled(self.ninja_sprite_sheet, (192, 336))
        target.blit(sprite, sprite.get_rect(center=(card.centerx, card.y + 285)))
        self._text(
            target,
            "SpriteSheet: 4 x 7 cells",
            (card.x + 16, card.bottom - 58),
            _MUTED,
            self.small_font,
        )

        card = self._panel(target, pygame.Rect(370, 124, 326, 530), animation_name)
        animated_frame = animation.current_frame
        shown = self._scaled(animated_frame, (128, 128))
        target.blit(shown, shown.get_rect(center=(card.centerx, card.y + 190)))
        walk_grid = self._scaled(self.ninja_walk_image, (256, 256))
        target.blit(walk_grid, walk_grid.get_rect(center=(card.centerx, card.y + 330)))
        self._text(
            target,
            f"{animation_name} row: 4 x 16px frames",
            (card.x + 16, card.bottom - 58),
            _MUTED,
            self.small_font,
        )
        self._text(
            target,
            f"Walk sheet: {self.ninja_walk.columns} x {self.ninja_walk.rows} grid",
            (card.x + 16, card.bottom - 34),
            _MUTED,
            self.small_font,
        )

        card = self._panel(target, pygame.Rect(717, 124, 529, 530), "Dungeon tileset")
        dungeon = self._scaled(self.ninja_dungeon, (384, 128))
        target.blit(dungeon, dungeon.get_rect(center=(card.centerx, card.y + 210)))
        house_size = self._fit_size(self.ninja_house, (480, 280))
        target.blit(self._scaled(self.ninja_house, house_size), (card.x + 22, card.y + 310))
        self._text(
            target,
            "House atlas shown at native scale",
            (card.x + 22, card.bottom - 36),
            _MUTED,
            self.small_font,
        )

    def _draw_dungeon(self, target: pygame.Surface) -> None:
        card = self._panel(target, pygame.Rect(34, 124, 656, 448), "Named tile samples")
        floor_tiles = {
            "floor": self._scaled(self.dungeon_floor, (32, 32)),
            "mud": self._scaled(self.dungeon_mud, (32, 32)),
        }
        room = TileMap(self.dungeon_room.rows, tile_size=32)
        room.draw(target, floor_tiles, origin=(card.x + 8, card.y + 42))
        torch = self._scaled(self.dungeon_torch, (28, 46))
        target.blit(torch, (card.x + 282, card.y + 140))
        wall = self._scaled(self.dungeon_wall, (32, 32))
        target.blit(wall, (card.x + 382, card.y + 141))
        door = self._scaled(self.dungeon_door, (64, 64))
        target.blit(door, (card.x + 440, card.y + 130))
        stairs = self._scaled(self.dungeon_stairs, (64, 32))
        target.blit(stairs, (card.x + 520, card.y + 260))
        self._text(
            target,
            "16px named tiles used in a preview-only floor map",
            (card.x + 12, card.bottom - 30),
            _MUTED,
            self.small_font,
        )

        card = self._panel(target, pygame.Rect(715, 124, 531, 448), "Original 512 x 256 atlas")
        target.blit(self.dungeon_atlas, (card.x + 8, card.y + 42))
        self._text(
            target,
            "JSON metadata retained beside the atlas",
            (card.x + 12, card.bottom - 30),
            _MUTED,
            self.small_font,
        )

    def _draw_crawler(self, target: pygame.Surface, delta_seconds: float) -> None:
        names = tuple(self.crawler_animations)
        selection = self.animation_selection[3] % len(names)
        animation_name = names[selection]
        animation = self.crawler_animations[animation_name]
        if not self.paused:
            animation.update(delta_seconds)

        card = self._panel(target, pygame.Rect(34, 124, 340, 530), animation_name)
        sprite = self._scaled(animation.current_frame, (192, 192))
        target.blit(sprite, sprite.get_rect(center=(card.centerx, card.y + 205)))
        self._text(
            target,
            f"{len(animation.frames)} x 64px cells",
            (card.x + 16, card.bottom - 60),
            _MUTED,
            self.small_font,
        )
        self._text(
            target,
            "Down-facing sheet; side/up files also included",
            (card.x + 16, card.bottom - 34),
            _MUTED,
            self.small_font,
        )

        tile_card = self._panel(
            target, pygame.Rect(398, 124, 848, 530), "Dungeon tiles and floors (native pixels)"
        )
        dungeon_size = self._fit_size(self.crawler_tiles, (400, 400))
        floor_size = self._fit_size(self.crawler_floors, (400, 400))
        target.blit(self._scaled(self.crawler_tiles, dungeon_size), (tile_card.x + 18, tile_card.y + 56))
        target.blit(self._scaled(self.crawler_floors, floor_size), (tile_card.x + 430, tile_card.y + 56))
        self._text(
            target,
            "Tileset layout is shown whole; no unverified grid slicing",
            (tile_card.x + 18, tile_card.bottom - 34),
            _MUTED,
            self.small_font,
        )

    @staticmethod
    def _fit_size(
        image: pygame.Surface, maximum: tuple[int, int]
    ) -> tuple[int, int]:
        scale = min(
            maximum[0] / image.get_width(),
            maximum[1] / image.get_height(),
            1.0,
        )
        return (
            max(1, round(image.get_width() * scale)),
            max(1, round(image.get_height() * scale)),
        )

    def handle_key(self, key: int) -> bool:
        if key == pygame.K_ESCAPE:
            return False
        if pygame.K_1 <= key <= pygame.K_4:
            self.current_pack = key - pygame.K_1
        elif key in (pygame.K_a, pygame.K_LEFT):
            self._cycle_animation(-1)
        elif key in (pygame.K_d, pygame.K_RIGHT):
            self._cycle_animation(1)
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
        return True

    def _cycle_animation(self, offset: int) -> None:
        if self.current_pack == 1:
            count = 2
        elif self.current_pack == 3:
            count = len(self.crawler_animations)
        else:
            return
        selection = self.animation_selection[self.current_pack]
        self.animation_selection[self.current_pack] = (selection + offset) % count
        if self.current_pack == 3:
            for animation in self.crawler_animations.values():
                animation.reset()


def main() -> int:
    pygame.init()
    display = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("ONIKAGE - Asset Pack Preview")
    clock = pygame.time.Clock()
    preview = AssetPackPreview()

    if "--smoke" in sys.argv:
        for index in range(4):
            preview.current_pack = index
            preview.draw(display)
            pygame.display.flip()
            print(f"Rendered preview {index + 1}/4: {display.get_size()}")
        pygame.quit()
        return 0

    running = True
    while running:
        delta_seconds = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                running = preview.handle_key(event.key)
        preview.draw(display, delta_seconds)
        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
