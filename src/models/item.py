from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict
from enum import Enum


class ItemQuality(Enum):
    COMMON = "下品"
    RARE = "中品"
    EPIC = "上品"
    LEGENDARY = "极品"
    ARTIFACT = "法宝"


class ItemCategory(Enum):
    WEAPON = "武器"
    ARMOR = "护甲"
    ACCESSORY = "首饰"
    ARTIFACT = "法宝"
    PILL = "丹药"
    SKILL_BOOK = "技能书"


@dataclass
class Item:
    item_id: str
    name: str
    quality: ItemQuality
    category: ItemCategory
    stat_bonuses: Dict[str, int] = field(default_factory=dict)
    description: str = ""
    base_value: int = 10
    price: int = 0

    def get_total_value(self) -> int:
        quality_multipliers = {
            ItemQuality.COMMON: 1.0,
            ItemQuality.RARE: 5.0,
            ItemQuality.EPIC: 20.0,
            ItemQuality.LEGENDARY: 50.0,
            ItemQuality.ARTIFACT: 100.0
        }
        multiplier = quality_multipliers.get(self.quality, 1.0)
        return int(self.base_value * multiplier)
