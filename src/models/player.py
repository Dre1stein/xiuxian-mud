from __future__ import annotations
"""
修仙文字MUD - 数据模型
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class CultivationStage(Enum):
    """修仙境界"""
    QI = "炼气期"
    ZHUJI = "筑基期"
    JINDAN = "金丹期"
    YUANYING = "元婴期"
    YUANSHEN = "元神期"
    HUASHEN = "化神期"
    LIANXU = "炼虚期"
    HETI = "合体期"
    DACHENG = "大乘期"
    DUJIE = "渡劫期"
    ZHENXIAN = "真仙境"
    JINXIAN = "金仙境"
    TAIYI = "太乙境"
    DALUO = "大罗境"


class SectType(Enum):
    """门派类型"""
    QINGYUN = "青云门"
    DANDING = "丹鼎门"
    WANHUA = "万花谷"
    XIAOYAO = "逍遥宗"
    SHUSHAN = "蜀山派"
    KUNLUN = "昆仑派"
    YINYIN = "幻音坊"
    XUEMO = "血魔宗"


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

    # 流派进度
    school_progress: Dict[str, Dict] = field(default_factory=dict)

    # === Long-term Progression Fields ===
    # Playtime tracking
    total_playtime_hours: float = 0.0  # 累计在线时长

    # Offline growth tracking
    last_offline_claim: Optional[str] = None  # ISO datetime string

    # Login streak
    login_streak: int = 0
    last_login_date: Optional[str] = None  # ISO date string

    # Catch-up bonus
    catch_up_bonus: Dict[str, Any] = field(default_factory=lambda: {
        "tier": "none",
        "expires_at": None,
        "instant_claimed": False,
    })

    # Combat stats
    total_combats: int = 0
    total_victories: int = 0

    # Milestone claims
    milestone_claims: Dict[str, str] = field(default_factory=dict)  # milestone_id -> claimed_at

    # Titles
    titles: List[str] = field(default_factory=list)
    active_title: Optional[str] = None

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
    },
    SectType.KUNLUN: {
        "name": "昆仑派",
        "type": SectType.KUNLUN,
        "description": "以剑术、冰系法术、防御著称",
        "cultivation": 999,
        "title": "昆仑仙尊",
        "color": "#00CED1",
        "stats": {
            "attack": 25,
            "defense": 30,
            "ice_damage": 20,
            "ice_resist": 25
        },
        "skills": ["昆仑剑诀", "寒冰神掌", "冰封万里", "昆仑护体"]
    },
    SectType.YINYIN: {
        "name": "幻音坊",
        "type": SectType.YINYIN,
        "description": "以音律、幻术、控制著称",
        "cultivation": 999,
        "title": "幻音仙子",
        "color": "#FF69B4",
        "stats": {
            "magic_attack": 35,
            "crowd_control": 25,
            "charm": 20,
            "spirit": 15
        },
        "skills": ["幻音奏", "迷魂曲", "清心普善", "魔音贯耳"]
    },
    SectType.XUEMO: {
        "name": "血魔宗",
        "type": SectType.XUEMO,
        "description": "以血术、暗杀、爆发著称",
        "cultivation": 999,
        "title": "血魔老祖",
        "color": "#8B0000",
        "stats": {
            "attack": 45,
            "lifesteal": 30,
            "critical_damage": 25,
            "shadow_damage": 20
        },
        "skills": ["血祭", "嗜血术", "血影遁", "血海滔天"]
    }
}


# ============================================================================
# 门派克制关系 - 基于五行相生相克理论
# ============================================================================
#
# 五行对应:
#   青云门 - 风 (风无形，能吹散万物)
#   丹鼎门 - 火 (火烈炎，能熔金炼器)
#   万花谷 - 木 (木生息，能克制污秽)
#   逍遥宗 - 虚 (虚空幻，难以捉摸)
#   蜀山派 - 雷 (雷刚猛，破风斩邪)
#   昆仑派 - 冰 (冰凝静，能封印万物)
#   幻音坊 - 音 (音无形，能惑人心)
#   血魔宗 - 血 (血污秽，以血为力)
#
# 克制关系设计原则:
#   - 每个门派克制2-3个门派，被2-3个门派克制
#   - 优势值 > 1.0 表示攻击方伤害加成
#   - 优势值 < 1.0 表示攻击方伤害减免
#   - 总体保持平衡，无绝对强势门派
#
# 克制矩阵:
#   青云门(风) → 克: 万花谷, 逍遥宗 | 被克: 蜀山派, 昆仑派
#   丹鼎门(火) → 克: 昆仑派, 蜀山派 | 被克: 万花谷, 逍遥宗
#   万花谷(木) → 克: 逍遥宗, 血魔宗 | 被克: 青云门, 丹鼎门
#   逍遥宗(虚) → 克: 丹鼎门, 昆仑派 | 被克: 万花谷, 幻音坊
#   蜀山派(雷) → 克: 青云门, 幻音坊 | 被克: 丹鼎门, 血魔宗
#   昆仑派(冰) → 克: 青云门, 幻音坊 | 被克: 丹鼎门, 逍遥宗
#   幻音坊(音) → 克: 逍遥宗, 血魔宗 | 被克: 蜀山派, 昆仑派
#   血魔宗(血) → 克: 蜀山派, 丹鼎门 | 被克: 万花谷, 幻音坊
# ============================================================================

SECT_ADVANTAGES = {
    # -------------------------------------------------------------------------
    # 青云门(风) 克制关系
    # -------------------------------------------------------------------------
    (SectType.QINGYUN, SectType.WANHUA): 1.25,   # 风吹散木 - 风力强劲时能摧折花木
    (SectType.QINGYUN, SectType.XIAOYAO): 1.20,  # 风破虚 - 风能吹散虚幻之气
    (SectType.QINGYUN, SectType.SHUSHAN): 0.80,  # 雷破风 - 雷电能劈开风障
    (SectType.QINGYUN, SectType.KUNLUN): 0.85,   # 冰封风 - 冰霜能冻结风流

    # -------------------------------------------------------------------------
    # 丹鼎门(火) 克制关系
    # -------------------------------------------------------------------------
    (SectType.DANDING, SectType.KUNLUN): 1.30,   # 火熔冰 - 烈火能融化冰雪
    (SectType.DANDING, SectType.SHUSHAN): 1.20,  # 火炼金 - 火能熔炼金属剑器
    (SectType.DANDING, SectType.WANHUA): 0.80,   # 木生火反噬 - 木虽生火但灵木能吸纳火焰
    (SectType.DANDING, SectType.XIAOYAO): 0.85,  # 虚空无物可燃 - 虚幻之道不受火焰伤害

    # -------------------------------------------------------------------------
    # 万花谷(木) 克制关系
    # -------------------------------------------------------------------------
    (SectType.WANHUA, SectType.XIAOYAO): 1.25,   # 木克虚 - 万物生长能填满虚空
    (SectType.WANHUA, SectType.XUEMO): 1.30,     # 灵药净血 - 灵药能净化血污之术
    (SectType.WANHUA, SectType.QINGYUN): 0.80,   # 风折木 - 狂风能摧折花木
    (SectType.WANHUA, SectType.DANDING): 1.20,   # 木克火吸纳 - 灵木吸纳火焰化为己用

    # -------------------------------------------------------------------------
    # 逍遥宗(虚) 克制关系
    # -------------------------------------------------------------------------
    (SectType.XIAOYAO, SectType.DANDING): 1.25,  # 虚无不受火 - 虚空之道不受火焰伤害
    (SectType.XIAOYAO, SectType.KUNLUN): 1.20,   # 虚不受冰 - 虚幻之道难以被冰封
    (SectType.XIAOYAO, SectType.WANHUA): 0.80,   # 实克虚 - 实体之物能填充虚空
    (SectType.XIAOYAO, SectType.YINYIN): 0.75,   # 音扰虚 - 音律能扰乱虚静之心

    # -------------------------------------------------------------------------
    # 蜀山派(雷) 克制关系
    # -------------------------------------------------------------------------
    (SectType.SHUSHAN, SectType.QINGYUN): 1.25,  # 雷破风 - 雷电能劈开风障
    (SectType.SHUSHAN, SectType.YINYIN): 1.20,   # 雷破音 - 雷鸣之声能震破音律
    (SectType.SHUSHAN, SectType.DANDING): 0.80,  # 火炼金 - 火能熔炼金属剑器
    (SectType.SHUSHAN, SectType.XUEMO): 0.75,    # 血污金 - 血污之术能腐蚀剑器

    # -------------------------------------------------------------------------
    # 昆仑派(冰) 克制关系
    # -------------------------------------------------------------------------
    (SectType.KUNLUN, SectType.QINGYUN): 1.15,   # 冰封风 - 冰霜能冻结风流
    (SectType.KUNLUN, SectType.YINYIN): 1.25,    # 冰静音 - 极寒能冻结音波传播
    (SectType.KUNLUN, SectType.DANDING): 0.70,   # 火熔冰 - 烈火能融化冰雪
    (SectType.KUNLUN, SectType.XIAOYAO): 0.80,   # 虚不受冰 - 虚幻之道难以被冰封

    # -------------------------------------------------------------------------
    # 幻音坊(音) 克制关系
    # -------------------------------------------------------------------------
    (SectType.YINYIN, SectType.XIAOYAO): 1.25,   # 音扰虚 - 音律能扰乱虚静之心
    (SectType.YINYIN, SectType.XUEMO): 1.20,     # 清音净血 - 清心之音能净化血术
    (SectType.YINYIN, SectType.SHUSHAN): 0.80,   # 雷破音 - 雷鸣之声能震破音律
    (SectType.YINYIN, SectType.KUNLUN): 0.75,    # 冰静音 - 极寒能冻结音波传播

    # -------------------------------------------------------------------------
    # 血魔宗(血) 克制关系
    # -------------------------------------------------------------------------
    (SectType.XUEMO, SectType.SHUSHAN): 1.25,    # 血污金 - 血污之术能腐蚀剑器
    (SectType.XUEMO, SectType.DANDING): 1.15,    # 血灭火 - 血海能浇灭烈火
    (SectType.XUEMO, SectType.WANHUA): 0.70,     # 灵药净血 - 灵药能净化血污之术
    (SectType.XUEMO, SectType.YINYIN): 0.80,     # 清音净血 - 清心之音能净化血术
}


def get_sect_advantage(attacker: SectType, defender: SectType) -> float:
    """获取门派克制加成

    Args:
        attacker: 攻击方门派
        defender: 防守方门派

    Returns:
        float: 伤害倍率 (>1.0为优势, <1.0为劣势, =1.0为中立)
    """
    return SECT_ADVANTAGES.get((attacker, defender), 1.0)


def get_sect_counter_info(sect: SectType) -> Dict:
    """获取门派克制信息

    返回指定门派的完整克制关系信息，包括:
    - advantages: 该门派克制的门派列表
    - disadvantages: 克制该门派的门派列表
    - multipliers: 该门派对所有其他门派的伤害倍率

    Args:
        sect: 要查询的门派类型

    Returns:
        Dict: 包含 advantages, disadvantages, multipliers 的字典
    """
    advantages = []      # 该门派克制的目标
    disadvantages = []   # 克制该门派的来源
    multipliers = {}     # 对各门派的伤害倍率

    # 获取所有其他门派
    all_sects = list(SectType)

    for other_sect in all_sects:
        if other_sect == sect:
            continue

        # 获取该门派攻击其他门派的倍率
        attack_mult = SECT_ADVANTAGES.get((sect, other_sect), 1.0)
        multipliers[other_sect] = attack_mult

        # 判断克制关系
        if attack_mult > 1.0:
            advantages.append(other_sect)
        elif attack_mult < 1.0:
            disadvantages.append(other_sect)

    return {
        "sect": sect,
        "sect_name": sect.value,
        "advantages": advantages,
        "advantage_names": [s.value for s in advantages],
        "disadvantages": disadvantages,
        "disadvantage_names": [s.value for s in disadvantages],
        "multipliers": multipliers,
    }


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
