"""
Offline and Progression API Routes
"""
from flask import Blueprint, jsonify, request, session
from datetime import datetime, date, timedelta
import traceback

from src.data.storage_factory import get_storage
from src.progression.offline_growth import OfflineGrowthCalculator
from src.progression.milestone import ProgressionMilestoneTracker
from src.progression.daily_activity import DailyActivityTracker, ActivityStreak, STREAK_REWARDS, MILESTONE_ATTR_MAP
from src.progression.catch_up import CatchUpMechanics


offline_bp = Blueprint('offline', __name__, url_prefix='/api/offline')


def _get_player_data():
    """Helper to get logged-in player data."""
    player_name = session.get('player_name')
    if not player_name:
        return None, jsonify({'error': '未登录'}), 401

    player_data = get_storage().load_by_name(player_name)
    if not player_data:
        return None, jsonify({'error': '角色不存在'}), 404

    return player_data, None, None


def _parse_datetime(dt_str):
    """Parse datetime from string or return None."""
    if not dt_str:
        return None
    try:
        if isinstance(dt_str, str):
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt_str
    except (ValueError, AttributeError):
        return None


@offline_bp.route('/rewards', methods=['GET'])
def get_offline_rewards():
    """获取待领取的离线奖励"""
    player_data, error_response, status_code = _get_player_data()
    if error_response:
        return error_response, status_code

    try:
        # Get last active time
        last_active_str = player_data.get('last_active')
        last_active = _parse_datetime(last_active_str)

        if not last_active:
            # First time playing or no last_active set
            last_active = datetime.now()

        # Initialize calculator
        calculator = OfflineGrowthCalculator()

        # Get player stats
        player_level = player_data.get('level', 1)
        player_stage = player_data.get('stage', '炼气期')
        total_playtime = player_data.get('total_playtime_hours', 0.0)
        has_sect = player_data.get('sect') is not None

        # Calculate offline rewards
        accumulation = calculator.calculate_offline_rewards(
            player_id=player_data.get('player_id', ''),
            last_online=last_active,
            current_time=datetime.now(),
            player_level=player_level,
            player_stage=player_stage,
            total_playtime_hours=total_playtime,
            has_sect=has_sect
        )

        # Format rewards for response
        rewards_list = []
        for reward in accumulation.rewards:
            rewards_list.append({
                'type': reward.reward_type.value,
                'amount': reward.amount,
                'source': reward.source
            })

        response = {
            'success': True,
            'offline_rewards': {
                'is_eligible': accumulation.is_eligible,
                'offline_hours': round(accumulation.offline_hours, 2),
                'effective_hours': round(accumulation.offline_hours - accumulation.capped_hours, 2),
                'capped_hours': round(accumulation.capped_hours, 2),
                'rewards': rewards_list,
                'summary': {
                    'total_xp': accumulation.total_xp,
                    'total_spirit_stones': accumulation.total_spirit_stones,
                    'total_cultivation': accumulation.total_cultivation
                }
            }
        }

        if not accumulation.is_eligible:
            response['offline_rewards']['ineligibility_reason'] = accumulation.ineligibility_reason

        return jsonify(response)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'计算离线奖励失败: {str(e)}'
        }), 500


