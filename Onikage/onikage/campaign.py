"""Persistent story progression for ONIKAGE's five-mask campaign.

The campaign model is deliberately independent of Pygame so progression can be
validated and tested without opening a game window.
"""
from __future__ import annotations

from dataclasses import dataclass, field


REGION_ORDER = (
    "kagehama_village",
    "burning_village",
    "drowned_temple",
    "cedar_forest",
    "kurogane_castle",
    "realm_between_worlds",
)

GUARDIAN_BY_REGION = {
    "burning_village": "ashen_oni",
    "drowned_temple": "weeping_bride",
    "cedar_forest": "hollow_stalker",
    "kurogane_castle": "fallen_shogun",
    "realm_between_worlds": "nameless_one",
}

VALID_ENDINGS = {"humanity", "curse", "exile"}


# Story fragments are unlocked through the main quest and guardian victories.
# They are stored in CampaignProgress so the journal survives save/load.
LORE_FRAGMENTS = {
    "prologue": {
        "title": "The Exile's Bell",
        "region": "Kagehama Village",
        "text": "For seven winters Akihiro carried no crest and spoke no clan name. On the night he reached Kagehama, the shrine bell rang without a hand to strike it. Hana says the sound is older than the village: it is the warning that the Five Masks have begun to wake.",
    },
    "wrath": {
        "title": "Ash Beneath the Tongue",
        "region": "Burning Village",
        "text": "The Wrath Mask was forged from the last breath of a village burned in a lord's campaign. The Ashen Oni is not the fire's master but its prisoner. The villagers who vanished here were bound to the mask by a promise of vengeance.",
    },
    "grief": {
        "title": "The Bride Below the Water",
        "region": "Drowned Temple",
        "text": "The Weeping Bride once guarded the temple's names of the dead. When the river swallowed the sanctuary, she kept every name in her drowned heart. The Grief Mask feeds on memories that the living refuse to mourn.",
    },
    "fear": {
        "title": "Footsteps in the Cedar Dark",
        "region": "Whispering Cedar Forest",
        "text": "The Hollow Stalker was born from travelers who abandoned one another in the forest. It follows the sound of a frightened heartbeat. The Fear Mask teaches its wearer to vanish, but every shadow-step leaves a memory behind.",
    },
    "pride": {
        "title": "The Shogun's Empty Throne",
        "region": "Fallen Kurogane Castle",
        "text": "The Fallen Shogun wore the Pride Mask to become a ruler no blade could challenge. His court survived as echoes inside the castle walls. The mask preserved his title but devoured the person who once answered to it.",
    },
    "deception": {
        "title": "A Face Without a Name",
        "region": "Realm Between Worlds",
        "text": "The Nameless One is the lie at the center of the Five Masks: the belief that a person can escape grief, fear, wrath and pride by becoming someone else. It offers Akihiro a world where the past never happened.",
    },
    "humanity_ending": {
        "title": "The Bell Rings Once More",
        "region": "Humanity Ending",
        "text": "Akihiro refuses the throne of masks. He seals their power and returns the stolen names to the dead. At dawn, the shrine bell rings by human hands. The curse ends, but the memories remain—and so does the duty to remember.",
    },
    "curse_ending": {
        "title": "Keeper of the Five",
        "region": "Curse Ending",
        "text": "Akihiro takes the masks into himself and becomes their keeper. The villages are quiet, the spirits obey, and no guardian rises again. Yet each night another voice speaks from behind his own. Peace has been purchased with an endless watch.",
    },
    "exile_ending": {
        "title": "Beyond the Northern Pass",
        "region": "Exile Ending",
        "text": "Akihiro carries the masks beyond the known provinces. Kagehama is spared, but the curse travels with him into lands no map records. The bell falls silent. Somewhere far away, another shrine begins to tremble.",
    },
}


