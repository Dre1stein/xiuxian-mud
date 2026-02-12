"""
Catch-up Mechanics - 回归玩家加速机制

根据离线时长给予不同的加成，帮助回归玩家快速追赶进度
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from enum import Enum


class CatchUpTier(Enum):
    """回归玩家加速等级"""
    NONE = "none"          # 活跃玩家
    LIGHT = "light"        # 离线 7-14 天
    MODERATE = "moderate"  # 离线 14-30 天
    HEAVY = "heavy"        # 离线 30-90 天
    EXTREME = "extreme"    # 离线 90+ 天


@dataclass
class CatchUpBonus:
    """回归玩家加成详情"""
    tier: CatchUpTier
    offline_days: float

    # 加成
    xp_multiplier: float = 1.0
    stone_multiplier: float = 1.0
    drop_rate_bonus: float = 0.0

    # 持续时间
    duration_days: int = 0
    expires_at: Optional[str] = None  # ISO datetime string

    # 即时奖励
    instant_xp: int = 0
    instant_spirit_stones: int = 0

    # 领取状态
    instant_claimed: bool = False


# 回归等级配置
CATCH_UP_CONFIG = {
    CatchUpTier.NONE: {
        "min_days": 0,
        "max_days": 7,
        "xp_mult": 1.0,
        "stone_mult": 1.0,
        "drop_bonus": 0.0,
        "duration_days": 0,
        "instant_xp": 0,
        "instant_stones": 0,
    },
    CatchUpTier.LIGHT: {
        "min_days": 7,
        "max_days": 14,
        "xp_mult": 1.25,
        "stone_mult": 1.25,
        "drop_bonus": 0.05,
        "duration_days": 3,
        "instant_xp": 10000,
        "instant_stones": 5000,
    },
    CatchUpTier.MODERATE: {
        "min_days": 14,
        "max_days": 30,
        "xp_mult": 1.5,
        "stone_mult": 1.5,
        "drop_bonus": 0.10,
        "duration_days": 7,
        "instant_xp": 50000,
        "instant_stones": 25000,
    },
    CatchUpTier.HEAVY: {
        "min_days": 30,
        "max_days": 90,
        "xp_mult": 2.0,
        "stone_mult": 2.0,
        "drop_bonus": 0.15,
        "duration_days": 14,
        "instant_xp": 200000,
        "instant_stones": 100000,
    },
    CatchUpTier.EXTREME: {
        "min_days": 90,
        "max_days": 999999,
        "xp_mult": 3.0,
        "stone_mult": 3.0,
        "drop_bonus": 0.25,
        "duration_days": 30,
        "instant_xp": 1000000,
        "instant_stones": 500000,
    },
}


class CatchUpMechanics:
    """
    回归玩家加速机制

    根据离线时长给予不同的加成
    """

    def __init__(self):
        pass

    def calculate_catch_up_bonus(
        self,
        last_online: datetime,
        current_time: Optional[datetime] = None,
        player_level: int = 1
    ) -> CatchUpBonus:
        """
        计算回归加成

        Args:
            last_online: 上次在线时间
            current_time: 当前时间 (默认现在)
            player_level: 玩家等级 (影响即时奖励)

        Returns:
            CatchUpBonus 包含所有加成详情
        """
        if current_time is None:
            current_time = datetime.now()

        # 计算离线天数
        offline_delta = current_time - last_online
        offline_days = offline_delta.total_seconds() / 86400

        # 获取回归等级
        tier = self.get_tier_from_days(offline_days)

        # 获取配置
        config = CATCH_UP_CONFIG[tier]

        # 计算即时奖励 (按等级缩放: +1% per level)
        level_multiplier = 1.0 + (player_level - 1) * 0.01
        instant_xp = int(config["instant_xp"] * level_multiplier)
        instant_stones = int(config["instant_stones"] * level_multiplier)

        # 计算过期时间
        expires_at = None
        if config["duration_days"] > 0:
            expires_at = (current_time + timedelta(days=config["duration_days"])).isoformat()

        bonus = CatchUpBonus(
            tier=tier,
            offline_days=offline_days,
            xp_multiplier=config["xp_mult"],
            stone_multiplier=config["stone_mult"],
            drop_rate_bonus=config["drop_bonus"],
            duration_days=config["duration_days"],
            expires_at=expires_at,
            instant_xp=instant_xp,
            instant_spirit_stones=instant_stones,
            instant_claimed=False,
        )

        return bonus

    def get_tier_from_days(self, offline_days: float) -> CatchUpTier:
        """
        根据离线天数获取加速等级

        Args:
            offline_days: 离线天数

        Returns:
            对应的 CatchUpTier
        """
        for tier, config in CATCH_UP_CONFIG.items():
            if config["min_days"] <= offline_days < config["max_days"]:
                return tier
        # 默认返回 NONE
        return CatchUpTier.NONE

    def is_catch_up_active(
        self,
        catch_up_bonus: CatchUpBonus,
        current_time: Optional[datetime] = None
    ) -> bool:
        """
        检查加成是否仍有效

        Args:
            catch_up_bonus: 回归加成数据
            current_time: 当前时间 (默认现在)

        Returns:
            True 如果加成仍有效
        """
        if current_time is None:
            current_time = datetime.now()

        # NONE 等级没有加成
        if catch_up_bonus.tier == CatchUpTier.NONE:
            return False

        # 如果没有过期时间，说明没有持续加成
        if catch_up_bonus.expires_at is None:
            return False

        try:
            expires_at = datetime.fromisoformat(catch_up_bonus.expires_at)
            return current_time < expires_at
        except (ValueError, TypeError):
            return False

    def claim_instant_reward(self, bonus: CatchUpBonus) -> Dict[str, Any]:
        """
        领取即时奖励

        Args:
            bonus: 回归加成数据

        Returns:
            {"success": bool, "rewards": {...}, "error": str}
        """
        if bonus.tier == CatchUpTier.NONE:
            return {
                "success": False,
                "rewards": {},
                "error": "No catch-up bonus available for active players"
            }

        if bonus.instant_claimed:
            return {
                "success": False,
                "rewards": {},
                "error": "Instant rewards already claimed"
            }

        # 标记为已领取
        bonus.instant_claimed = True

        # 返回奖励
        return {
            "success": True,
            "rewards": {
                "xp": bonus.instant_xp,
                "spirit_stones": bonus.instant_spirit_stones,
            },
            "error": None
        }

    def to_dict(self, bonus: CatchUpBonus) -> Dict[str, Any]:
        """
        转换为可存储的字典

        Args:
            bonus: 回归加成数据

        Returns:
            可序列化的字典
        """
        return {
            "tier": bonus.tier.value,
            "offline_days": bonus.offline_days,
            "xp_multiplier": bonus.xp_multiplier,
            "stone_multiplier": bonus.stone_multiplier,
            "drop_rate_bonus": bonus.drop_rate_bonus,
            "duration_days": bonus.duration_days,
            "expires_at": bonus.expires_at,
            "instant_xp": bonus.instant_xp,
            "instant_spirit_stones": bonus.instant_spirit_stones,
            "instant_claimed": bonus.instant_claimed,
        }

    def from_dict(self, data: Dict[str, Any]) -> CatchUpBonus:
        """
        从字典创建 CatchUpBonus

        Args:
            data: 包含回归加成数据的字典

        Returns:
            CatchUpBonus 实例
        """
        tier_value = data.get("tier", "none")
        tier = CatchUpTier(tier_value)

        return CatchUpBonus(
            tier=tier,
            offline_days=data.get("offline_days", 0.0),
            xp_multiplier=data.get("xp_multiplier", 1.0),
            stone_multiplier=data.get("stone_multiplier", 1.0),
            drop_rate_bonus=data.get("drop_rate_bonus", 0.0),
            duration_days=data.get("duration_days", 0),
            expires_at=data.get("expires_at"),
            instant_xp=data.get("instant_xp", 0),
            instant_spirit_stones=data.get("instant_spirit_stones", 0),
            instant_claimed=data.get("instant_claimed", False),
        )