@offline_bp.route('/rewards/claim', methods=['POST'])
def claim_offline_rewards():
    """领取离线奖励"""
    player_data, error_response, status_code = _get_player_data()
    if error_response:
        return error_response, status_code

    try:
        # Get last active time
        last_active_str = player_data.get('last_active')
        last_active = _parse_datetime(last_active_str)

        if not last_active:
            last_active = datetime.now()

        # Initialize calculator
        calculator = OfflineGrowthCalculator()

        # Get player stats
        player_level = player_data.get('level', 1)
        player_stage = player_data.get('stage', '炼气期')
        total_playtime = player_data.get('total_playtime_hours', 0.0)
        has_sect = player_data.get('sect') is not None

        # Calculate offline rewards
        accumulation = calculator.calculate_offline_rewards(
            player_id=player_data.get('player_id', ''),
            last_online=last_active,
            current_time=datetime.now(),
            player_level=player_level,
            player_stage=player_stage,
            total_playtime_hours=total_playtime,
            has_sect=has_sect
        )

        if not accumulation.is_eligible:
            return jsonify({
                'success': False,
                'error': accumulation.ineligibility_reason or '无资格获得离线奖励'
            }), 400

        # Check if rewards are worth claiming (minimum 1 hour offline)
        min_hours = 1.0
        if accumulation.offline_hours < min_hours:
            return jsonify({
                'success': False,
                'error': f'离线时间不足 {min_hours} 小时'
            }), 400

        # Apply rewards to player
        player_data['xp'] = player_data.get('xp', 0) + accumulation.total_xp
        player_data['spirit_stones'] = player_data.get('spirit_stones', 0) + accumulation.total_spirit_stones
        player_data['cultivation'] = player_data.get('cultivation', 0) + accumulation.total_cultivation

        # Update last_active to current time
        player_data['last_active'] = datetime.now().isoformat()

        # Save player data
        if get_storage().save(player_data['player_id'], player_data):
            return jsonify({
                'success': True,
                'rewards_claimed': {
                    'xp': accumulation.total_xp,
                    'spirit_stones': accumulation.total_spirit_stones,
                    'cultivation': accumulation.total_cultivation,
                    'offline_hours': round(accumulation.offline_hours, 2)
                },
                'new_totals': {
                    'xp': player_data['xp'],
                    'spirit_stones': player_data['spirit_stones'],
                    'cultivation': player_data['cultivation']
                }
            })
        else:
            return jsonify({'success': False, 'error': '保存失败'}), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'领取离线奖励失败: {str(e)}'
        }), 500


