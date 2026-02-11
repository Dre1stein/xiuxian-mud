# 暗黑风格装备系统设计文档

## 概述

本设计借鉴《暗黑破坏神》系列的装备系统精髓，结合修仙世界观，打造一个极具深度和可玩性的装备系统。

---

## 一、装备稀有度体系

### 1.1 稀有度等级（由低到高）

| 稀有度 | 名称 | 颜色代码 | 词缀数量 | 特性 |
|--------|------|----------|----------|------|
| 0 | 破损 | #808080 (灰) | 0-1 | 基础属性-20%，无特殊效果 |
| 1 | 普通 | #FFFFFF (白) | 0-2 | 基础属性 |
| 2 | 优秀 | #1EFF00 (绿) | 2-3 | 基础属性+10% |
| 3 | 稀有 | #0070DD (蓝) | 3-4 | 基础属性+25%，随机词缀 |
| 4 | 史诗 | #A335EE (紫) | 4-5 | 基础属性+50%，固定词缀+随机词缀 |
| 5 | 传说 | #FF8000 (橙) | 5-6 | 基础属性+100%，独特词缀 |
| 6 | 神话 | #E6CC80 (金) | 6-8 | 基础属性+200%，多独特词缀 |
| 7 | 远古 | #00FFFF (青) | 8-10 | 基础属性+300%，远古词缀 |
| 8 | 灵魂 | #FF00FF (粉) | 10+ | 基础属性+500%，灵魂绑定特性 |

### 1.2 稀有度掉落概率

```python
DROP_RATES = {
    "破损": 0.30,      # 30%
    "普通": 0.25,      # 25%
    "优秀": 0.20,      # 20%
    "稀有": 0.12,      # 12%
    "史诗": 0.07,      # 7%
    "传说": 0.035,     # 3.5%
    "神话": 0.015,     # 1.5%
    "远古": 0.008,     # 0.8%
    "灵魂": 0.002,     # 0.2%
}
```

---

## 二、词缀系统（Affix System）

### 2.1 词缀类型

#### 前缀词缀（Prefix）- 进攻型
```python
PREFIX_AFFIXES = {
    # 基础属性类
    "锋利": {"attack": (5, 50)},           # 攻击力+5-50
    "破甲": {"armor_penetration": (3, 30)}, # 护甲穿透+3-30
    "疾风": {"attack_speed": (1, 15)},      # 攻击速度+1-15%
    "致命": {"crit_rate": (1, 20)},         # 暴击率+1-20%
    "毁灭": {"crit_damage": (10, 100)},     # 暴击伤害+10-100%
    "穿透": {"pierce": (5, 50)},            # 穿透+5-50

    # 元素属性类
    "烈焰": {"fire_damage": (10, 100)},     # 火焰伤害+10-100
    "寒冰": {"ice_damage": (10, 100)},      # 冰霜伤害+10-100
    "雷电": {"lightning_damage": (10, 100)}, # 雷电伤害+10-100
    "毒素": {"poison_damage": (5, 50)},     # 毒素伤害+5-50/秒
    "神圣": {"holy_damage": (10, 100)},     # 神圣伤害+10-100
    "暗影": {"shadow_damage": (10, 100)},   # 暗影伤害+10-100

    # 修仙特殊类
    "聚灵": {"spirit_power": (10, 100)},    # 灵力+10-100
    "凝气": {"qi_max": (50, 500)},          # 真气上限+50-500
    "破魔": {"demon_damage": (20, 200)},    # 对妖魔伤害+20-200%
    "诛仙": {"immortal_damage": (10, 100)}, # 对仙人伤害+10-100%
}
```

#### 后缀词缀（Suffix）- 防御/辅助型
```python
SUFFIX_AFFIXES = {
    # 基础防御类
    "坚固": {"defense": (5, 50)},           # 防御力+5-50
    "厚甲": {"armor": (10, 100)},           # 护甲+10-100
    "闪避": {"dodge": (1, 15)},             # 闪避率+1-15%
    "格挡": {"block": (1, 20)},             # 格挡率+1-20%
    "坚韧": {"tenacity": (5, 50)},          # 韧性+5-50

    # 生命恢复类
    "生命": {"hp_max": (50, 500)},          # 生命上限+50-500
    "再生": {"hp_regen": (5, 50)},          # 生命回复+5-50/秒
    "吸血": {"life_steal": (1, 15)},        # 生命偷取+1-15%
    "愈合": {"healing_bonus": (5, 50)},     # 治疗效果+5-50%

    # 修仙特殊类
    "辟邪": {"curse_resist": (10, 100)},    # 诅咒抗性+10-100
    "护体": {"damage_reduce": (1, 20)},     # 伤害减免+1-20%
    "长生": {"life_extend": (100, 1000)},   # 寿命+100-1000年
    "道心": {"cultivation_speed": (5, 50)}, # 修炼速度+5-50%
}
```

