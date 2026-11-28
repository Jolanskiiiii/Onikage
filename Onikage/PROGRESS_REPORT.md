# ONIKAGE: The Curse of the Fallen Samurai

## Project progress

**Current milestone:** A playable village exploration slice with one NPC quest and an integrated real-time combat encounter. Pass 8 adds versioned save reliability, recovery, autosave, and removal of obsolete isometric-only files.

**Weapon system:** Akihiro starts with a Katana. Dual Blades are the existing shrine quest reward, a Yari can be found through village exploration, and the Odachi is earned from the existing wraith encounter. Weapon profiles define separate combo, heavy attack, timing, range, stamina, speed, and hitbox data; ownership and equipment are saved.

**Cursed masks:** Pass 9 aligns the system with the five story masks: Wrath, Grief, Fear, Pride, and Deception. New acquisition is tied to each mask's own guardian-defeated progression flag. Existing legacy ownership and upgrade progress are migrated and preserved.

**Development environment:** Python 3.13.17 and Pygame 2.6.1.

**Visual pass 1:** The samurai and starting village now use a consistent, cached pixel-art style. Existing gameplay and the main menu remain unchanged.

**Visual pass 2:** Dialogue, quest, inventory, and battle screens now share a framed pixel-art UI; the wraith and battle samurai reuse cached sprites.

**Visual pass 3:** Procedural assets are organized by category under `onikage/art/`; village effects, village props, battle environments, and font setup now have dedicated modules. The game retains a traditional top-down camera and rectangular world layout.

**Visual pass 4:** Refined the existing top-down pixel art without changing world geometry or gameplay: added small armor/cloth details to Akihiro, expanded the wraith idle animation to four subtle frames, and added deterministic grass/path accents plus roof, cedar-branch, and bark highlights. Sprite output sizes and existing rendering entry points remain compatible.

**Visual pass 5 — Akihiro sprite upgrade:** Replaced Akihiro's procedural placeholder with a bundled transparent 4-direction sprite sheet (down, up, left, right), including idle and walking poses. The sprite is larger than the collision body but its feet remain anchored to the existing ground position; movement speed, collision rectangles, camera, combat, and top-down perspective are unchanged.

**Licensed asset pass:** The game UI now bundles DotGothic16, a Japanese-capable pixel font under the SIL Open Font License. Kenney's CC0 RPG Audio pack supplies footsteps, interface sounds, and battle effects. The pack's generic medieval tiles were reviewed but not used because they conflict with the Japanese village's visual style.

## Perspective correction

The project is intentionally a traditional 2D top-down RPG. Player WASD/arrow movement follows the screen axes directly, diagonal movement is normalized, mouse attacks use direct screen-space aim, target assistance compares screen-space directions, and Shadow Step movement follows the same top-down direction vectors. Existing rectangular world coordinates, camera, collision rectangles, and Y-based foreground occlusion are retained. The unused isometric projection module and isometric-only tests were removed in Pass 8; no production code imported them.

## What works

- The existing main menu is preserved. New Game enters the village; Settings, Exit, and F11 fullscreen remain available.
- Akihiro uses a bundled 4-direction transparent sprite sheet with cached idle and two-step walking frames; the sprite's feet remain aligned to the existing collision ground point.
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
- The five canonical mask definitions now match the story document's regions, guardians, and named abilities.
- Inferno Slash uses the charged heavy-attack system; Spirit Veil grants temporary protection; Shadow Step performs a collision-aware dash; Heavenly Judgment performs a timed counter; Phantom Double creates a temporary decoy target for enemy attacks.
- New masks are awarded only through the matching guardian progression API. The current starting village shrine and Wraith milestones do not award regional masks; the regional guardian chapters are not yet implemented.

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
- `onikage/art/characters/player_sprite.py` loads and caches Akihiro's directional frames from `onikage/art/characters/akihiro_sheet.png`.
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
- `onikage/save_data.py` persists versioned player progress, weapon state, quest progress, wraith health, and mask ownership/upgrades to the local JSON save; it validates data, retains a previous-save backup, and can recover from a corrupted primary save.
- `onikage/masks.py` defines the five story masks, guardian-gated acquisition, abilities, energy, switching, upgrades, and legacy save migration.

