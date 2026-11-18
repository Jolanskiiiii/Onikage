"""Cached image, sprite-sheet, animation, and tile-map helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import lru_cache
from pathlib import Path

import pygame


@lru_cache(maxsize=256)
def _load_image(resolved_path: str) -> pygame.Surface:
    image = pygame.image.load(resolved_path)
    if pygame.display.get_surface() is not None:
        return image.convert_alpha()
    return image.copy()


def load_image(path: str | Path) -> pygame.Surface:
    """Load an RGBA image once per resolved path and return its cached surface."""
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Asset image does not exist: {resolved}")
    return _load_image(str(resolved))


def clear_asset_cache() -> None:
    """Clear decoded image and sprite-sheet caches, primarily for tests/tools."""
    _load_image.cache_clear()
    _load_sprite_sheet.cache_clear()


class SpriteSheet:
    """Row-major fixed-cell view of a sheet whose cell dimensions are known."""

    def __init__(
        self, image: pygame.Surface, frame_size: tuple[int, int]
    ) -> None:
        frame_width, frame_height = frame_size
        if frame_width <= 0 or frame_height <= 0:
            raise ValueError("Frame dimensions must be positive.")
        if image.get_width() % frame_width or image.get_height() % frame_height:
            raise ValueError(
                f"Sheet size {image.get_size()} is not divisible by "
                f"frame size {frame_size}."
            )

        self.frame_size = frame_size
        self.columns = image.get_width() // frame_width
        self.rows = image.get_height() // frame_height
        self._frames = tuple(
            image.subsurface(
                (
                    column * frame_width,
                    row * frame_height,
                    frame_width,
                    frame_height,
                )
            ).copy()
            for row in range(self.rows)
            for column in range(self.columns)
        )

    def frame(self, column: int, row: int = 0) -> pygame.Surface:
        """Return a frame by explicit zero-based column and row."""
        if not 0 <= column < self.columns or not 0 <= row < self.rows:
            raise IndexError(
                f"Frame ({column}, {row}) is outside "
                f"{self.columns}x{self.rows} sheet."
            )
        return self._frames[row * self.columns + column]

    def row(self, row: int) -> tuple[pygame.Surface, ...]:
        """Return all frames in a zero-based row."""
        if not 0 <= row < self.rows:
            raise IndexError(f"Row {row} is outside a {self.rows}-row sheet.")
        start = row * self.columns
        return self._frames[start : start + self.columns]


@lru_cache(maxsize=64)
def _load_sprite_sheet(
    resolved_path: str, frame_width: int, frame_height: int
) -> SpriteSheet:
    return SpriteSheet(
        load_image(resolved_path), (frame_width, frame_height)
    )


def load_sprite_sheet(
    path: str | Path, frame_size: tuple[int, int]
) -> SpriteSheet:
    """Load and cache a sheet using explicitly supplied native frame size."""
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Sprite sheet does not exist: {resolved}")
    return _load_sprite_sheet(str(resolved), *frame_size)


class Animation:
    """Time-based playback over an explicitly selected sequence of frames."""

    def __init__(
        self,
        frames: Sequence[pygame.Surface],
        frame_duration: float = 0.12,
        loop: bool = True,
    ) -> None:
        if not frames:
            raise ValueError("An animation requires at least one frame.")
        if frame_duration <= 0:
            raise ValueError("Frame duration must be positive.")
        self.frames = tuple(frames)
        self.frame_duration = frame_duration
        self.loop = loop
        self.elapsed = 0.0
        self.index = 0
        self.finished = False

    @property
    def current_frame(self) -> pygame.Surface:
        return self.frames[self.index]

    def reset(self) -> None:
        self.elapsed = 0.0
        self.index = 0
        self.finished = False

    def update(self, delta_seconds: float) -> None:
        if delta_seconds < 0:
            raise ValueError("Animation delta cannot be negative.")
        if self.finished or delta_seconds == 0:
            return

        self.elapsed += delta_seconds
        steps = int(self.elapsed / self.frame_duration)
        if steps == 0:
            return
        self.elapsed -= steps * self.frame_duration
        next_index = self.index + steps
        if self.loop:
            self.index = next_index % len(self.frames)
            return

        if next_index >= len(self.frames):
            self.index = len(self.frames) - 1
            self.elapsed = 0.0
            self.finished = True
        else:
            self.index = next_index


def scale_nearest(
    image: pygame.Surface, size: tuple[int, int]
) -> pygame.Surface:
    """Scale with pygame's nearest-neighbor transform, preserving pixel edges."""
    width, height = size
    if width <= 0 or height <= 0:
        raise ValueError("Scaled dimensions must be positive.")
    if image.get_size() == size:
        return image
    return pygame.transform.scale(image, size)


class TileMap:
    """Render a rectangular grid of named, same-sized tile surfaces."""

    def __init__(
        self,
        rows: Sequence[Sequence[str | None]],
        tile_size: int,
    ) -> None:
        if tile_size <= 0:
            raise ValueError("Tile size must be positive.")
        if not rows or not rows[0]:
            raise ValueError("A tile map must contain at least one cell.")
        row_width = len(rows[0])
        if any(len(row) != row_width for row in rows):
            raise ValueError("Tile-map rows must have equal lengths.")
        self.rows = tuple(tuple(row) for row in rows)
        self.tile_size = tile_size

    def draw(
        self,
        target: pygame.Surface,
        tiles: Mapping[str, pygame.Surface],
        origin: tuple[int, int] = (0, 0),
    ) -> None:
        used_tiles = {
            tile_name
            for row in self.rows
            for tile_name in row
            if tile_name is not None
        }
        missing_tiles = used_tiles.difference(tiles)
        if missing_tiles:
            raise KeyError(f"Missing tile images: {sorted(missing_tiles)}")

        for tile_name in used_tiles:
            if tiles[tile_name].get_size() != (self.tile_size, self.tile_size):
                raise ValueError(
                    f"Tile {tile_name!r} has size {tiles[tile_name].get_size()}, "
                    f"expected {(self.tile_size, self.tile_size)}."
                )

        origin_x, origin_y = origin
        for row_index, row in enumerate(self.rows):
            for column_index, tile_name in enumerate(row):
                if tile_name is None:
                    continue
                target.blit(
                    tiles[tile_name],
                    (
                        origin_x + column_index * self.tile_size,
                        origin_y + row_index * self.tile_size,
                    ),
                )
