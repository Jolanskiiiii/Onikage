import unittest

import pygame

from onikage.art.effects.ground_shadows import (
    _ground_shadow_surface,
    draw_ground_shadow,
)
from onikage.art.objects.village import (
    draw_village_object,
    _lantern_glow_origin,
    _lantern_ground_glow_origin,
)

from onikage.npc import NPC
from onikage.village import VillageWorld


class VillageVisualAlignmentTests(unittest.TestCase):
    def test_ground_shadow_surface_has_soft_alpha_edges_and_cached_reuse(self):
        shadow = _ground_shadow_surface(31, 9, 86)
        self.assertIs(shadow, _ground_shadow_surface(31, 9, 86))
        self.assertEqual(shadow.get_size(), (31, 9))
        self.assertEqual(shadow.get_at((0, 4)).a, 0)
        self.assertGreater(shadow.get_at((15, 4)).a, 0)
        self.assertLessEqual(shadow.get_at((15, 4)).a, 86)

    def test_ground_shadow_draw_is_confined_to_requested_footprint(self):
        canvas = pygame.Surface((64, 32), pygame.SRCALPHA)
        draw_ground_shadow(canvas, (10, 8, 31, 9), opacity=80)
        self.assertEqual(canvas.get_at((0, 0)).a, 0)
        self.assertGreater(canvas.get_at((25, 12)).a, 0)
        self.assertEqual(canvas.get_at((50, 12)).a, 0)

    def test_refined_shrine_and_barrel_shadows_render(self):
        for kind in ("shrine", "barrel"):
            with self.subTest(kind=kind):
                canvas = pygame.Surface((96, 96), pygame.SRCALPHA)
                draw_village_object(canvas, 24, 20, kind, pygame.Vector2(0, 0))
                self.assertNotEqual(canvas.get_bounding_rect(), pygame.Rect(0, 0, 0, 0))

    def test_lantern_glow_center_matches_flame_anchor(self):
        origin = _lantern_glow_origin(200, 150)
        glow_center = (origin[0] + 32, origin[1] + 32)
        self.assertEqual(glow_center, (212, 159))

    def test_ground_glow_is_centered_on_lantern_ground_contact(self):
        origin = _lantern_ground_glow_origin(200, 150)
        self.assertEqual(origin, (148, 147))
        self.assertEqual((origin[0] + 64, origin[1] + 36), (212, 183))

    def test_decoration_ground_anchors_match_rendered_bases(self):
        self.assertEqual(VillageWorld._decoration_ground_y(100, "lantern"), 133)
        self.assertEqual(VillageWorld._decoration_ground_y(100, "shrine"), 144)
        self.assertEqual(VillageWorld._decoration_ground_y(100, "barrel"), 130)

    def test_tree_ground_anchor_includes_shadow_contact(self):
        self.assertEqual(VillageWorld._tree_ground_y(200, 36), 240)

    def test_sign_collision_covers_supports_and_ground_footprint(self):
        world = VillageWorld.__new__(VillageWorld)
        world.sign_position = (788, 574)
        world.sign_rect = pygame.Rect(794, 594, 24, 24)
        self.assertEqual(world.sign_ground_y, 618)
        self.assertEqual(world.sign_rect.bottom, world.sign_ground_y)
        self.assertTrue(world.sign_rect.collidepoint(798, 615))
        self.assertTrue(world.sign_rect.collidepoint(814, 615))

    def test_hana_collision_bottom_matches_sprite_ground_anchor(self):
        hana = NPC(970, 590, "Hana, Village Keeper", ("Hello",))
        self.assertEqual(hana.rect.bottom, hana.position[1] + 36)

    def test_depth_entries_are_sorted_by_ground_row_then_x(self):
        entries = [
            (140, 80, "lantern", "later"),
            (120, 90, "tree", "right"),
            (120, 30, "sign", "left"),
        ]
        ordered = VillageWorld._sort_depth_entries(entries)
        self.assertEqual([entry[3] for entry in ordered], ["left", "right", "later"])

    def test_entity_in_front_uses_ground_row_not_sprite_top(self):
        self.assertFalse(VillageWorld._is_foreground_depth(200, 200))
        self.assertFalse(VillageWorld._is_foreground_depth(199, 200))
        self.assertTrue(VillageWorld._is_foreground_depth(201, 200))

    def test_lantern_and_shrine_anchors_match_their_drawn_ground_bases(self):
        self.assertEqual(VillageWorld._decoration_ground_y(550, "lantern"), 583)
        self.assertEqual(VillageWorld._decoration_ground_y(710, "shrine"), 754)


if __name__ == "__main__":
    unittest.main()
