"""装备生成器"""
import random
import uuid
from typing import Dict, List, Optional
from datetime import datetime

from .models import Rarity, EquipmentSlot, AffixType, AffixInstance, Equipment
from .config_loader import get_config_loader, EquipmentConfigLoader


class EquipmentGenerator:
    """装备生成器"""

    def __init__(self, config_loader: Optional[EquipmentConfigLoader] = None):
        self.config = config_loader or get_config_loader()

    def generate(
        self,
        level: int,
        slot: EquipmentSlot,
        source: str = "normal_monster",
        forced_rarity: Optional[Rarity] = None
    ) -> Equipment:
        """生成随机装备"""
        # 1. 确定稀有度
        if forced_rarity:
            rarity = forced_rarity
        else:
            rarity = self._roll_rarity(source, level)

        # 2. 生成基础属性
        base_stats = self._generate_base_stats(slot, level, rarity)

        # 3. 生成词缀
        affix_count = rarity.affix_slots
        affixes = self._generate_affixes(slot, level, affix_count)

        # 4. 生成装备名称
        name = self._generate_name(slot, rarity)

        return Equipment(
            equipment_id=f"equip_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{uuid.uuid4().hex[:6]}",
            base_item_id=f"base_{slot.name.lower()}",
            name=name,
            slot=slot,
            rarity=rarity,
            level=level,
            base_stats=base_stats,
            affixes=affixes,
        )

    def _roll_rarity(self, source: str, level: int) -> Rarity:
        """根据掉落表随机选择稀有度"""
        drop_table = self.config.get_drop_table(source)
        if not drop_table:
            return Rarity.NORMAL

        weights = drop_table.get("weights", {})
        total = sum(weights.values())
        roll = random.random() * total
        cumulative = 0

        for rarity_name, weight in weights.items():
            cumulative += weight
            if roll <= cumulative:
                return Rarity[rarity_name]

        return Rarity.NORMAL

    def _generate_base_stats(self, slot: EquipmentSlot, level: int, rarity: Rarity) -> Dict[str, int]:
        """生成基础属性"""
        # 基础属性模板
        base_values = {
            EquipmentSlot.WEAPON: {"attack": 10, "speed": 5},
            EquipmentSlot.HELMET: {"defense": 8, "hp": 50},
            EquipmentSlot.ARMOR: {"defense": 15, "hp": 100},
            EquipmentSlot.GLOVES: {"attack": 5, "speed": 3},
            EquipmentSlot.BOOTS: {"speed": 10, "dodge": 2},
            EquipmentSlot.BELT: {"hp": 50, "defense": 5},
            EquipmentSlot.AMULET: {"spirit": 10, "mp": 30},
            EquipmentSlot.RING_LEFT: {"attack": 3, "crit_rate": 1},
            EquipmentSlot.RING_RIGHT: {"attack": 3, "crit_rate": 1},
            EquipmentSlot.ARTIFACT: {"spirit": 20, "attack": 5},
        }

        stats = base_values.get(slot, {"attack": 5}).copy()

        # 应用等级和稀有度倍率
        for stat in stats:
            stats[stat] = int(stats[stat] * (1 + level * 0.1) * rarity.multiplier)

        return stats

    def _generate_affixes(self, slot: EquipmentSlot, level: int, count: int) -> List[AffixInstance]:
        """生成随机词缀"""
        affixes = []
        affix_config = self.config.load_affixes()

        # 获取允许的词缀
        all_prefixes = [a for a in affix_config.get("prefixes", [])
                        if self._affix_allowed_for_slot(a, slot)]
        all_suffixes = [a for a in affix_config.get("suffixes", [])
                        if self._affix_allowed_for_slot(a, slot)]

        used_ids = set()

        for i in range(count):
            # 交替前缀后缀
            if i % 2 == 0 and all_prefixes:
                pool = all_prefixes
                affix_type = AffixType.PREFIX
            else:
                pool = all_suffixes
                affix_type = AffixType.SUFFIX

            if not pool:
                continue

            # 按权重随机选择
            affix_def = self._weighted_choice(pool, used_ids)
            if affix_def:
                used_ids.add(affix_def["id"])
                affixes.append(self._create_affix_instance(affix_def, affix_type, level))

        return affixes

    def _affix_allowed_for_slot(self, affix: Dict, slot: EquipmentSlot) -> bool:
        """检查词缀是否允许在该槽位"""
        allowed = affix.get("allowed_slots", ["*"])
        if "*" in allowed:
            return True
        return slot.name in allowed

    def _weighted_choice(self, items: List[Dict], exclude: set) -> Optional[Dict]:
        """加权随机选择"""
        available = [i for i in items if i.get("id") not in exclude]
        if not available:
            return None

        total_weight = sum(i.get("weight", 100) for i in available)
        roll = random.random() * total_weight
        cumulative = 0

        for item in available:
            cumulative += item.get("weight", 100)
            if roll <= cumulative:
                return item

        return available[0]

    def _create_affix_instance(self, affix_def: Dict, affix_type: AffixType, level: int) -> AffixInstance:
        """创建词缀实例"""
        stats = affix_def.get("stats", {})
        stat_modifiers = {}
        flat_modifiers = {}

        for stat, range_val in stats.items():
            min_val = range_val.get("min", 1)
            max_val = range_val.get("max", 10)
            # 应用等级缩放
            scaled_min = int(min_val * (1 + level * 0.05))
            scaled_max = int(max_val * (1 + level * 0.05))
            actual = random.randint(scaled_min, scaled_max)

            # 百分比属性
            if stat.endswith("_rate") or stat.endswith("_damage"):
                stat_modifiers[stat] = actual / 100.0
            else:
                flat_modifiers[stat] = actual

        return AffixInstance(
            affix_id=affix_def["id"],
            name=affix_def["name"],
            affix_type=affix_type,
            stat_modifiers=stat_modifiers,
            flat_modifiers=flat_modifiers,
            roll_value=random.uniform(0.5, 1.0)
        )

    def _generate_name(self, slot: EquipmentSlot, rarity: Rarity) -> str:
        """生成装备基础名称"""
        names = {
            EquipmentSlot.WEAPON: "长剑",
            EquipmentSlot.HELMET: "头盔",
            EquipmentSlot.ARMOR: "护甲",
            EquipmentSlot.GLOVES: "护手",
            EquipmentSlot.BOOTS: "战靴",
            EquipmentSlot.BELT: "腰带",
            EquipmentSlot.AMULET: "项链",
            EquipmentSlot.RING_LEFT: "戒指",
            EquipmentSlot.RING_RIGHT: "戒指",
            EquipmentSlot.ARTIFACT: "法宝",
        }
        base_name = names.get(slot, "装备")
        return f"{rarity.display_name}{base_name}"


# 全局实例
_generator: Optional[EquipmentGenerator] = None


def get_generator() -> EquipmentGenerator:
    """获取全局装备生成器"""
    global _generator
    if _generator is None:
        _generator = EquipmentGenerator()
    return _generator