## Pass 8 — Save reliability and top-down project cleanup

- New journeys write an initial save immediately.
- Active exploration autosaves every 30 seconds when no encounter is active.
- The game saves before pausing to the menu, before menu exit, and on the window-close event.
- Saves remain JSON and use atomic temporary-file replacement.
- A valid previous save is retained as `save.json.bak`; a corrupt or invalid primary save can recover from that backup.
- Save data uses schema version 2 and continues to load existing version 1 saves.
- Player position, direction, statistics, and progression values are validated before a save is accepted.
- Save failures are reported in-game rather than terminating the game loop.
- Removed `onikage/isometric.py` and `tests/test_isometric.py`; the production source had no imports of the isometric module.
- Added `tests/test_save_data.py` and `tests/test_game_saving.py` for save validation, migration, backup recovery, autosave timing, and snapshot persistence.

## Verification

The project source is syntax-compiled after Pass 8. All 16 new Pass 8 unit tests passed in isolated runners using a lightweight Pygame import stub (the tests exercise save logic and autosave integration without rendering). Pygame 2.6.1 is not installed in the patch-generation environment and package installation is unavailable, so the game-integration tests, full existing test suite, and actual game launch could not be executed here. Run the full test suite in the user's Python 3.13.17/Pygame 2.6.1 environment before treating runtime verification as complete.

Existing automated tests cover damage, duplicate hit prevention, attack frame timing, combo windows, top-down mouse attack direction, movement during light/heavy attacks, weapon profiles/switching/persistence, and mask progression, switching, energy, cooldowns, effects, upgrades, and persistence. Pass 8 adds save validation, version migration, backup recovery, autosave timing, and snapshot persistence coverage. Pass 9 adds story identity, guardian gating, legacy mask-ID migration, and combat ability tests for the five canonical masks.

## Asset sources and licenses

