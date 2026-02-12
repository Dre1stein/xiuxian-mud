#!/usr/bin/env python3
"""
修仙文字MUD - 简化版Flask Web应用（无需数据库）
"""

from flask import Flask, render_template, request, jsonify, session
import os
import sys
import random
from datetime import datetime

from src.web.equipment_routes import equipment_bp
from src.web import combat_routes
from src.web.exploration_routes import exploration_bp
from src.web.offline_routes import offline_bp
from src.game.experience import ExperienceCalculator
from src.web.rate_limiter import create_limiter, rate_limit_exceeded_handler
from src.web.swagger import init_swagger

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.data.storage_factory import get_storage
from src.models.player import Player, CultivationStage, SectType
from src.models.sect import SECT_PRESETS
from src.models.school import SchoolProgress, SchoolProgressManager, get_school_by_id, get_sect_schools

app = Flask(__name__)
app.secret_key = 'xiuxian-simple-secret-key'

# Initialize rate limiter
limiter = create_limiter(app)

@app.errorhandler(429)
def ratelimit_handler(e):
    return rate_limit_exceeded_handler(e)

# Initialize Swagger API documentation
init_swagger(app)

# 注册装备系统蓝图
app.register_blueprint(equipment_bp)
# 注册战斗系统蓝图
app.register_blueprint(combat_routes.combat_bp)
# 注册探索系统蓝图
app.register_blueprint(exploration_bp)
# 注册离线和进度系统蓝图
app.register_blueprint(offline_bp)


def get_stage_from_level(level: int):
    if level <= 99:
        return CultivationStage.QI
    elif level <= 199:
        return CultivationStage.ZHUJI
    elif level <= 299:
        return CultivationStage.JINDAN
    elif level <= 499:
        return CultivationStage.YUANYING
    else:
        return CultivationStage.YUANSHEN


def calculate_level_from_xp(xp: int) -> int:
    if xp < 100000:
        return min(99, max(1, int((xp / 1000) ** 0.5)))
    elif xp < 1000000:
        return min(199, 100 + int((xp - 100000) / 10000))
    elif xp < 10000000:
        return min(299, 200 + int((xp - 1000000) / 50000))
    elif xp < 100000000:
        return min(499, 300 + int((xp - 10000000) / 200000))
    else:
        return min(999, 500 + int((xp - 100000000) / 500000))


@app.route('/')
def index():
    player_name = session.get('player_name')
    if not player_name:
        return render_template('login.html')
    return render_template('game.html')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/api/player/create', methods=['POST'])
def create_player():
    """
    创建新玩家
    ---
    tags:
      - player
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: 玩家角色名
            sect:
              type: string
              description: 门派ID (qingyun, danding, wanhua, xiaoyao, shushan, kunlun, yinyin, xuemo)
              default: qingyun
    responses:
      200:
        description: 创建成功
        schema:
          type: object
          properties:
            success:
              type: boolean
            player:
              type: object
              properties:
                name:
                  type: string
                level:
                  type: integer
                sect:
                  type: string
                combat_power:
                  type: integer
      400:
        description: 参数错误
      500:
        description: 服务器错误
    """
    data = request.json
    name = data.get('name')
    sect = data.get('sect', 'qingyun')
    
    if not name:
        return jsonify({'error': '名字不能为空'}), 400
    
    existing = get_storage().load_by_name(name)
    if existing:
        return jsonify({'error': '角色名已存在'}), 400
    
    sect_mapping = {
        'qingyun': SectType.QINGYUN,
        'danding': SectType.DANDING,
        'wanhua': SectType.WANHUA,
        'xiaoyao': SectType.XIAOYAO,
        'shushan': SectType.SHUSHAN,
        'kunlun': SectType.KUNLUN,
        'yinyin': SectType.YINYIN,
        'xuemo': SectType.XUEMO
    }
    
    sect_type = sect_mapping.get(sect, SectType.QINGYUN)
    sect_preset = SECT_PRESETS[sect_type]
    
    player = Player(
        player_id=f"player_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        name=name,
        level=1,
        xp=0,
        stage=CultivationStage.QI,
        sect=sect_type,
        cultivation=0,
        sect_stats=sect_preset['stats'],
        base_stats={"attack": 10, "defense": 10, "speed": 10, "agility": 10, "constitution": 10, "intellect": 10},
        spirit_stones=1000,
        current_map="宗门",
        talents=[sect_preset['skills'][0]]
    )
    
    if get_storage().save(player.player_id, player.__dict__):
        session['player_name'] = name
        return jsonify({
            'success': True,
            'player': {
                'name': player.name,
                'level': player.level,
                'sect': player.sect.value,
                'combat_power': player.get_combat_power()
            }
        })
    else:
        return jsonify({'error': '保存失败'}), 500


