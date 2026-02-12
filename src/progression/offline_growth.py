"""
Offline Growth Calculator - 计算玩家离线期间的成长奖励

核心功能:
1. 计算离线时间 (含上限处理)
2. 检查激活条件
3. 应用境界倍率
4. 计算各类奖励来源
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import yaml
import os


class OfflineRewardType(Enum):
    XP = "xp"
    SPIRIT_STONES = "spirit_stones"
    CULTIVATION = "cultivation"


@dataclass
class OfflineReward:
    """单个离线奖励"""
    reward_type: OfflineRewardType
    amount: int
    source: str
    hours_accumulated: float = 0.0
    rate_per_hour: float = 0.0


@dataclass
class OfflineAccumulation:
    """完整的离线积累数据"""
    player_id: str
    last_online: datetime
    calculated_at: datetime
    offline_hours: float

    # 资格
    is_eligible: bool
    ineligibility_reason: Optional[str] = None

    # 积累的奖励
    rewards: List[OfflineReward] = field(default_factory=list)
    total_xp: int = 0
    total_spirit_stones: int = 0
    total_cultivation: int = 0

    # 上限信息
    capped_hours: float = 0.0
    cap_limit_hours: float = 336.0


class OfflineGrowthCalculator:
    """
    离线成长计算器

    从 config/progression/offline_growth.yaml 加载配置
    """

    DEFAULT_CONFIG = {
        "offline_growth": {
            "enabled": True,
            "growth_rate_percentage": 0.20,
            "max_accumulation_hours": 336,
            "min_accumulation_hours": 1,
            "activation": {
                "min_level": 10,
                "min_playtime_hours": 10,
                "require_any": True
            },
            "stage_multipliers": {},
            "reward_sources": {}
        }
    }

    def __init__(self, config_path: str = "config/progression/offline_growth.yaml"):
        self.config = self._load_config(config_path)
        self.growth_config = self.config.get("offline_growth", self.DEFAULT_CONFIG["offline_growth"])

    def _load_config(self, config_path: str) -> Dict:
        """加载YAML配置"""
        if not os.path.exists(config_path):
            return self.DEFAULT_CONFIG

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if loaded is None:
                    return self.DEFAULT_CONFIG
                return loaded
        except (yaml.YAMLError, IOError, OSError):
            return self.DEFAULT_CONFIG

    def check_eligibility(
        self,
        player_level: int,
        total_playtime_hours: float
    ) -> Tuple[bool, Optional[str]]:
        """
        检查玩家是否有资格获得离线奖励

        Returns:
            (is_eligible, reason_if_not)
        """
        if not self.growth_config.get("enabled", True):
            return False, "Offline growth is disabled"

        activation = self.growth_config.get("activation", {})
        min_level = activation.get("min_level", 10)
        min_playtime = activation.get("min_playtime_hours", 10)
        require_any = activation.get("require_any", True)

        level_meets = player_level >= min_level
        playtime_meets = total_playtime_hours >= min_playtime

        if require_any:
            if level_meets or playtime_meets:
                return True, None
            return False, f"Requires Level {min_level}+ or {min_playtime}h playtime"
        else:
            if level_meets and playtime_meets:
                return True, None
            reasons = []
            if not level_meets:
                reasons.append(f"Level {min_level}+")
            if not playtime_meets:
                reasons.append(f"{min_playtime}h playtime")
            return False, f"Requires: {', '.join(reasons)}"

    def get_stage_multiplier(self, stage: str) -> float:
        """获取境界倍率"""
        multipliers = self.growth_config.get("stage_multipliers", {})
        return multipliers.get(stage, 1.0)

    def calculate_offline_rewards(
        self,
        player_id: str,
        last_online: datetime,
        current_time: Optional[datetime] = None,
        player_level: int = 1,
        player_stage: str = "炼气期",
        total_playtime_hours: float = 0.0,
        has_sect: bool = False
    ) -> OfflineAccumulation:
        """
        计算所有离线奖励

        这是主要入口点
        """
        if current_time is None:
            current_time = datetime.now()

        # 计算离线时间
        offline_delta = current_time - last_online
        offline_hours = offline_delta.total_seconds() / 3600

        # 检查最小积累时间
        min_hours = self.growth_config.get("min_accumulation_hours", 1)
        if offline_hours < min_hours:
            return OfflineAccumulation(
                player_id=player_id,
                last_online=last_online,
                calculated_at=current_time,
                offline_hours=offline_hours,
                is_eligible=False,
                ineligibility_reason=f"Offline time ({offline_hours:.1f}h) below minimum ({min_hours}h)"
            )

        # 检查激活条件
        is_eligible, ineligibility_reason = self.check_eligibility(player_level, total_playtime_hours)

        cap_limit = self.growth_config.get("max_accumulation_hours", 336)
        effective_hours = min(offline_hours, cap_limit)
        capped_hours = max(0, offline_hours - cap_limit)

        accumulation = OfflineAccumulation(
            player_id=player_id,
            last_online=last_online,
            calculated_at=current_time,
            offline_hours=offline_hours,
            is_eligible=is_eligible,
            ineligibility_reason=ineligibility_reason if not is_eligible else None,
            capped_hours=capped_hours,
            cap_limit_hours=cap_limit
        )

        if not is_eligible:
            return accumulation

        # 获取成长率
        growth_rate = self.growth_config.get("growth_rate_percentage", 0.20)

        # 获取境界倍率
        stage_multiplier = self.get_stage_multiplier(player_stage)

        # 获取奖励源配置
        reward_sources = self.growth_config.get("reward_sources", {})

        # 计算各类奖励
        rewards = []

        # 冥想奖励
        meditation = reward_sources.get("meditation", {})
        if meditation.get("enabled", True):
            xp_per_hour = meditation.get("xp_per_hour", 5)
            stones_per_hour = meditation.get("stones_per_hour", 2)

            xp_amount = int(xp_per_hour * effective_hours * growth_rate * stage_multiplier)
            stones_amount = int(stones_per_hour * effective_hours * growth_rate * stage_multiplier)

            if xp_amount > 0:
                rewards.append(OfflineReward(
                    reward_type=OfflineRewardType.XP,
                    amount=xp_amount,
                    source="meditation",
                    hours_accumulated=effective_hours,
                    rate_per_hour=xp_per_hour * growth_rate * stage_multiplier
                ))
                accumulation.total_xp += xp_amount

            if stones_amount > 0:
                rewards.append(OfflineReward(
                    reward_type=OfflineRewardType.SPIRIT_STONES,
                    amount=stones_amount,
                    source="meditation",
                    hours_accumulated=effective_hours,
                    rate_per_hour=stones_per_hour * growth_rate * stage_multiplier
                ))
                accumulation.total_spirit_stones += stones_amount

        # 门派津贴
        sect_allowance = reward_sources.get("sect_allowance", {})
        if sect_allowance.get("enabled", True):
            if not sect_allowance.get("requires_sect", True) or has_sect:
                stones_per_hour = sect_allowance.get("stones_per_hour", 1)
                cult_per_hour = sect_allowance.get("cultivation_per_hour", 1)

                stones_amount = int(stones_per_hour * effective_hours * growth_rate * stage_multiplier)
                cult_amount = int(cult_per_hour * effective_hours * growth_rate * stage_multiplier)

                if stones_amount > 0:
                    rewards.append(OfflineReward(
                        reward_type=OfflineRewardType.SPIRIT_STONES,
                        amount=stones_amount,
                        source="sect_allowance",
                        hours_accumulated=effective_hours,
                        rate_per_hour=stones_per_hour * growth_rate * stage_multiplier
                    ))
                    accumulation.total_spirit_stones += stones_amount

                if cult_amount > 0:
                    rewards.append(OfflineReward(
                        reward_type=OfflineRewardType.CULTIVATION,
                        amount=cult_amount,
                        source="sect_allowance",
                        hours_accumulated=effective_hours,
                        rate_per_hour=cult_per_hour * growth_rate * stage_multiplier
                    ))
                    accumulation.total_cultivation += cult_amount

        # 被动修炼
        passive = reward_sources.get("passive_cultivation", {})
        if passive.get("enabled", True):
            xp_per_hour = passive.get("xp_per_hour", 3)
            cult_per_hour = passive.get("cultivation_per_hour", 2)

            xp_amount = int(xp_per_hour * effective_hours * growth_rate * stage_multiplier)
            cult_amount = int(cult_per_hour * effective_hours * growth_rate * stage_multiplier)

            if xp_amount > 0:
                rewards.append(OfflineReward(
                    reward_type=OfflineRewardType.XP,
                    amount=xp_amount,
                    source="passive_cultivation",
                    hours_accumulated=effective_hours,
                    rate_per_hour=xp_per_hour * growth_rate * stage_multiplier
                ))
                accumulation.total_xp += xp_amount

            if cult_amount > 0:
                rewards.append(OfflineReward(
                    reward_type=OfflineRewardType.CULTIVATION,
                    amount=cult_amount,
                    source="passive_cultivation",
                    hours_accumulated=effective_hours,
                    rate_per_hour=cult_per_hour * growth_rate * stage_multiplier
                ))
                accumulation.total_cultivation += cult_amount

        accumulation.rewards = rewards
        return accumulation
