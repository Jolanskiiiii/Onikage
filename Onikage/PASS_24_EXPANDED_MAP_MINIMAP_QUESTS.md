# Pass 24 — Expanded World, Circular Minimap, Quest HUD

- Expanded inherited region dimensions to 84 x 60 tiles (2688 x 1920 world pixels).
- Updated save-position bounds to match the expanded world.
- Increased deterministic woodland placement and populated the new outskirts with trees.
- Extended Kagehama's main road across the expanded width and added an eastern woodland trail with a southward bend.
- Replaced the rectangular minimap panel and rectangular camera-viewport outline with a circular, borderless terrain radar in the lower-left corner.
- Added region-aware radar colors, building/NPC/shrine/guardian markers, and an active shrine-quest destination marker.
- Kept the J quest journal and active objective HUD tracker.

Validation: Python compileall passed. Pygame runtime validation is not available in this build environment; test in the Windows game before treating the UI as visually verified.
