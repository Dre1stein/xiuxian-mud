"""
QA Validation - 修仙游戏长期养成系统 (PyTest Compatible)

Comprehensive validation test suite for all progression systems.
Tests offline growth, milestones, daily activity, catch-up mechanics, and time curve.
"""
import pytest
from datetime import datetime, date, timedelta

from src.progression import (
    OfflineGrowthCalculator, OfflineAccumulation,
    ProgressionMilestoneTracker, Milestone, PlayerMilestones,
    DailyActivityTracker, ActivityStreak, STREAK_REWARDS,
    CatchUpMechanics, CatchUpBonus, CatchUpTier,
    TimeCurveCalculator, StageTimeAllocation
)
from src.web.offline_routes import offline_bp

# ============================================================================
# OFFLINE GROWTH SYSTEM TESTS
# ============================================================================

class TestOfflineGrowthSystem:
    """Test suite for offline growth system"""

    def test_7_days_offline_rewards(self):
        """Test 1: 7天离线 - should calculate rewards correctly"""
        calc = OfflineGrowthCalculator()
        last_online = datetime.now() - timedelta(days=7)

        result = calc.calculate_offline_rewards(
            player_id="test_player",
            last_online=last_online,
            player_level=50,
            player_stage="金丹期",
            total_playtime_hours=100,
            has_sect=True
        )

        assert result.is_eligible == True
        assert result.offline_hours >= 167
        assert result.offline_hours < 169
        assert result.total_xp > 0
        assert result.total_spirit_stones > 0

    def test_15_days_offline_capped(self):
        """Test 2: 15天离线 - should apply cap"""
        calc = OfflineGrowthCalculator()
        last_online = datetime.now() - timedelta(days=15)

        result = calc.calculate_offline_rewards(
            player_id="test_player",
            last_online=last_online,
            player_level=50,
            player_stage="金丹期",
            total_playtime_hours=100,
            has_sect=True
        )

        assert result.capped_hours > 0
        assert result.cap_limit_hours == 336

    def test_inactive_player_not_eligible(self):
        """Test 3: 未激活玩家 - should not be eligible"""
        calc = OfflineGrowthCalculator()
        last_online = datetime.now() - timedelta(days=7)

        result = calc.calculate_offline_rewards(
            player_id="test_player",
            last_online=last_online,
            player_level=5,
            player_stage="炼气期",
            total_playtime_hours=2,
            has_sect=False
        )

        assert result.is_eligible == False
        assert result.ineligibility_reason is not None

    def test_offline_below_minimum(self):
        """Test 4: 离线时间不足 - should not be eligible"""
        calc = OfflineGrowthCalculator()
        last_online = datetime.now() - timedelta(minutes=30)

        result = calc.calculate_offline_rewards(
            player_id="test_player",
            last_online=last_online,
            player_level=20,
            player_stage="筑基期",
            total_playtime_hours=50,
            has_sect=True
        )

        assert result.is_eligible == False
        assert "below minimum" in result.ineligibility_reason.lower()

    def test_stage_multipliers(self):
        """Test 5: 境界倍率 - higher stages should get more rewards"""
        calc = OfflineGrowthCalculator()
        last_online = datetime.now() - timedelta(days=7)

        result_zhuji = calc.calculate_offline_rewards(
            player_id="test_player",
            last_online=last_online,
            player_level=150,
            player_stage="筑基期",
            total_playtime_hours=100,
            has_sect=True
        )

        result_jindan = calc.calculate_offline_rewards(
            player_id="test_player",
            last_online=last_online,
            player_level=250,
            player_stage="金丹期",
            total_playtime_hours=100,
            has_sect=True
        )

        assert result_jindan.total_xp > result_zhuji.total_xp


# ============================================================================
# MILESTONE SYSTEM TESTS
# ============================================================================

class TestMilestoneSystem:
    """Test suite for milestone system"""

    def test_milestones_loaded(self):
        """Test 6: Milestone configuration loaded"""
        tracker = ProgressionMilestoneTracker()
        assert len(tracker.milestones) > 0

    def test_level_progress_tracking(self):
        """Test 7: Level milestone progress tracking"""
        tracker = ProgressionMilestoneTracker()
        progress = tracker.get_player_progress(
            player_id="test_player",
            player_level=100,
            player_stage="筑基期",
            total_playtime_hours=50,
            total_combats=100
        )

        assert progress.completed_count > 0
        assert progress.total_count > 0

    def test_realm_breakthrough(self):
        """Test 8: Realm breakthrough milestone"""
        tracker = ProgressionMilestoneTracker()
        progress = tracker.get_player_progress(
            player_id="test_player",
            player_level=200,
            player_stage="金丹期",
            total_playtime_hours=100,
            total_combats=500
        )

        jindan_milestone = progress.progress.get("breakthrough_jindan")
        assert jindan_milestone is not None
        assert jindan_milestone.is_completed

    def test_claim_milestone(self):
        """Test 9: Claim milestone reward"""
        tracker = ProgressionMilestoneTracker()
        progress = tracker.get_player_progress(
            player_id="test_player",
            player_level=100,
            player_stage="筑基期",
            total_playtime_hours=50,
            total_combats=100
        )

        # Find a completed but unclaimed milestone
        completed_milestone_id = None
        for mid, mprogress in progress.progress.items():
            if mprogress.is_completed and not mprogress.is_claimed:
                completed_milestone_id = mid
                break

        if completed_milestone_id:
            result = tracker.claim_milestone(progress, completed_milestone_id)
            assert result["success"] == True

    def test_duplicate_claim_rejected(self):
        """Test 10: Cannot claim milestone twice"""
        tracker = ProgressionMilestoneTracker()
        progress = tracker.get_player_progress(
            player_id="test_player",
            player_level=100,
            player_stage="筑基期",
            total_playtime_hours=50,
            total_combats=100
        )

        # Find a completed milestone
        completed_milestone_id = None
        for mid, mprogress in progress.progress.items():
            if mprogress.is_completed:
                completed_milestone_id = mid
                break

        if completed_milestone_id:
            # First claim
            tracker.claim_milestone(progress, completed_milestone_id)
            # Second claim should fail
            result = tracker.claim_milestone(progress, completed_milestone_id)
            assert result["success"] == False
            assert "already claimed" in result["error"].lower()


