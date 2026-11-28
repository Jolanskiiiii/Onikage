import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from onikage.game import Game
from onikage.game_state import GameState


class GameAutosaveTests(unittest.TestCase):
    def make_game(self):
        game = Game.__new__(Game)
        game.state_manager = SimpleNamespace(current_state=GameState.EXPLORATION)
        game.combat = None
        game._autosave_elapsed = 0.0
        game._save_progress = Mock(return_value=True)
        return game

    def test_autosave_occurs_at_thirty_seconds(self):
        game = self.make_game()
        game._update_autosave(29.9)
        game._save_progress.assert_not_called()
        game._update_autosave(0.1)
        game._save_progress.assert_called_once_with()
        self.assertEqual(game._autosave_elapsed, 0.0)

    def test_active_combat_resets_autosave_accumulator(self):
        game = self.make_game()
        game._autosave_elapsed = 22.0
        game.combat = object()
        game._update_autosave(10.0)
        game._save_progress.assert_not_called()
        self.assertEqual(game._autosave_elapsed, 0.0)

    def test_non_exploration_states_do_not_autosave(self):
        game = self.make_game()
        game.state_manager.current_state = GameState.DIALOGUE
        game._update_autosave(90.0)
        game._save_progress.assert_not_called()
        self.assertEqual(game._autosave_elapsed, 0.0)

    def test_negative_delta_time_does_not_reduce_accumulator(self):
        game = self.make_game()
        game._autosave_elapsed = 4.0
        game._update_autosave(-3.0)
        self.assertEqual(game._autosave_elapsed, 4.0)

    def test_save_progress_writes_a_complete_current_snapshot(self):
        game = Game.__new__(Game)
        game.player = SimpleNamespace(
            position=SimpleNamespace(x=420.5, y=610.25),
            direction="left",
            health=83,
            stamina=67.5,
            level=2,
            experience=125,
            rations=2,
            weapon_inventory=SimpleNamespace(to_dict=lambda: {"owned": ["katana"], "equipped": "katana"}),
            mask_manager=SimpleNamespace(to_dict=lambda: {"owned": [], "equipped": None}),
        )
        game.world = SimpleNamespace(wraith=SimpleNamespace(health=41))
        game.quest_log = SimpleNamespace(quests=[])
        game.save_manager = SimpleNamespace(save=Mock())
        game.menu = SimpleNamespace(set_continue_available=Mock())

        self.assertTrue(game._save_progress())
        saved = game.save_manager.save.call_args.args[0]
        self.assertEqual((saved.player_x, saved.player_y), (420.5, 610.25))
        self.assertEqual(saved.health, 83)
        self.assertEqual(saved.wraith_health, 41)
        game.menu.set_continue_available.assert_called_once_with(True, "Continue your journey")

    def test_save_failure_is_reported_without_raising(self):
        game = Game.__new__(Game)
        game.player = SimpleNamespace(
            position=SimpleNamespace(x=10.0, y=20.0),
            direction="down",
            health=100,
            stamina=100.0,
            level=1,
            experience=0,
            rations=3,
            weapon_inventory=SimpleNamespace(to_dict=lambda: {"owned": ["katana"], "equipped": "katana"}),
            mask_manager=SimpleNamespace(to_dict=lambda: {"owned": [], "equipped": None}),
        )
        game.world = SimpleNamespace(wraith=SimpleNamespace(health=72))
        game.quest_log = SimpleNamespace(quests=[])
        game.save_manager = SimpleNamespace(save=Mock(side_effect=OSError("disk full")))
        game.menu = SimpleNamespace(set_continue_available=Mock())
        game.notice = ""
        game.notice_time = 0.0

        self.assertFalse(game._save_progress())
        self.assertIn("Unable to save", game.notice)
        game.menu.set_continue_available.assert_not_called()


if __name__ == "__main__":
    unittest.main()
