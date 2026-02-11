from __future__ import annotations
"""
修仙文字MUD - 数据模型
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime


class CultivationStage(Enum):
    """修仙境界"""
    QI = "炼气期"
    ZHUJI = "筑基期"
    JINDAN = "金丹期"
    YUANYING = "元婴期"
    YUANSHEN = "元神期"


class SectType(Enum):
    """门派类型"""
    QINGYUN = "青云门"
    DANDING = "丹鼎门"
    WANHUA = "万花谷"
    XIAOYAO = "逍遥宗"
    SHUSHAN = "蜀山派"


class ItemQuality(Enum):
    """装备品质"""
    COMMON = "下品"
    RARE = "中品"
    EPIC = "上品"
    LEGENDARY = "极品"
    ARTIFACT = "法宝"


class ItemCategory(Enum):
    """装备类型"""
    WEAPON = "武器"
    ARMOR = "护甲"
    ACCESSORY = "首饰"
    ARTIFACT = "法宝"
    PILL = "丹药"
    SKILL_BOOK = "技能书"


@dataclass
class Player:
    """玩家数据类"""
    player_id: str
    name: str
    level: int = 1
    xp: int = 0
    stage: CultivationStage = CultivationStage.QI
    sect: Optional[SectType] = None
    cultivation: int = 0
    sect_stats: Dict[str, int] = field(default_factory=dict)
    base_stats: Dict[str, int] = field(default_factory=lambda: {
        "attack": 10,
        "defense": 10,
        "speed": 10,
        "agility": 10,
        "constitution": 10,
        "intellect": 10
    })
    spirit_stones: int = 1000
    equipment: List[str] = field(default_factory=list)
    current_map: str = "宗门"
    talents: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)

    # 装备系统 - 槽位管理
    equipment_slots: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "WEAPON": None,
        "HELMET": None,
        "ARMOR": None,
        "GLOVES": None,
        "BOOTS": None,
        "BELT": None,
        "AMULET": None,
        "RING_LEFT": None,
        "RING_RIGHT": None,
        "ARTIFACT": None,
    })

    # 装备背包
    inventory: List[str] = field(default_factory=list)
    inventory_capacity: int = 50

    def get_combat_power(self) -> int:
        """计算战斗力"""
        base = (self.base_stats["attack"] + self.base_stats["speed"] + 
                self.base_stats["agility"] * self.base_stats["intellect"]) // 5
        
        sect_bonus = 0
        if self.sect_stats:
            sect_bonus = sum(self.sect_stats.values())
        
        return base + sect_bonus
    
    def get_stage_requirements(self) -> int:
        """获取境界突破所需经验"""
        if self.stage == CultivationStage.QI:
            return 10000  # 炼气→筑基
        elif self.stage == CultivationStage.ZHUJI:
            return 100000  # 筑基→金丹
        elif self.stage == CultivationStage.JINDAN:
            return 1000000  # 金丹→元婴
        elif self.stage == CultivationStage.YUANYING:
            return 10000000  # 元婴→元神
        return 0

    def equip_item(self, slot: str, equipment_id: str) -> Optional[str]:
        """装备物品到指定槽位，返回被替换的装备ID"""
        old = self.equipment_slots.get(slot)
        self.equipment_slots[slot] = equipment_id
        if equipment_id in self.inventory:
            self.inventory.remove(equipment_id)
        if old and old not in self.inventory:
            self.inventory.append(old)
        return old

    def unequip_item(self, slot: str) -> Optional[str]:
        """卸下指定槽位的装备"""
        equipment_id = self.equipment_slots.get(slot)
        if equipment_id:
            self.equipment_slots[slot] = None
            if len(self.inventory) < self.inventory_capacity:
                self.inventory.append(equipment_id)
                return equipment_id
        return None

    def get_equipped_ids(self) -> List[str]:
        """获取所有已装备的装备ID"""
        return [eid for eid in self.equipment_slots.values() if eid is not None]


@dataclass
class Sect:
    sect_id: str
    name: str
    type: SectType
    description: str
    title: str
    cultivation: int = 999
    color: str = "#FFFFFF"
    skills: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)


@dataclass
class Item:
    """装备/物品数据类"""
    item_id: str
    name: str
    quality: ItemQuality
    category: ItemCategory
    stat_bonuses: Dict[str, int] = field(default_factory=dict)
    description: str = ""
    base_value: int = 10
    price: int = 0

    def get_total_value(self) -> int:
        """获取物品总价值"""
        quality_multipliers = {
            ItemQuality.COMMON: 1.0,
            ItemQuality.RARE: 5.0,
            ItemQuality.EPIC: 20.0,
            ItemQuality.LEGENDARY: 50.0,
            ItemQuality.ARTIFACT: 100.0
        }
        multiplier = quality_multipliers.get(self.quality, 1.0)
        return int(self.base_value * multiplier)


@dataclass
class Monster:
    monster_id: str
    name: str
    level: int
    stage: CultivationStage
    hp: int
    max_hp: int
    attack: int
    defense: int
    sect: Optional[SectType] = None
    sect_stats: Dict[str, int] = field(default_factory=dict)
    experience: int = 0
    drop_rate: float = 0.1
    drops: List[str] = field(default_factory=list)

    def get_combat_power(self) -> int:
        """计算怪物战斗力"""
        return (self.attack + self.defense + self.sect_stats.get("attack", 0))


@dataclass
class Quest:
    """任务数据类"""
    quest_id: str
    type: str
    title: str
    description: str
    objectives: Dict[str, Any] = field(default_factory=dict)
    rewards: Dict[str, Any] = field(default_factory=dict)
    status: str = "available"


@dataclass
class Transaction:
    """交易数据类"""
    transaction_id: str
    player_id: str
    type: str  # "earn", "spend", "trade"
    amount: int
    timestamp: datetime = field(default_factory=datetime.now)


# 门派预设数据
SECT_PRESETS = {
    SectType.QINGYUN: {
        "name": "青云门",
        "type": SectType.QINGYUN,
        "description": "以风清静、逍遥自在著称",
        "cultivation": 999,
        "title": "青云掌门",
        "color": "#87CEEB",
        "stats": {
            "speed": 20,
            "agility": 15,
            "attack": 10,
            "defense": 5
        },
        "skills": ["青云剑诀", "清风诀", "流云步法"]
    },
    SectType.DANDING: {
        "name": "丹鼎门",
        "type": SectType.DANDING,
        "description": "以炼丹、鼎炉、火属性著称",
        "cultivation": 999,
        "title": "丹鼎掌门",
        "color": "#FF5733",
        "stats": {
            "attack": 30,
            "defense": 25,
            "constitution": 15,
            "intellect": 5
        },
        "skills": ["金鼎诀", "三昧真火", "九鼎炼术"]
    },
    SectType.WANHUA: {
        "name": "万花谷",
        "type": SectType.WANHUA,
        "description": "以灵药、医术、疗愈著称",
        "cultivation": 999,
        "title": "万花谷主",
        "color": "#FFB6C1",
        "stats": {
            "constitution": 30,
            "healing": 25,
            "resistance": 20,
            "poison_resist": 20
        },
        "skills": ["万花医术", "炼金散", "回春术", "毒术精通"]
    },
    SectType.XIAOYAO: {
        "name": "逍遥宗",
        "type": SectType.XIAOYAO,
        "description": "以逍遥自在、潇洒不羁著称",
        "cultivation": 999,
        "title": "逍遥仙尊",
        "color": "#9B59B6",
        "stats": {
            "dodge": 25,
            "stealth": 10,
            "movement": 20,
            "crit": 10
        },
        "skills": ["逍遥步", "无相功法", "逍遥心法", "逍遥游身"]
    },
    SectType.SHUSHAN: {
        "name": "蜀山派",
        "type": SectType.SHUSHAN,
        "description": "以武力、坚韧、忠诚著称",
        "cultivation": 999,
        "title": "蜀山掌门",
        "color": "#FFD700",
        "stats": {
            "attack": 40,
            "defense": 20,
            "constitution": 15,
            "crit": 15
        },
        "skills": ["蜀山剑法", "八卦掌法", "金刚伏魔功", "内功心法"]
    }
}


# 门派克制关系
SECT_ADVANTAGES = {
    (SectType.QINGYUN, SectType.WANHUA): 1.2,  # 青云克万花（风克土）
    (SectType.QINGYUN, SectType.XIAOYAO): 1.5,  # 青云克逍遥（风克风？不，应该是顺风）
    (SectType.QINGYUN, SectType.SHUSHAN): 0.8,  # 青云被蜀山克制
    (SectType.QINGYUN, SectType.DANDING): 0.9,  # 青云对丹鼎（风火相生）
}


def get_sect_advantage(attacker: SectType, defender: SectType) -> float:
    """获取门派克制加成"""
    return SECT_ADVANTAGES.get((attacker, defender), 1.0)


if __name__ == "__main__":
    # 测试数据模型
    print("✅ 修仙文字MUD数据模型测试")
    
    # 创建测试玩家
    player = Player(
        player_id="test_player",
        name="逍遥散人",
        level=1,
        xp=0,
        stage=CultivationStage.QI,
        sect=SectType.QINGYUN,
        cultivation=0,
        sect_stats=SECT_PRESETS[SectType.QINGYUN]["stats"],
        spirit_stones=1000,
        current_map="宗门",
        talents=["青云剑诀"]
    )
    
    print(f"✅ 玩家创建成功: {player.name}")
    print(f"   等级: {player.level}")
    print(f"   修为: {player.cultivation}")
    print(f"   门派: {player.sect.value}")
    print(f"   战斗力: {player.get_combat_power()}")
    print(f"   突破条件: {player.get_stage_requirements()} 经验")
