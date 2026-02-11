"""
战斗技能系统
Combat Skills System for Cultivation Game
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
import copy

from .damage import Element, DamageCalculator, DamageType


class SkillType(Enum):
    """技能类型"""
    ACTIVE = "主动技能"
    PASSIVE = "被动技能"
    TOGGLE = "开关技能"
    TRIGGER = "触发技能"


class SkillTarget(Enum):
    """技能目标"""
    SELF = "自身"
    SINGLE_ENEMY = "单体敌人"
    ALL_ENEMIES = "全体敌人"
    SINGLE_ALLY = "单体友方"
    ALL_ALLIES = "全体友方"


@dataclass
class SkillEffect:
    """技能效果"""
    effect_type: str  # "damage", "heal", "buff", "debuff"
    value_base: int
    value_scaling: float  # 属性加成比例
    scaling_stat: str  # "attack", "magic_attack", etc.
    element: Optional[Element] = None
    buff_id: Optional[str] = None
    debuff_id: Optional[str] = None
    duration: int = 0
    hit_count: int = 1  # 多段攻击


@dataclass
class CombatAction:
    """战斗行动"""
    action_type: str  # "attack", "heal", "buff", "debuff"
    caster_id: str
    target_id: str
    skill_id: str
    value: int = 0
    element: Optional[Element] = None
    is_crit: bool = False
    buff_id: Optional[str] = None
    duration: int = 0


@dataclass
class CombatUnit:
    """战斗单位"""
    unit_id: str
    name: str
    level: int = 1
    hp: int = 100
    max_hp: int = 100
    mp: int = 50
    max_mp: int = 50
    attack: int = 20
    defense: int = 10
    magic_attack: int = 15
    magic_resist: int = 8
    speed: int = 10
    intellect: int = 10
    crit_rate: float = 0.05
    crit_damage: float = 1.5
    dodge_rate: float = 0.05
    element: Optional[Element] = None
    buffs: List[Dict[str, Any]] = field(default_factory=list)
    debuffs: List[Dict[str, Any]] = field(default_factory=list)
    is_dead: bool = False
    healing_received: float = 1.0


class CombatSkill:
    """战斗技能"""

    def __init__(
        self,
        skill_id: str,
        name: str,
        description: str,
        skill_type: SkillType,
        target_type: SkillTarget,
        mp_cost: int = 0,
        hp_cost: int = 0,
        cooldown: int = 0,
        effects: List[SkillEffect] = None,
        required_level: int = 1,
        required_stage: Optional[str] = None,
        required_sect: Optional[str] = None,
        element: Optional[Element] = None,
    ):
        self.skill_id = skill_id
        self.name = name
        self.description = description
        self.skill_type = skill_type
        self.target_type = target_type
        self.mp_cost = mp_cost
        self.hp_cost = hp_cost
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.effects = effects or []
        self.required_level = required_level
        self.required_stage = required_stage
        self.required_sect = required_sect
        self.element = element

    def can_use(self, caster_mp: int, caster_hp: int) -> bool:
        """检查是否可以使用"""
        if self.current_cooldown > 0:
            return False
        if caster_mp < self.mp_cost:
            return False
        if caster_hp < self.hp_cost:
            return False
        return True

    def apply_cooldown(self):
        """开始冷却"""
        self.current_cooldown = self.cooldown

    def reduce_cooldown(self):
        """减少冷却"""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

    def clone(self) -> "CombatSkill":
        """克隆技能（用于实例化）"""
        skill = CombatSkill(
            skill_id=self.skill_id,
            name=self.name,
            description=self.description,
            skill_type=self.skill_type,
            target_type=self.target_type,
            mp_cost=self.mp_cost,
            hp_cost=self.hp_cost,
            cooldown=self.cooldown,
            effects=copy.deepcopy(self.effects),
            required_level=self.required_level,
            required_stage=self.required_stage,
            required_sect=self.required_sect,
            element=self.element,
        )
        skill.current_cooldown = self.current_cooldown
        return skill


class SkillExecutor:
    """技能执行器"""

    def __init__(self, damage_calculator: DamageCalculator):
        self.damage_calc = damage_calculator

    def execute_skill(
        self,
        skill: CombatSkill,
        caster: CombatUnit,
        targets: List[CombatUnit],
    ) -> List[CombatAction]:
        """
        执行技能，返回行动列表

        Args:
            skill: 要使用的技能
            caster: 施法者
            targets: 目标列表

        Returns:
            行动列表
        """
        actions: List[CombatAction] = []

        # 检查是否可以使用
        if not skill.can_use(caster.mp, caster.hp):
            return actions

        # 消耗资源
        caster.mp -= skill.mp_cost
        caster.hp -= skill.hp_cost

        # 开始冷却
        skill.apply_cooldown()

        # 根据目标类型选择目标
        actual_targets = self._select_targets(skill, caster, targets)

        # 对每个目标应用效果
        for target in actual_targets:
            if target.is_dead:
                continue
            action = self.apply_effects(skill.effects, caster, target)
            actions.append(action)

        return actions

    def _select_targets(
        self,
        skill: CombatSkill,
        caster: CombatUnit,
        available_targets: List[CombatUnit],
    ) -> List[CombatUnit]:
        """根据技能目标类型选择目标"""
        if skill.target_type == SkillTarget.SELF:
            return [caster]
        elif skill.target_type == SkillTarget.SINGLE_ENEMY:
            # 简化：选择第一个存活的敌人
            return [t for t in available_targets if not t.is_dead][:1]
        elif skill.target_type == SkillTarget.ALL_ENEMIES:
            return [t for t in available_targets if not t.is_dead]
        elif skill.target_type == SkillTarget.SINGLE_ALLY:
            # 简化：选择第一个存活的友方目标（优先选择目标列表中的）
            living_targets = [t for t in available_targets if not t.is_dead]
            if living_targets:
                return living_targets[:1]
            return [caster]
        elif skill.target_type == SkillTarget.ALL_ALLIES:
            # 简化：返回所有存活单位（包括自己）
            return [caster] + [t for t in available_targets if not t.is_dead]
        return []

    def apply_effects(
        self,
        effects: List[SkillEffect],
        caster: CombatUnit,
        target: CombatUnit,
    ) -> CombatAction:
        """
        应用技能效果

        Args:
            effects: 效果列表
            caster: 施法者
            target: 目标

        Returns:
            战斗行动
        """
        total_value = 0
        primary_effect_type = effects[0].effect_type if effects else "damage"
        element = effects[0].element if effects else None
        is_crit = False

        for effect in effects:
            if effect.effect_type == "damage":
                # 计算伤害
                damage_type = DamageType.PHYSICAL if effect.element == Element.PHYSICAL else DamageType.MAGIC
                result = self.damage_calc.calculate_damage(
                    attacker=caster,
                    defender=target,
                    element=effect.element or Element.PHYSICAL,
                    damage_type=damage_type,
                    base_value=effect.value_base,
                    scaling_stat=effect.scaling_stat,
                    scaling_multiplier=effect.value_scaling,
                )

                # 多段攻击
                total_damage = result.damage * effect.hit_count
                total_value += total_damage
                is_crit = result.is_crit

                # 应用伤害
                target.hp = max(0, target.hp - total_damage)
                if target.hp <= 0:
                    target.is_dead = True

            elif effect.effect_type == "heal":
                # 计算治疗
                heal_value = self.damage_calc.calculate_healing(
                    caster=caster,
                    target=target,
                    base_value=effect.value_base,
                    scaling_stat=effect.scaling_stat,
                    scaling_multiplier=effect.value_scaling,
                )
                total_value += heal_value

                # 应用治疗
                target.hp = min(target.max_hp, target.hp + heal_value)

            elif effect.effect_type == "buff":
                # 应用增益
                buff = {
                    "buff_id": effect.buff_id,
                    "duration": effect.duration,
                    "value": effect.value_base,
                }
                target.buffs.append(buff)
                total_value += effect.value_base

            elif effect.effect_type == "debuff":
                # 应用减益
                debuff = {
                    "debuff_id": effect.debuff_id,
                    "duration": effect.duration,
                    "value": effect.value_base,
                }
                target.debuffs.append(debuff)
                total_value += effect.value_base

        return CombatAction(
            action_type=primary_effect_type,
            caster_id=caster.unit_id,
            target_id=target.unit_id,
            skill_id="",
            value=total_value,
            element=element,
            is_crit=is_crit,
        )


# ============================================================================
# 技能库 SKILL_REGISTRY
# ============================================================================

SKILL_REGISTRY: Dict[str, CombatSkill] = {}


def register_skill(skill: CombatSkill):
    """注册技能到技能库"""
    SKILL_REGISTRY[skill.skill_id] = skill


# 青云门 (风系)
register_skill(CombatSkill(
    skill_id="qingyun_sword_qi",
    name="青云剑气",
    description="凝聚青云真气，挥出强劲剑气，对单体敌人造成风属性伤害",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.SINGLE_ENEMY,
    mp_cost=10,
    cooldown=0,
    effects=[
        SkillEffect(
            effect_type="damage",
            value_base=30,
            value_scaling=1.2,
            scaling_stat="attack",
            element=Element.WIND,
        )
    ],
    required_sect="青云门",
    element=Element.WIND,
))

register_skill(CombatSkill(
    skill_id="feng_xing_shu",
    name="风行术",
    description="借助风力提升自身速度",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.SELF,
    mp_cost=15,
    cooldown=3,
    effects=[
        SkillEffect(
            effect_type="buff",
            value_base=20,
            value_scaling=0.0,
            scaling_stat="speed",
            buff_id="speed_boost",
            duration=3,
        )
    ],
    required_sect="青云门",
    element=Element.WIND,
))

register_skill(CombatSkill(
    skill_id="yu_feng_sword_jue",
    name="御风剑诀",
    description="御风而行，连续挥出多道剑气",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.SINGLE_ENEMY,
    mp_cost=25,
    cooldown=2,
    effects=[
        SkillEffect(
            effect_type="damage",
            value_base=20,
            value_scaling=0.8,
            scaling_stat="attack",
            element=Element.WIND,
            hit_count=3,
        )
    ],
    required_level=10,
    required_sect="青云门",
    element=Element.WIND,
))

# 丹鼎门 (火系)
register_skill(CombatSkill(
    skill_id="sanmei_zhenhuo",
    name="三昧真火",
    description="凝聚体内真火，对单体敌人造成火属性伤害",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.SINGLE_ENEMY,
    mp_cost=15,
    cooldown=0,
    effects=[
        SkillEffect(
            effect_type="damage",
            value_base=35,
            value_scaling=1.5,
            scaling_stat="magic_attack",
            element=Element.FIRE,
        )
    ],
    required_sect="丹鼎门",
    element=Element.FIRE,
))

register_skill(CombatSkill(
    skill_id="yan_long_shu",
    name="炎龙术",
    description="召唤炎龙之魂，对全体敌人造成火属性伤害",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.ALL_ENEMIES,
    mp_cost=30,
    cooldown=3,
    effects=[
        SkillEffect(
            effect_type="damage",
            value_base=40,
            value_scaling=1.2,
            scaling_stat="magic_attack",
            element=Element.FIRE,
        )
    ],
    required_level=10,
    required_sect="丹鼎门",
    element=Element.FIRE,
))

register_skill(CombatSkill(
    skill_id="hui_chun_dan",
    name="回春丹",
    description="炼制回春丹，恢复友方生命值",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.SINGLE_ALLY,
    mp_cost=20,
    cooldown=2,
    effects=[
        SkillEffect(
            effect_type="heal",
            value_base=50,
            value_scaling=1.0,
            scaling_stat="intellect",
        )
    ],
    required_sect="丹鼎门",
))

# 万花谷 (木系)
register_skill(CombatSkill(
    skill_id="wanhua_yishu",
    name="万花医术",
    description="施展万花谷秘传医术，强力恢复友方生命值",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.SINGLE_ALLY,
    mp_cost=25,
    cooldown=2,
    effects=[
        SkillEffect(
            effect_type="heal",
            value_base=80,
            value_scaling=1.5,
            scaling_stat="intellect",
        )
    ],
    required_sect="万花谷",
    element=Element.WOOD,
))

register_skill(CombatSkill(
    skill_id="du_wu",
    name="毒雾",
    description="释放毒雾，对全体敌人施加中毒效果",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.ALL_ENEMIES,
    mp_cost=20,
    cooldown=3,
    effects=[
        SkillEffect(
            effect_type="debuff",
            value_base=15,
            value_scaling=0.5,
            scaling_stat="magic_attack",
            element=Element.WOOD,
            debuff_id="poison",
            duration=3,
        )
    ],
    required_level=5,
    required_sect="万花谷",
    element=Element.WOOD,
))

register_skill(CombatSkill(
    skill_id="hua_ling_zhaohuan",
    name="花灵召唤",
    description="召唤花灵协助战斗，对敌人造成持续伤害",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.SINGLE_ENEMY,
    mp_cost=30,
    cooldown=4,
    effects=[
        SkillEffect(
            effect_type="damage",
            value_base=25,
            value_scaling=0.8,
            scaling_stat="magic_attack",
            element=Element.WOOD,
            debuff_id="flower_curse",
            duration=3,
        )
    ],
    required_level=15,
    required_sect="万花谷",
    element=Element.WOOD,
))

# 逍遥宗 (虚系)
register_skill(CombatSkill(
    skill_id="xiaoyao_bu",
    name="逍遥步",
    description="施展逍遥步法，提升自身闪避率",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.SELF,
    mp_cost=12,
    cooldown=3,
    effects=[
        SkillEffect(
            effect_type="buff",
            value_base=30,
            value_scaling=0.0,
            scaling_stat="dodge_rate",
            buff_id="dodge_boost",
            duration=3,
        )
    ],
    required_sect="逍遥宗",
    element=Element.VOID,
))

register_skill(CombatSkill(
    skill_id="xukong_zhan",
    name="虚空斩",
    description="斩破虚空，对单体敌人造成高伤害",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.SINGLE_ENEMY,
    mp_cost=30,
    cooldown=2,
    effects=[
        SkillEffect(
            effect_type="damage",
            value_base=60,
            value_scaling=2.0,
            scaling_stat="attack",
            element=Element.VOID,
        )
    ],
    required_level=10,
    required_sect="逍遥宗",
    element=Element.VOID,
))

register_skill(CombatSkill(
    skill_id="huan_jing",
    name="幻境",
    description="制造幻境，使敌人陷入困惑状态",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.SINGLE_ENEMY,
    mp_cost=25,
    cooldown=4,
    effects=[
        SkillEffect(
            effect_type="debuff",
            value_base=20,
            value_scaling=0.0,
            scaling_stat="accuracy",
            debuff_id="confusion",
            duration=2,
        )
    ],
    required_level=15,
    required_sect="逍遥宗",
    element=Element.VOID,
))

# 蜀山派 (雷系)
register_skill(CombatSkill(
    skill_id="shushan_swordfa",
    name="蜀山剑法",
    description="蜀山派基础剑法，造成物理伤害",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.SINGLE_ENEMY,
    mp_cost=8,
    cooldown=0,
    effects=[
        SkillEffect(
            effect_type="damage",
            value_base=40,
            value_scaling=1.5,
            scaling_stat="attack",
            element=Element.PHYSICAL,
        )
    ],
    required_sect="蜀山派",
    element=Element.LIGHTNING,
))

register_skill(CombatSkill(
    skill_id="zixiao_shenlei",
    name="紫霄神雷",
    description="召唤紫霄神雷，对全体敌人造成雷属性伤害",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.ALL_ENEMIES,
    mp_cost=35,
    cooldown=4,
    effects=[
        SkillEffect(
            effect_type="damage",
            value_base=50,
            value_scaling=1.3,
            scaling_stat="magic_attack",
            element=Element.LIGHTNING,
        )
    ],
    required_level=10,
    required_sect="蜀山派",
    element=Element.LIGHTNING,
))

register_skill(CombatSkill(
    skill_id="wanjian_guizong",
    name="万剑归宗",
    description="蜀山派终极剑诀，召唤万千飞剑",
    skill_type=SkillType.ACTIVE,
    target_type=SkillTarget.ALL_ENEMIES,
    mp_cost=50,
    cooldown=6,
    effects=[
        SkillEffect(
            effect_type="damage",
            value_base=80,
            value_scaling=2.0,
            scaling_stat="attack",
            element=Element.LIGHTNING,
            hit_count=5,
        )
    ],
    required_level=30,
    required_sect="蜀山派",
    element=Element.LIGHTNING,
))


def get_skill(skill_id: str) -> Optional[CombatSkill]:
    """获取技能克隆实例"""
    skill = SKILL_REGISTRY.get(skill_id)
    if skill:
        return skill.clone()
    return None


def get_skills_by_sect(sect_name: str) -> List[CombatSkill]:
    """获取门派所有技能"""
    return [
        skill.clone()
        for skill in SKILL_REGISTRY.values()
        if skill.required_sect == sect_name
    ]


if __name__ == "__main__":
    # 测试技能系统
    print("测试战斗技能系统")

    # 创建战斗单位
    player = CombatUnit(
        unit_id="player1",
        name="青云弟子",
        level=10,
        hp=200,
        max_hp=200,
        mp=100,
        max_mp=100,
        attack=50,
        defense=20,
        magic_attack=30,
        magic_resist=15,
        speed=15,
        element=Element.WIND,
    )

    enemy = CombatUnit(
        unit_id="enemy1",
        name="山贼",
        level=8,
        hp=150,
        max_hp=150,
        mp=50,
        max_mp=50,
        attack=30,
        defense=15,
        magic_resist=10,
    )

    # 创建技能执行器
    damage_calc = DamageCalculator()
    executor = SkillExecutor(damage_calc)

    # 测试青云剑气
    skill = get_skill("qingyun_sword_qi")
    print(f"\n使用技能: {skill.name}")
    print(f"描述: {skill.description}")

    actions = executor.execute_skill(skill, player, [enemy])
    for action in actions:
        print(f"对 {enemy.name} 造成 {action.value} 点伤害 (暴击: {action.is_crit})")
        print(f"敌人剩余HP: {enemy.hp}/{enemy.max_hp}")

    # 测试万花医术
    healer = CombatUnit(
        unit_id="healer1",
        name="万花谷弟子",
        level=10,
        hp=150,
        max_hp=150,
        mp=100,
        max_mp=100,
        intellect=40,
    )

    heal_skill = get_skill("wanhua_yishu")
    print(f"\n使用技能: {heal_skill.name}")

    actions = executor.execute_skill(heal_skill, healer, [player])
    for action in actions:
        print(f"对 {player.name} 恢复 {action.value} 点生命值")
        print(f"玩家剩余HP: {player.hp}/{player.max_hp}")

    print("\n技能系统测试完成")
