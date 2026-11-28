import unittest
from pathlib import Path

import pygame

from onikage.art.enemies.wraith_sprite import (
    ANIMATIONS,
    DIRECTIONS,
    wraith_animation_frame,
)
from onikage.enemy import Enemy


class WraithAnimationTests(unittest.TestCase):
    def test_sprite_atlas_exists_and_contains_five_animation_rows(self):
        atlas = Path(__file__).parents[1] / "onikage" / "art" / "enemies" / "wraith_sheet.png"
        self.assertTrue(atlas.is_file())
        self.assertEqual(ANIMATIONS, ("idle", "walk", "attack", "hurt", "death"))
        self.assertEqual(DIRECTIONS, ("down", "left", "up", "right"))

    def test_every_animation_direction_returns_a_transparent_sprite(self):
        for animation in ANIMATIONS:
            for direction in DIRECTIONS:
                with self.subTest(animation=animation, direction=direction):
                    frame = wraith_animation_frame(animation, direction, 0)
                    self.assertEqual(frame.get_size(), (72, 80))
                    self.assertIsNotNone(frame.get_flags())
                    self.assertGreater(frame.get_bounding_rect().width, 0)

    def test_enemy_animation_changes_without_changing_collision_geometry(self):
        enemy = Enemy(100, 200)
        original_rect = enemy.rect.copy()
        enemy.set_animation("attack", "left")
        self.assertEqual(enemy.animation, "attack")
        self.assertEqual(enemy.direction, "left")
        self.assertEqual(enemy.rect, original_rect)

    def test_death_animation_finishes_after_four_frames(self):
        enemy = Enemy(100, 200)
        enemy.set_animation("death")
        enemy.update(0.9)
        self.assertTrue(enemy.death_animation_finished)


if __name__ == "__main__":
    unittest.main()
