"""装备属性计算器"""
from typing import Dict, List, Optional

from .models import Equipment, EquipmentSlot, Rarity, AffixType
from .config_loader import get_config_loader, EquipmentConfigLoader


class EquipmentCalculator:
    """装备属性计算器"""

    def __init__(self, config_loader: Optional[EquipmentConfigLoader] = None):
        self.config = config_loader or get_config_loader()
        self._cache: Dict[str, Dict] = {}

    def calculate_equipment_stats(self, equipment: Equipment) -> Dict[str, float]:
        """计算单件装备总属性 = 基础 + 词缀 + 强化"""
        total: Dict[str, float] = {}

        # 1. 基础属性
        for stat, value in equipment.base_stats.items():
            total[stat] = float(value)

        # 2. 应用稀有度倍率
        for stat in total:
            total[stat] *= equipment.rarity.multiplier

        # 3. 词缀属性
        for affix in equipment.affixes:
            # 百分比加成
            for stat, value in affix.stat_modifiers.items():
                total[stat] = total.get(stat, 0) + value
            # 固定加成
            for stat, value in affix.flat_modifiers.items():
                total[stat] = total.get(stat, 0) + value

        # 4. 强化加成 (每级+10%)
        enhance_mult = 1 + equipment.enhance_level * 0.1
        for stat in total:
            if stat not in ["crit_rate", "dodge"]:  # 百分比属性不加成
                total[stat] *= enhance_mult

        return {k: round(v, 2) for k, v in total.items()}

    def calculate_player_total_stats(
        self,
        equipments: List[Equipment]
    ) -> Dict[str, float]:
        """计算玩家装备总属性"""
        total: Dict[str, float] = {}

        for equipment in equipments:
            stats = self.calculate_equipment_stats(equipment)
            for stat, value in stats.items():
                total[stat] = total.get(stat, 0) + value

        # 计算套装加成
        set_bonuses = self._calculate_set_bonuses(equipments)
        for stat, value in set_bonuses.items():
            total[stat] = total.get(stat, 0) + value

        return {k: round(v, 2) for k, v in total.items()}

    def _calculate_set_bonuses(self, equipments: List[Equipment]) -> Dict[str, float]:
        """计算套装加成"""
        bonuses: Dict[str, float] = {}

        # 统计各套装件数
        set_counts: Dict[str, int] = {}
        set_equipment_map: Dict[str, List[Equipment]] = {}

        for eq in equipments:
            if eq.set_id:
                set_counts[eq.set_id] = set_counts.get(eq.set_id, 0) + 1
                if eq.set_id not in set_equipment_map:
                    set_equipment_map[eq.set_id] = []
                set_equipment_map[eq.set_id].append(eq)

        # 应用套装奖励
        for set_id, count in set_counts.items():
            set_def = self.config.get_set_by_id(set_id)
            if not set_def:
                continue

            for bonus in set_def.get("bonuses", []):
                required = bonus.get("pieces_required", 0)
                if count >= required:
                    # 应用属性加成
                    for stat, value in bonus.get("stat_modifiers", {}).items():
                        bonuses[stat] = bonuses.get(stat, 0) + value
                    for stat, value in bonus.get("flat_modifiers", {}).items():
                        bonuses[stat] = bonuses.get(stat, 0) + value

        return bonuses

    def calculate_combat_power(self, stats: Dict[str, float]) -> int:
        """计算战斗力"""
        # 战斗力 = 攻击 * 速度 + 防御 * 体质 + 暴击率 * 1000
        attack = stats.get("attack", 0)
        defense = stats.get("defense", 0)
        speed = stats.get("speed", 0)
        hp = stats.get("hp", 0)
        crit_rate = stats.get("crit_rate", 0)
        dodge = stats.get("dodge", 0)

        power = (
            attack * speed * 0.5 +
            defense * 2 +
            hp * 0.1 +
            crit_rate * 5000 +
            dodge * 3000
        )

        return int(power)

    def get_active_set_bonuses(self, equipments: List[Equipment]) -> List[Dict]:
        """获取当前激活的套装效果"""
        active = []

        set_counts: Dict[str, int] = {}
        for eq in equipments:
            if eq.set_id:
                set_counts[eq.set_id] = set_counts.get(eq.set_id, 0) + 1

        for set_id, count in set_counts.items():
            set_def = self.config.get_set_by_id(set_id)
            if not set_def:
                continue

            for bonus in set_def.get("bonuses", []):
                required = bonus.get("pieces_required", 0)
                if count >= required:
                    active.append({
                        "set_id": set_id,
                        "set_name": set_def.get("name", ""),
                        "pieces": count,
                        "required": required,
                        "description": bonus.get("description", ""),
                    })

        return active

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()


# 全局实例
_calculator: Optional[EquipmentCalculator] = None


def get_calculator() -> EquipmentCalculator:
    """获取全局计算器实例"""
    global _calculator
    if _calculator is None:
        _calculator = EquipmentCalculator()
    return _calculator
