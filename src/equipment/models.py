"""
Equipment System Core Data Models
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class Rarity(Enum):
    """9-level rarity system"""
    NORMAL = ("普通", "#FFFFFF", 1.0, 0)
    MAGIC = ("魔法", "#4169E1", 1.2, 1)
    RARE = ("稀有", "#FFD700", 1.5, 2)
    EPIC = ("史诗", "#A020F0", 2.0, 3)
    LEGENDARY = ("传说", "#FFA500", 3.0, 4)
    MYTHIC = ("神话", "#00CED1", 4.0, 5)
    DIVINE = ("神圣", "#FF69B4", 5.0, 6)
    IMMORTAL = ("不朽", "#FF0000", 7.0, 7)
    ETHEREAL = ("虚无", "#00FF00", 10.0, 8)

    def __init__(self, display_name: str, color: str, multiplier: float, affix_slots: int):
        self.display_name = display_name
        self.color = color
        self.multiplier = multiplier
        self.affix_slots = affix_slots


class EquipmentSlot(Enum):
    """Equipment slot types"""
    WEAPON = "武器"
    HELMET = "头盔"
    ARMOR = "护甲"
    GLOVES = "护手"
    BOOTS = "战靴"
    BELT = "腰带"
    AMULET = "项链"
    RING_LEFT = "左戒指"
    RING_RIGHT = "右戒指"
    ARTIFACT = "法宝"


class AffixType(Enum):
    """Affix types"""
    PREFIX = "前缀"
    SUFFIX = "后缀"
    LEGENDARY = "传奇"


class AffixInstance(BaseModel):
    """Affix instance on equipment"""
    model_config = ConfigDict(use_enum_values=False)

    affix_id: str
    name: str
    affix_type: AffixType
    stat_modifiers: Dict[str, float] = Field(default_factory=dict)
    flat_modifiers: Dict[str, int] = Field(default_factory=dict)
    roll_value: float = 1.0  # 0.5-1.0 roll value


class Equipment(BaseModel):
    """Equipment instance"""
    model_config = ConfigDict(use_enum_values=False)

    equipment_id: str = Field(default_factory=lambda: f"equip_{datetime.now().strftime('%Y%m%d%H%M%S%f')}")
    base_item_id: str
    name: str
    slot: EquipmentSlot
    rarity: Rarity
    level: int = 1
    enhance_level: int = 0

    base_stats: Dict[str, int] = Field(default_factory=dict)
    affixes: List[AffixInstance] = Field(default_factory=list)

    set_id: Optional[str] = None
    set_name: Optional[str] = None

    identified: bool = True
    locked: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

    def get_display_name(self) -> str:
        """Get full display name"""
        prefix_names = [a.name for a in self.affixes if a.affix_type == AffixType.PREFIX]
        suffix_names = [a.name for a in self.affixes if a.affix_type == AffixType.SUFFIX]

        parts = []
        if prefix_names:
            parts.append("".join(prefix_names))
        parts.append(self.name)
        if suffix_names:
            parts.append("之" + "".join(suffix_names))

        enhance_str = f"+{self.enhance_level}" if self.enhance_level > 0 else ""
        return f"{''.join(parts)}{enhance_str}"


class EquipmentSetBonus(BaseModel):
    """Set bonus definition"""
    model_config = ConfigDict(use_enum_values=False)

    pieces_required: int
    description: str
    stat_modifiers: Dict[str, float] = Field(default_factory=dict)
    flat_modifiers: Dict[str, int] = Field(default_factory=dict)
    special_effects: List[str] = Field(default_factory=list)


class EquipmentSet(BaseModel):
    """Equipment set definition"""
    model_config = ConfigDict(use_enum_values=False)

    set_id: str
    name: str
    description: str
    pieces: List[str]
    bonuses: List[EquipmentSetBonus]


class PlayerEquipment(BaseModel):
    """Player equipment management"""
    model_config = ConfigDict(use_enum_values=False)

    player_id: str
    slots: Dict[str, Optional[str]] = Field(default_factory=lambda: {
        slot.name: None for slot in EquipmentSlot
    })
    inventory: List[str] = Field(default_factory=list)

    def equip(self, slot: EquipmentSlot, equipment_id: str) -> Optional[str]:
        """Equip item, returns replaced equipment ID"""
        old_equipment = self.slots.get(slot.name)
        self.slots[slot.name] = equipment_id
        if equipment_id in self.inventory:
            self.inventory.remove(equipment_id)
        if old_equipment and old_equipment not in self.inventory:
            self.inventory.append(old_equipment)
        return old_equipment

    def unequip(self, slot: EquipmentSlot) -> Optional[str]:
        """Unequip item from slot"""
        equipment_id = self.slots.get(slot.name)
        if equipment_id:
            self.slots[slot.name] = None
            self.inventory.append(equipment_id)
        return equipment_id


# Old quality to new rarity mapping
QUALITY_TO_RARITY_MAP = {
    "COMMON": Rarity.NORMAL,
    "RARE": Rarity.MAGIC,
    "EPIC": Rarity.RARE,
    "LEGENDARY": Rarity.EPIC,
    "ARTIFACT": Rarity.LEGENDARY,
}


def rarity_from_string(name: str) -> Rarity:
    """Get rarity from string name"""
    for rarity in Rarity:
        if rarity.name == name or rarity.display_name == name:
            return rarity
    return Rarity.NORMAL
