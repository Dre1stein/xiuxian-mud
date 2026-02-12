"""
Daily Activity Tracker - 每日活动和连续登录追踪
"""
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum


@dataclass
class ActivityStreak:
    """连续登录数据"""
    player_id: str
    current_streak: int = 0
    longest_streak: int = 0
    last_login_date: Optional[str] = None  # ISO date string

    # 里程碑领取状态
    milestone_7_claimed: bool = False
    milestone_14_claimed: bool = False
    milestone_30_claimed: bool = False
    milestone_60_claimed: bool = False
    milestone_100_claimed: bool = False
    milestone_365_claimed: bool = False
    milestone_1000_claimed: bool = False


# 连续登录奖励配置
STREAK_REWARDS = {
    7: {"spirit_stones": 1000, "school_points": 5, "title": None},
    14: {"spirit_stones": 2500, "school_points": 10, "title": None},
    30: {"spirit_stones": 5000, "school_points": 20, "title": "月度修士"},
    60: {"spirit_stones": 10000, "school_points": 30, "title": None},
    100: {"spirit_stones": 20000, "school_points": 50, "title": "百日道友"},
    365: {"spirit_stones": 100000, "school_points": 100, "title": "年度真修"},
    1000: {"spirit_stones": 1000000, "school_points": 500, "title": "千年仙人"},
}


# 里程碑天数到属性名称的映射
MILESTONE_ATTR_MAP = {
    7: "milestone_7_claimed",
    14: "milestone_14_claimed",
    30: "milestone_30_claimed",
    60: "milestone_60_claimed",
    100: "milestone_100_claimed",
    365: "milestone_365_claimed",
    1000: "milestone_1000_claimed",
}


class DailyActivityTracker:
    """
    每日活动追踪器

    功能:
    1. 连续登录天数追踪
    2. 宽限期处理 (2-3天不断连击)
    3. 连续登录奖励发放
    """

    def __init__(self):
        pass

    def record_login(
        self,
        streak: ActivityStreak,
        login_date: Optional[date] = None
    ) -> ActivityStreak:
        """
        记录登录并更新连续天数

        宽限期规则:
        - 1天后登录: 连击+1
        - 2-3天后登录: 连击-1 (但不重置)
        - 4+天后登录: 连击重置为1

        Args:
            streak: 当前的连续登录数据
            login_date: 登录日期 (默认今天)

        Returns:
            更新后的 ActivityStreak
        """
        if login_date is None:
            login_date = date.today()

        login_str = login_date.isoformat()

        # 首次登录
        if streak.last_login_date is None:
            streak.current_streak = 1
            streak.longest_streak = 1
            streak.last_login_date = login_str
            return streak

        # 解析上次登录日期
        try:
            last_login = datetime.fromisoformat(streak.last_login_date).date()
        except (ValueError, AttributeError):
            last_login = None

        if last_login is None:
            # 无法解析上次登录日期，重置
            streak.current_streak = 1
            streak.last_login_date = login_str
            return streak

        # 同一天登录，不更新连击
        if last_login == login_date:
            return streak

        # 计算距离上次登录的天数
        days_since_last = (login_date - last_login).days

        if days_since_last == 1:
            # 连续登录，连击+1
            streak.current_streak += 1
        elif 2 <= days_since_last <= 3:
            # 宽限期: 连击-1 (但不低于1)
            streak.current_streak = max(1, streak.current_streak - 1)
        else:
            # 4天以上，重置连击
            streak.current_streak = 1

        # 更新最长连击
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        streak.last_login_date = login_str
        return streak

    def get_available_streak_rewards(self, streak: ActivityStreak) -> List[Dict[str, Any]]:
        """
        获取可领取的连续登录奖励

        Returns:
            [{"milestone_days": 7, "rewards": {...}}, ...]
        """
        available = []

        for milestone_days, rewards in STREAK_REWARDS.items():
            # 检查是否已达到里程碑天数
            if streak.current_streak >= milestone_days:
                # 检查是否已领取
                attr_name = MILESTONE_ATTR_MAP.get(milestone_days)
                if attr_name is not None:
                    is_claimed = getattr(streak, attr_name, False)
                    if not is_claimed:
                        available.append({
                            "milestone_days": milestone_days,
                            "rewards": rewards.copy()
                        })

        return available

    def claim_streak_reward(
        self,
        streak: ActivityStreak,
        days: int
    ) -> Dict[str, Any]:
        """
        领取连续登录奖励

        Returns:
            {"success": bool, "milestone_days": int, "rewards": {...}, "error": str}
        """
        # 检查里程碑是否存在
        if days not in STREAK_REWARDS:
            return {
                "success": False,
                "milestone_days": days,
                "rewards": {},
                "error": f"No milestone reward configured for {days} days"
            }

        # 检查是否达到里程碑天数
        if streak.current_streak < days:
            return {
                "success": False,
                "milestone_days": days,
                "rewards": {},
                "error": f"Current streak ({streak.current_streak}) is less than required ({days})"
            }

        # 检查是否已领取
        attr_name = MILESTONE_ATTR_MAP.get(days)
        if attr_name is None:
            return {
                "success": False,
                "milestone_days": days,
                "rewards": {},
                "error": f"Invalid milestone days: {days}"
            }

        if getattr(streak, attr_name, False):
            return {
                "success": False,
                "milestone_days": days,
                "rewards": {},
                "error": f"Reward for {days} days already claimed"
            }

        # 标记为已领取
        setattr(streak, attr_name, True)

        # 返回奖励
        return {
            "success": True,
            "milestone_days": days,
            "rewards": STREAK_REWARDS[days].copy(),
            "error": None
        }

    def create_streak_from_player(self, player_data: Dict[str, Any]) -> ActivityStreak:
        """
        从玩家数据创建 ActivityStreak

        Args:
            player_data: 包含玩家信息的字典，应包含 player_id

        Returns:
            新的 ActivityStreak 实例
        """
        player_id = player_data.get("player_id", "unknown")

        streak = ActivityStreak(
            player_id=player_id,
            current_streak=player_data.get("current_streak", 0),
            longest_streak=player_data.get("longest_streak", 0),
            last_login_date=player_data.get("last_login_date"),
            milestone_7_claimed=player_data.get("milestone_7_claimed", False),
            milestone_14_claimed=player_data.get("milestone_14_claimed", False),
            milestone_30_claimed=player_data.get("milestone_30_claimed", False),
            milestone_60_claimed=player_data.get("milestone_60_claimed", False),
            milestone_100_claimed=player_data.get("milestone_100_claimed", False),
            milestone_365_claimed=player_data.get("milestone_365_claimed", False),
            milestone_1000_claimed=player_data.get("milestone_1000_claimed", False),
        )

        return streak

    def to_dict(self, streak: ActivityStreak) -> Dict[str, Any]:
        """
        将 ActivityStreak 转换为可存储的字典

        Returns:
            包含所有 streak 数据的字典
        """
        return {
            "player_id": streak.player_id,
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
            "last_login_date": streak.last_login_date,
            "milestone_7_claimed": streak.milestone_7_claimed,
            "milestone_14_claimed": streak.milestone_14_claimed,
            "milestone_30_claimed": streak.milestone_30_claimed,
            "milestone_60_claimed": streak.milestone_60_claimed,
            "milestone_100_claimed": streak.milestone_100_claimed,
            "milestone_365_claimed": streak.milestone_365_claimed,
            "milestone_1000_claimed": streak.milestone_1000_claimed,
        }
