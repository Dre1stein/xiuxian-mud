import random
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from .models import Equipment, Rarity


@dataclass
class EnhanceResult:
    success: bool
    old_level: int
    new_level: int
    message: str
    materials_consumed: Dict[str, int]


ENHANCE_SUCCESS_RATES = {
    0: 1.0,    # +0 → +1: 100%
    1: 0.95,   # +1 → +2: 95%
    2: 0.90,   # +2 → +3: 90%
    3: 0.85,
    4: 0.80,
    5: 0.70,
    6: 0.60,
    7: 0.50,
    8: 0.40,
    9: 0.30,
    10: 0.25,
    11: 0.20,
    12: 0.15,
    13: 0.10,
    14: 0.05,  # +14 → +15: 5%
}
MAX_ENHANCE_LEVEL = 15


class EquipmentEnhancer:
    def __init__(self):
        pass

    def enhance(
        self,
        equipment: Equipment,
        use_protection: bool = False,
        luck_bonus: float = 0.0
    ) -> EnhanceResult:
        """强化装备"""
        old_level = equipment.enhance_level

        # 检查是否已满级
        if old_level >= MAX_ENHANCE_LEVEL:
            return EnhanceResult(
                success=False,
                old_level=old_level,
                new_level=old_level,
                message="装备已达最高强化等级",
                materials_consumed={}
            )

        # 计算成功率
        base_rate = ENHANCE_SUCCESS_RATES.get(old_level, 0.05)
        final_rate = min(1.0, base_rate + luck_bonus)

        # 消耗材料
        cost = self._calculate_cost(old_level)
        materials = {"spirit_stones": cost}

        # 随机判定
        roll = random.random()

        if roll < final_rate:
            # 成功
            equipment.enhance_level = old_level + 1
            return EnhanceResult(
                success=True,
                old_level=old_level,
                new_level=old_level + 1,
                message=f"强化成功！{old_level} → {old_level + 1}",
                materials_consumed=materials
            )
        else:
            # 失败
            if use_protection:
                # 使用保护符，等级不变
                materials["protection_stone"] = 1
                return EnhanceResult(
                    success=False,
                    old_level=old_level,
                    new_level=old_level,
                    message="强化失败，保护符生效，等级保持不变",
                    materials_consumed=materials
                )
            else:
                # 降级
                new_level = max(0, old_level - 1)
                equipment.enhance_level = new_level
                return EnhanceResult(
                    success=False,
                    old_level=old_level,
                    new_level=new_level,
                    message=f"强化失败，等级下降 {old_level} → {new_level}",
                    materials_consumed=materials
                )

    def _calculate_cost(self, current_level: int) -> int:
        """计算强化消耗"""
        return 100 * ((current_level + 1) ** 2)

    def get_success_rate(self, level: int) -> float:
        """获取成功率"""
        return ENHANCE_SUCCESS_RATES.get(level, 0.05)

    def get_cost(self, level: int) -> int:
        """获取强化消耗"""
        return self._calculate_cost(level)


_enhancer: Optional[EquipmentEnhancer] = None

def get_enhancer() -> EquipmentEnhancer:
    global _enhancer
    if _enhancer is None:
        _enhancer = EquipmentEnhancer()
    return _enhancer