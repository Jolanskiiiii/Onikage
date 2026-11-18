# ONIKAGE Visual Style Guide

## Art direction

**Identity:** restrained, hand-built pixel art for a haunted Japanese historical-fantasy RPG. Prioritize readable silhouettes, layered wood/stone architecture, worn materials, negative space, and ominous lighting over asset quantity or ornate detail.

**Mood:** lonely, dangerous, elegiac. The blood moon and vermilion shrine accents should be rare focal points, balanced by ink-dark cedar silhouettes, weathered timber, cold slate, paper, and pale spirit-blue. Avoid bright greens, saturated medieval-fantasy gold, cheerful village palettes, and unrelated generic monsters.

## Palette tokens

Use these as initial project palette targets, then derive material ramps from actual reference art and chosen licensed assets:

| Role | Starting color | Use |
|---|---|---|
| Ink / deepest silhouette | `#11151B` | Night sky, outlines, deepest shadows |
| Charcoal lacquer | `#20232B` | Samurai armor, UI wells |
| Cedar shadow | `#1B302F` | Forest masses and cold green-black shade |
| Cedar midtone | `#315048` | Select foliage planes, never broad bright grass |
| Aged timber | `#60463B` | House beams, shrines, bridges |
| Weathered wood light | `#927158` | Sparse edge highlights |
| Slate stone | `#46505A` | Temple, castle, road stone |
| Parchment | `#C9B997` | Legible text and paper surfaces |
| Restrained vermilion | `#96383C` | Torii, seal marks, blood-moon accents |
| Old brass | `#B28B52` | UI borders, fittings, rare highlights |
| Spirit blue | `#70CDEB` | Yokai and mask magic; glow must not obscure pixels |
| Mist | `#93A8AA` | Low-opacity layered fog, separated from opaque pixel art |

Keep value separation strong enough that the player, interactables, collision props, and enemies read clearly against dark backgrounds. Reserve the brightest pixels for eyes, steel edges, spirit flames, and selected UI focus.

## Pixel scale and rendering

- Preserve the current 1280x720 window/fullscreen behavior and gameplay coordinate system unless an approved technical change is needed.
- Preserve native pixel-art pixels. Scale sprite sheets only by integer nearest-neighbor factors where possible; never smooth-scale pixel art.
- Inspect native image and cell dimensions first. Do not infer frame dimensions, row ordering, or direction order from a pack name.
- Current world terrain uses 32x32 tiles while the current procedural player source is 16x24, rendered at 32x48. Any new art must be fit by deliberate integer scaling or consistent frame sizing, never arbitrary stretching.
- Keep collision shapes in world coordinates and independent from sprite dimensions. Align obstacle/collision footprints to visible trunks, walls, furniture, and solid ruins.
- Load images once, convert after display initialization where appropriate, cache sheets/frames/tiles, and avoid filesystem or decoding work in the update/draw loop.
- Use explicit animation metadata (native frame size, frame count, row/direction mapping, frame duration, loop/once behavior). Disable an animation mapping until confirmed against the real sheet.

## Scene and lighting principles

- **Mizukawa village:** dark timber, stone paths, shrine ropes, cedar shadows, sparse warm windows, and restrained vermilion. Keep paths and interaction landmarks legible.
- **Village of Ashes:** charred beams, ash drifts, collapsed roofs, ember flecks, and low red light. Avoid reusing the intact village palette without visible damage.
- **Whispering Cedar Forest:** deep layered trunks, root silhouettes, narrow readable paths, blue spirit flames, drifting fog, and sparse falling leaves.
- **Drowned Temple:** cold slate, water reflection bands, submerged offerings, moss, and broken sacred architecture.
- **Fallen Kurogane Castle:** black lacquer and iron, damaged banners, ash, blood-red moonlight, and strong boss silhouettes.
- **Realm Between Worlds:** sparse void composition, broken shrine/castle fragments, floating paper/embers, and the most restrained use of spirit-blue.
- Build lighting from layered transparent overlays or cached light surfaces. Keep pixel edges crisp and keep fog/particles in a separate inexpensive layer.

## Characters, enemies, and UI

- Silhouettes and costume shapes must identify Akihiro, Hana, Jin, Lord Masanori, Yurei, and each yokai before facial details do.
- Do not cast an unrelated generic pack character as a named story figure or major boss. Use original art until a fitting, licensed sprite exists.
- Target consistent feet baselines and world scale for characters. Keep attack/hit/defeat effects readable and brief; don't change combat rules to accommodate animation assets.
- UI: dark lacquer/ink panels, fine parchment text, old-brass rules, restrained vermilion focus, small Japanese-inspired geometric motifs. Preserve existing controls and screen functionality. Text contrast and safe margins take priority over decoration.

## Asset intake checklist

Before approving any external asset: exact source and creator; license text; attribution requirements; file list; image dimensions; native cell dimensions; confirmed animation layout; palette/style fit; integer-scale plan; frame baseline; transparent-pixel behavior; collision footprint; and an in-game screenshot/review. Log accepted assets in `ASSET_CREDITS.md` and `ASSET_INVENTORY.md`.