@app.route('/api/player/login', methods=['POST'])
def login_player():
    """
    玩家登录
    ---
    tags:
      - player
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: 玩家角色名
    responses:
      200:
        description: 登录成功
        schema:
          type: object
          properties:
            success:
              type: boolean
            player:
              type: object
              properties:
                name:
                  type: string
                level:
                  type: integer
                stage:
                  type: string
                sect:
                  type: string
                spirit_stones:
                  type: integer
                xp:
                  type: integer
      400:
        description: 参数错误
      404:
        description: 角色不存在
    """
    data = request.json
    name = data.get('name')
    
    if not name:
        return jsonify({'error': '名字不能为空'}), 400
    
    player_data = get_storage().load_by_name(name)
    if not player_data:
        return jsonify({'error': '角色不存在'}), 404
    
    session['player_name'] = name

    # === 离线奖励计算 ===
    from src.progression.offline_growth import OfflineGrowthCalculator
    from src.progression.daily_activity import DailyActivityTracker
    from datetime import datetime as dt

    offline_rewards = None

    try:
        # 1. 计算离线奖励
        calc = OfflineGrowthCalculator()
        last_active_str = player_data.get('last_active')
        if last_active_str:
            try:
                last_active = dt.fromisoformat(last_active_str.replace('Z', '+00:00'))
            except:
                last_active = dt.now()
        else:
            last_active = dt.now()

        accumulation = calc.calculate_offline_rewards(
            player_id=player_data['player_id'],
            last_online=last_active,
            player_level=player_data.get('level', 1),
            player_stage=player_data.get('stage', '炼气期'),
            total_playtime_hours=player_data.get('total_playtime_hours', 0),
            has_sect=player_data.get('sect') is not None
        )

        # 2. 更新登录连续天数
        tracker = DailyActivityTracker()
        streak_data = player_data.get('login_streak', {})
        streak = tracker.create_streak_from_player({'login_streak': streak_data, 'player_id': player_data['player_id']})
        streak = tracker.record_login(streak)
        player_data['login_streak'] = tracker.to_dict(streak)

        # 3. 如果有离线奖励，添加到响应中
        if accumulation.is_eligible and accumulation.offline_hours >= 1:
            offline_rewards = {
                'has_rewards': True,
                'offline_hours': accumulation.offline_hours,
                'total_xp': accumulation.total_xp,
                'total_spirit_stones': accumulation.total_spirit_stones,
                'total_cultivation': accumulation.total_cultivation,
            }
            player_data['offline_rewards_pending'] = offline_rewards

        # 4. 更新 last_active
        player_data['last_active'] = dt.now().isoformat()

        # 5. 保存玩家数据
        get_storage().save(player_data['player_id'], player_data)

    except Exception as e:
        # 离线奖励计算失败不影响登录成功
        import logging
        logging.getLogger(__name__).warning(f"Failed to calculate offline rewards: {e}")
        offline_rewards = None

    return jsonify({
        'success': True,
        'player': {
            'name': player_data.get('name'),
            'level': player_data.get('level'),
            'stage': player_data.get('stage'),
            'sect': player_data.get('sect'),
            'spirit_stones': player_data.get('spirit_stones'),
            'xp': player_data.get('xp')
        },
        'offline_rewards': offline_rewards
    })


@app.route('/api/player/status', methods=['GET'])
def player_status():
    """
    获取玩家状态
    ---
    tags:
      - player
    responses:
      200:
        description: 成功获取玩家状态
        schema:
          type: object
          properties:
            success:
              type: boolean
            player:
              type: object
              description: 玩家完整数据
      401:
        description: 未登录
      404:
        description: 角色不存在
    """
    player_name = session.get('player_name')
    if not player_name:
        return jsonify({'error': '未登录'}), 401
    
    player_data = get_storage().load_by_name(player_name)
    if not player_data:
        return jsonify({'error': '角色不存在'}), 404
    
    return jsonify({
        'success': True,
        'player': player_data
    })