@offline_bp.route('/milestones', methods=['GET'])
def get_milestones():
    """获取里程碑进度"""
    player_data, error_response, status_code = _get_player_data()
    if error_response:
        return error_response, status_code

    try:
        # Initialize tracker
        tracker = ProgressionMilestoneTracker()

        # Get player stats
        player_level = player_data.get('level', 1)
        player_stage = player_data.get('stage', '炼气期')
        total_playtime = player_data.get('total_playtime_hours', 0.0)
        total_combats = player_data.get('total_combats', 0)

        # Get claimed milestones from player data
        claimed_milestones = player_data.get('claimed_milestones', {})

        # Get progress
        player_milestones = tracker.get_player_progress(
            player_id=player_data.get('player_id', ''),
            player_level=player_level,
            player_stage=player_stage,
            total_playtime_hours=total_playtime,
            total_combats=total_combats,
            claimed_milestones=claimed_milestones
        )

        # Format milestones for response
        milestones_list = []
        for milestone_id, progress in player_milestones.progress.items():
            milestone = tracker.get_milestone(milestone_id)
            if milestone:
                milestone_dict = {
                    'id': milestone_id,
                    'name': milestone.name,
                    'description': milestone.description,
                    'type': milestone.type.value,
                    'current_value': progress.current_value,
                    'target_value': progress.target_value,
                    'is_completed': progress.is_completed,
                    'is_claimed': progress.is_claimed,
                    'rewards': {
                        'xp': milestone.reward_xp,
                        'spirit_stones': milestone.reward_spirit_stones,
                        'school_points': milestone.reward_school_points,
                        'title': milestone.reward_title
                    }
                }
                milestones_list.append(milestone_dict)

        return jsonify({
            'success': True,
            'milestones': milestones_list,
            'summary': {
                'completed': player_milestones.completed_count,
                'total': player_milestones.total_count,
                'claimed': len(claimed_milestones)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取里程碑失败: {str(e)}'
        }), 500


@offline_bp.route('/milestones/<milestone_id>/claim', methods=['POST'])
def claim_milestone(milestone_id: str):
    """领取里程碑奖励"""
    player_data, error_response, status_code = _get_player_data()
    if error_response:
        return error_response, status_code

    try:
        # Initialize tracker
        tracker = ProgressionMilestoneTracker()

        # Get player stats
        player_level = player_data.get('level', 1)
        player_stage = player_data.get('stage', '炼气期')
        total_playtime = player_data.get('total_playtime_hours', 0.0)
        total_combats = player_data.get('total_combats', 0)

        # Get claimed milestones from player data
        claimed_milestones = player_data.get('claimed_milestones', {})

        # Get progress
        player_milestones = tracker.get_player_progress(
            player_id=player_data.get('player_id', ''),
            player_level=player_level,
            player_stage=player_stage,
            total_playtime_hours=total_playtime,
            total_combats=total_combats,
            claimed_milestones=claimed_milestones
        )

        # Claim milestone
        result = tracker.claim_milestone(player_milestones, milestone_id)

        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error', '领取失败')
            }), 400

        # Apply rewards to player
        rewards = result['rewards']
        player_data['xp'] = player_data.get('xp', 0) + rewards.get('xp', 0)
        player_data['spirit_stones'] = player_data.get('spirit_stones', 0) + rewards.get('spirit_stones', 0)

        # Update school points if present
        if 'school_points' in rewards:
            player_data['school_points'] = player_data.get('school_points', 0) + rewards['school_points']

        # Update claimed milestones
        claimed_milestones[milestone_id] = datetime.now().isoformat()
        player_data['claimed_milestones'] = claimed_milestones

        # Update titles if present
        if 'title' in rewards:
            titles = player_data.get('titles', [])
            if rewards['title'] not in titles:
                titles.append(rewards['title'])
            player_data['titles'] = titles

        # Save player data
        if get_storage().save(player_data['player_id'], player_data):
            return jsonify({
                'success': True,
                'milestone_id': milestone_id,
                'rewards': rewards
            })
        else:
            return jsonify({'success': False, 'error': '保存失败'}), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'领取里程碑奖励失败: {str(e)}'
        }), 500


@offline_bp.route('/streak', methods=['GET'])
def get_streak():
    """获取登录连续信息"""
    player_data, error_response, status_code = _get_player_data()
    if error_response:
        return error_response, status_code

    try:
        # Initialize tracker
        tracker = DailyActivityTracker()

        # Get or create streak from player data
        streak = tracker.create_streak_from_player(player_data)

        # Record login (update streak if needed)
        last_login = streak.last_login_date
        today = date.today().isoformat()

        # Only update streak if this is a new day login
        if last_login != today:
            streak = tracker.record_login(streak, date.today())

        # Save updated streak
        streak_dict = tracker.to_dict(streak)
        for key, value in streak_dict.items():
            player_data[key] = value

        # Save player data
        get_storage().save(player_data['player_id'], player_data)

        # Get available rewards
        available_rewards = tracker.get_available_streak_rewards(streak)

        # Get all milestone rewards info
        all_milestones = []
        for days, rewards in STREAK_REWARDS.items():
            attr_name = MILESTONE_ATTR_MAP.get(days, '')
            is_claimed = getattr(streak, attr_name, False) if attr_name else False
            is_reached = streak.current_streak >= days

            all_milestones.append({
                'days': days,
                'rewards': rewards,
                'is_reached': is_reached,
                'is_claimed': is_claimed
            })

        return jsonify({
            'success': True,
            'streak': {
                'current_streak': streak.current_streak,
                'longest_streak': streak.longest_streak,
                'last_login_date': streak.last_login_date
            },
            'available_rewards': available_rewards,
            'all_milestones': all_milestones
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取连续登录信息失败: {str(e)}'
        }), 500


