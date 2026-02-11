#!/usr/bin/env python3
"""
修仙文字MUD - Flask Web服务器
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.data.simple_storage import save_player, load_player, load_player_by_name
from src.models.player import Player, CultivationStage, SectType
from src.models.sect import SECT_PRESETS

app = Flask(__name__)
app.secret_key = 'xiuxian-wuxia-secret-key-2024'

CURRENT_PLAYER = None


def get_stage_from_level(level: int) -> CultivationStage:
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
    return render_template('index.html')


@app.route('/api/player/create', methods=['POST'])
def create_player_api():
    data = request.json
    name = data.get('name')
    sect = data.get('sect', 'qingyun')
    
    if not name:
        return jsonify({'error': '名字不能为空'}), 400
    
    existing = load_player_by_name(name)
    if existing:
        return jsonify({'error': '角色名已存在'}), 400
    
    sect_mapping = {
        'qingyun': SectType.QINGYUN,
        'danding': SectType.DANDING,
        'wanhua': SectType.WANHUA,
        'xiaoyao': SectType.XIAOYAO,
        'shushan': SectType.SHUSHAN
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
    
    if save_player(player.__dict__):
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
def login_player_api():
    data = request.json
    name = data.get('name')
    
    if not name:
        return jsonify({'error': '名字不能为空'}), 400
    
    player_data = load_player_by_name(name)
    if not player_data:
        return jsonify({'error': '角色不存在'}), 404
    
    session['player_name'] = name
    
    return jsonify({
        'success': True,
        'player': {
            'name': player_data.get('name'),
            'level': player_data.get('level'),
            'stage': player_data.get('stage'),
            'sect': player_data.get('sect'),
            'spirit_stones': player_data.get('spirit_stones'),
            'xp': player_data.get('xp')
        }
    })


@app.route('/api/player/status', methods=['GET'])
def player_status_api():
    player_name = session.get('player_name')
    if not player_name:
        return jsonify({'error': '未登录'}), 401
    
    player_data = load_player_by_name(player_name)
    if not player_data:
        return jsonify({'error': '角色不存在'}), 404
    
    return jsonify({
        'success': True,
        'player': player_data
    })


@app.route('/api/action/cultivate', methods=['POST'])
def cultivate_api():
    player_name = session.get('player_name')
    if not player_name:
        return jsonify({'error': '未登录'}), 401
    
    player_data = load_player_by_name(player_name)
    if not player_data:
        return jsonify({'error': '角色不存在'}), 404
    
    data = request.json
    hours = data.get('hours', 1)
    
    if hours < 1 or hours > 24:
        return jsonify({'error': '时间必须在1-24小时之间'}), 400
    
    # 计算收益
    import random
    xp_gain = 10 * hours
    stones_gain = sum(random.randint(10, 20) for _ in range(hours))
    
    # 更新玩家数据
    player_data['xp'] = player_data.get('xp', 0) + xp_gain
    player_data['spirit_stones'] = player_data.get('spirit_stones', 0) + stones_gain
    
    # 检查升级
    old_level = player_data.get('level', 1)
    new_level = calculate_level_from_xp(player_data['xp'])
    
    level_up = False
    stage_up = False
    new_stage_value = None
    
    if new_level > old_level:
        player_data['level'] = new_level
        level_up = True
        
        # 检查境界突破
        new_stage = get_stage_from_level(new_level)
        old_stage_value = player_data.get('stage', '炼气期')
        
        if isinstance(new_stage, CultivationStage):
            new_stage_value = new_stage.value
        else:
            new_stage_value = str(new_stage)
        
        if new_stage_value != old_stage_value:
            player_data['stage'] = new_stage_value
            stage_up = True
    
    # 保存玩家数据
    if save_player(player_data):
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
def get_sects_api():
    """获取所有门派信息"""
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


@app.route('/game')
def game_page():
    """游戏主页面"""
    return render_template('game.html')


@app.route('/login')
def login_page():
    """登录页面"""
    return render_template('login.html')


@app.route('/register')
def register_page():
    """注册页面"""
    return render_template('register.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
