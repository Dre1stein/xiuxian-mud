"""
流派系统 - School/Stream System

8个门派，每个门派5个流派，共40个流派。
每个流派有独特的核心属性、主属性、特色技能。
"""
from __future__ import annotations

import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict

# 从player.py导入SectType，保持门派定义统一
from src.models.player import SectType


class SchoolFocus(Enum):
    """流派核心定位"""
    SPEED_DODGE = "速度闪避"
    CRIT_PENETRATE = "暴击穿透"
    SURVIVAL_MOBILITY = "生存机动"
    BURST_CONTROL = "爆发控制"
    AOE_CONTROL = "AOE控制"
    DEFENSE_REFLECT = "防御反伤"
    HEALING_SUPPORT = "治疗辅助"
    POISON_DOT = "毒素DOT"
    SUMMON_CONTROL = "召唤控制"
    CONTROL_RESTRAINT = "控制束缚"
    PURE_ATTACK = "纯攻击"
    RANGED_AOE = "远程AOE"
    BALANCE = "攻守平衡"
    PARALYSIS = "麻痹控制"
    SWORD_INTENT = "剑意Buff"
    FREEZE_CONTROL = "冻结控制"
    SUPPORT_BUFF = "辅助增益"
    STEALTH_INVISIBILITY = "隐身隐匿"
    REBOUND_BALANCE = "反弹平衡"
    MENTAL_ATTACK = "精神攻击"
    LIFESTEED = "续航吸血"
    TANK_AGGRO = "坦克仇恨"
    DEBUFF_DOT = "DebuffDOT"


class StatType(Enum):
    """属性类型"""
    STRENGTH = "力量"
    AGILITY = "敏捷"
    CONSTITUTION = "体质"
    INTELLECT = "智力"
    WISDOM = "悟性"


@dataclass
class SectSchool:
    """流派数据类"""
    school_id: str
    name: str
    sect: SectType
    focus: str
    primary_stat: str
    secondary_stat: str
    description: str
    skills: List[str] = field(default_factory=list)
    passives: List[str] = field(default_factory=list)
    bonuses: Dict[str, float] = field(default_factory=dict)
    unlock_level: int = 20

    # 流派造诣
    mastery_levels: int = 10
    points_per_level: float = 1.0


@dataclass
class SchoolProgress:
    """流派进度"""
    school_id: str
    points_invested: int = 0
    points_available: int = 0
    unlocked_skills: List[str] = field(default_factory=list)
    active_skills: List[str] = field(default_factory=list)
    mastery_level: int = 1  # 1-10
    skill_investments: Dict[str, int] = field(default_factory=dict)


