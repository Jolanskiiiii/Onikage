import unittest

import pygame

from onikage.directions import direction_name, normalized_direction


class TopDownDirectionTests(unittest.TestCase):
    def test_cardinal_screen_directions(self) -> None:
        self.assertEqual(direction_name(1, 0), "right")
        self.assertEqual(direction_name(0, 1), "down")
        self.assertEqual(direction_name(-1, 0), "left")
        self.assertEqual(direction_name(0, -1), "up")

    def test_diagonal_movement_is_normalized(self) -> None:
        vector = normalized_direction(1, 1)
        self.assertAlmostEqual(vector.length(), 1.0)
        self.assertAlmostEqual(vector.x, 2 ** -0.5)
        self.assertAlmostEqual(vector.y, 2 ** -0.5)

    def test_no_input_stays_zero(self) -> None:
        self.assertEqual(normalized_direction(0, 0), pygame.Vector2())


if __name__ == "__main__":
    unittest.main()
