# ONIKAGE: The Curse of the Fallen Samurai

## Project progress

**Current milestone:** A playable village exploration slice with one NPC quest and an integrated real-time combat encounter.

**Weapon system:** Akihiro starts with a Katana. Dual Blades are the existing shrine quest reward, a Yari can be found through village exploration, and the Odachi is earned from the existing wraith encounter. Weapon profiles define separate combo, heavy attack, timing, range, stamina, speed, and hitbox data; ownership and equipment are saved.

**Cursed masks:** Shadows and Wrath are gated by the existing shrine quest and wraith encounter; Tengu and Suffering are gated exploration discoveries, and Onikage awakens after the four lesser masks are acquired. Each mask has a passive, energy-based active ability, cooldown, upgrade path, and transition feedback.

**Development environment:** Python 3.13.17 and Pygame 2.6.1.

**Visual pass 1:** The samurai and starting village now use a consistent, cached pixel-art style. Existing gameplay and the main menu remain unchanged.

**Visual pass 2:** Dialogue, quest, inventory, and battle screens now share a framed pixel-art UI; the wraith and battle samurai reuse cached sprites.

**Visual pass 3:** Procedural assets are organized by category under `onikage/art/`; village effects, village props, battle environments, and font setup now have dedicated modules. The game retains a traditional top-down camera and rectangular world layout.

**Licensed asset pass:** The game UI now bundles DotGothic16, a Japanese-capable pixel font under the SIL Open Font License. Kenney's CC0 RPG Audio pack supplies footsteps, interface sounds, and battle effects. The pack's generic medieval tiles were reviewed but not used because they conflict with the Japanese village's visual style.

## Perspective correction

The project is intentionally a traditional 2D top-down RPG. The unused isometric projection module and isometric-only tests have been removed. Player WASD/arrow movement now follows the screen axes directly, diagonal movement is normalized, mouse attacks use direct screen-space aim, target assistance compares screen-space directions, and mask dash movement follows the same top-down direction vectors. Existing rectangular world coordinates, camera, collision rectangles, and Y-based foreground occlusion are retained.

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
- A wraith encounter can be started by facing it and pressing **E** or **C**, or by attacking it with the mouse while nearby.
- **Left mouse** performs a directional light attack with a three-hit combo; **right mouse** performs a stamina-costing heavy strike. Both aim directly in screen-space top-down directions and include startup, active, and recovery timing.
- Combat updates in the village loop. Light attacks allow movement; heavy attacks lock movement during their active strike. Hits use per-attack hitboxes, enemy hurtboxes, knockback, hit reactions, and brief hit-stop.
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
- `onikage/directions.py` provides normalized top-down movement, eight-way facing, and interaction directions.
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
- `onikage/combat.py` contains health, damage, hitbox/hurtbox, attack timing, combo, target assist, and real-time encounter components.
- `onikage/weapons.py` defines the weapon catalog and player weapon inventory.
- `onikage/save_data.py` persists player progress, weapon state, and mask ownership/upgrades to the local JSON save.
- `onikage/masks.py` defines mask abilities, progression gates, energy, switching, upgrades, and mask save state.

## Verification

Automated tests cover damage, duplicate hit prevention, attack frame timing, combo windows, top-down mouse attack direction, movement during light/heavy attacks, weapon profiles/switching/persistence, and mask progression, switching, energy, cooldowns, effects, upgrades, and persistence.

## Asset sources and licenses

- [DotGothic16](https://fonts.google.com/specimen/DotGothic16) by the DotGothic16 Project Authors, bundled under SIL Open Font License 1.1. The license is in `onikage/assets/fonts/OFL.txt`.
- [RPG Audio](https://kenney.nl/assets/rpg-audio) by Kenney, selected sound effects bundled under CC0. The license is in `onikage/assets/audio/LICENSE.txt`.
- No external sprite sheets were added: the reviewed generic RPG pack did not fit the game's Japanese village art direction.

## Not implemented yet

- Additional maps and transitions to a full forest area.
- More NPCs, enemies, quests, bosses, and battle skills.
- Persistent leveling/stat progression beyond the current experience reward.
- A fully interactive equipment and inventory system.
- External sprite sheets and final assets for the remaining characters, enemies, UI, audio, and music.
- Background music and additional ambient sound effects.
- Additional enemy types, attack animation art, and combat tuning.