- [DotGothic16](https://fonts.google.com/specimen/DotGothic16) by the DotGothic16 Project Authors, bundled under SIL Open Font License 1.1. The license is in `onikage/assets/fonts/OFL.txt`.
- [RPG Audio](https://kenney.nl/assets/rpg-audio) by Kenney, selected sound effects bundled under CC0. The license is in `onikage/assets/audio/LICENSE.txt`.
- `onikage/art/characters/akihiro_sheet.png` is a custom-generated sprite sheet created for this project; no third-party character sprite pack was imported.

## Not implemented yet

- Additional maps and transitions to a full forest area.
- More NPCs, enemies, quests, bosses, and battle skills.
- Persistent leveling/stat progression beyond the current experience reward.
- A fully interactive equipment and inventory system.
- Matching sprite sheets for Hana, other NPCs, and additional enemies; their current visuals remain procedural.
- Additional environment variations and tile art; current village graphics remain largely procedural.
- Additional UI icon art, background music, and ambient sound variations.
- Background music and additional ambient sound effects.
- Additional enemy types, attack animation art, and combat tuning.


## Pass 9 — Five Mask Story Alignment

- Canonical mask identities are Wrath, Grief, Fear, Pride, and Deception. Each definition includes its story region, guardian, and ability name.
- Active abilities: Inferno Slash (charged flame-infused heavy strike), Spirit Veil (temporary protection), Shadow Step (collision-aware directional dash), Heavenly Judgment (timed counter), and Phantom Double (temporary combat decoy that attracts enemy attacks and can be destroyed or expire).
- Mask acquisition now requires the matching `guardian_defeated:<mask-id>` progression flag. Village shrine and Wraith milestones no longer award regional masks, and the starting village no longer contains mask pickups.
- Legacy identifiers (`shadows`, `tengu`, `suffering`, and `onikage`) migrate to `grief`, `fear`, `pride`, and `deception`. Existing ownership, equipped mask, upgrade levels, energy, and upgrade tokens are retained. Previously owned masks are grandfathered so migration does not remove progress; new acquisitions remain guardian-gated.
- The regional maps and five guardian encounters are not part of Pass 9. This pass provides the canonical definitions and guardian-award API for those future chapters.

**Pass 9 verification:** All project Python files pass syntax compilation. Four Pygame-independent story/migration tests pass. Pygame 2.6.1 is unavailable in the patch-generation environment, so Pygame-dependent combat tests, the full suite, and a game launch could not be executed here. Run `python -m unittest discover -s tests -v` in the local Python 3.13.17/Pygame 2.6.1 environment.


## Pass 11 — Village visual refinement (focused polish)

- Corrected the broad lantern ground-glow placement so its center aligns with the lantern's lower plinth/contact row. The small flame halo remains unchanged.
- Increased the number and slight depth variation of deterministic grass/road boundary flecks. The road tile footprint, road collision assumptions, map layout, and tile coordinates are unchanged.
- Added restrained timber pegs and grain marks to the notice board without changing its position, collision rectangle, or ground anchor.
- Preserved the existing shrine, barrel, cedar-tree, and accepted ground-shadow treatments. No scenery positions or gameplay interactions were changed.

**Pass 11 verification:** Updated source files pass Python syntax compilation. Pygame is not installed in the patch-generation environment, so visual rendering and the Pygame-dependent unit suite could not be run here. Run the full local test suite and inspect the village in-game before accepting the visual changes.


## Pass 11.1 — Village Visual Polish Fixes

- Replaced the Wraith's hard, oversized oval with a compact feathered ground shadow.
- Added a restrained two-pixel hover motion while keeping the shadow fixed to the ground anchor.
- Increased lantern flame and ground illumination slightly, with a smaller ground-light footprint aligned to the lantern base.
- Tightened the signboard contact shadow and added separate support-foot contact marks.
- Increased deterministic road-edge fleck depth by a few pixels without changing road dimensions or collision.
- Updated visual tests for the revised lantern ground-glow footprint.

Validation: Python source compilation passed. Pygame is not installed in the build environment, so runtime rendering and Pygame-dependent unit tests require local verification.


## Pass 13 — Burning Village Guardian Progression (2026-11-27)

- Fixed the Burning Village boss reward path: defeating the Ashen Oni now records the correct guardian victory and awards the Mask of Wrath / Inferno Slash rather than incorrectly granting the ordinary Wraith rewards.
- The campaign progression record unlocks the Drowned Temple after the Ashen Oni victory.
- A save loaded in the Burning Village preserves the Ashen Oni's defeated state.
- Ordinary Kagehama Wraith rewards remain unchanged.

**Validation:** All source files pass `compileall`. Pygame-dependent tests and live rendering could not be run in this environment because Pygame is unavailable and package installation is blocked. **Important:** the Drowned Temple and remaining guardian chapters are not yet playable; this is a progression fix, not completion of the five-mask campaign.

## Pass 15 — Drowned Temple playable chapter foundation (2026-11-28)

- Added `onikage/drowned_temple.py` with a distinct flooded temple palette, animated water channels, drifting mist, and the Weeping Bride guardian encounter.
- Added travel from the Burning Village to the Drowned Temple after the Ashen Oni victory; the return route leads back to the Burning Village.
- Added save/continue world restoration for the Drowned Temple and persistent guardian defeat handling.
- Added Weeping Bride victory progression: Grief Mask / Spirit Veil reward and Cedar Forest unlock.
- Preserved the existing top-down camera, tile size, player collision pipeline, and realtime combat implementation.
- Validation: Python syntax compilation passed. Full Pygame runtime and test suite could not be run in this build environment because Pygame is not installed. Run `py -3.13 -m unittest discover -s tests -v` on the Windows development machine.

**Remaining campaign work:** Cedar Forest, Kurogane Castle, Realm Between Worlds, final guardian/ending sequence, and full playtesting. This build is not yet the complete game.
