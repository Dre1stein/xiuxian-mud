"""
修仙游戏战斗系统
Combat System for Cultivation Game
"""

from .damage import Element, DamageType, DamageCalculator, DamageResult
from .skills import (
    SkillType,
    SkillTarget,
    SkillEffect,
    CombatSkill,
    CombatAction,
    CombatUnit,
    SkillExecutor,
    SKILL_REGISTRY,
    get_skill,
    get_skills_by_sect,
)

__all__ = [
    # Damage module
    "Element",
    "DamageType",
    "DamageCalculator",
    "DamageResult",
    # Skills module
    "SkillType",
    "SkillTarget",
    "SkillEffect",
    "CombatSkill",
    "CombatAction",
    "CombatUnit",
    "SkillExecutor",
    "SKILL_REGISTRY",
    "get_skill",
    "get_skills_by_sect",
]

# 版本信息
__version__ = "1.0.0"
