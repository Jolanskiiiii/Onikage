# ONIKAGE Pass 22 — Distinct Environmental Props

## Implemented
- Added 14 transparent pixel-art prop assets under `onikage/art/assets/region_props/`.
- Kagehama now uses a dedicated warm timber house, leafy maple/sakura-style canopy, revised tōrō lantern and cedar fence sprites.
- Burning Village, Drowned Temple, Whispering Cedar Forest, Kurogane Castle and Realm Between Worlds now draw separate biome-specific house/landmark silhouettes, tree species, fence runs and lantern props.
- Region props are anchored in world coordinates and camera-offset during rendering.
- Existing collision and interaction systems were not modified; the new decorative prop runs are visual-only.

## Validation
- `python -m compileall -q .` passed.
- Pygame runtime rendering and in-game visual validation were not available in this environment because Pygame is not installed.
- Please test each region in the Windows Pygame runtime. Decorative sprites may need positional adjustments based on actual camera framing and collision footprints.
