# ONIKAGE Pass 21 — Region Art Integration

This pass replaces the procedural noise-only ground renderers in the five non-Kagehama chapters with dedicated pixel-art terrain atlases (four ground variants and four path variants per region):

- Burning Village: ash, charcoal soil, ember-scored evacuation paving.
- Drowned Temple: dark flooded ground, water ripples, submerged stone causeways.
- Whispering Cedar Forest: deep moss, fern flecks, root-scored trails.
- Fallen Kurogane Castle: basalt masonry, cracked flagstone, muted crimson stone accents.
- Realm Between Worlds: void ground, spectral flecks, fractured violet pathways.

The renderer uses a spatial hash for stable, non-checkerboard variation. Drowned Temple now has a dedicated sanctuary structure. The Temple, Forest, Castle, and Realm no longer render Kagehama's generic wooden houses. Burning Village retains settlement shells but uses its own scorched atlas and charred overlays.

Kagehama remains on its existing village tileset. Player/NPC/enemy sprites and collision/navigation systems are unchanged.

Validation performed: Python syntax compilation and archive integrity. Pygame runtime rendering has not been verified in this environment because Pygame is unavailable.
