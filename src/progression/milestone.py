"""
Progression Milestone Tracker - 追踪玩家里程碑进度
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import yaml
import os


class MilestoneType(Enum):
    REALM = "realm"
    LEVEL = "level"
    PLAYTIME = "playtime"
    COMBAT = "combat"


# 境界顺序参考 - 用于境界里程碑检查
STAGE_ORDER = [
    "炼气期", "筑基期", "金丹期", "元婴期", "元神期",
    "化神期", "炼虚期", "合体期", "大乘期", "渡劫期",
    "真仙境", "金仙境", "太乙境", "大罗境"
]


@dataclass
class Milestone:
    """里程碑定义"""
    id: str
    name: str
    description: str = ""
    type: MilestoneType = MilestoneType.LEVEL

    # 条件
    required_level: int = 0
    required_stage: Optional[str] = None
    required_playtime_hours: float = 0.0
    required_combats: int = 0

    # 奖励
    reward_xp: int = 0
    reward_spirit_stones: int = 0
    reward_school_points: int = 0
    reward_title: Optional[str] = None


@dataclass
class MilestoneProgress:
    """玩家在特定里程碑上的进度"""
    milestone_id: str
    current_value: int = 0
    target_value: int = 0
    is_completed: bool = False
    is_claimed: bool = False
    completed_at: Optional[str] = None
    claimed_at: Optional[str] = None


@dataclass
class PlayerMilestones:
    """玩家的完整里程碑状态"""
    player_id: str
    completed_count: int = 0
    total_count: int = 0
    progress: Dict[str, MilestoneProgress] = field(default_factory=dict)


class ProgressionMilestoneTracker:
    """
    里程碑追踪器

    从 config/progression/milestones.yaml 加载里程碑定义
    """

    DEFAULT_CONFIG = {
        "milestones": {
            "realm": [],
            "level": [],
            "playtime": [],
            "combat": []
        }
    }

    def __init__(self, config_path: str = "config/progression/milestones.yaml"):
        self.milestones = self._load_milestones(config_path)

    def _load_milestones(self, config_path: str) -> Dict[str, Milestone]:
        """加载里程碑配置"""
        if not os.path.exists(config_path):
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config is None:
                    return {}
        except (yaml.YAMLError, IOError, OSError):
            return {}

        milestones = {}
        milestones_config = config.get("milestones", {})

        # 加载各类型里程碑
        for milestone_type in ["realm", "level", "playtime", "combat"]:
            type_config = milestones_config.get(milestone_type, [])
            for milestone_data in type_config:
                milestone = self._parse_milestone(milestone_data, MilestoneType(milestone_type))
                if milestone:
                    milestones[milestone.id] = milestone

        return milestones

    def _parse_milestone(self, data: Dict, milestone_type: MilestoneType) -> Optional[Milestone]:
        """解析单个里程碑配置"""
        if not data or "id" not in data or "name" not in data:
            return None

        rewards = data.get("rewards", {})

        return Milestone(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            type=milestone_type,
            required_level=data.get("required_level", 0),
            required_stage=data.get("required_stage"),
            required_playtime_hours=data.get("required_playtime_hours", 0.0),
            required_combats=data.get("required_combats", 0),
            reward_xp=rewards.get("xp", 0),
            reward_spirit_stones=rewards.get("spirit_stones", 0),
            reward_school_points=rewards.get("school_points", 0),
            reward_title=rewards.get("title")
        )

    def get_player_progress(
        self,
        player_id: str,
        player_level: int,
        player_stage: str,
        total_playtime_hours: float,
        total_combats: int,
        claimed_milestones: Dict[str, str] = None
    ) -> PlayerMilestones:
        """
        获取玩家里程碑进度

        Args:
            player_id: 玩家ID
            player_level: 当前等级
            player_stage: 当前境界
            total_playtime_hours: 累计游戏时间
            total_combats: 累计战斗次数
            claimed_milestones: 已领取的里程碑 {id: claimed_at}

        Returns:
            PlayerMilestones 包含所有里程碑进度
        """
        if claimed_milestones is None:
            claimed_milestones = {}

        progress_dict = {}
        completed_count = 0

        for milestone_id, milestone in self.milestones.items():
            is_completed, current_value, target_value = self.check_milestone_completed(
                milestone, player_level, player_stage, total_playtime_hours, total_combats
            )

            is_claimed = milestone_id in claimed_milestones
            claimed_at = claimed_milestones.get(milestone_id) if is_claimed else None
            completed_at = None

            if is_completed:
                completed_count += 1
                # 如果已领取，使用领取时间；否则使用当前时间
                if is_claimed and claimed_at:
                    completed_at = claimed_at
                else:
                    completed_at = datetime.now().isoformat()

            progress_dict[milestone_id] = MilestoneProgress(
                milestone_id=milestone_id,
                current_value=current_value,
                target_value=target_value,
                is_completed=is_completed,
                is_claimed=is_claimed,
                completed_at=completed_at,
                claimed_at=claimed_at
            )

        return PlayerMilestones(
            player_id=player_id,
            completed_count=completed_count,
            total_count=len(self.milestones),
            progress=progress_dict
        )

    def check_milestone_completed(
        self,
        milestone: Milestone,
        player_level: int,
        player_stage: str,
        total_playtime_hours: float,
        total_combats: int
    ) -> Tuple[bool, int, int]:
        """
        检查单个里程碑是否完成

        Returns:
            (is_completed, current_value, target_value)
        """
        if milestone.type == MilestoneType.LEVEL:
            target_value = milestone.required_level
            current_value = player_level
            return current_value >= target_value, current_value, target_value

        elif milestone.type == MilestoneType.REALM:
            target_value = STAGE_ORDER.index(milestone.required_stage) + 1 if milestone.required_stage in STAGE_ORDER else 999
            current_value = STAGE_ORDER.index(player_stage) + 1 if player_stage in STAGE_ORDER else 0
            return current_value >= target_value, current_value, target_value

        elif milestone.type == MilestoneType.PLAYTIME:
            target_value = int(milestone.required_playtime_hours)
            current_value = int(total_playtime_hours)
            return current_value >= target_value, current_value, target_value

        elif milestone.type == MilestoneType.COMBAT:
            target_value = milestone.required_combats
            current_value = total_combats
            return current_value >= target_value, current_value, target_value

        return False, 0, 0

    def claim_milestone(
        self,
        player_milestones: PlayerMilestones,
        milestone_id: str
    ) -> Dict[str, Any]:
        """
        领取里程碑奖励

        Returns:
            {"success": bool, "rewards": {...}, "error": str}
        """
        if milestone_id not in self.milestones:
            return {"success": False, "error": f"Milestone {milestone_id} not found"}

        milestone = self.milestones[milestone_id]

        if milestone_id not in player_milestones.progress:
            return {"success": False, "error": "Milestone progress not found"}

        progress = player_milestones.progress[milestone_id]

        if not progress.is_completed:
            return {"success": False, "error": "Milestone not completed"}

        if progress.is_claimed:
            return {"success": False, "error": "Milestone already claimed"}

        # 标记为已领取
        progress.is_claimed = True
        progress.claimed_at = datetime.now().isoformat()

        # 返回奖励
        rewards = {}
        if milestone.reward_xp > 0:
            rewards["xp"] = milestone.reward_xp
        if milestone.reward_spirit_stones > 0:
            rewards["spirit_stones"] = milestone.reward_spirit_stones
        if milestone.reward_school_points > 0:
            rewards["school_points"] = milestone.reward_school_points
        if milestone.reward_title:
            rewards["title"] = milestone.reward_title

        return {"success": True, "rewards": rewards}

    def get_milestone_rewards(self, milestone_id: str) -> Optional[Dict[str, Any]]:
        """获取里程碑奖励配置"""
        if milestone_id not in self.milestones:
            return None

        milestone = self.milestones[milestone_id]
        rewards = {}
        if milestone.reward_xp > 0:
            rewards["xp"] = milestone.reward_xp
        if milestone.reward_spirit_stones > 0:
            rewards["spirit_stones"] = milestone.reward_spirit_stones
        if milestone.reward_school_points > 0:
            rewards["school_points"] = milestone.reward_school_points
        if milestone.reward_title:
            rewards["title"] = milestone.reward_title

        return rewards

    def get_milestones_by_type(self, milestone_type: MilestoneType) -> List[Milestone]:
        """按类型获取里程碑列表"""
        return [m for m in self.milestones.values() if m.type == milestone_type]

    def get_milestone(self, milestone_id: str) -> Optional[Milestone]:
        """获取单个里程碑"""
        return self.milestones.get(milestone_id)
