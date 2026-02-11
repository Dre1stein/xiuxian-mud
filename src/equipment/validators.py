from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from .models import Equipment, EquipmentSlot, Rarity, AffixInstance, AffixType
from .config_loader import get_config_loader, EquipmentConfigLoader


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]


class EquipmentValidator:
    def __init__(self, config_loader: Optional[EquipmentConfigLoader] = None):
        self.config = config_loader or get_config_loader()

    def validate_equipment(self, equipment: Equipment) -> Tuple[bool, List[str]]:
        """验证装备完整性"""
        errors = []

        # 检查词缀数量
        rarity_config = self.config.get_rarity(equipment.rarity.name)
        if rarity_config:
            max_affixes = rarity_config.get("affix_slots", 0)
            if len(equipment.affixes) > max_affixes + 2:  # 允许少量溢出
                errors.append(f"词缀数量超过限制: {len(equipment.affixes)} > {max_affixes}")

        # 检查词缀互斥
        affix_errors = self._check_affix_conflicts(equipment.affixes)
        errors.extend(affix_errors)

        # 检查强化等级
        if equipment.enhance_level < 0 or equipment.enhance_level > 15:
            errors.append(f"强化等级无效: {equipment.enhance_level}")

        # 检查等级
        if equipment.level < 1:
            errors.append(f"装备等级无效: {equipment.level}")

        return (len(errors) == 0, errors)

    def _check_affix_conflicts(self, affixes: List[AffixInstance]) -> List[str]:
        """检查词缀冲突"""
        errors = []
        exclusions = self.config.load_exclusions()

        affix_ids = [a.affix_id for a in affixes]

        for group in exclusions:
            group_id = group.get("group_id", "")
            group_affixes = set(group.get("affixes", []))
            conflicts = group_affixes.intersection(set(affix_ids))

            if len(conflicts) > 1:
                errors.append(f"词缀互斥冲突 [{group_id}]: {', '.join(conflicts)}")

        return errors

    def validate_slot(self, equipment: Equipment, target_slot: EquipmentSlot) -> Tuple[bool, str]:
        """验证装备是否可以放入目标槽位"""
        if equipment.slot != target_slot:
            return (False, f"装备类型不匹配: {equipment.slot.value} != {target_slot.value}")
        return (True, "")

    def validate_affix_compatibility(
        self,
        affix: AffixInstance,
        slot: EquipmentSlot
    ) -> Tuple[bool, str]:
        """验证词缀是否适合该槽位"""
        affix_def = self.config.get_affix_by_id(affix.affix_id)
        if not affix_def:
            return (True, "")  # 找不到定义时跳过

        allowed = affix_def.get("allowed_slots", ["*"])
        if "*" in allowed or slot.name in allowed:
            return (True, "")

        return (False, f"词缀 {affix.name} 不允许在 {slot.value} 槽位")

    def validate_equip_requirements(
        self,
        equipment: Equipment,
        player_level: int
    ) -> Tuple[bool, List[str]]:
        """验证玩家是否满足装备需求"""
        errors = []

        if player_level < equipment.level:
            errors.append(f"等级不足: 需要 {equipment.level}, 当前 {player_level}")

        return (len(errors) == 0, errors)


_validator: Optional[EquipmentValidator] = None

def get_validator() -> EquipmentValidator:
    global _validator
    if _validator is None:
        _validator = EquipmentValidator()
    return _validator