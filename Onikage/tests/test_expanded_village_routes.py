"""Regression checks for the expanded Kagehama route network."""
import ast
from functools import lru_cache
from pathlib import Path
import unittest


class ExpandedVillageRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).parents[1] / "onikage" / "village.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        world = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "VillageWorld")
        method = next(node for node in world.body if isinstance(node, ast.FunctionDef) and node.name == "_is_road")
        module = ast.Module(body=[method], type_ignores=[])
        namespace = {"lru_cache": lru_cache}
        exec(compile(module, str(source), "exec"), namespace)
        cls.is_road = staticmethod(namespace["_is_road"])

    def test_expanded_world_has_connected_routes_into_outer_districts(self):
        roads = {(x, y) for y in range(60) for x in range(84) if self.is_road(x, y)}
        self.assertGreater(len(roads), 850)
        self.assertTrue(any(x >= 75 and y >= 45 for x, y in roads))
        self.assertTrue(any(x <= 8 and y >= 40 for x, y in roads))
        unseen = set(roads)
        components = 0
        while unseen:
            components += 1
            stack = [unseen.pop()]
            while stack:
                x, y = stack.pop()
                for neighbor in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        stack.append(neighbor)
        self.assertEqual(components, 1)

    def test_route_function_stays_inside_world_bounds(self):
        self.assertFalse(self.is_road(-20, -20))
        self.assertFalse(self.is_road(120, 90))


if __name__ == "__main__":
    unittest.main()