### 2.2 词缀数值范围

词缀数值根据装备等级动态计算：

```python
def calculate_affix_value(base_range: tuple, item_level: int, quality: int) -> int:
    """
    计算词缀实际数值
    base_range: 基础范围 (min, max)
    item_level: 装备等级 (1-999)
    quality: 装备品质 (0-8)
    """
    min_val, max_val = base_range

    # 等级加成
    level_mult = 1 + (item_level / 100)

    # 品质加成
    quality_mult = 1 + (quality * 0.2)

    # 计算最终范围
    final_min = int(min_val * level_mult * quality_mult)
    final_max = int(max_val * level_mult * quality_mult)

    # 随机取值
    return random.randint(final_min, final_max)
```

### 2.3 特殊词缀（传奇/神话专属）

```python
LEGENDARY_AFFIXES = {
    # 传奇词缀（传说及以上）
    "嗜血狂魔": {
        "description": "每次攻击恢复造成伤害的3-8%",
        "effect": {"life_steal_percent": (3, 8)},
        "rarity_required": 5
    },
    "毁灭之怒": {
        "description": "暴击时造成300-500%暴击伤害",
        "effect": {"crit_damage_multiplier": (3.0, 5.0)},
        "rarity_required": 5
    },
    "不灭之魂": {
        "description": "死亡时有10-30%几率复活并恢复50%生命",
        "effect": {"resurrect_chance": (10, 30)},
        "rarity_required": 5
    },
    "时空裂隙": {
        "description": "攻击有5-15%几率触发时空裂隙，造成200%伤害",
        "effect": {"rift_chance": (5, 15), "rift_damage": 2.0},
        "rarity_required": 5
    },

    # 神话词缀（神话及以上）
    "天道眷顾": {
        "description": "所有修炼速度提升50-100%",
        "effect": {"all_cultivation_speed": (50, 100)},
        "rarity_required": 6
    },
    "九天玄雷": {
        "description": "攻击召唤九天玄雷，对范围内敌人造成200-500%雷电伤害",
        "effect": {"thunder_storm_damage": (2.0, 5.0), "thunder_radius": 3},
        "rarity_required": 6
    },
    "不死金身": {
        "description": "受到致命伤害时，有50-80%几率化为金身，免疫该伤害",
        "effect": {"golden_body_chance": (50, 80)},
        "rarity_required": 6
    },

    # 远古诗缀（远古及以上）
    "远古之力": {
        "description": "所有属性提升100-200%",
        "effect": {"all_stats_multiplier": (1.0, 2.0)},
        "rarity_required": 7
    },
    "毁灭领主": {
        "description": "每秒对周围敌人造成装备攻击力50-100%的伤害",
        "effect": {"aura_damage_percent": (50, 100), "aura_radius": 5},
        "rarity_required": 7
    },

    # 灵魂词缀（灵魂专属）
    "灵魂共鸣": {
        "description": "装备与其灵魂共鸣，属性随玩家等级成长",
        "effect": {"soul_scaling": True, "soul_growth_rate": 0.1},
        "rarity_required": 8
    },
}
```

---

## 三、套装系统

### 3.1 套装结构

```python
@dataclass
class SetBonus:
    pieces_required: int          # 所需件数
    bonuses: Dict[str, Any]       # 奖励属性
    special_effect: Optional[str] # 特殊效果描述

@dataclass
class EquipmentSet:
    set_id: str                   # 套装ID
    name: str                     # 套装名称
    description: str              # 套装描述
    lore: str                     # 套装背景故事
    pieces: List[str]             # 包含的装备ID列表
    bonuses: List[SetBonus]       # 套装奖励（2件/4件/6件）
    rarity_required: int          # 最低稀有度要求
```

### 3.2 套装示例

