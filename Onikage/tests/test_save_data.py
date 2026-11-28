import json
import tempfile
import unittest
from pathlib import Path

from onikage.save_data import SAVE_VERSION, SaveData, SaveManager


class SaveDataValidationTests(unittest.TestCase):
    def test_new_saves_use_current_version(self):
        self.assertEqual(SaveData().to_dict()["version"], SAVE_VERSION)

    def test_version_one_save_remains_loadable(self):
        legacy = SaveData().to_dict()
        legacy["version"] = 1
        loaded = SaveData.from_dict(legacy)
        self.assertEqual(loaded.version, SAVE_VERSION)
        self.assertEqual(loaded.player_x, 755.0)

    def test_unsupported_version_is_rejected(self):
        data = SaveData().to_dict()
        data["version"] = SAVE_VERSION + 1
        with self.assertRaises(ValueError):
            SaveData.from_dict(data)

    def test_non_finite_or_out_of_world_coordinates_are_rejected(self):
        for coordinate in (float("nan"), float("inf"), -1, 99999):
            with self.subTest(coordinate=coordinate):
                data = SaveData().to_dict()
                data["player"]["x"] = coordinate
                with self.assertRaises(ValueError):
                    SaveData.from_dict(data)

    def test_diagonal_facing_is_preserved_and_invalid_direction_is_rejected(self):
        data = SaveData().to_dict()
        data["player"]["direction"] = "up-left"
        self.assertEqual(SaveData.from_dict(data).direction, "up-left")

        data["player"]["direction"] = "northwest"
        with self.assertRaises(ValueError):
            SaveData.from_dict(data)

        data = SaveData().to_dict()
        data["player"]["stamina"] = -5
        with self.assertRaises(ValueError):
            SaveData.from_dict(data)


class SaveManagerRecoveryTests(unittest.TestCase):
    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = SaveManager(Path(directory) / "save.json")
            self.assertIsNone(manager.load())
            manager.save(SaveData(player_x=321.5, player_y=456.25))
            loaded = manager.load()
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.player_x, 321.5)
            self.assertEqual(manager.last_load_source, "primary")

    def test_second_save_keeps_previous_valid_save_as_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = SaveManager(Path(directory) / "save.json")
            manager.save(SaveData(player_x=100))
            manager.save(SaveData(player_x=200))
            backup = json.loads(manager.backup_path.read_text(encoding="utf-8"))
            self.assertEqual(backup["player"]["x"], 100)
            self.assertEqual(manager.load().player_x, 200)

    def test_corrupt_primary_recovers_from_backup_and_restores_primary(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = SaveManager(Path(directory) / "save.json")
            manager.save(SaveData(player_x=100))
            manager.save(SaveData(player_x=200))
            manager.path.write_text("{broken json", encoding="utf-8")

            loaded = manager.load()

            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.player_x, 100)
            self.assertEqual(manager.last_load_source, "backup")
            restored = json.loads(manager.path.read_text(encoding="utf-8"))
            self.assertEqual(restored["player"]["x"], 100)

    def test_invalid_primary_and_backup_return_no_save(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = SaveManager(Path(directory) / "save.json")
            manager.path.parent.mkdir(parents=True, exist_ok=True)
            manager.path.write_text("not json", encoding="utf-8")
            manager.backup_path.write_text("also not json", encoding="utf-8")
            self.assertIsNone(manager.load())
            self.assertFalse(manager.exists)

    def test_invalid_in_memory_save_is_not_written(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = SaveManager(Path(directory) / "save.json")
            with self.assertRaises(ValueError):
                manager.save(SaveData(player_x=float("nan")))
            self.assertFalse(manager.path.exists())


if __name__ == "__main__":
    unittest.main()
