# ONIKAGE Visual Asset Project Progress

**Current stage:** Visual Milestone 4 — the starting village visual overhaul is implemented and verified; other region redesign remains in progress.

## Milestones

| Milestone | Status | Evidence / exit criteria |
|---|---|---|
| 1. Audit repository and available art packs | **Complete** | `ASSET_INVENTORY.md` lists the baseline and inspects four downloaded packs. Japanese Village & Villagers is still missing. |
| 2. Asset pipeline and pack previews | **Complete** | Cached image/sheet loading, nearest-neighbor scaling, animation playback, and tile-map drawing are implemented and tested. Samples from all four packs appear in a standalone preview; Feudal props also feed the live village renderer. |
| 3. Player and NPC redesign | **Not started** | Approved/licensed character assets; four-direction idle/walk integrated; movement, collision, dialogue, and interactions regression-tested. |
| 4. Environment redesign | **In progress — starting village overhauled** | The live village now has varied dark ground, connected irregular dirt roads, distinctive house treatments, original sakura/bamboo/bridge art, and a stream crossing. Real `Game` renderer screenshots were inspected at the spawn and bridge; 21 tests pass, including shrine interaction, bridge passage, and river collisions. Forest and remaining regions still need their own passes. |
| 5. Enemies and combat | **Not started** | Fitting licensed or original enemies; no unrelated asset assigned to a named boss; combat commands and outcomes verified. |
| 6. UI and atmosphere | **Not started** | Existing controls retained; readable lacquer/parchment UI and performant tested effects. |
| 7. Final verification | **Not started** | Complete screen/map/interaction/combat/audio regression pass and performance review on Python 3.13.17/Pygame 2.6.1. |

## Current asset scope and blockers

- Curated copies from Feudal Japan Props Vol.1, Ninja Adventure, 0x72 Dungeon, and Pixel Crawler Exterior are in `onikage/assets/artpacks/`. Feudal props are used in the live starting village; the other three packs remain preview-only. Japanese Village & Villagers remains unavailable.
- Feudal Japan Props Vol.1 is integrated into the starting village. The other three packs remain preview-only; a separate approval is required before further asset integration.
- Ninja Adventure walk-row directions and Pixel Crawler tileset grid remain unverified; previews intentionally do not assign or slice them.
- The asset pack named `New folder` is an unrelated Unity game distribution/asset-bundle tree; it has no established visual-pack license and is excluded.
- Existing bundled third-party assets are the DotGothic16 font (OFL 1.1) and selected Kenney RPG Audio effects (CC0), not visual sprite packs.
- See `ASSET_INVENTORY.md` for detailed findings, `ASSET_CREDITS.md` for verified credits and terms, and `VISUAL_STYLE_GUIDE.md` for the target direction.

## Verified village overhaul

- Ground is rendered from cached 32x32 original tiles: 16 grass variants, 128 connected dirt-road variants, and four stream patterns.
- The road network follows winding, connected routes from the north gate through the village, shrine, and south bridge. Solid river banks leave a narrow walkable bridge crossing.
- Existing houses have differentiated palettes/facade details. Original pixel art adds three sakura variations, bamboo groves, and a wooden bridge; licensed Feudal Japan props remain in use.
- Captured and inspected the actual game renderer at spawn and at the bridge using Python 3.13.17/Pygame 2.6.1. The renderings show the new road/ground work, visible stream, and bridge. Controls, shrine, NPC, and combat systems are unchanged.
- Verification: `py -3.13 -m unittest discover -s tests -v` — 21 tests passed.

## Next action

Continue the environment pass with the forest and remaining regions; preserve existing interaction/collision behavior and verify each live scene before marking it complete.

No full-game visual redesign is claimed complete.