#### 套装1：青云剑仙套装（青云门专属）
```python
QINGYUN_SET = {
    "set_id": "qingyun_sword_immortal",
    "name": "青云剑仙套装",
    "description": "传说中青云门开山祖师留下的至宝",
    "lore": """
        千年前，青云祖师飞升之际，将其一身修为凝聚成这套装备。
        传说集齐此套装者，可领悟青云剑意，剑气纵横三万里。
    """,
    "pieces": [
        "qingyun_sword",      # 青云剑
        "qingyun_robe",       # 青云法袍
        "qingyun_crown",      # 青云冠
        "qingyun_boots",      # 青云履
        "qingyun_ring",       # 青云戒
        "qingyun_amulet",     # 青云玉佩
    ],
    "bonuses": [
        SetBonus(2, {"attack": 100, "speed": 50}, None),
        SetBonus(4, {"crit_rate": 15, "crit_damage": 50}, "青云剑气：攻击有20%几率释放剑气波"),
        SetBonus(6, {"all_stats": 200}, "青云剑意：所有剑系技能伤害提升100%"),
    ],
    "rarity_required": 5,  # 传说
}
```

#### 套装2：幽冥死神套装（通用）
```python
YOUMING_SET = {
    "set_id": "youming_death_god",
    "name": "幽冥死神套装",
    "description": "来自幽冥界的死亡气息",
    "lore": """
        这套装备曾被一位堕落的仙人所穿戴，他在幽冥界称霸千年。
        套装中残留着他的死亡意志，穿戴者将承受无尽的噩梦...
    """,
    "pieces": [
        "death_scythe",       # 死神镰刀
        "death_armor",        # 死神铠甲
        "death_helm",         # 死神头盔
        "death_gauntlets",    # 死神护手
        "death_boots",        # 死神战靴
        "death_cloak",        # 死神斗篷
    ],
    "bonuses": [
        SetBonus(2, {"shadow_damage": 150, "life_steal": 10}, None),
        SetBonus(4, {"crit_damage": 100, "poison_damage": 100}, "死亡凝视：暴击时附加200%毒素伤害"),
        SetBonus(6, {"immortal_damage": 300}, "死神降临：死亡时对周围敌人造成1000%暗影伤害并复活"),
    ],
    "rarity_required": 6,  # 神话
}
```

#### 套装3：九天雷神套装（丹鼎门专属）
```python
LEISHEN_SET = {
    "set_id": "jiutian_thunder_god",
    "name": "九天雷神套装",
    "description": "蕴含九天玄雷之力的神器",
    "lore": """
        天劫降临时，有人不从天意，逆天改命。
        这套装备便是从天劫雷霆中淬炼而生的逆天之器。
    """,
    "pieces": [
        "thunder_hammer",     # 雷神之锤
        "thunder_armor",      # 雷神铠甲
        "thunder_crown",      # 雷神之冠
        "thunder_wings",      # 雷神之翼
        "thunder_ring",       # 雷神之戒
        "thunder_belt",       # 雷神腰带
    ],
    "bonuses": [
        SetBonus(2, {"lightning_damage": 200, "attack_speed": 20}, None),
        SetBonus(4, {"crit_rate": 25, "lightning_damage": 300}, "雷神之怒：攻击有30%几率召唤雷霆"),
        SetBonus(6, {"all_damage": 500}, "九天雷劫：释放雷霆风暴，每秒对周围敌人造成500%雷电伤害"),
    ],
    "rarity_required": 6,  # 神话
}
```

### 3.3 套装数量规划

| 阶段 | 套装数量 | 类型 |
|------|---------|------|
| 初期 | 10套 | 各门派专属 + 通用 |
| 中期 | 20套 | 秘境套装 + BOSS套装 |
| 后期 | 50+套 | 活动套装 + 限时套装 |

---

## 四、装备类型与槽位

### 4.1 装备槽位

```python
EQUIPMENT_SLOTS = {
    # 主要装备槽（13个）
    "main_hand": "主手武器",
    "off_hand": "副手武器/盾牌",
    "head": "头部",
    "chest": "胸甲",
    "shoulder": "护肩",
    "hands": "手套",
    "waist": "腰带",
    "legs": "护腿",
    "feet": "鞋子",
    "neck": "项链",
    "ring1": "戒指1",
    "ring2": "戒指2",
    "artifact": "法宝",

    # 时装槽位（不影响属性）
    "costume": "时装",
    "weapon_skin": "武器外观",
}
```

### 4.2 武器类型