@app.route('/api/action/cultivate', methods=['POST'])
def cultivate():
    """
    修炼行动
    ---
    tags:
      - action
    parameters:
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            hours:
              type: integer
              description: 修炼时长(1-24小时)
              default: 1
              minimum: 1
              maximum: 24
    responses:
      200:
        description: 修炼成功
        schema:
          type: object
          properties:
            success:
              type: boolean
            cultivation:
              type: object
              properties:
                hours:
                  type: integer
                xp_gain:
                  type: integer
                stones_gain:
                  type: integer
                current_xp:
                  type: integer
                current_level:
                  type: integer
                current_stones:
                  type: integer
                level_up:
                  type: boolean
                stage_up:
                  type: boolean
      400:
        description: 参数错误
      401:
        description: 未登录
      404:
        description: 角色不存在
    """
    player_name = session.get('player_name')
    if not player_name:
        return jsonify({'error': '未登录'}), 401
    
    player_data = get_storage().load_by_name(player_name)
    if not player_data:
        return jsonify({'error': '角色不存在'}), 404
    
    data = request.json
    hours = data.get('hours', 1)
    
    if hours < 1 or hours > 24:
        return jsonify({'error': '时间必须在1-24小时之间'}), 400
    
    xp_gain = 10 * hours
    stones_gain = sum(random.randint(10, 20) for _ in range(hours))
    
    player_data['xp'] = player_data.get('xp', 0) + xp_gain
    player_data['spirit_stones'] = player_data.get('spirit_stones', 0) + stones_gain
    
    old_level = player_data.get('level', 1)
    new_level = calculate_level_from_xp(player_data['xp'])
    
    level_up = False
    stage_up = False
    new_stage_value = None
    
    if new_level > old_level:
        player_data['level'] = new_level
        level_up = True
        
        new_stage = get_stage_from_level(new_level)
        old_stage_value = player_data.get('stage', '炼气期')
        
        if isinstance(new_stage, CultivationStage):
            new_stage_value = new_stage.value
        else:
            new_stage_value = str(new_stage)
        
        if new_stage_value != old_stage_value:
            player_data['stage'] = new_stage_value
            stage_up = True
    
    if get_storage().save(player_data['player_id'], player_data):
        result = {
            'success': True,
            'cultivation': {
                'hours': hours,
                'xp_gain': xp_gain,
                'stones_gain': stones_gain,
                'current_xp': player_data['xp'],
                'current_level': player_data.get('level', 1),
                'current_stones': player_data['spirit_stones'],
                'level_up': level_up,
                'stage_up': stage_up
            }
        }
        
        if level_up:
            result['cultivation']['old_level'] = old_level
            result['cultivation']['new_level'] = new_level
        
        if stage_up:
            result['cultivation']['new_stage'] = new_stage_value
        
        return jsonify(result)
    else:
        return jsonify({'error': '保存失败'}), 500


@app.route('/api/sects', methods=['GET'])
def get_sects():
    sects = []
    
    for sect_type in SectType:
        preset = SECT_PRESETS[sect_type]
        sects.append({
            'id': sect_type.name,
            'name': preset['name'],
            'type': preset['type'].value,
            'description': preset['description'],
            'color': preset['color'],
            'skills': preset['skills'],
            'stats': preset['stats']
        })
    
    return jsonify({
        'success': True,
        'sects': sects
    })


@app.route('/logout')
def logout():
    session.pop('player_name', None)
    return jsonify({'success': True, 'message': '已登出'})


# ============================================================================
# School Progress API Endpoints
# ============================================================================