@dataclass
class CampaignProgress:
    """Tracks unlocked regions, guardian victories, and the chosen ending."""

    current_region: str = "kagehama_village"
    unlocked_regions: list[str] = field(default_factory=lambda: ["kagehama_village"])
    defeated_guardians: list[str] = field(default_factory=list)
    ending: str | None = None
    lore_unlocked: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if self.current_region not in REGION_ORDER:
            raise ValueError("Unknown campaign region.")
        if not isinstance(self.unlocked_regions, list) or not self.unlocked_regions:
            raise ValueError("Campaign must have at least one unlocked region.")
        if any(region not in REGION_ORDER for region in self.unlocked_regions):
            raise ValueError("Campaign contains an unknown unlocked region.")
        if len(set(self.unlocked_regions)) != len(self.unlocked_regions):
            raise ValueError("Campaign contains duplicate unlocked regions.")
        if "kagehama_village" not in self.unlocked_regions:
            raise ValueError("Kagehama Village must remain unlocked.")
        if self.current_region not in self.unlocked_regions:
            raise ValueError("Current region must be unlocked.")
        if not isinstance(self.defeated_guardians, list):
            raise ValueError("Guardian progress must be a list.")
        valid_guardians = set(GUARDIAN_BY_REGION.values())
        if any(name not in valid_guardians for name in self.defeated_guardians):
            raise ValueError("Campaign contains an unknown guardian.")
        if len(set(self.defeated_guardians)) != len(self.defeated_guardians):
            raise ValueError("Campaign contains duplicate guardian records.")
        if self.ending is not None and self.ending not in VALID_ENDINGS:
            raise ValueError("Campaign ending is invalid.")
        if not isinstance(self.lore_unlocked, list) or any(key not in LORE_FRAGMENTS for key in self.lore_unlocked):
            raise ValueError("Campaign lore records are invalid.")
        if len(set(self.lore_unlocked)) != len(self.lore_unlocked):
            raise ValueError("Campaign contains duplicate lore records.")

    def complete_prologue(self) -> bool:
        """Unlock the first mask chapter after the village shrine quest."""
        if "burning_village" in self.unlocked_regions:
            return False
        self.unlocked_regions.append("burning_village")
        self.unlock_lore("prologue")
        return True

    def unlock_region(self, region: str) -> bool:
        if region not in REGION_ORDER:
            raise ValueError(f"Unknown campaign region: {region}")
        index = REGION_ORDER.index(region)
        if index == 0:
            return False
        required = GUARDIAN_BY_REGION.get(REGION_ORDER[index - 1])
        if required and required not in self.defeated_guardians:
            return False
        if region in self.unlocked_regions:
            return False
        self.unlocked_regions.append(region)
        return True

    def record_guardian_victory(self, guardian: str) -> bool:
        if guardian not in GUARDIAN_BY_REGION.values():
            raise ValueError(f"Unknown guardian: {guardian}")
        if guardian in self.defeated_guardians:
            return False
        region = next(key for key, value in GUARDIAN_BY_REGION.items() if value == guardian)
        # The campaign model records confirmed boss victories independently of
        # travel state. The gameplay layer is responsible for preventing access
        # to a locked boss arena; keeping this model permissive also supports
        # imported/tested progress snapshots and post-battle recovery.
        self.defeated_guardians.append(guardian)
        lore_key = {
            "ashen_oni": "wrath",
            "weeping_bride": "grief",
            "hollow_stalker": "fear",
            "fallen_shogun": "pride",
            "nameless_one": "deception",
        }[guardian]
        self.unlock_lore(lore_key)
        next_index = REGION_ORDER.index(region) + 1
        if next_index < len(REGION_ORDER):
            self.unlock_region(REGION_ORDER[next_index])
        return True

    def travel_to(self, region: str) -> bool:
        if region not in self.unlocked_regions:
            return False
        self.current_region = region
        return True

    def choose_ending(self, ending: str) -> None:
        if ending not in VALID_ENDINGS:
            raise ValueError("Ending must be humanity, curse, or exile.")
        if "nameless_one" not in self.defeated_guardians:
            raise ValueError("The final guardian must be defeated before choosing an ending.")
        self.ending = ending
        self.unlock_lore(f"{ending}_ending")

    def unlock_lore(self, key: str) -> bool:
        if key not in LORE_FRAGMENTS:
            raise ValueError(f"Unknown lore fragment: {key}")
        if key in self.lore_unlocked:
            return False
        self.lore_unlocked.append(key)
        return True

    def to_dict(self) -> dict:
        return {
            "current_region": self.current_region,
            "unlocked_regions": list(self.unlocked_regions),
            "defeated_guardians": list(self.defeated_guardians),
            "ending": self.ending,
            "lore_unlocked": list(self.lore_unlocked),
        }

    @classmethod
    def from_dict(cls, data: object) -> "CampaignProgress":
        if not isinstance(data, dict):
            raise ValueError("Campaign save data must be an object.")
        return cls(
            current_region=data.get("current_region", "kagehama_village"),
            unlocked_regions=data.get("unlocked_regions", ["kagehama_village"]),
            defeated_guardians=data.get("defeated_guardians", []),
            ending=data.get("ending"),
            lore_unlocked=data.get("lore_unlocked", []),
        )