```python
WEAPON_TYPES = {
    # 单手武器
    "sword": {"name": "剑", "attack_base": 100, "attack_speed": 1.2, "range": 2},
    "blade": {"name": "刀", "attack_base": 120, "attack_speed": 1.0, "range": 2},
    "spear": {"name": "枪", "attack_base": 90, "attack_speed": 1.1, "range": 3},
    "dagger": {"name": "匕首", "attack_base": 60, "attack_speed": 1.8, "range": 1},
    "axe": {"name": "斧", "attack_base": 140, "attack_speed": 0.8, "range": 2},
    "fan": {"name": "扇", "attack_base": 70, "attack_speed": 1.5, "range": 2},

    # 双手武器
    "greatsword": {"name": "巨剑", "attack_base": 200, "attack_speed": 0.7, "range": 3, "two_handed": True},
    "staff": {"name": "法杖", "attack_base": 80, "attack_speed": 1.0, "range": 4, "two_handed": True, "magic_bonus": 50},
    "bow": {"name": "弓", "attack_base": 100, "attack_speed": 1.3, "range": 10, "two_handed": True},

    # 修仙特殊武器
    "flying_sword": {"name": "飞剑", "attack_base": 150, "attack_speed": 1.4, "range": 15, "two_handed": True},
    "spirit_mirror": {"name": "灵镜", "attack_base": 60, "attack_speed": 1.2, "range": 5, "magic_bonus": 80},
    "dharma_wheel": {"name": "法轮", "attack_base": 100, "attack_speed": 1.5, "range": 8},

    # 副手装备
    "shield": {"name": "盾牌", "defense_base": 100, "block_chance": 15},
    "talisman": {"name": "符箓", "magic_defense": 50, "skill_cooldown": -5},
    "offhand_orb": {"name": "灵珠", "spirit_power": 80, "mana_regen": 10},
}
```

### 4.3 防具类型

```python
ARMOR_TYPES = {
    # 头部
    "helmet": {"name": "头盔", "defense_base": 50, "slots": ["head"]},
    "crown": {"name": "冠冕", "defense_base": 30, "magic_bonus": 20, "slots": ["head"]},
    "hood": {"name": "兜帽", "defense_base": 20, "stealth": 10, "slots": ["head"]},

    # 胸甲
    "plate": {"name": "板甲", "defense_base": 150, "weight": 50, "slots": ["chest"]},
    "chainmail": {"name": "锁甲", "defense_base": 100, "weight": 30, "slots": ["chest"]},
    "robe": {"name": "法袍", "defense_base": 50, "magic_bonus": 30, "weight": 10, "slots": ["chest"]},
    "leather": {"name": "皮甲", "defense_base": 80, "agility": 15, "weight": 20, "slots": ["chest"]},

    # 护肩
    "pauldrons": {"name": "肩甲", "defense_base": 40, "slots": ["shoulder"]},
    "cape": {"name": "披风", "defense_base": 20, "stealth": 5, "slots": ["shoulder"]},

    # 手套
    "gauntlets": {"name": "护手", "defense_base": 30, "attack_speed": 5, "slots": ["hands"]},
    "bracers": {"name": "护腕", "defense_base": 25, "cast_speed": 5, "slots": ["hands"]},

    # 腰带
    "belt": {"name": "腰带", "defense_base": 25, "inventory_bonus": 10, "slots": ["waist"]},
    "sash": {"name": "束带", "defense_base": 15, "agility": 10, "slots": ["waist"]},

    # 护腿
    "greaves": {"name": "护腿", "defense_base": 60, "slots": ["legs"]},
    "pants": {"name": "长裤", "defense_base": 40, "agility": 5, "slots": ["legs"]},

    # 鞋子
    "boots": {"name": "战靴", "defense_base": 35, "movement_speed": 10, "slots": ["feet"]},
    "sandals": {"name": "草鞋", "defense_base": 10, "movement_speed": 20, "slots": ["feet"]},
}
```

---

## 五、宝石镶嵌系统

### 5.1 宝石类型