@app.route('/api/school/progress', methods=['GET'])
def get_school_progress():
    """Get all school progress for the current player."""
    player_name = session.get('player_name')
    if not player_name:
        return jsonify({'error': '未登录'}), 401

    player_data = get_storage().load_by_name(player_name)
    if not player_data:
        return jsonify({'error': '角色不存在'}), 404

    school_progress = player_data.get('school_progress', {})
    manager = SchoolProgressManager()

    progress_list = []
    for school_id, progress_data in school_progress.items():
        progress = SchoolProgress(
            school_id=progress_data.get('school_id', school_id),
            points_invested=progress_data.get('points_invested', 0),
            points_available=progress_data.get('points_available', 0),
            unlocked_skills=progress_data.get('unlocked_skills', []),
            active_skills=progress_data.get('active_skills', []),
            mastery_level=progress_data.get('mastery_level', 1),
            skill_investments=progress_data.get('skill_investments', {})
        )
        progress_list.append(manager.get_progress_summary(progress))

    # Also include available schools for the player's sect
    sect_value = player_data.get('sect')
    available_schools = []
    if sect_value:
        for sect_type in SectType:
            if sect_type.value == sect_value or sect_type.name == sect_value:
                available_schools = [
                    {
                        "school_id": s.school_id,
                        "name": s.name,
                        "focus": s.focus,
                        "description": s.description,
                        "skills": s.skills,
                        "unlock_level": s.unlock_level
                    }
                    for s in get_sect_schools(sect_type)
                ]
                break

    return jsonify({
        'success': True,
        'school_progress': progress_list,
        'available_schools': available_schools
    })


@app.route('/api/school/invest', methods=['POST'])
def invest_school_point():
    """Invest a point into a skill."""
    player_name = session.get('player_name')
    if not player_name:
        return jsonify({'error': '未登录'}), 401

    player_data = get_storage().load_by_name(player_name)
    if not player_data:
        return jsonify({'error': '角色不存在'}), 404

    data = request.json
    school_id = data.get('school_id')
    skill_id = data.get('skill_id')

    if not school_id or not skill_id:
        return jsonify({'error': '缺少school_id或skill_id'}), 400

    school_progress = player_data.get('school_progress', {})

    if school_id not in school_progress:
        school_progress[school_id] = {
            'school_id': school_id,
            'points_invested': 0,
            'points_available': 0,
            'unlocked_skills': [],
            'active_skills': [],
            'mastery_level': 1,
            'skill_investments': {}
        }

    progress_data = school_progress[school_id]
    progress = SchoolProgress(
        school_id=progress_data.get('school_id', school_id),
        points_invested=progress_data.get('points_invested', 0),
        points_available=progress_data.get('points_available', 0),
        unlocked_skills=progress_data.get('unlocked_skills', []),
        active_skills=progress_data.get('active_skills', []),
        mastery_level=progress_data.get('mastery_level', 1),
        skill_investments=progress_data.get('skill_investments', {})
    )

    manager = SchoolProgressManager()
    success = manager.invest_point(progress, skill_id)

    if not success:
        return jsonify({'error': '无法投入点数，请检查是否有足够点数或技能是否有效'}), 400

    school_progress[school_id] = {
        'school_id': progress.school_id,
        'points_invested': progress.points_invested,
        'points_available': progress.points_available,
        'unlocked_skills': progress.unlocked_skills,
        'active_skills': progress.active_skills,
        'mastery_level': progress.mastery_level,
        'skill_investments': progress.skill_investments
    }

    player_data['school_progress'] = school_progress
    get_storage().save(player_data['player_id'], player_data)

    return jsonify({
        'success': True,
        'progress': manager.get_progress_summary(progress)
    })


