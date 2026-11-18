import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from onikage.forest import ForestWorld
from onikage.game import Game
from onikage.game_state import GameState
from onikage.combat import BattleSystem
from onikage.quests import QuestStatus
from onikage.save_data import GameSave, SaveError, SaveRepository, SavedQuest
from onikage.village import VillageWorld


def sample_save() -> GameSave:
    return GameSave(
        map_id="village",
        x=755.0,
        y=580.0,
        direction="right",
        health=80,
        stamina=70.5,
        level=1,
        experience=30,
        rations=3,
        village_wraith_health=40,
        forest_wraith_health=84,
        quests=(
            SavedQuest(
                quest_id="village_shrine_prayer",
                title="A Prayer for the Village",
                giver="Hana, Village Keeper",
                description="Offer a prayer.",
                objective="Visit the village shrine.",
                status="ACTIVE",
            ),
        ),
    )


class SaveRepositoryTests(unittest.TestCase):
    def test_round_trip_preserves_campaign_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = SaveRepository(Path(directory) / "save.json")

            repository.save(sample_save())

            self.assertEqual(repository.load(), sample_save())
            self.assertTrue(repository.has_save)

    def test_rejects_unsupported_save_version(self) -> None:
        payload = sample_save().to_dict()
        payload["version"] = 99

        with self.assertRaisesRegex(SaveError, "Unsupported save version"):
            GameSave.from_dict(payload)

    def test_rejects_invalid_player_values(self) -> None:
        payload = sample_save().to_dict()
        player = payload["player"]
        self.assertIsInstance(player, dict)
        player["stamina"] = float("nan")

        with self.assertRaisesRegex(SaveError, "must be finite"):
            GameSave.from_dict(payload)

    def test_rejects_player_outside_map_bounds(self) -> None:
        payload = sample_save().to_dict()
        payload["player"]["x"] = 1792

        with self.assertRaisesRegex(SaveError, "outside the known maps"):
            GameSave.from_dict(payload)

    def test_reports_missing_save(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = SaveRepository(Path(directory) / "missing.json")

            with self.assertRaisesRegex(SaveError, "No save file exists"):
                repository.load()


class GameResumeTests(unittest.TestCase):
    def tearDown(self) -> None:
        pygame.quit()

    def test_continue_restores_forest_player_quest_and_enemy_states(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = SaveRepository(Path(directory) / "save.json")
            game = Game(repository)
            self.assertFalse(game.menu.buttons[1].enabled)
            game._start_new_game()
            self.assertTrue(repository.has_save)
            game.current_map = "forest"
            game.world = ForestWorld()
            game.player.position.update(895, 1120)
            game.player.rect.topleft = (895, 1120)
            game.player.direction = "left"
            game.player.health = 61
            game.player.stamina = 32.5
            game.player.level = 2
            game.player.experience = 75
            game.player.rations = 2
            game.quest_log.accept("village_shrine_prayer")
            game.enemy_health["village"] = 0
            game.world.wraith.health = 47
            self.assertTrue(game._save_game(show_notice=False))

            pygame.quit()
            resumed = Game(repository)
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN))
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
            resumed._handle_events()

            self.assertEqual(resumed.state_manager.current_state, GameState.EXPLORATION)
            self.assertIsInstance(resumed.world, ForestWorld)
            self.assertEqual(resumed.player.position, pygame.Vector2(895, 1120))
            self.assertEqual(resumed.player.direction, "left")
            self.assertEqual(resumed.player.health, 61)
            self.assertEqual(resumed.player.stamina, 32.5)
            self.assertEqual(resumed.player.level, 2)
            self.assertEqual(resumed.player.experience, 75)
            self.assertEqual(resumed.player.rations, 2)
            self.assertEqual(resumed.world.wraith.health, 47)
            self.assertEqual(resumed.enemy_health["village"], 0)
            self.assertEqual(
                resumed.quest_log.get("village_shrine_prayer").status,
                QuestStatus.ACTIVE,
            )
            self.assertTrue(resumed.menu.buttons[1].enabled)
            resumed._draw()

            resumed.state_manager.transition_to(GameState.COMBAT)
            resumed.battle = BattleSystem(resumed.player, resumed.world.wraith)
            resumed.battle.finished = True
            resumed.battle.result = "defeat"
            resumed._handle_combat_event(
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
            )

            self.assertIsInstance(resumed.world, VillageWorld)
            self.assertEqual(resumed.world.wraith.health, 0)
            self.assertNotIn(resumed.world.wraith.rect, resumed.world.obstacles)
            saved_after_retreat = repository.load()
            self.assertEqual(saved_after_retreat.map_id, "village")
            self.assertEqual(saved_after_retreat.village_wraith_health, 0)
            self.assertEqual(saved_after_retreat.forest_wraith_health, 47)


if __name__ == "__main__":
    unittest.main()