```python
GEM_TYPES = {
    # 基础宝石
    "ruby": {
        "name": "红宝石",
        "color": "#FF0000",
        "slots": ["weapon", "ring", "amulet"],
        "effects": {
            1: {"attack": 10},
            2: {"attack": 25, "fire_damage": 20},
            3: {"attack": 50, "fire_damage": 50},
            4: {"attack": 100, "fire_damage": 100, "fire_resist": 20},
            5: {"attack": 200, "fire_damage": 200, "fire_resist": 40},
        }
    },
    "sapphire": {
        "name": "蓝宝石",
        "color": "#0000FF",
        "slots": ["helmet", "chest", "shield"],
        "effects": {
            1: {"defense": 10},
            2: {"defense": 25, "ice_damage": 20},
            3: {"defense": 50, "ice_damage": 50},
            4: {"defense": 100, "ice_damage": 100, "ice_resist": 20},
            5: {"defense": 200, "ice_damage": 200, "ice_resist": 40},
        }
    },
    "emerald": {
        "name": "祖母绿",
        "color": "#00FF00",
        "slots": ["boots", "pants", "belt"],
        "effects": {
            1: {"agility": 10},
            2: {"agility": 25, "poison_damage": 20},
            3: {"agility": 50, "poison_damage": 50},
            4: {"agility": 100, "poison_damage": 100, "poison_resist": 20},
            5: {"agility": 200, "poison_damage": 200, "poison_resist": 40},
        }
    },
    "amethyst": {
        "name": "紫水晶",
        "color": "#9900FF",
        "slots": ["helmet", "ring", "amulet"],
        "effects": {
            1: {"spirit_power": 10},
            2: {"spirit_power": 25, "mana_max": 100},
            3: {"spirit_power": 50, "mana_max": 250},
            4: {"spirit_power": 100, "mana_max": 500, "mana_regen": 10},
            5: {"spirit_power": 200, "mana_max": 1000, "mana_regen": 25},
        }
    },
    "diamond": {
        "name": "钻石",
        "color": "#FFFFFF",
        "slots": ["all"],
        "effects": {
            1: {"all_stats": 5},
            2: {"all_stats": 12},
            3: {"all_stats": 25},
            4: {"all_stats": 50, "crit_damage": 20},
            5: {"all_stats": 100, "crit_damage": 50},
        }
    },

    # 特殊宝石
    "soul_gem": {
        "name": "灵魂宝石",
        "color": "#FF00FF",
        "slots": ["all"],
        "effects": {
            1: {"soul_damage": 50},
            2: {"soul_damage": 100, "life_steal": 5},
            3: {"soul_damage": 200, "life_steal": 10},
            4: {"soul_damage": 400, "life_steal": 15, "soul_regen": 5},
            5: {"soul_damage": 800, "life_steal": 20, "soul_regen": 10},
        }
    },
    "dragon_eye": {
        "name": "龙眼石",
        "color": "#FFD700",
        "slots": ["weapon", "artifact"],
        "effects": {
            1: {"dragon_damage": 100},
            2: {"dragon_damage": 250, "fire_damage": 100},
            3: {"dragon_damage": 500, "fire_damage": 250, "fire_resist": 30},
            4: {"dragon_damage": 1000, "fire_damage": 500, "fire_resist": 50},
            5: {"dragon_damage": 2000, "fire_damage": 1000, "fire_resist": 80, "dragon_slayer": True},
        }
    },
}
```

### 5.2 宝石槽位

```python
SOCKET_CONFIG = {
    # 每个装备部位的槽位数量范围
    "weapon": {"min": 1, "max": 3, "legendary_max": 5},
    "head": {"min": 1, "max": 2, "legendary_max": 3},
    "chest": {"min": 1, "max": 3, "legendary_max": 4},
    "legs": {"min": 1, "max": 2, "legendary_max": 3},
    "ring": {"min": 1, "max": 1, "legendary_max": 2},
    "amulet": {"min": 1, "max": 2, "legendary_max": 3},
    # ... 其他部位
}

def get_socket_count(item_rarity: int, slot: str) -> int:
    """根据稀有度和部位计算宝石槽数量"""
    config = SOCKET_CONFIG.get(slot, {"min": 0, "max": 0, "legendary_max": 0})

    if item_rarity >= 5:  # 传说及以上
        return random.randint(config["min"], config["legendary_max"])
    else:
        return random.randint(config["min"], config["max"])
```

---

## 六、装备强化系统

### 6.1 强化等级

