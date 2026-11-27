import unittest

import pygame

from onikage.isometric import (
    IsoTransform,
    direction_name,
    ground_depth,
    interaction_point,
    normalized_direction,
)
from onikage.player import Player


class IsometricCoordinateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.transform = IsoTransform(tile_width=64, tile_height=32)

    def test_world_screen_round_trip(self) -> None:
        world = pygame.Vector2(240, 160)
        screen = self.transform.world_to_screen(world.x, world.y)
        restored = self.transform.screen_to_world(screen.x, screen.y)
        self.assertAlmostEqual(world.x, restored.x)
        self.assertAlmostEqual(world.y, restored.y)

    def test_origin_offsets_are_preserved(self) -> None:
        screen = self.transform.world_to_screen(10, 20, 640, 360)
        world = self.transform.screen_to_world(screen.x, screen.y, 640, 360)
        self.assertAlmostEqual(world.x, 10)
        self.assertAlmostEqual(world.y, 20)


class MovementTests(unittest.TestCase):
    def test_diagonal_movement_is_normalized(self) -> None:
        movement = normalized_direction(1, 1)
        self.assertAlmostEqual(movement.length(), 1.0)
        self.assertAlmostEqual(movement.x, movement.y)

    def test_eight_direction_names(self) -> None:
        cases = (
            ((1, 0), "right"), ((1, 1), "down-right"),
            ((0, 1), "down"), ((-1, 1), "down-left"),
            ((-1, 0), "left"), ((-1, -1), "up-left"),
            ((0, -1), "up"), ((1, -1), "up-right"),
        )
        for vector, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(direction_name(*vector), expected)

    def test_player_collision_uses_axis_and_ground_position(self) -> None:
        player = Player(100, 100)
        obstacle = pygame.Rect(124, 100, 30, 36)
        player._move_axis(20, 0, [obstacle])
        self.assertEqual(player.rect.right, obstacle.left)
        self.assertEqual(player.ground_position.y, player.rect.bottom)


class InteractionTests(unittest.TestCase):
    def test_interaction_position_tracks_facing(self) -> None:
        ground = pygame.Vector2(300, 400)
        right = interaction_point(ground, "right", 32)
        down = interaction_point(ground, "down", 32)
        self.assertEqual((right.x, right.y), (332, 400))
        self.assertEqual((down.x, down.y), (300, 432))

    def test_ground_depth_sorts_higher_y_and_x_later(self) -> None:
        shallow = ground_depth(100, 100)
        deep = ground_depth(300, 300)
        self.assertLess(shallow, deep)


if __name__ == "__main__":
    unittest.main()
