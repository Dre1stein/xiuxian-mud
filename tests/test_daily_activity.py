"""
Test DailyActivityTracker functionality
"""
import sys
sys.path.insert(0, '/home/echo/code_work/game_xiuxian')

from datetime import date, timedelta
from src.progression.daily_activity import (
    DailyActivityTracker,
    ActivityStreak,
    STREAK_REWARDS,
)


def test_continuous_login_30_days():
    """
    验收标准 1: 连续登录 1-30 天，current_streak = 30
    """
    print("Test 1: Continuous login for 30 days...")
    tracker = DailyActivityTracker()
    streak = ActivityStreak(player_id="test_player_1")

    base_date = date(2025, 1, 1)
    for i in range(30):
        login_date = base_date + timedelta(days=i)
        streak = tracker.record_login(streak, login_date)

    assert streak.current_streak == 30, f"Expected 30, got {streak.current_streak}"
    assert streak.longest_streak == 30, f"Expected longest 30, got {streak.longest_streak}"
    print("  PASS: current_streak = 30")


def test_grace_period_2_days():
    """
    验收标准 2: 中断 2 天后登录，current_streak = 29 (不是重置)
    """
    print("\nTest 2: 2-day break (grace period)...")
    tracker = DailyActivityTracker()
    streak = ActivityStreak(player_id="test_player_2")

    base_date = date(2025, 1, 1)
    # 连续登录 30 天
    for i in range(30):
        login_date = base_date + timedelta(days=i)
        streak = tracker.record_login(streak, login_date)

    # 中断 2 天后登录
    login_date = base_date + timedelta(days=32)
    streak = tracker.record_login(streak, login_date)

    assert streak.current_streak == 29, f"Expected 29, got {streak.current_streak}"
    print("  PASS: current_streak = 29 (grace period applied)")


def test_reset_after_5_days():
    """
    验收标准 3: 中断 5 天后登录，current_streak = 1 (重置)
    """
    print("\nTest 3: 5-day break (reset)...")
    tracker = DailyActivityTracker()
    streak = ActivityStreak(player_id="test_player_3")

    base_date = date(2025, 1, 1)
    # 连续登录 30 天
    for i in range(30):
        login_date = base_date + timedelta(days=i)
        streak = tracker.record_login(streak, login_date)

    # 中断 5 天后登录
    login_date = base_date + timedelta(days=35)
    streak = tracker.record_login(streak, login_date)

    assert streak.current_streak == 1, f"Expected 1, got {streak.current_streak}"
    print("  PASS: current_streak = 1 (reset)")


def test_claim_30_day_title():
    """
    验收标准 4: 连续 30 天可领取 "月度修士" 称号
    """
    print("\nTest 4: Claim '月度修士' title at 30 days...")
    tracker = DailyActivityTracker()
    streak = ActivityStreak(player_id="test_player_4")

    base_date = date(2025, 1, 1)
    # 连续登录 30 天
    for i in range(30):
        login_date = base_date + timedelta(days=i)
        streak = tracker.record_login(streak, login_date)

    # 获取可领取奖励
    available = tracker.get_available_streak_rewards(streak)
    thirty_day_reward = [r for r in available if r["milestone_days"] == 30]

    assert len(thirty_day_reward) == 1, f"Expected 1 available reward for 30 days, got {len(thirty_day_reward)}"
    assert thirty_day_reward[0]["rewards"]["title"] == "月度修士", "Expected title '月度修士'"
    print("  PASS: '月度修士' title available at 30 days")

    # 领取奖励
    result = tracker.claim_streak_reward(streak, 30)
    assert result["success"], f"Claim failed: {result.get('error')}"
    assert result["rewards"]["title"] == "月度修士", "Expected '月度修士' title in rewards"
    print("  PASS: Successfully claimed '月度修士' title")


