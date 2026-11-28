# ONIKAGE Pass 20 — Distinct Region Layouts and Art Direction

## What changed

This pass replaces the shared rectangular road grid with region-specific route topologies. All regions remain traditional top-down and retain the existing world bounds, camera, player movement, collision system, NPC/guardian hooks, and campaign IDs.

- **Kagehama Village:** market lane with separate shrine approach, residential spurs, garden loop, and southern lane.
- **Burning Village:** broken evacuation route with an offset bend, north escape lane, and southern ally route.
- **Drowned Temple:** narrow causeways, temple-island connections, a north bridge, a southern bridge, and an inner shrine walk.
- **Whispering Cedar Forest:** winding trail with alternating bends and a shrine loop.
- **Fallen Kurogane Castle:** approach road, outer bailey, central court, north gate, and keep avenue.
- **Realm Between Worlds:** fractured diagonal route, cross-platform, and isolated altar ring.

Each region already has a distinct rendering palette and thematic effects in its chapter module; the new route geometry makes those palettes read as different places instead of recolored copies of the same road grid.

## Validation

- `python -m compileall -q .` passed.
- Standalone campaign progression tests passed (4 tests).
- Full Pygame suite cannot run in this build environment because Pygame is not installed. Eleven test modules fail to import for that reason; this is an environment limitation, not a passing runtime test.

## Important limitation

This is a layout/topology redesign pass, not a claim that every map now has a fully hand-painted bespoke tileset. Existing shared building and prop renderers remain in use. Further art integration should replace shared prop silhouettes with region-specific asset sets and should be verified in-game on Windows.