```python
ENHANCEMENT_SYSTEM = {
    "max_level": 20,
    "success_rates": {
        1: 1.00,   # 1级: 100%
        2: 0.95,   # 2级: 95%
        3: 0.90,   # 3级: 90%
        4: 0.85,   # ...
        5: 0.80,
        6: 0.70,
        7: 0.60,
        8: 0.50,
        9: 0.40,
        10: 0.30,
        11: 0.25,
        12: 0.20,
        13: 0.15,
        14: 0.10,
        15: 0.08,
        16: 0.05,
        17: 0.03,
        18: 0.02,
        19: 0.01,
        20: 0.005,
    },
    "stat_bonus_per_level": 0.10,  # 每级+10%基础属性
    "cost_formula": lambda level: 100 * (level ** 2),  # 强化消耗仙石
}
```

### 6.2 强化保护

```python
PROTECTION_ITEMS = {
    "protection_stone": {
        "name": "护体石",
        "description": "强化失败时保护装备不降级",
        "cost": 500,
    },
    "luck_stone": {
        "name": "幸运石",
        "description": "强化成功率+10%",
        "cost": 200,
    },
    "blessing_stone": {
        "name": "祝福石",
        "description": "强化必定成功（最高+10）",
        "cost": 5000,
    },
}
```

---

## 七、装备锻造与合成

### 7.1 锻造系统

```python
@dataclass
class ForgeRecipe:
    recipe_id: str
    name: str
    materials: Dict[str, int]    # 材料及数量
    result_item: str             # 产出装备ID
    result_rarity_range: tuple   # 稀有度范围
    success_rate: float          # 成功率
    required_level: int          # 需要锻造等级

FORGE_RECIPES = {
    "basic_sword": ForgeRecipe(
        recipe_id="basic_sword",
        name="普通长剑",
        materials={"iron_ore": 10, "wood": 5},
        result_item="sword_basic",
        result_rarity_range=(0, 2),
        success_rate=0.95,
        required_level=1,
    ),
    "legendary_blade": ForgeRecipe(
        recipe_id="legendary_blade",
        name="传说神剑",
        materials={
            "celestial_iron": 50,
            "dragon_blood": 10,
            "star_essence": 5,
            "soul_crystal": 1,
        },
        result_item="blade_legendary",
        result_rarity_range=(5, 7),
        success_rate=0.30,
        required_level=50,
    ),
}
```

### 7.2 装备合成（暗黑式）

```python
def synthesize_equipment(items: List[Item]) -> Item:
    """
    合成装备 - 类似暗黑3的卡奈魔盒
    规则：
    - 3件同稀有度装备 → 1件高一阶装备
    - 保留平均词缀数量
    - 有几率获得特殊词缀
    """
    if len(items) != 3:
        raise ValueError("需要3件装备进行合成")

    rarity = items[0].rarity
    if not all(item.rarity == rarity for item in items):
        raise ValueError("所有装备稀有度必须相同")

    # 计算新装备属性
    new_rarity = min(rarity + 1, 8)
    avg_level = sum(item.level for item in items) // 3
    avg_affixes = sum(len(item.affixes) for item in items) // 3

    # 生成新装备
    new_item = generate_item(
        level=avg_level,
        rarity=new_rarity,
        affix_count=avg_affixes + random.randint(0, 2)
    )

    # 特殊合成奖励
    if random.random() < 0.1:  # 10%几率
        new_item.add_legendary_affix(random.choice(LEGENDARY_AFFIXES))

    return new_item
```

---

## 八、装备鉴定系统

### 8.1 鉴定机制

```python
IDENTIFICATION_SYSTEM = {
    # 未鉴定装备无法查看词缀
    "unidentified_bonuses": {
        "base_stats_visible": True,    # 基础属性可见
        "affixes_visible": False,      # 词缀不可见
        "set_info_visible": False,     # 套装信息不可见
    },

    # 鉴定方式
    "identification_methods": {
        "scroll": {                     # 鉴定卷轴
            "name": "鉴定卷轴",
            "cost": 100,
            "success_rate": 1.0,
        },
        "npc": {                        # NPC鉴定
            "name": "鉴宝师",
            "cost": 500,
            "bonus": "可鉴定出隐藏属性",
        },
        "skill": {                      # 技能鉴定
            "name": "天眼术",
            "required_level": 50,
            "mana_cost": 100,
        },
    },
}
```

### 8.2 隐藏属性

