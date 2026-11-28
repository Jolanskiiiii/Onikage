# Kagehama Graphics Asset Update

This build adds an original coordinated environment atlas generated for ONIKAGE.

## Integrated in this build
- `onikage/art/tiles/kagehama_ground_atlas.png`: 14 grass/moss ground variants and 14 earth/cobblestone ground variants, used by `make_village_tiles()` at the game's 32px tile scale.
- `onikage/art/tiles/kagehama_props_atlas.png`: transparent-background prop reference atlas included with the project for the next scenery integration pass.
- `tests/test_environment_atlas.py`: verifies both graphics assets are packaged.

## Important scope note
The ground atlas is integrated into Kagehama's terrain renderer. The prop atlas is packaged but not yet wired into the existing tree, house, lantern, and shrine drawing functions. Those objects still use the existing renderers in this build. This is an incremental real asset integration, not yet a complete match to the visual concept.

## Runtime
The atlas loader uses `pygame.image.load(...).convert_alpha()` during `VillageWorld` construction, after the game display is initialized. If the atlas is unavailable, the existing procedural fallback remains available.