@offline_bp.route('/streak/<int:days>/claim', methods=['POST'])
def claim_streak_reward(days: int):
    """领取连续登录奖励"""
    player_data, error_response, status_code = _get_player_data()
    if error_response:
        return error_response, status_code

    try:
        # Initialize tracker
        tracker = DailyActivityTracker()

        # Get streak from player data
        streak = tracker.create_streak_from_player(player_data)

        # Claim reward
        result = tracker.claim_streak_reward(streak, days)

        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error', '领取失败')
            }), 400

        # Apply rewards to player
        rewards = result['rewards']
        player_data['spirit_stones'] = player_data.get('spirit_stones', 0) + rewards.get('spirit_stones', 0)

        # Update school points if present
        if 'school_points' in rewards:
            player_data['school_points'] = player_data.get('school_points', 0) + rewards['school_points']

        # Update titles if present
        if 'title' in rewards:
            titles = player_data.get('titles', [])
            if rewards['title'] not in titles:
                titles.append(rewards['title'])
            player_data['titles'] = titles

        # Save updated streak to player data
        streak_dict = tracker.to_dict(streak)
        for key, value in streak_dict.items():
            player_data[key] = value

        # Save player data
        if get_storage().save(player_data['player_id'], player_data):
            return jsonify({
                'success': True,
                'milestone_days': days,
                'rewards': rewards
            })
        else:
            return jsonify({'success': False, 'error': '保存失败'}), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'领取连续登录奖励失败: {str(e)}'
        }), 500


@offline_bp.route('/catch-up', methods=['GET'])
def get_catch_up():
    """获取回归玩家加速状态"""
    player_data, error_response, status_code = _get_player_data()
    if error_response:
        return error_response, status_code

    try:
        # Initialize mechanics
        mechanics = CatchUpMechanics()

        # Get last active time
        last_active_str = player_data.get('last_active')
        last_active = _parse_datetime(last_active_str)

        if not last_active:
            # First time player
            return jsonify({
                'success': True,
                'catch_up': {
                    'tier': 'none',
                    'offline_days': 0,
                    'is_eligible': False,
                    'message': '首次登录，无回归加成'
                }
            })

        # Calculate catch-up bonus
        player_level = player_data.get('level', 1)
        bonus = mechanics.calculate_catch_up_bonus(
            last_online=last_active,
            current_time=datetime.now(),
            player_level=player_level
        )

        # Check if bonus is still active
        is_active = mechanics.is_catch_up_active(bonus)

        # Get any existing catch-up data from player
        existing_catch_up = player_data.get('catch_up_bonus', {})

        # Format response
        response = {
            'success': True,
            'catch_up': {
                'tier': bonus.tier.value,
                'offline_days': round(bonus.offline_days, 1),
                'is_eligible': bonus.tier.value != 'none',
                'is_active': is_active,
                'instant_claimed': existing_catch_up.get('instant_claimed', False),
                'bonuses': {
                    'xp_multiplier': bonus.xp_multiplier,
                    'stone_multiplier': bonus.stone_multiplier,
                    'drop_rate_bonus': bonus.drop_rate_bonus
                },
                'duration_days': bonus.duration_days,
                'expires_at': bonus.expires_at,
                'instant_rewards': {
                    'xp': bonus.instant_xp,
                    'spirit_stones': bonus.instant_spirit_stones
                }
            }
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取回归加成失败: {str(e)}'
        }), 500