```python
HIDDEN_ATTRIBUTES = {
    "cursed": {
        "name": "诅咒",
        "description": "装备受到诅咒，无法取下",
        "effect": {"unremovable": True},
        "chance": 0.05,  # 5%几率
    },
    "blessed": {
        "name": "祝福",
        "description": "装备受到神明祝福，属性额外+20%",
        "effect": {"stat_multiplier": 1.2},
        "chance": 0.03,
    },
    "soulbound": {
        "name": "灵魂绑定",
        "description": "装备与灵魂绑定，死亡不掉落",
        "effect": {"soulbound": True},
        "chance": 0.10,
    },
    "volatile": {
        "name": "不稳定",
        "description": "装备属性每6小时随机变化",
        "effect": {"volatile": True},
        "chance": 0.02,
    },
}
```

---

## 九、装备数据模型

### 9.1 完整数据结构

```python
@dataclass
class EquipmentAffix:
    affix_id: str
    name: str
    type: str  # prefix, suffix, legendary, mythic
    stats: Dict[str, Any]
    description: str
    is_identified: bool = True

@dataclass
class GemSocket:
    socket_id: str
    socket_type: str  # normal, legendary
    gem: Optional['Gem'] = None
    is_locked: bool = False

@dataclass
class Gem:
    gem_id: str
    gem_type: str
    name: str
    level: int  # 1-5
    stats: Dict[str, Any]
    is_fused: bool = False

@dataclass
class Equipment:
    # 基础信息
    item_id: str
    name: str
    base_type: str              # 基础类型ID
    equipment_slot: str         # 装备槽位
    level: int                  # 装备等级
    rarity: int                 # 稀有度 0-8
    quality: float              # 品质 0.8-1.2

    # 属性
    base_stats: Dict[str, int]  # 基础属性
    affixes: List[EquipmentAffix]  # 词缀列表
    sockets: List[GemSocket]    # 宝石槽
    enhancement_level: int      # 强化等级 0-20

    # 套装
    set_id: Optional[str]       # 套装ID

    # 特殊属性
    is_identified: bool         # 是否已鉴定
    is_cursed: bool             # 是否诅咒
    is_soulbound: bool          # 是否灵魂绑定
    is_volatile: bool           # 是否不稳定

    # 灵魂装备专属
    soul_owner: Optional[str]   # 灵魂绑定玩家ID
    soul_growth_rate: float     # 灵魂成长率

    # 元数据
    created_at: datetime
    acquired_at: datetime
    acquired_from: str          # 获取来源

    def get_total_stats(self) -> Dict[str, int]:
        """计算装备总属性"""
        total = {}

        # 基础属性
        for stat, value in self.base_stats.items():
            total[stat] = total.get(stat, 0) + value

        # 品质加成
        for stat in total:
            total[stat] = int(total[stat] * self.quality)

        # 强化加成
        enhancement_mult = 1 + (self.enhancement_level * 0.10)
        for stat in total:
            total[stat] = int(total[stat] * enhancement_mult)

        # 词缀加成
        for affix in self.affixes:
            if affix.is_identified:
                for stat, value in affix.stats.items():
                    total[stat] = total.get(stat, 0) + value

        # 宝石加成
        for socket in self.sockets:
            if socket.gem:
                for stat, value in socket.gem.stats.items():
                    total[stat] = total.get(stat, 0) + value

        return total

    def get_display_name(self) -> str:
        """获取显示名称（含词缀）"""
        parts = []

        # 前缀词缀
        for affix in self.affixes:
            if affix.type == "prefix" and affix.is_identified:
                parts.append(affix.name)

        # 基础名称
        parts.append(self.name)

        # 后缀词缀
        for affix in self.affixes:
            if affix.type == "suffix" and affix.is_identified:
                parts.append(f"之{affix.name}")

        # 强化等级
        if self.enhancement_level > 0:
            parts.append(f"+{self.enhancement_level}")

        return " ".join(parts)

    def get_rarity_color(self) -> str:
        """获取稀有度颜色"""
        RARITY_COLORS = [
            "#808080",  # 破损
            "#FFFFFF",  # 普通
            "#1EFF00",  # 优秀
            "#0070DD",  # 稀有
            "#A335EE",  # 史诗
            "#FF8000",  # 传说
            "#E6CC80",  # 神话
            "#00FFFF",  # 远古
            "#FF00FF",  # 灵魂
        ]
        return RARITY_COLORS[self.rarity]
```

---

## 十、装备获取途径

### 10.1 获取方式

