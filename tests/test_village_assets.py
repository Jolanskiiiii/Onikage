import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from onikage.art.objects.village import draw_village_object
from onikage.art.tiles.village import make_village_tiles, road_tile_index
from onikage.player import Player
from onikage.village import VillageWorld


class VillageAssetIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.quit()

    def test_feudal_props_are_drawn_from_the_cached_pack_images(self) -> None:
        props = (
            "shrine",
            "barrel",
            "bamboo",
            "paper_lantern",
            "katana_stand",
            "fence",
        )
        for kind in props:
            with self.subTest(kind=kind):
                surface = pygame.Surface((128, 128), pygame.SRCALPHA)
                surface.fill((13, 17, 23, 255))

                draw_village_object(
                    surface, 48, 48, kind, pygame.Vector2(0, 0)
                )

                self.assertGreater(
                    sum(
                        1
                        for y in range(surface.get_height())
                        for x in range(surface.get_width())
                        if surface.get_at((x, y)) != (13, 17, 23, 255)
                    ),
                    0,
                )

    def test_asset_backdrops_are_transparent_in_game(self) -> None:
        background = (13, 17, 23, 255)
        for kind in (
            "shrine",
            "barrel",
            "bamboo",
            "paper_lantern",
            "katana_stand",
            "fence",
        ):
            with self.subTest(kind=kind):
                surface = pygame.Surface((128, 128), pygame.SRCALPHA)
                surface.fill(background)

                draw_village_object(
                    surface, 48, 48, kind, pygame.Vector2(0, 0)
                )

                if kind == "shrine":
                    transparent_corner = (40, 46)
                elif kind == "barrel":
                    transparent_corner = (46, 53)
                else:
                    transparent_corner = (48, 48)
                self.assertEqual(surface.get_at(transparent_corner), background)
                self.assertGreater(
                    sum(
                        1
                        for y in range(surface.get_height())
                        for x in range(surface.get_width())
                        if surface.get_at((x, y)) != background
                    ),
                    0,
                )

    def test_village_draw_keeps_shrine_interaction_and_existing_objects(self) -> None:
        world = VillageWorld()
        prop_kinds = {kind for _, _, kind in world.decorations}

        self.assertIn("shrine", prop_kinds)
        self.assertIn("barrel", prop_kinds)
        self.assertIn("bamboo", prop_kinds)
        self.assertIn("paper_lantern", prop_kinds)
        self.assertIn("katana_stand", prop_kinds)
        self.assertIn("fence", prop_kinds)
        self.assertIn("sakura", prop_kinds)
        self.assertIn("bamboo_grove", prop_kinds)
        self.assertIn("bridge", prop_kinds)
        self.assertIn("stone_lantern", prop_kinds)
        self.assertTrue(world.is_near_shrine((811, 735)))
        self.assertEqual(
            world.interact((811, 735)), "The shrine bells answer your prayer."
        )

        screen = pygame.Surface((1280, 720))
        world.draw(screen, pygame.Vector2(115, 220), player_y=610)
        world.draw_foreground(screen, pygame.Vector2(115, 220), player_y=610)

    def test_connected_road_tiles_and_bridge_route_are_renderable(self) -> None:
        world = VillageWorld()
        grass, road = make_village_tiles(world.TILE_SIZE)

        self.assertGreater(
            len({tuple(tile.get_at((8, 8))) for tile in grass}),
            4,
        )
        self.assertEqual(len(road), 16 * 8)
        self.assertTrue(world._is_road(25, 29))
        self.assertFalse(world._is_road(20, 29))
        self.assertEqual(road_tile_index(15, 7), len(road) - 1)

        bridge_crossing = pygame.Rect(790, 936, 20, 20)
        self.assertFalse(
            any(bridge_crossing.colliderect(obstacle) for obstacle in world.obstacles)
        )
        self.assertTrue(
            any(
                obstacle.colliderect(pygame.Rect(700, 936, 20, 20))
                for obstacle in world.river_obstacles
            )
        )
        self.assertFalse(
            any(
                obstacle.colliderect(building)
                for obstacle in world.river_obstacles
                for building in world.buildings
            )
        )
        player = Player(788, 900)
        player._move_axis(80, 1, world.obstacles)
        self.assertEqual(player.rect.y, 980)

        terrain_screen = pygame.Surface((1280, 720))
        camera = pygame.Vector2(160, 600)
        world._draw_tiles(terrain_screen, camera)
        stream_tile = world.stream_tiles[(16 * 3 + 29) % len(world.stream_tiles)]
        self.assertEqual(terrain_screen.get_at((352, 328)), stream_tile.get_at((0, 0)))

    def test_original_village_art_is_visible_in_the_live_world(self) -> None:
        surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
        background = (11, 14, 17, 255)
        surface.fill(background)
        world = VillageWorld()
        camera = pygame.Vector2(0, 300)
        world.draw(surface, camera, player_y=600)
        world.draw_foreground(surface, camera, player_y=600)

        self.assertGreater(
            sum(
                surface.get_at((x, y)) != background
                for y in range(surface.get_height())
                for x in range(surface.get_width())
            ),
            1280 * 720 // 4,
        )
        bridge_surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
        bridge_surface.fill(background)
        draw_village_object(bridge_surface, 800, 960, "bridge", pygame.Vector2(160, 560))
        self.assertGreater(
            sum(
                bridge_surface.get_at((x, y)) != background
                for y in range(280, 420)
                for x in range(500, 700)
            ),
            300,
        )

    def test_new_solid_prop_collisions_are_present(self) -> None:
        world = VillageWorld()
        existing_objects = [
            *world.buildings,
            *[
                pygame.Rect(x - 9, y + 19, 18, 13)
                for x, y, _ in world.trees
            ],
            world.sign_rect,
            world.villager.rect,
            world.wraith.rect,
            world.shrine_rect,
        ]

        self.assertTrue(
            all(
                obstacle in world.obstacles
                for obstacle in world.prop_obstacles
            )
        )
        self.assertFalse(
            any(
                prop.colliderect(existing)
                for prop in world.prop_obstacles
                for existing in existing_objects
            )
        )


if __name__ == "__main__":
    unittest.main()
