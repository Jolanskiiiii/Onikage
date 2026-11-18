# ONIKAGE: The Curse of the Fallen Samurai

## Project progress

**Current milestone:** A playable village exploration slice with one NPC quest and one turn-based battle encounter.

**Development environment:** Python 3.13.17 and Pygame 2.6.1.

**Visual pass 1:** The samurai and starting village now use a consistent, cached pixel-art style. Existing gameplay and the main menu remain unchanged.

**Visual pass 2:** Dialogue, quest, inventory, and battle screens now share a framed pixel-art UI; the wraith and battle samurai reuse cached sprites.

**Visual pass 3:** Procedural assets are organized by category under `onikage/art/`; village effects, village props, battle environments, and font setup now have dedicated modules.

**Licensed asset pass:** The game UI now bundles DotGothic16, a Japanese-capable pixel font under the SIL Open Font License. Kenney's CC0 RPG Audio pack supplies footsteps, interface sounds, and battle effects. The pack's generic medieval tiles were reviewed but not used because they conflict with the Japanese village's visual style.

## What works

- The existing main menu is preserved. New Game enters the village; Settings, Exit, and F11 fullscreen remain available.
- The player has four facing directions and three cached frames per direction, with a two-step walk cycle and a pixel-art katana.
- The player can walk in four directions, sprint, and collide with village scenery.
- Movement, inventory/journal panels, and successful battle actions have sound effects.
- A camera follows the player through a tile-based village with houses, roads, trees, a shrine, lanterns, mist, and a notice sign.
- Village terrain uses deterministic, cached grass and road tiles; buildings and cedar trees have layered pixel details, shadows, and depth-aware occlusion.
- Lanterns cast cached warm light, ambient fireflies drift through the village, and the mist overlay is reused instead of allocated every frame.
- Press **E** near the sign to read it. Talk to Hana to hear dialogue and accept or decline her shrine request.
- Complete “A Prayer for the Village” by interacting with the shrine. Press **J** to open the quest journal.
- Press **I** to see the travel pack.
- A wraith encounter can be started by facing the wraith and pressing **E** or **C**.
- Battle commands: **1 Attack**, **2 Defend**, **3 Spirit Slash**, **4 Use Ration**. Arrow keys or **W/S** change the selected command; **Enter** confirms. Press Enter after victory or defeat to return to the village.
- Victory grants experience. Defeat returns the player to the village with some health restored.

## Run the game

In the VS Code terminal, run:

```powershell
& 'C:\Users\olmoj\AppData\Local\Python\pythoncore-3.13-64\python.exe' 'C:\Users\olmoj\OneDrive\Desktop\Onikage\main.py'
```

## Code layout

- `main.py` starts the game.
- `onikage/game.py` runs the main loop, handles input, and draws screens.
- `onikage/game_state.py` manages screen transitions.
- `onikage/main_menu.py` contains the existing main menu; it has not been redesigned.
- `onikage/player.py` defines the player and movement.
- `onikage/village.py` defines the starting village and its interactable objects.
- `onikage/art/characters/player_sprite.py` builds the cached directional samurai frames.
- `onikage/art/enemies/wraith_sprite.py` builds the animated wraith frames.
- `onikage/art/environments/battlefield.py` draws the layered combat backdrop.
- `onikage/art/environments/village.py` draws houses and cedar trees.
- `onikage/art/objects/village.py` draws village props and cached lantern lighting.
- `onikage/art/effects/village_atmosphere.py` draws reusable mist and firefly effects.
- `onikage/art/tiles/village.py` builds the cached village ground tiles.
- `onikage/art/ui/panels.py` contains reusable interface frames, portraits, and item icons.
- `onikage/art/fonts/ui.py` loads the bundled DotGothic16 font for the game interface.
- `onikage/art/audio/sfx.py` loads and plays the bundled sound effects.
- `onikage/assets/fonts/` contains DotGothic16 and its SIL Open Font License.
- `onikage/assets/audio/` contains selected Kenney RPG Audio effects and its CC0 license.
- `onikage/npc.py` defines village characters.
- `onikage/dialogue.py` presents NPC conversations.
- `onikage/quests.py` tracks quest status.
- `onikage/enemy.py` defines the village wraith.
- `onikage/combat.py` resolves turn-based battle commands.

## Verification

Python source compilation and headless rendering checks passed for exploration, dialogue, inventory, quest offer/journal, battle screens, player and wraith sprites, and item icons. Regression checks passed for menu-to-game state transitions, dialogue and quest controls, inventory/journal controls, combat commands, victory rewards, and returning to the village. The player has also confirmed the village, quest, and battle run on their PC.

## Asset sources and licenses

- [DotGothic16](https://fonts.google.com/specimen/DotGothic16) by the DotGothic16 Project Authors, bundled under SIL Open Font License 1.1. The license is in `onikage/assets/fonts/OFL.txt`.
- [RPG Audio](https://kenney.nl/assets/rpg-audio) by Kenney, selected sound effects bundled under CC0. The license is in `onikage/assets/audio/LICENSE.txt`.
- No external sprite sheets were added: the reviewed generic RPG pack did not fit the game's Japanese village art direction.

## Not implemented yet

- Five collectible masks and their abilities/consequences.
- Additional maps and transitions to a full forest area.
- More NPCs, enemies, quests, bosses, and battle skills.
- Persistent leveling/stat progression beyond the current experience reward.
- A fully interactive equipment and inventory system.
- Save/load and Continue.
- External sprite sheets and final assets for the remaining characters, enemies, UI, audio, and music.
- Background music and additional ambient sound effects.
- Dedicated automated tests in the project.