# ============================================================================
# CATCH-UP MECHANICS TESTS
# ============================================================================

class TestCatchUpMechanics:
    """Test suite for catch-up mechanics"""

    def test_light_tier(self):
        """Test 11: Light catch-up tier (7-14 days)"""
        mechanics = CatchUpMechanics()
        last_online = datetime.now() - timedelta(days=10)

        bonus = mechanics.calculate_catch_up_bonus(last_online, player_level=50)
        assert bonus.tier == CatchUpTier.LIGHT
        assert bonus.xp_multiplier == 1.25

    def test_moderate_tier(self):
        """Test 12: Moderate catch-up tier (14-30 days)"""
        mechanics = CatchUpMechanics()
        last_online = datetime.now() - timedelta(days=20)

        bonus = mechanics.calculate_catch_up_bonus(last_online, player_level=50)
        assert bonus.tier == CatchUpTier.MODERATE
        assert bonus.xp_multiplier == 1.5

    def test_heavy_tier(self):
        """Test 13: Heavy catch-up tier (30-90 days)"""
        mechanics = CatchUpMechanics()
        last_online = datetime.now() - timedelta(days=30)

        bonus = mechanics.calculate_catch_up_bonus(last_online, player_level=50)
        assert bonus.tier == CatchUpTier.HEAVY
        assert bonus.xp_multiplier == 2.0

    def test_extreme_tier(self):
        """Test 14: Extreme catch-up tier (90+ days)"""
        mechanics = CatchUpMechanics()
        last_online = datetime.now() - timedelta(days=100)

        bonus = mechanics.calculate_catch_up_bonus(last_online, player_level=50)
        assert bonus.tier == CatchUpTier.EXTREME
        assert bonus.xp_multiplier == 3.0

    def test_level_scaling(self):
        """Test 15: Level scaling for instant rewards"""
        mechanics = CatchUpMechanics()
        last_online = datetime.now() - timedelta(days=30)

        bonus_low = mechanics.calculate_catch_up_bonus(last_online, player_level=10)
        bonus_high = mechanics.calculate_catch_up_bonus(last_online, player_level=100)

        assert bonus_high.instant_xp > bonus_low.instant_xp

    def test_claim_reward(self):
        """Test 16: Claim instant catch-up reward"""
        mechanics = CatchUpMechanics()
        last_online = datetime.now() - timedelta(days=30)

        bonus = mechanics.calculate_catch_up_bonus(last_online, player_level=50)
        result = mechanics.claim_instant_reward(bonus)

        assert result["success"] == True
        assert bonus.instant_claimed == True

    def test_duplicate_claim_rejected(self):
        """Test 17: Cannot claim instant reward twice"""
        mechanics = CatchUpMechanics()
        last_online = datetime.now() - timedelta(days=30)

        bonus = mechanics.calculate_catch_up_bonus(last_online, player_level=50)
        mechanics.claim_instant_reward(bonus)
        result = mechanics.claim_instant_reward(bonus)

        assert result["success"] == False
        assert "already claimed" in result["error"].lower()


# ============================================================================
# TIME CURVE CALCULATOR TESTS
# ============================================================================

class TestTimeCurveCalculator:
    """Test suite for time curve calculator"""

    def test_total_time_calculation(self):
        """Test 18: Total time calculation"""
        calc = TimeCurveCalculator()

        total_online = calc.get_total_online_hours()
        total_offline = calc.get_total_offline_days()

        assert total_online >= 900
        assert total_offline >= 1000

    def test_stage_for_level(self):
        """Test 19: Get stage for level"""
        calc = TimeCurveCalculator()

        stage_50 = calc.get_stage_for_level(50)
        assert stage_50.name == "炼气期"

        stage_150 = calc.get_stage_for_level(150)
        assert stage_150.name == "筑基期"

    def test_progress_percentage(self):
        """Test 20: Progress percentage calculation"""
        calc = TimeCurveCalculator()

        progress = calc.get_progress_percentage(500, 50000000)
        assert "level_progress" in progress
        assert "time_progress" in progress
        assert "current_stage" in progress

    def test_completion_estimate(self):
        """Test 21: Completion time estimation"""
        calc = TimeCurveCalculator()

        estimate = calc.estimate_completion_time(500, daily_play_hours=1.5)
        assert "remaining_days" in estimate
        assert "remaining_months" in estimate
        assert "remaining_years" in estimate


# ============================================================================
# API ROUTE VALIDATION
# ============================================================================

class TestAPIRoutes:
    """Test suite for API routes"""

    def test_blueprint_registered(self):
        """Test 22: Offline blueprint registered"""
        assert offline_bp is not None
        assert offline_bp.name == 'offline'

    def test_blueprint_has_routes(self):
        """Test 23: Blueprint has route functions"""
        # Check that the blueprint has deferred functions (routes are registered)
        assert len(offline_bp.deferred_functions) > 0
        # The deferred functions contain the route registrations
        assert offline_bp.url_prefix == '/api/offline'
