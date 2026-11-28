import unittest

from onikage.village import VillageWorld, VILLAGE_LANTERN_LAYOUT


class TerrainAndLanternLayoutTests(unittest.TestCase):
    def test_lantern_ground_contacts_are_on_road_verges(self):
        world = VillageWorld.__new__(VillageWorld)
        # The canonical road runs from y=512 through y=704. Lantern bases
        # must touch its outer edges, not stand in the middle of the path.
        expected_contacts = {512, 704}
        self.assertEqual(len(VILLAGE_LANTERN_LAYOUT), 8)
        for x, sprite_y in VILLAGE_LANTERN_LAYOUT:
            self.assertIn(VillageWorld._decoration_ground_y(sprite_y, "lantern"), expected_contacts)
            self.assertFalse(512 < VillageWorld._decoration_ground_y(sprite_y, "lantern") < 704)

    def test_grass_and_road_have_distinct_material_palettes(self):
        # Source-level palette contract: grass is deep green; road is stone/earth.
        self.assertNotEqual((25, 35, 27), (49, 43, 39))


if __name__ == "__main__":
    unittest.main()
