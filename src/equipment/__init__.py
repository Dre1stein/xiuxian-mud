"""
装备系统模块

提供暗黑风格的装备系统，包括:
- 9级稀有度体系
- 词缀系统
- 套装系统
- 强化系统
- 属性计算

使用示例:
    from src.equipment import EquipmentGenerator, Equipment

    generator = get_generator()
    weapon = generator.generate(level=10, slot=EquipmentSlot.WEAPON)
"""

__version__ = "1.0.0"

# 枚举
from .models import Rarity, EquipmentSlot, AffixType

# 数据模型
from .models import (
    AffixInstance,
    Equipment,
    EquipmentSetBonus,
    EquipmentSet,
    PlayerEquipment,
    QUALITY_TO_RARITY_MAP,
    rarity_from_string,
)

# 配置
from .config_loader import EquipmentConfigLoader, get_config_loader

# 核心功能
from .generator import EquipmentGenerator, get_generator
from .calculator import EquipmentCalculator, get_calculator
from .enhancer import EquipmentEnhancer, EnhanceResult, get_enhancer
from .validators import EquipmentValidator, get_validator

__all__ = [
    # 版本
    "__version__",

    # 枚举
    "Rarity",
    "EquipmentSlot",
    "AffixType",

    # 数据模型
    "AffixInstance",
    "Equipment",
    "EquipmentSetBonus",
    "EquipmentSet",
    "PlayerEquipment",
    "QUALITY_TO_RARITY_MAP",
    "rarity_from_string",

    # 配置
    "EquipmentConfigLoader",
    "get_config_loader",

    # 核心功能
    "EquipmentGenerator",
    "get_generator",
    "EquipmentCalculator",
    "get_calculator",
    "EquipmentEnhancer",
    "EnhanceResult",
    "get_enhancer",
    "EquipmentValidator",
    "get_validator",
]