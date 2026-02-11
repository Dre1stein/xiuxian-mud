"""
战斗伤害系统
Damage calculation and element system for combat
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import random


class Element(Enum):
    """元素属性"""
    WIND = "风"       # 青云门
    FIRE = "火"       # 丹鼎门
    WOOD = "木"       # 万花谷
    VOID = "虚"       # 逍遥宗
    LIGHTNING = "雷"  # 蜀山派
    ICE = "冰"        # 昆仑派
    SOUND = "音"      # 幻音坊
    BLOOD = "血"      # 血魔宗
    PHYSICAL = "物理"  # 普通物理
    NONE = "无"


class DamageType(Enum):
    """伤害类型"""
    PHYSICAL = "物理"
    MAGIC = "法术"
    TRUE = "真实"


# 元素克制关系
ELEMENT_COUNTERS: Dict[Element, List[Element]] = {
    Element.WIND: [Element.WOOD, Element.SOUND],      # 风克木、音
    Element.FIRE: [Element.WOOD, Element.ICE],        # 火克木、冰
    Element.WOOD: [Element.FIRE, Element.BLOOD],      # 木克火、血
    Element.VOID: [Element.LIGHTNING, Element.WIND],  # 虚克雷、风
    Element.LIGHTNING: [Element.WOOD, Element.SOUND], # 雷克木、音
    Element.ICE: [Element.FIRE, Element.WIND],        # 冰克火、风
    Element.SOUND: [Element.VOID, Element.LIGHTNING], # 音克虚、雷
    Element.BLOOD: [Element.WOOD, Element.VOID],      # 血克木、虚
}


def get_element_multiplier(attacker_element: Element, defender_element: Element) -> float:
    """获取元素克制倍率"""
    if attacker_element == Element.NONE or defender_element == Element.NONE:
        return 1.0
    if attacker_element in ELEMENT_COUNTERS.get(defender_element, []):
        return 1.5  # 克制 +50% 伤害
    if defender_element in ELEMENT_COUNTERS.get(attacker_element, []):
        return 0.75  # 被克 -25% 伤害
    return 1.0  # 正常


@dataclass
class DamageResult:
    """伤害结果"""
    damage: int
    is_crit: bool
    element: Element
    damage_type: DamageType
    element_multiplier: float = 1.0
    blocked: bool = False
    dodged: bool = False


class DamageCalculator:
    """伤害计算器"""

    @staticmethod
    def calculate_damage(
        attacker: Any,
        defender: Any,
        element: Element = Element.PHYSICAL,
        damage_type: DamageType = DamageType.PHYSICAL,
        base_value: int = 0,
        scaling_stat: str = "attack",
        scaling_multiplier: float = 1.0,
    ) -> DamageResult:
        """
        计算伤害

        Args:
            attacker: 攻击者 (需要有 attack, magic_attack, crit_rate, crit_damage 等属性)
            defender: 防御者 (需要有 defense, magic_resist, dodge_rate, hp 等属性)
            element: 元素属性
            damage_type: 伤害类型
            base_value: 基础伤害值
            scaling_stat: 缩放属性 ("attack", "magic_attack", 等)
            scaling_multiplier: 缩放倍率

        Returns:
            DamageResult: 伤害结果
        """
        # 检查闪避
        dodge_rate = getattr(defender, "dodge_rate", 0)
        if random.random() < dodge_rate:
            return DamageResult(
                damage=0,
                is_crit=False,
                element=element,
                damage_type=damage_type,
                dodged=True
            )

        # 获取攻击力
        if damage_type == DamageType.PHYSICAL:
            attack_stat = getattr(attacker, "attack", 10)
            defense_stat = getattr(defender, "defense", 5)
        else:
            attack_stat = getattr(attacker, "magic_attack", 10)
            defense_stat = getattr(defender, "magic_resist", 5)

        # 计算基础伤害
        scaling_value = getattr(attacker, scaling_stat, 10)
        base_damage = base_value + (scaling_value * scaling_multiplier)

        # 防御减伤
        effective_defense = defense_stat * 0.5  # 简化防御计算
        damage = max(1, int(base_damage - effective_defense))

        # 真实伤害无视防御
        if damage_type == DamageType.TRUE:
            damage = int(base_damage)

        # 元素克制
        defender_element = getattr(defender, "element", Element.NONE)
        element_multiplier = get_element_multiplier(element, defender_element)
        damage = int(damage * element_multiplier)

        # 暴击判定
        crit_rate = getattr(attacker, "crit_rate", 0.05)
        crit_damage = getattr(attacker, "crit_damage", 1.5)
        is_crit = random.random() < crit_rate

        if is_crit:
            damage = int(damage * crit_damage)

        return DamageResult(
            damage=damage,
            is_crit=is_crit,
            element=element,
            damage_type=damage_type,
            element_multiplier=element_multiplier
        )

    @staticmethod
    def calculate_healing(
        caster: Any,
        target: Any,
        base_value: int = 0,
        scaling_stat: str = "intellect",
        scaling_multiplier: float = 1.0,
    ) -> int:
        """计算治疗量"""
        scaling_value = getattr(caster, scaling_stat, 10)
        base_heal = base_value + (scaling_value * scaling_multiplier)

        # 目标的治疗加成
        healing_bonus = getattr(target, "healing_received", 1.0)

        return max(1, int(base_heal * healing_bonus))


if __name__ == "__main__":
    # 测试伤害计算
    print("测试伤害计算系统")

    class MockUnit:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    attacker = MockUnit(
        attack=100,
        magic_attack=80,
        crit_rate=0.2,
        crit_damage=2.0,
        element=Element.FIRE
    )

    defender = MockUnit(
        defense=30,
        magic_resist=25,
        dodge_rate=0.1,
        hp=1000,
        element=Element.WOOD
    )

    calc = DamageCalculator()

    # 测试物理伤害
    result = calc.calculate_damage(
        attacker, defender,
        element=Element.PHYSICAL,
        damage_type=DamageType.PHYSICAL,
        base_value=50,
        scaling_stat="attack",
        scaling_multiplier=1.0
    )
    print(f"物理伤害: {result.damage} (暴击: {result.is_crit})")

    # 测试法术伤害
    result = calc.calculate_damage(
        attacker, defender,
        element=Element.FIRE,
        damage_type=DamageType.MAGIC,
        base_value=30,
        scaling_stat="magic_attack",
        scaling_multiplier=1.5
    )
    print(f"火焰伤害: {result.damage} (暴击: {result.is_crit}, 元素倍率: {result.element_multiplier})")

    print("伤害计算系统测试完成")
