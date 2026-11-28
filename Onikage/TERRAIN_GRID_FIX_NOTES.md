# Terrain grid fix — 27 November 2026

## Root cause
The grass/road atlas had pale, opaque border pixels baked into the 32×32 cells, plus transparent edge pixels. The previous regression test only searched for near-white pixels above a higher threshold and therefore missed the grey-white outlines. The renderer was not drawing a debug grid.

## Changes
- Cleaned the 14 grass cells (atlas row 0) and 14 road cells (atlas row 1), removing pale outline pixels from their 2px perimeter.
- Extruded each tile's nearest opaque interior edge color into transparent perimeter pixels to prevent background-colored seams when adjacent tiles are blitted.
- Replaced the weak atlas test with a perimeter regression test for both rows.
- No map coordinates, collision, player movement, quests, NPCs, combat, or camera behavior were changed.

## Verification
- Atlas dimensions remain 448×128 (14 columns × 4 rows, 32px cells).
- Static image validation confirms all perimeter pixels in the used grass/road rows are opaque and contain no pale neutral outline pixels.
- Full Pygame test suite was not executable in this Linux build container because Pygame is not installed here. Run `py -3.13 -m unittest discover -s tests -v` on the Windows development machine after extracting.
