"""Region-specific hand-pixelled environmental props for ONIKAGE."""
from functools import lru_cache
from pathlib import Path
import pygame

ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "region_props"

@lru_cache(maxsize=32)
def sprite(name: str) -> pygame.Surface:
    return pygame.image.load(str(ASSET_DIR / name)).convert_alpha()

def draw_region_set(surface: pygame.Surface, camera: pygame.Vector2, region: str) -> None:
    """Draw bespoke architecture, tree species, lanterns and fence runs per biome."""
    ox, oy = round(camera.x), round(camera.y)
    # Anchors are deliberately off the main traversal lanes and are decorative landmarks.
    layouts = {
      "burning_village": {
        "houses": [(260,245),(1330,760)], "trees": [(170,410),(420,820),(1480,330),(1580,850)],
        "fences": [(480,740),(1120,260)], "lanterns": [(600,470),(1240,650)]},
      "drowned_temple": {
        "houses": [(300,250),(1320,260)], "trees": [(190,430),(1480,430),(400,850)],
        "fences": [(470,760),(1200,760)], "lanterns": [(560,470),(1220,470)]},
      "cedar_forest": {
        "houses": [(260,260),(1380,760)], "trees": [(180,360),(390,280),(520,820),(960,260),(1430,390),(1570,720),(760,900)],
        "fences": [(560,730),(1110,340)], "lanterns": [(650,500),(1270,680)]},
      "kurogane_castle": {
        "houses": [(270,250),(1320,250),(760,820)], "trees": [(160,440),(1510,430),(430,860)],
        "fences": [(470,740),(1160,740)], "lanterns": [(570,470),(1190,470)]},
      "realm_between_worlds": {
        "houses": [(300,250),(1300,760)], "trees": [(180,400),(520,830),(1440,390),(1570,820)],
        "fences": [(520,720),(1120,310)], "lanterns": [(650,470),(1240,650)]},
    }
    data = layouts.get(region)
    if not data: return
    for x,y in data["houses"]:
        surface.blit(sprite(f"{region}_house.png"), (x-ox-64,y-oy-80))
    for i,(x,y) in enumerate(data["trees"]):
        tree = sprite(f"{region}_tree.png")
        if i % 2: tree = pygame.transform.flip(tree, True, False)
        surface.blit(tree, (x-ox-36,y-oy-80))
    for x,y in data["fences"]:
        fence = sprite("kagehama_fence.png")
        if region in ("burning_village","kurogane_castle"):
            fence = pygame.transform.flip(fence, True, False)
        surface.blit(fence, (x-ox,y-oy))
    for x,y in data["lanterns"]:
        surface.blit(sprite("kagehama_lantern.png"), (x-ox-20,y-oy-50))
