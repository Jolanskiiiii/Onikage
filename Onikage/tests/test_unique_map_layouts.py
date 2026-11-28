"""Source-level checks for region-specific route topology (no Pygame required)."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1] / "onikage"


class UniqueMapLayoutTests(unittest.TestCase):
    def _road_method(self, filename, class_name):
        tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
        method = next(n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "_is_road")
        return ast.dump(method, include_attributes=False)

    def test_each_region_has_its_own_route_topology(self):
        layouts = {
            "village": self._road_method("village.py", "VillageWorld"),
            "burning": self._road_method("burning_village.py", "BurningVillageWorld"),
            "temple": self._road_method("drowned_temple.py", "DrownedTempleWorld"),
            "forest": self._road_method("cedar_forest.py", "CedarForestWorld"),
            "castle": self._road_method("kurogane_castle.py", "KuroganeCastleWorld"),
            "realm": self._road_method("realm_between_worlds.py", "RealmBetweenWorlds"),
        }
        self.assertEqual(len(set(layouts.values())), len(layouts))


if __name__ == "__main__":
    unittest.main()