@app.route('/api/school/unlock', methods=['POST'])
def unlock_school_skill():
    """Unlock a skill if prerequisites met."""
    player_name = session.get('player_name')
    if not player_name:
        return jsonify({'error': '未登录'}), 401

    player_data = get_storage().load_by_name(player_name)
    if not player_data:
        return jsonify({'error': '角色不存在'}), 404

    data = request.json
    school_id = data.get('school_id')
    skill_id = data.get('skill_id')

    if not school_id or not skill_id:
        return jsonify({'error': '缺少school_id或skill_id'}), 400

    school_progress = player_data.get('school_progress', {})

    if school_id not in school_progress:
        school_progress[school_id] = {
            'school_id': school_id,
            'points_invested': 0,
            'points_available': 0,
            'unlocked_skills': [],
            'active_skills': [],
            'mastery_level': 1,
            'skill_investments': {}
        }

    progress_data = school_progress[school_id]
    progress = SchoolProgress(
        school_id=progress_data.get('school_id', school_id),
        points_invested=progress_data.get('points_invested', 0),
        points_available=progress_data.get('points_available', 0),
        unlocked_skills=progress_data.get('unlocked_skills', []),
        active_skills=progress_data.get('active_skills', []),
        mastery_level=progress_data.get('mastery_level', 1),
        skill_investments=progress_data.get('skill_investments', {})
    )

    manager = SchoolProgressManager()
    success = manager.unlock_skill(progress, skill_id)

    if not success:
        return jsonify({'error': '无法解锁技能，请检查前置条件或点数是否足够'}), 400

    school_progress[school_id] = {
        'school_id': progress.school_id,
        'points_invested': progress.points_invested,
        'points_available': progress.points_available,
        'unlocked_skills': progress.unlocked_skills,
        'active_skills': progress.active_skills,
        'mastery_level': progress.mastery_level,
        'skill_investments': progress.skill_investments
    }

    player_data['school_progress'] = school_progress
    get_storage().save(player_data['player_id'], player_data)

    return jsonify({
        'success': True,
        'progress': manager.get_progress_summary(progress)
    })


@app.route('/api/school/equip', methods=['POST'])
def equip_school_skill():
    """Equip a skill to active slot (max 3 active)."""
    player_name = session.get('player_name')
    if not player_name:
        return jsonify({'error': '未登录'}), 401

    player_data = get_storage().load_by_name(player_name)
    if not player_data:
        return jsonify({'error': '角色不存在'}), 404

    data = request.json
    school_id = data.get('school_id')
    skill_id = data.get('skill_id')

    if not school_id or not skill_id:
        return jsonify({'error': '缺少school_id或skill_id'}), 400

    school_progress = player_data.get('school_progress', {})

    if school_id not in school_progress:
        return jsonify({'error': '流派进度不存在'}), 404

    progress_data = school_progress[school_id]
    progress = SchoolProgress(
        school_id=progress_data.get('school_id', school_id),
        points_invested=progress_data.get('points_invested', 0),
        points_available=progress_data.get('points_available', 0),
        unlocked_skills=progress_data.get('unlocked_skills', []),
        active_skills=progress_data.get('active_skills', []),
        mastery_level=progress_data.get('mastery_level', 1),
        skill_investments=progress_data.get('skill_investments', {})
    )

    manager = SchoolProgressManager()
    success = manager.equip_skill(progress, skill_id)

    if not success:
        return jsonify({'error': '无法装备技能，请检查技能是否已解锁或已达到上限(3个)'}), 400

    school_progress[school_id] = {
        'school_id': progress.school_id,
        'points_invested': progress.points_invested,
        'points_available': progress.points_available,
        'unlocked_skills': progress.unlocked_skills,
        'active_skills': progress.active_skills,
        'mastery_level': progress.mastery_level,
        'skill_investments': progress.skill_investments
    }

    player_data['school_progress'] = school_progress
    get_storage().save(player_data['player_id'], player_data)

    return jsonify({
        'success': True,
        'progress': manager.get_progress_summary(progress)
    })


@app.route('/api/school/unequip', methods=['POST'])
def unequip_school_skill():
    """Unequip a skill from active slot."""
    player_name = session.get('player_name')
    if not player_name:
        return jsonify({'error': '未登录'}), 401

    player_data = get_storage().load_by_name(player_name)
    if not player_data:
        return jsonify({'error': '角色不存在'}), 404

    data = request.json
    school_id = data.get('school_id')
    skill_id = data.get('skill_id')

    if not school_id or not skill_id:
        return jsonify({'error': '缺少school_id或skill_id'}), 400

    school_progress = player_data.get('school_progress', {})

    if school_id not in school_progress:
        return jsonify({'error': '流派进度不存在'}), 404

    progress_data = school_progress[school_id]
    progress = SchoolProgress(
        school_id=progress_data.get('school_id', school_id),
        points_invested=progress_data.get('points_invested', 0),
        points_available=progress_data.get('points_available', 0),
        unlocked_skills=progress_data.get('unlocked_skills', []),
        active_skills=progress_data.get('active_skills', []),
        mastery_level=progress_data.get('mastery_level', 1),
        skill_investments=progress_data.get('skill_investments', {})
    )

    manager = SchoolProgressManager()
    success = manager.unequip_skill(progress, skill_id)

    if not success:
        return jsonify({'error': '无法卸下技能'}), 400

    school_progress[school_id] = {
        'school_id': progress.school_id,
        'points_invested': progress.points_invested,
        'points_available': progress.points_available,
        'unlocked_skills': progress.unlocked_skills,
        'active_skills': progress.active_skills,
        'mastery_level': progress.mastery_level,
        'skill_investments': progress.skill_investments
    }

    player_data['school_progress'] = school_progress
    get_storage().save(player_data['player_id'], player_data)

    return jsonify({
        'success': True,
        'progress': manager.get_progress_summary(progress)
    })


