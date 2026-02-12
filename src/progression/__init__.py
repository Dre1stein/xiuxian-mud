"""
Progression System - 角色成长系统

包含:
- OfflineGrowthCalculator: 离线成长计算器
- ProgressionMilestoneTracker: 里程碑追踪器
- DailyActivityTracker: 每日活动和连续登录追踪
- TimeCurveCalculator: 时间曲线计算器
"""

from .offline_growth import (
    OfflineGrowthCalculator,
    OfflineReward,
    OfflineAccumulation,
    OfflineRewardType,
)

from .milestone import (
    ProgressionMilestoneTracker,
    Milestone,
    MilestoneProgress,
    MilestoneType,
    PlayerMilestones,
    STAGE_ORDER,
)

from .daily_activity import (
    DailyActivityTracker,
    ActivityStreak,
    STREAK_REWARDS,
    MILESTONE_ATTR_MAP,
)

from .catch_up import (
    CatchUpMechanics,
    CatchUpBonus,
    CatchUpTier,
    CATCH_UP_CONFIG,
)

from .time_curve import (
    TimeCurveCalculator,
    StageTimeAllocation,
)

__all__ = [
    "OfflineGrowthCalculator",
    "OfflineReward",
    "OfflineAccumulation",
    "OfflineRewardType",
    "ProgressionMilestoneTracker",
    "Milestone",
    "MilestoneProgress",
    "MilestoneType",
    "PlayerMilestones",
    "STAGE_ORDER",
    "DailyActivityTracker",
    "ActivityStreak",
    "STREAK_REWARDS",
    "MILESTONE_ATTR_MAP",
    "CatchUpMechanics",
    "CatchUpBonus",
    "CatchUpTier",
    "CATCH_UP_CONFIG",
    "TimeCurveCalculator",
    "StageTimeAllocation",
]
