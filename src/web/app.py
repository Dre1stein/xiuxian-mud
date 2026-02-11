#!/usr/bin/env python3
"""
修仙文字MUD - Flask Web应用
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data.database import get_session, init_db
from src.models.player import Player, CultivationStage, SectType
from src.models.sect import Sect, SECT_PRESETS
from src.game.game_systems import CultivationSystem, SectSystem, EconomySystem


app = Flask(__name__)
CORS(app)


# 路由

@app.route('/')
def index():
    """首页"""
    return jsonify({
        "game": "修仙文字MUD",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "修仙境界体系（炼气→筑基→金丹→元婴→元神）",
            "五大门派（青雲、丹鼎、万花谷、逍遥宗、蜀山派）",
            "装备和法宝系统",
            "仙石经济",
            "秘境探索",
            "考据数值体系"
        ]
    })


@app.route('/api/player', methods=['POST'])
def create_player():
    """创建玩家"""
    data = request.json
    
    player_id = data.get('player_id')
    name = data.get('name')
    sect_type = data.get('sect', 'QINGYUN')
    
    if not player_id or not name:
        return jsonify({"error": "player_id and name are required"}), 400
    
    # 映射门派类型
    sect_mapping = {
        'QINGYUN': SectType.QINGYUN,
        'DANDING': SectType.DANDING,
        'WANHUA': SectType.WANHUA,
        'XIAOYAO': SectType.XIAOYAO,
        'SHUSHAN': SectType.SHUSHAN
    }
    
    sect = sect_mapping.get(sect_type.upper(), SectType.QINGYUN)
    sect_preset = SECT_PRESETS[sect]
    
    # 创建玩家
    player = Player(
        player_id=player_id,
        name=name,
        level=1,
        xp=0,
        stage=CultivationStage.QI,
        sect=sect,
        cultivation=0,
        sect_stats=sect_preset['stats'],
        base_stats={
            "attack": 10,
            "defense": 10,
            "speed": 10,
            "agility": 10,
            "constitution": 10,
            "intellect": 10
        },
        spirit_stones=1000,
        equipment=[],
        current_map="宗门",
        talents=[sect_preset['skills'][0]]
    )
    
    try:
        with get_session() as session:
            session.add(player)
            session.commit()
        
        return jsonify({
            "status": "success",
            "player": {
                "player_id": player.player_id,
                "name": player.name,
                "level": player.level,
                "stage": player.stage.value,
                "sect": player.sect.value,
                "spirit_stones": player.spirit_stones,
                "combat_power": player.get_combat_power()
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/player/<player_id>', methods=['GET'])
def get_player(player_id: str):
    """获取玩家信息"""
    try:
        with get_session() as session:
            player = session.query(Player).filter(Player.player_id == player_id).first()
            
            if not player:
                return jsonify({"error": "Player not found"}), 404
            
            return jsonify({
                "status": "success",
                "player": {
                    "player_id": player.player_id,
                    "name": player.name,
                    "level": player.level,
                    "xp": player.xp,
                    "stage": player.stage.value,
                    "sect": player.sect.value,
                    "cultivation": player.cultivation,
                    "sect_stats": player.sect_stats,
                    "base_stats": player.base_stats,
                    "spirit_stones": player.spirit_stones,
                    "equipment": player.equipment,
                    "current_map": player.current_map,
                    "combat_power": player.get_combat_power()
                }
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/cultivate/<player_id>', methods=['POST'])
def cultivate(player_id: str):
    """修炼"""
    data = request.json
    hours = data.get('hours', 1)
    
    if hours < 1 or hours > 24:
        return jsonify({"error": "hours must be between 1 and 24"}), 400
    
    try:
        with get_session() as session:
            player = session.query(Player).filter(Player.player_id == player_id).first()
            
            if not player:
                return jsonify({"error": "Player not found"}), 404
            
            # 创建修仙系统
            cult = CultivationSystem()
            cult.level = player.level
            cult.xp = player.xp
            
            # 计算经验
            experience_gain = 10 * hours
            result = cult.add_experience(experience_gain)
            
            # 更新玩家
            player.level = cult.level
            player.xp = cult.xp
            
            if result.get('stage_up'):
                player.stage = CultivationStage(cult.stage) if isinstance(cult.stage, str) else cult.stage
            
            session.commit()
            
            return jsonify({
                "status": "success",
                "cultivation": {
                    "hours": hours,
                    "experience_gain": experience_gain,
                    "old_level": result.get('old_level'),
                    "new_level": result.get('new_level'),
                    "stage_up": result.get('stage_up'),
                    "new_stage": result.get('new_stage'),
                    "current_level": player.level,
                    "current_xp": player.xp,
                    "current_stage": player.stage.value
                }
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/sects', methods=['GET'])
def get_sects():
    """获取所有门派信息"""
    sects = []
    
    for sect_type in SectType:
        preset = SECT_PRESETS[sect_type]
        sects.append({
            "id": sect_type.value,
            "name": preset['name'],
            "type": preset['type'].value,
            "description": preset['description'],
            "color": preset['color'],
            "skills": preset['skills'],
            "stats": preset['stats']
        })
    
    return jsonify({
        "status": "success",
        "sects": sects,
        "count": len(sects)
    })


@app.route('/api/status', methods=['GET'])
def api_status():
    """API状态"""
    return jsonify({
        "status": "running",
        "version": "1.0.0",
        "endpoints": [
            "GET /",
            "POST /api/player",
            "GET /api/player/<player_id>",
            "POST /api/cultivate/<player_id>",
            "GET /api/sects"
        ]
    })


if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 运行Flask应用
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