# ============================================================================
# XP Breakdown API Endpoints
# ============================================================================

_xp_calculator = None


def get_xp_calculator():
    """Get or create the XP calculator instance."""
    global _xp_calculator
    if _xp_calculator is None:
        _xp_calculator = ExperienceCalculator()
    return _xp_calculator


@app.route('/api/xp/breakdown', methods=['GET'])
def get_xp_breakdown():
    """Get detailed XP breakdown information for the current player.

    Query parameters:
        base_xp: Base XP amount to calculate (default: 100)
    """
    player_name = session.get('player_name')
    if not player_name:
        return jsonify({'error': '未登录'}), 401

    player_data = get_storage().load_by_name(player_name)
    if not player_data:
        return jsonify({'error': '角色不存在'}), 404

    # Get base XP from query params or use default
    base_xp = request.args.get('base_xp', 100, type=int)

    # Get player stage
    stage = player_data.get('stage', '炼气期')

    # Calculate offline time for rest bonus
    last_active_str = player_data.get('last_active')
    rest_bonus_active = False
    offline_hours = 0.0

    if last_active_str:
        try:
            if isinstance(last_active_str, str):
                last_active = datetime.fromisoformat(last_active_str.replace('Z', '+00:00'))
            else:
                last_active = last_active_str
            now = datetime.now(last_active.tzinfo) if last_active.tzinfo else datetime.now()
            offline_hours = (now - last_active).total_seconds() / 3600

            calc = get_xp_calculator()
            rest_bonus_active, _ = calc.calculate_rest_bonus(offline_hours)
        except Exception:
            pass

    # Calculate XP with bonuses
    calc = get_xp_calculator()
    breakdown = calc.calculate_xp(
        base_xp=base_xp,
        player_stage=stage,
        player_vip=False,  # Could be extended to check VIP status
        first_win_today=False,  # Could be extended to track daily wins
        event_active=False,  # Could be extended to check event status
        rest_bonus_active=rest_bonus_active
    )

    # Get XP configuration info
    xp_info = calc.get_xp_breakdown_info()

    return jsonify({
        'success': True,
        'xp_breakdown': {
            'base_xp': breakdown.base_xp,
            'bonuses': breakdown.bonuses,
            'total_xp': breakdown.total_xp,
            'breakdown_text': breakdown.breakdown_text,
        },
        'player_info': {
            'stage': stage,
            'offline_hours': round(offline_hours, 2),
            'rest_bonus_eligible': rest_bonus_active,
        },
        'config_info': xp_info
    })


@app.route('/api/xp/info', methods=['GET'])
def get_xp_info():
    """Get general XP system information (stage multipliers, bonus rates, etc.)."""
    calc = get_xp_calculator()
    xp_info = calc.get_xp_breakdown_info()

    return jsonify({
        'success': True,
        'experience_system': xp_info
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🎮 修仙文字MUD Web服务器")
    print("=" * 60)
    print("\n🌐 访问地址:")
    print("   本地: http://localhost:5000")
    print("   网络: http://0.0.0.0:5000")
    print("\n📖 页面:")
    print("   /         - 游戏主页")
    print("   /login    - 登录页面")
    print("   /register - 注册页面")
    print("\n⚙️  系统模块:")
    print("   装备系统已启用 - /api/equipment/*")
    print("   战斗系统已启用 - /api/combat/*")
    print("\n⚠️  按 Ctrl+C 停止服务器")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