```python
ACQUISITION_METHODS = {
    "monster_drop": {
        "name": "怪物掉落",
        "rarity_modifier": 1.0,
        "description": "击杀怪物有几率掉落装备",
    },
    "boss_drop": {
        "name": "BOSS掉落",
        "rarity_modifier": 2.0,
        "description": "击杀BOSS必掉装备，稀有度更高",
    },
    "treasure_chest": {
        "name": "宝箱",
        "rarity_modifier": 1.5,
        "description": "秘境中发现的宝箱",
    },
    "crafting": {
        "name": "锻造",
        "rarity_modifier": 1.0,
        "description": "使用材料锻造装备",
    },
    "quest_reward": {
        "name": "任务奖励",
        "rarity_modifier": 1.2,
        "description": "完成任务获得的奖励",
    },
    "shop": {
        "name": "商店购买",
        "rarity_modifier": 0.8,
        "description": "从商店购买（稀有度较低）",
    },
    "trading": {
        "name": "玩家交易",
        "rarity_modifier": 1.0,
        "description": "与其他玩家交易",
    },
    "event": {
        "name": "活动奖励",
        "rarity_modifier": 2.5,
        "description": "限时活动特殊奖励",
    },
}
```

### 10.2 掉落表设计

```python
@dataclass
class DropTable:
    table_id: str
    name: str
    items: Dict[str, float]      # item_id: drop_weight
    guaranteed_drops: List[str]  # 必掉物品
    rarity_weights: Dict[int, float]  # 稀有度权重

# 示例：炼气洞BOSS掉落表
LIANQI_BOSS_DROP = DropTable(
    table_id="lianqi_boss",
    name="炼气洞BOSS掉落",
    items={
        "sword_qingyun": 10,
        "robe_apprentice": 15,
        "ring_spirit": 5,
        "pill_cultivation": 30,
    },
    guaranteed_drops=["spirit_stone_100"],
    rarity_weights={
        2: 0.40,  # 优秀 40%
        3: 0.35,  # 稀有 35%
        4: 0.20,  # 史诗 20%
        5: 0.05,  # 传说 5%
    }
)
```

---

## 十一、实现优先级

### 第一阶段（核心功能）
1. ✅ 装备数据模型
2. ✅ 稀有度系统
3. ✅ 基础词缀系统
4. ✅ 装备槽位系统

### 第二阶段（进阶功能）
1. 宝石镶嵌系统
2. 装备强化系统
3. 套装系统
4. 装备鉴定系统

### 第三阶段（高级功能）
1. 装备锻造系统
2. 装备合成系统
3. 灵魂装备系统
4. 装备交易系统

---

## 十二、UI展示建议

### 装备提示框（Tooltip）

```
┌─────────────────────────────────────────────┐
│ 【远古·嗜血的幽冥死神镰刀+15】              │ ← 名称（稀有度颜色）
│ ─────────────────────────────────────────── │
│ 攻击力: 1,250 - 1,580                       │ ← 基础属性
│ 攻击速度: 1.2                               │
│                                             │
│ ◆ 远古词缀:                                 │ ← 远古诗缀（青色）
│   └ 所有属性提升150%                        │
│                                             │
│ ★ 传奇词缀:                                 │ ← 传奇词缀（橙色）
│   └ 嗜血狂魔: 每次攻击恢复造成伤害的5%     │
│   └ 毁灭之怒: 暴击伤害+400%                 │
│                                             │
│ ◇ 随机词缀:                                 │ ← 随机词缀（蓝色）
│   └ 攻击力+680                              │
│   └ 暴击率+18%                              │
│   └ 生命偷取+12%                            │
│                                             │
│ ◈ 宝石:                                     │ ← 宝石（宝石颜色）
│   [Lv5 龙眼石] 龙族伤害+2000               │
│   [Lv5 灵魂宝石] 灵魂伤害+800              │
│                                             │
│ ─────────────────────────────────────────── │
│ 套装: 幽冥死神 (2/6)                        │ ← 套装信息
│ (2) 暗影伤害+150, 生命偷取+10%             │
│ (4) 暴击伤害+100, 毒素伤害+100             │
│ (6) 死神降临特效                            │
│                                             │
│ ─────────────────────────────────────────── │
│ "死亡不是终点，而是新的开始..."             │ ← 装备描述/传说
│                                             │
│ 等级需求: 300                               │ ← 装备需求
│ 门派需求: 无                                │
│ 物品等级: 350                               │
└─────────────────────────────────────────────┘
```

---

**文档版本**: 1.0
**最后更新**: 2024-02-11
**作者**: Claude Opus 4.6