class SchoolProgressManager:
    """流派进度管理器"""

    MAX_ACTIVE_SKILLS = 3
    POINTS_PER_MASTERY_LEVEL = 10

    def invest_point(self, progress: SchoolProgress, skill_id: str) -> bool:
        """Invest a point into a skill. Returns True if successful."""
        if progress.points_available <= 0:
            return False

        school = get_school_by_id(progress.school_id)
        if not school:
            return False

        if skill_id not in school.skills:
            return False

        progress.points_available -= 1
        progress.points_invested += 1

        if skill_id in progress.skill_investments:
            progress.skill_investments[skill_id] += 1
        else:
            progress.skill_investments[skill_id] = 1

        progress.mastery_level = self.calculate_mastery_level(progress)

        return True

    def unlock_skill(self, progress: SchoolProgress, skill_id: str) -> bool:
        """Unlock a skill if prerequisites met and points available."""
        if skill_id in progress.unlocked_skills:
            return False

        school = get_school_by_id(progress.school_id)
        if not school:
            return False

        if skill_id not in school.skills:
            return False

        skill_index = school.skills.index(skill_id)
        points_required = (skill_index + 1) * 2

        if progress.points_available < points_required:
            return False

        if skill_index > 0:
            prev_skill = school.skills[skill_index - 1]
            if prev_skill not in progress.unlocked_skills:
                return False

        progress.points_available -= points_required
        progress.points_invested += points_required
        progress.unlocked_skills.append(skill_id)

        if skill_id in progress.skill_investments:
            progress.skill_investments[skill_id] += points_required
        else:
            progress.skill_investments[skill_id] = points_required

        progress.mastery_level = self.calculate_mastery_level(progress)

        return True

    def equip_skill(self, progress: SchoolProgress, skill_id: str) -> bool:
        """Equip an unlocked skill to active slot (max 3 active)."""
        if skill_id not in progress.unlocked_skills:
            return False

        if skill_id in progress.active_skills:
            return False

        if len(progress.active_skills) >= self.MAX_ACTIVE_SKILLS:
            return False

        progress.active_skills.append(skill_id)
        return True

    def unequip_skill(self, progress: SchoolProgress, skill_id: str) -> bool:
        """Unequip a skill from active slot."""
        if skill_id not in progress.active_skills:
            return False

        progress.active_skills.remove(skill_id)
        return True

    def get_mastery_bonus(self, progress: SchoolProgress) -> Dict[str, float]:
        """Get stat bonuses based on mastery level."""
        base_bonus = 0.05
        bonus_multiplier = progress.mastery_level * base_bonus

        school = get_school_by_id(progress.school_id)
        if not school:
            return {"all_stats": bonus_multiplier}

        bonuses = {}
        if school.bonuses:
            for stat, base_value in school.bonuses.items():
                bonuses[stat] = base_value * (1 + bonus_multiplier)

        bonuses["mastery_level"] = progress.mastery_level
        bonuses["bonus_multiplier"] = bonus_multiplier

        return bonuses

    def calculate_mastery_level(self, progress: SchoolProgress) -> int:
        """Calculate mastery level (1-10) based on total investments."""
        total_investments = sum(progress.skill_investments.values())
        total_unlocked = len(progress.unlocked_skills) * 5

        total_points = total_investments + total_unlocked
        mastery = (total_points // self.POINTS_PER_MASTERY_LEVEL) + 1

        return min(10, max(1, mastery))

    def add_points(self, progress: SchoolProgress, points: int) -> int:
        """Add points to the progress. Returns new total available."""
        progress.points_available += points
        return progress.points_available

    def get_progress_summary(self, progress: SchoolProgress) -> Dict[str, Any]:
        """Get a summary of the progress."""
        school = get_school_by_id(progress.school_id)

        return {
            "school_id": progress.school_id,
            "school_name": school.name if school else "Unknown",
            "points_available": progress.points_available,
            "points_invested": progress.points_invested,
            "mastery_level": progress.mastery_level,
            "unlocked_skills": progress.unlocked_skills,
            "active_skills": progress.active_skills,
            "skill_investments": progress.skill_investments,
            "mastery_bonus": self.get_mastery_bonus(progress),
            "total_skills": len(school.skills) if school else 0,
            "can_unlock_more": len(progress.unlocked_skills) < len(school.skills) if school else False,
        }


# 流派配置加载器
class SchoolConfigLoader:
    """流派配置加载器"""

    # 必需字段
    REQUIRED_FIELDS = ["school_id", "name", "sect", "focus", "primary_stat", "secondary_stat", "description"]

    def __init__(self, config_path: str = "config/schools.yaml"):
        self.config_path = Path(config_path)
        self._cache: Optional[Dict[str, Any]] = None

    def _load_yaml(self) -> Dict:
        """加载 YAML 文件"""
        if self._cache is not None:
            return self._cache

        if not self.config_path.exists():
            raise FileNotFoundError(f"流派配置文件不存在: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self._cache = data
            return data

    def _validate_school(self, school_data: Dict, index: int) -> None:
        """验证流派数据完整性"""
        missing = [field for field in self.REQUIRED_FIELDS if field not in school_data]
        if missing:
            school_id = school_data.get("school_id", f"index_{index}")
            raise ValueError(f"流派 '{school_id}' 缺少必需字段: {', '.join(missing)}")

        # 验证 sect 是有效的 SectType (支持枚举名或值)
        sect_value = school_data["sect"]
        valid_names = [s.name for s in SectType]
        valid_values = [s.value for s in SectType]
        if sect_value not in valid_names and sect_value not in valid_values:
            raise ValueError(f"流派 '{school_data['school_id']}' 的 sect 值 '{sect_value}' 无效，有效值: {valid_values}")

    def load_schools(self) -> Dict[str, SectSchool]:
        """加载所有流派"""
        data = self._load_yaml()
        schools = {}

        school_list = data.get("schools", [])
        if not school_list:
            raise ValueError("流派配置文件中没有定义任何流派")

        for index, school_data in enumerate(school_list):
            # 验证数据完整性
            self._validate_school(school_data, index)

            # 转换 sect 字符串为 SectType 枚举 (支持枚举名或值)
            sect_str = school_data["sect"]
            sect = SectType[sect_str] if sect_str in [s.name for s in SectType] else SectType(sect_str)

            school = SectSchool(
                school_id=school_data["school_id"],
                name=school_data["name"],
                sect=sect,
                focus=school_data["focus"],
                primary_stat=school_data["primary_stat"],
                secondary_stat=school_data["secondary_stat"],
                description=school_data["description"],
                skills=school_data.get("skills", []),
                passives=school_data.get("passives", []),
                bonuses=school_data.get("bonuses", {}),
                unlock_level=school_data.get("unlock_level", 20)
            )
            schools[school.school_id] = school

        return schools

    def clear_cache(self):
        """清除缓存"""
        self._cache = None


# 全局配置加载器实例
_config_loader: Optional[SchoolConfigLoader] = None


def get_config_loader() -> SchoolConfigLoader:
    """获取全局配置加载器"""
    global _config_loader
    if _config_loader is None:
        _config_loader = SchoolConfigLoader()
    return _config_loader


# 40流派定义
def _initialize_schools() -> Dict[str, SectSchool]:
    """初始化40个流派，从YAML配置加载"""
    loader = get_config_loader()
    return loader.load_schools()


# 初始化所有流派
ALL_SCHOOLS_DICT = _initialize_schools()


def get_all_schools() -> List[SectSchool]:
    """获取所有流派列表"""
    return list(ALL_SCHOOLS_DICT.values())


def get_sect_schools(sect: SectType) -> List[SectSchool]:
    """获取指定门派的所有流派"""
    return [s for s in ALL_SCHOOLS_DICT.values() if s.sect == sect]


def get_school_by_id(school_id: str) -> Optional[SectSchool]:
    """根据ID获取流派"""
    return ALL_SCHOOLS_DICT.get(school_id)


# 流派点数获取规则
SCHOOL_POINT_GAINS = {
    "level_up": 1,      # 每升10级获得1点
    "breakthrough": 10, # 境界突破获得10点
    "quest": 3,          # 完成流派任务获得3点
}


def get_school_point_capacity(player_level: int, cultivation_stage: str) -> int:
    """获取流派点数上限"""
    base_capacity = player_level // 10  # 每10级1点

    # 根据境界加成
    stage_bonus = {
        "炼气期": 0,
        "筑基期": 5,
        "金丹期": 15,
        "元婴期": 30,
        "元神期": 50,
        "化神期": 80,
        "炼虚期": 120,
        "合体期": 170,
        "大乘期": 230,
        "渡劫期": 300,
        "真仙境": 400,
        "金仙境": 550,
        "太乙境": 750,
        "大罗境": 999,
    }.get(cultivation_stage, 0)

    return base_capacity + stage_bonus