def test_no_duplicate_claim():
    """
    验收标准 5: 奖励不可重复领取
    """
    print("\nTest 5: Cannot claim reward twice...")
    tracker = DailyActivityTracker()
    streak = ActivityStreak(player_id="test_player_5")

    base_date = date(2025, 1, 1)
    # 连续登录 30 天
    for i in range(30):
        login_date = base_date + timedelta(days=i)
        streak = tracker.record_login(streak, login_date)

    # 第一次领取
    result1 = tracker.claim_streak_reward(streak, 30)
    assert result1["success"], f"First claim failed: {result1.get('error')}"

    # 第二次领取
    result2 = tracker.claim_streak_reward(streak, 30)
    assert not result2["success"], "Second claim should fail"
    assert "already claimed" in result2["error"].lower(), f"Expected 'already claimed' error, got: {result2['error']}"
    print("  PASS: Cannot claim reward twice")


def test_grace_period_3_days():
    """
    额外测试: 中断 3 天后登录，current_streak = 29 (宽限期上限)
    Note: 中断3天意味着最后一次登录后过了3天才登录，即 days_since_last = 3
    """
    print("\nTest 6: 3-day break (grace period limit)...")
    tracker = DailyActivityTracker()
    streak = ActivityStreak(player_id="test_player_6")

    base_date = date(2025, 1, 1)
    # 连续登录 30 天 (最后一天是 day 29，即 2025-01-30)
    for i in range(30):
        login_date = base_date + timedelta(days=i)
        streak = tracker.record_login(streak, login_date)

    # 中断 3 天后登录 (最后一次登录是 day 29，现在登录 day 32，差值是 3)
    login_date = base_date + timedelta(days=32)
    streak = tracker.record_login(streak, login_date)

    assert streak.current_streak == 29, f"Expected 29, got {streak.current_streak}"
    print("  PASS: current_streak = 29 (3-day grace period)")


def test_all_milestones():
    """
    额外测试: 所有里程碑里程碑都能正确检测
    """
    print("\nTest 7: All milestone rewards...")
    tracker = DailyActivityTracker()
    streak = ActivityStreak(player_id="test_player_7")

    base_date = date(2025, 1, 1)
    # 连续登录 1000 天
    for i in range(1000):
        login_date = base_date + timedelta(days=i)
        streak = tracker.record_login(streak, login_date)

    available = tracker.get_available_streak_rewards(streak)
    available_milestones = {r["milestone_days"] for r in available}

    expected_milestones = {7, 14, 30, 60, 100, 365, 1000}
    assert available_milestones == expected_milestones, f"Expected {expected_milestones}, got {available_milestones}"
    print(f"  PASS: All {len(expected_milestones)} milestone rewards available")


def test_to_dict_and_from_player():
    """
    额外测试: to_dict 和 create_streak_from_player 正确序列化
    """
    print("\nTest 8: Serialization...")
    tracker = DailyActivityTracker()

    player_data = {
        "player_id": "test_player_8",
        "current_streak": 45,
        "longest_streak": 60,
        "last_login_date": "2025-01-15",
        "milestone_7_claimed": True,
        "milestone_14_claimed": True,
        "milestone_30_claimed": False,
    }

    streak = tracker.create_streak_from_player(player_data)
    assert streak.player_id == "test_player_8"
    assert streak.current_streak == 45
    assert streak.longest_streak == 60
    assert streak.milestone_7_claimed == True
    assert streak.milestone_30_claimed == False

    # 转换回字典
    serialized = tracker.to_dict(streak)
    assert serialized["player_id"] == "test_player_8"
    assert serialized["current_streak"] == 45
    assert serialized["milestone_7_claimed"] == True
    print("  PASS: Serialization works correctly")


if __name__ == "__main__":
    print("=" * 50)
    print("Running DailyActivityTracker Tests")
    print("=" * 50)

    test_continuous_login_30_days()
    test_grace_period_2_days()
    test_reset_after_5_days()
    test_claim_30_day_title()
    test_no_duplicate_claim()
    test_grace_period_3_days()
    test_all_milestones()
    test_to_dict_and_from_player()

    print("\n" + "=" * 50)
    print("All tests PASSED!")
    print("=" * 50)
