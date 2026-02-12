"""
Time Curve Calculator - 时间曲线计算器

计算1000小时在线/1000天离线的进度分配
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import yaml
import os


@dataclass
class StageTimeAllocation:
    """单个境界的时间分配"""
    name: str
    index: int
    level_start: int
    level_end: int
    online_hours: float
    offline_days: float
    time_multiplier: float
    cumulative_online_hours: float = 0.0
    cumulative_offline_days: float = 0.0


class TimeCurveCalculator:
    """
    时间曲线计算器

    从 config/progression/time_curve.yaml 加载配置
    """

    def __init__(self, config_path: str = "config/progression/time_curve.yaml"):
        self.allocations = self._load_config(config_path)

    def _load_config(self, config_path: str) -> List[StageTimeAllocation]:
        """加载配置并计算累积时间"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        stages = data['time_curve']['stages']
        allocations = []
        cumulative_online = 0.0
        cumulative_offline = 0.0

        for stage_data in stages:
            allocation = StageTimeAllocation(
                name=stage_data['name'],
                index=stage_data['index'],
                level_start=stage_data['level_start'],
                level_end=stage_data['level_end'],
                online_hours=stage_data['online_hours'],
                offline_days=stage_data['offline_days'],
                time_multiplier=stage_data['time_multiplier'],
                cumulative_online_hours=cumulative_online,
                cumulative_offline_days=cumulative_offline
            )
            allocations.append(allocation)

            cumulative_online += allocation.online_hours
            cumulative_offline += allocation.offline_days

            # Update with actual cumulative values
            allocation.cumulative_online_hours = cumulative_online
            allocation.cumulative_offline_days = cumulative_offline

        return allocations

    def get_total_online_hours(self) -> float:
        """获取总在线小时数"""
        if not self.allocations:
            return 0.0
        return self.allocations[-1].cumulative_online_hours

    def get_total_offline_days(self) -> float:
        """获取总离线天数"""
        if not self.allocations:
            return 0.0
        return self.allocations[-1].cumulative_offline_days

    def get_stage_for_level(self, level: int) -> StageTimeAllocation:
        """根据等级获取对应境界"""
        for allocation in reversed(self.allocations):
            if allocation.level_start <= level <= allocation.level_end:
                return allocation
        raise ValueError(f"等级 {level} 超出范围，配置中未定义")

    def get_progress_percentage(
        self,
        current_level: int,
        current_xp: int
    ) -> Dict[str, Any]:
        """
        计算整体进度百分比

        Returns:
            {
                "level_progress": float,
                "time_progress": float,
                "current_stage": str,
                "stages_completed": int
            }
        """
        # 获取当前阶段
        current_stage = self.get_stage_for_level(current_level)
        stages_completed = current_stage.index

        # 计算当前等级内的进度
        level_range = current_stage.level_end - current_stage.level_start + 1
        level_progress = (current_level - current_stage.level_start) / level_range if level_range > 0 else 0

        # 计算时间进度（基于累积时间）
        total_time = self.get_total_online_hours() + self.get_total_offline_days()

        # 计算当前已用时间
        current_time = current_stage.cumulative_online_hours + current_stage.cumulative_offline_days

        # 添加当前等级已花费的时间（基于XP估算）
        # 这里简化处理，只计算当前等级内的进度
        level_range = current_stage.level_end - current_stage.level_start + 1
        if current_level > current_stage.level_start and level_range > 0:
            level_progress_in_stage = (current_level - current_stage.level_start) / level_range
            stage_total_time = current_stage.online_hours + current_stage.offline_days
            current_time += level_progress_in_stage * stage_total_time

        time_progress = min(current_time / total_time, 1.0) if total_time > 0 else 0

        return {
            "level_progress": round(level_progress * 100, 2),
            "time_progress": round(time_progress * 100, 2),
            "current_stage": current_stage.name,
            "stages_completed": int(stages_completed)
        }

    def estimate_completion_time(
        self,
        current_level: int,
        daily_play_hours: float = 1.5,
        offline_efficiency: float = 0.2
    ) -> Dict[str, Any]:
        """
        估算完成时间

        Returns:
            {
                "remaining_online_hours": float,
                "remaining_days": float,
                "remaining_months": float,
                "remaining_years": float
            }
        """
        # 获取当前阶段
        current_stage = self.get_stage_for_level(current_level)

        # 计算剩余等级
        remaining_levels_in_stage = current_stage.level_end - current_level

        # 计算当前阶段剩余时间
        if remaining_levels_in_stage > 0:
            # 计算当前阶段总时间
            stage_time = current_stage.online_hours + current_stage.offline_days
            # 计算已使用时间的比例
            used_levels = current_level - current_stage.level_start
            total_levels = current_stage.level_end - current_stage.level_start + 1
            used_time_ratio = used_levels / total_levels if total_levels > 0 else 0
            remaining_stage_time = stage_time * (1 - used_time_ratio)
        else:
            remaining_stage_time = 0

        # 计算后续所有阶段的时间
        remaining_online_hours = 0.0
        remaining_offline_days = 0.0

        for allocation in self.allocations[current_stage.index + 1:]:
            remaining_online_hours += allocation.online_hours
            remaining_offline_days += allocation.offline_days

        # 加上当前阶段剩余时间
        total_remaining_online_hours = remaining_online_hours + remaining_stage_time * (current_stage.online_hours / (current_stage.online_hours + current_stage.offline_days + 0.0001))
        total_remaining_offline_days = remaining_offline_days + remaining_stage_time * (current_stage.offline_days / (current_stage.online_hours + current_stage.offline_days + 0.0001))

        # 计算总天数
        # 假设每天有daily_play_hours小时在线时间
        offline_equivalent_hours = total_remaining_offline_days * 24 * offline_efficiency
        total_hours_needed = total_remaining_online_hours + offline_equivalent_hours
        total_days_needed = total_hours_needed / daily_play_hours

        return {
            "remaining_online_hours": round(total_remaining_online_hours, 2),
            "remaining_days": round(total_days_needed, 2),
            "remaining_months": round(total_days_needed / 30, 2),
            "remaining_years": round(total_days_needed / 365, 2)
        }