@offline_bp.route('/catch-up/claim', methods=['POST'])
def claim_catch_up():
    """领取回归玩家即时奖励"""
    player_data, error_response, status_code = _get_player_data()
    if error_response:
        return error_response, status_code

    try:
        # Initialize mechanics
        mechanics = CatchUpMechanics()

        # Get last active time
        last_active_str = player_data.get('last_active')
        last_active = _parse_datetime(last_active_str)

        if not last_active:
            return jsonify({
                'success': False,
                'error': '首次登录，无回归奖励'
            }), 400

        # Calculate catch-up bonus
        player_level = player_data.get('level', 1)
        bonus = mechanics.calculate_catch_up_bonus(
            last_online=last_active,
            current_time=datetime.now(),
            player_level=player_level
        )

        # Load existing bonus state if any
        existing_catch_up = player_data.get('catch_up_bonus', {})
        if existing_catch_up.get('instant_claimed', False):
            return jsonify({
                'success': False,
                'error': '回归奖励已领取'
            }), 400

        # Claim instant reward
        result = mechanics.claim_instant_reward(bonus)

        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error', '领取失败')
            }), 400

        # Apply rewards to player
        rewards = result['rewards']
        player_data['xp'] = player_data.get('xp', 0) + rewards.get('xp', 0)
        player_data['spirit_stones'] = player_data.get('spirit_stones', 0) + rewards.get('spirit_stones', 0)

        # Save catch-up bonus state
        player_data['catch_up_bonus'] = mechanics.to_dict(bonus)

        # Update last_active
        player_data['last_active'] = datetime.now().isoformat()

        # Save player data
        if get_storage().save(player_data['player_id'], player_data):
            return jsonify({
                'success': True,
                'rewards': rewards,
                'bonus_details': {
                    'tier': bonus.tier.value,
                    'offline_days': round(bonus.offline_days, 1),
                    'duration_days': bonus.duration_days,
                    'expires_at': bonus.expires_at
                }
            })
        else:
            return jsonify({'success': False, 'error': '保存失败'}), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'领取回归奖励失败: {str(e)}'
        }), 500


@offline_bp.route('/progress', methods=['GET'])
def get_progress():
    """获取整体进度信息"""
    player_data, error_response, status_code = _get_player_data()
    if error_response:
        return error_response, status_code

    try:
        # Get current stage and level
        current_stage = player_data.get('stage', '炼气期')
        current_level = player_data.get('level', 1)
        current_xp = player_data.get('xp', 0)

        # Define progression milestones (level thresholds for stages)
        stage_levels = {
            '炼气期': 1,
            '筑基期': 100,
            '金丹期': 200,
            '元婴期': 300,
            '元神期': 500,
        }

        # Calculate level progress within current stage
        stages = ['炼气期', '筑基期', '金丹期', '元婴期', '元神期']
        current_stage_index = stages.index(current_stage) if current_stage in stages else 0

        # Calculate progress to next stage
        if current_stage_index < len(stages) - 1:
            next_stage = stages[current_stage_index + 1]
            next_level = stage_levels.get(next_stage, 100)
            level_progress = ((current_level - stage_levels.get(current_stage, 1)) /
                            (next_level - stage_levels.get(current_stage, 1))) * 100
        else:
            next_stage = '已达到最高境界'
            level_progress = 100

        # Estimate time to next milestones (rough calculation)
        # Assume 10 XP per hour of cultivation
        xp_per_hour = 10
        hours_per_level = 100 / xp_per_hour  # 100 XP per level base
        remaining_levels = next_level - current_level if current_stage_index < len(stages) - 1 else 0
        remaining_online_hours = remaining_levels * hours_per_level

        # Format time estimates
        remaining_days = remaining_online_hours / 24
        remaining_months = remaining_days / 30
        remaining_years = remaining_days / 365

        return jsonify({
            'success': True,
            'progress': {
                'level_progress': round(level_progress, 2),
                'time_progress': round((current_level / 1000) * 100, 2) if current_level < 1000 else 100,
                'current_stage': current_stage,
                'next_stage': next_stage if current_stage_index < len(stages) - 1 else None,
                'stages_completed': current_stage_index,
                'total_stages': len(stages),
                'current_level': current_level,
                'current_xp': current_xp
            },
            'estimate': {
                'remaining_online_hours': int(remaining_online_hours),
                'remaining_days': round(remaining_days, 1),
                'remaining_months': round(remaining_months, 1),
                'remaining_years': round(remaining_years, 2)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取进度信息失败: {str(e)}'
        }), 500
