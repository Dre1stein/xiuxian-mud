"""
战斗系统 API 路由
"""
from flask import Blueprint, request, jsonify, session
import sys
import os
import random
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.data.simple_storage import load_player_by_name, save_player
from src.models.player import CultivationStage, SectType, SECT_PRESETS

combat_bp = Blueprint('combat', __name__, url_prefix='/api/combat')

# 战斗会话缓存 (生产环境应该用Redis)
combat_sessions: Dict[str, 'CombatSession'] = {}


class ActionType(Enum):
    """行动类型"""
    ATTACK = "attack"
    SKILL = "skill"
    ITEM = "item"
    FLEE = "flee"
    DEFEND = "defend"


class CombatStatus(Enum):
    """战斗状态"""
    ACTIVE = "active"
    VICTORY = "victory"
    DEFEAT = "defeat"
    FLED = "fled"


@dataclass
class CombatEntity:
    """战斗实体"""
    id: str
    name: str
    level: int
    stage: str
    hp: int
    max_hp: int
    attack: int
    defense: int
    speed: int
    entity_type: str = "enemy"  # "player" or "enemy"
    skills: List[str] = field(default_factory=list)
    buffs: List[Dict] = field(default_factory=list)
    is_defending: bool = False

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "stage": self.stage,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "entity_type": self.entity_type,
            "skills": self.skills,
            "buffs": self.buffs,
            "is_defending": self.is_defending
        }


@dataclass
class CombatSession:
    """战斗会话"""
    session_id: str
    player: CombatEntity
    enemies: List[CombatEntity]
    turn_order: List[str]
    current_turn_index: int = 0
    status: str = CombatStatus.ACTIVE.value
    log: List[str] = field(default_factory=list)
    turn_count: int = 0

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "player": self.player.to_dict(),
            "enemies": [e.to_dict() for e in self.enemies],
            "turn_order": self.turn_order,
            "current_turn_index": self.current_turn_index,
            "status": self.status,
            "turn_count": self.turn_count
        }


@dataclass
class CombatResult:
    """战斗结果"""
    status: str
    turns: int
    xp_gained: int = 0
    stones_gained: int = 0
    items_dropped: List[str] = field(default_factory=list)
    log: List[str] = field(default_factory=list)


# 怪物数据定义
MONSTER_DATA = {
    "wolf": {
        "id": "wolf",
        "name": "妖狼",
        "level_range": [1, 10],
        "stage": CultivationStage.QI,
        "difficulty": "easy",
        "base_hp": 80,
        "base_attack": 15,
        "base_defense": 5,
        "base_speed": 12,
        "xp_reward": 50,
        "stone_reward": 10,
        "skills": ["撕咬", "狼爪"],
        "description": "炼气期常见怪物，物理攻击型"
    },
    "fire_spirit": {
        "id": "fire_spirit",
        "name": "火灵",
        "level_range": [10, 25],
        "stage": CultivationStage.ZHUJI,
        "difficulty": "normal",
        "base_hp": 200,
        "base_attack": 40,
        "base_defense": 20,
        "base_speed": 25,
        "xp_reward": 150,
        "stone_reward": 30,
        "skills": ["火球术", "烈焰冲击", "燃烧"],
        "description": "筑基期怪物，火属性攻击"
    },
    "ice_soul": {
        "id": "ice_soul",
        "name": "冰魄",
        "level_range": [25, 45],
        "stage": CultivationStage.JINDAN,
        "difficulty": "hard",
        "base_hp": 500,
        "base_attack": 80,
        "base_defense": 50,
        "base_speed": 40,
        "xp_reward": 400,
        "stone_reward": 80,
        "skills": ["冰封术", "寒冰刺", "冻结", "冰霜护盾"],
        "description": "金丹期怪物，冰属性攻击"
    },
    "demon_king": {
        "id": "demon_king",
        "name": "妖王",
        "level_range": [45, 60],
        "stage": CultivationStage.YUANYING,
        "difficulty": "boss",
        "base_hp": 2000,
        "base_attack": 200,
        "base_defense": 100,
        "base_speed": 60,
        "xp_reward": 2000,
        "stone_reward": 500,
        "skills": ["妖王斩", "妖气护体", "摄魂术", "妖火焚天"],
        "description": "Boss怪物，多技能"
    },
    "evil_cultivator": {
        "id": "evil_cultivator",
        "name": "邪修",
        "level_range": [5, 20],
        "stage": CultivationStage.QI,
        "difficulty": "normal",
        "base_hp": 150,
        "base_attack": 25,
        "base_defense": 15,
        "base_speed": 18,
        "xp_reward": 80,
        "stone_reward": 20,
        "skills": ["邪气斩", "吸血术"],
        "description": "堕落的修仙者"
    },
    "stone_golem": {
        "id": "stone_golem",
        "name": "石像鬼",
        "level_range": [15, 30],
        "stage": CultivationStage.ZHUJI,
        "difficulty": "hard",
        "base_hp": 400,
        "base_attack": 35,
        "base_defense": 60,
        "base_speed": 8,
        "xp_reward": 200,
        "stone_reward": 40,
        "skills": ["岩石撞击", "石化", "地震"],
        "description": "防御力极高的土属性怪物"
    }
}


def get_monster_data(monster_type: str, player_level: int) -> Dict:
    """根据类型和玩家等级生成怪物数据"""
    if monster_type not in MONSTER_DATA:
        # 随机选择一个适合玩家等级的怪物
        suitable_monsters = [
            m for m in MONSTER_DATA.values()
            if m["level_range"][0] <= player_level <= m["level_range"][1]
        ]
        if not suitable_monsters:
            suitable_monsters = list(MONSTER_DATA.values())
        monster_data = random.choice(suitable_monsters)
    else:
        monster_data = MONSTER_DATA[monster_type]

    # 根据玩家等级调整怪物属性
    level_multiplier = 1 + (player_level - monster_data["level_range"][0]) * 0.1
    level_multiplier = max(0.5, min(level_multiplier, 3.0))

    return {
        "id": f"{monster_data['id']}_{uuid.uuid4().hex[:8]}",
        "name": monster_data["name"],
        "level": max(1, min(player_level, monster_data["level_range"][1])),
        "stage": monster_data["stage"].value,
        "hp": int(monster_data["base_hp"] * level_multiplier),
        "max_hp": int(monster_data["base_hp"] * level_multiplier),
        "attack": int(monster_data["base_attack"] * level_multiplier),
        "defense": int(monster_data["base_defense"] * level_multiplier),
        "speed": int(monster_data["base_speed"] * level_multiplier),
        "skills": monster_data["skills"],
        "xp_reward": int(monster_data["xp_reward"] * level_multiplier),
        "stone_reward": int(monster_data["stone_reward"] * level_multiplier),
        "difficulty": monster_data["difficulty"]
    }


def create_player_entity(player_data: Dict) -> CombatEntity:
    """从玩家数据创建战斗实体"""
    # 计算玩家战斗属性
    base_stats = player_data.get("base_stats", {})
    sect_stats = player_data.get("sect_stats", {})
    sect_type = player_data.get("sect")
    stage = player_data.get("stage", CultivationStage.QI.value)

    # 获取门派技能
    skills = player_data.get("talents", [])
    if sect_type:
        sect_preset = SECT_PRESETS.get(SectType(sect_type) if isinstance(sect_type, str) else sect_type)
        if sect_preset:
            skills.extend(sect_preset.get("skills", []))

    # 计算总属性
    total_attack = base_stats.get("attack", 10) + sect_stats.get("attack", 0)
    total_defense = base_stats.get("defense", 10) + sect_stats.get("defense", 0)
    total_speed = base_stats.get("speed", 10) + sect_stats.get("speed", 0)

    # 根据境界加成
    stage_multipliers = {
        CultivationStage.QI.value: 1.0,
        CultivationStage.ZHUJI.value: 2.0,
        CultivationStage.JINDAN.value: 5.0,
        CultivationStage.YUANYING.value: 10.0,
        CultivationStage.YUANSHEN.value: 50.0
    }
    multiplier = stage_multipliers.get(stage, 1.0)

    # 计算HP
    constitution = base_stats.get("constitution", 10)
    max_hp = int(100 * multiplier + constitution * 10 * multiplier)

    return CombatEntity(
        id="player",
        name=player_data.get("name", "玩家"),
        level=player_data.get("level", 1),
        stage=stage,
        hp=max_hp,
        max_hp=max_hp,
        attack=int(total_attack * multiplier),
        defense=int(total_defense * multiplier),
        speed=int(total_speed * multiplier),
        entity_type="player",
        skills=list(set(skills))  # 去重
    )


def calculate_damage(attacker: CombatEntity, defender: CombatEntity, skill_multiplier: float = 1.0) -> int:
    """计算伤害"""
    base_damage = max(1, attacker.attack - defender.defense // 2)

    # 防御姿态减伤
    if defender.is_defending:
        base_damage = base_damage // 2

    # 暴击计算
    is_crit = random.random() < 0.15  # 15%暴击率
    if is_crit:
        base_damage = int(base_damage * 1.5)

    # 随机浮动
    damage = int(base_damage * skill_multiplier * random.uniform(0.9, 1.1))

    return max(1, damage)


def execute_skill(attacker: CombatEntity, target: CombatEntity, skill_name: str, session: CombatSession) -> Dict:
    """执行技能"""
    # 简单的技能系统
    skill_effects = {
        "撕咬": {"multiplier": 1.2, "damage_type": "physical"},
        "狼爪": {"multiplier": 1.0, "damage_type": "physical"},
        "火球术": {"multiplier": 1.5, "damage_type": "fire"},
        "烈焰冲击": {"multiplier": 2.0, "damage_type": "fire"},
        "燃烧": {"multiplier": 0.5, "damage_type": "fire", "dot": True},
        "冰封术": {"multiplier": 1.3, "damage_type": "ice", "slow": True},
        "寒冰刺": {"multiplier": 1.8, "damage_type": "ice"},
        "冻结": {"multiplier": 1.0, "damage_type": "ice", "stun": True},
        "冰霜护盾": {"multiplier": 0, "damage_type": "buff", "defense_buff": 20},
        "妖王斩": {"multiplier": 2.5, "damage_type": "dark"},
        "妖气护体": {"multiplier": 0, "damage_type": "buff", "defense_buff": 30},
        "摄魂术": {"multiplier": 1.5, "damage_type": "dark", "lifesteal": 0.3},
        "妖火焚天": {"multiplier": 3.0, "damage_type": "fire", "aoe": True},
        "邪气斩": {"multiplier": 1.4, "damage_type": "dark"},
        "吸血术": {"multiplier": 1.2, "damage_type": "dark", "lifesteal": 0.5},
        "岩石撞击": {"multiplier": 1.6, "damage_type": "earth"},
        "石化": {"multiplier": 0.5, "damage_type": "earth", "stun": True},
        "地震": {"multiplier": 2.0, "damage_type": "earth", "aoe": True},
        # 玩家技能
        "青云剑诀": {"multiplier": 1.5, "damage_type": "wind"},
        "清风诀": {"multiplier": 1.2, "damage_type": "wind"},
        "流云步法": {"multiplier": 0, "damage_type": "buff", "speed_buff": 20},
        "金鼎诀": {"multiplier": 1.4, "damage_type": "fire"},
        "三昧真火": {"multiplier": 2.2, "damage_type": "fire"},
        "九鼎炼术": {"multiplier": 0, "damage_type": "buff", "defense_buff": 25},
        "万花医术": {"multiplier": 0, "damage_type": "heal", "heal_amount": 50},
        "炼金散": {"multiplier": 1.3, "damage_type": "poison"},
        "回春术": {"multiplier": 0, "damage_type": "heal", "heal_amount": 80},
        "毒术精通": {"multiplier": 1.0, "damage_type": "poison", "dot": True},
        "逍遥步": {"multiplier": 0, "damage_type": "buff", "speed_buff": 30},
        "无相功法": {"multiplier": 1.6, "damage_type": "physical"},
        "逍遥心法": {"multiplier": 0, "damage_type": "heal", "heal_amount": 30},
        "逍遥游身": {"multiplier": 0, "damage_type": "buff", "dodge_buff": 25},
        "蜀山剑法": {"multiplier": 1.8, "damage_type": "physical"},
        "八卦掌法": {"multiplier": 1.5, "damage_type": "physical"},
        "金刚伏魔功": {"multiplier": 2.0, "damage_type": "physical"},
        "内功心法": {"multiplier": 0, "damage_type": "buff", "attack_buff": 20}
    }

    effect = skill_effects.get(skill_name, {"multiplier": 1.0, "damage_type": "physical"})

    result = {
        "skill": skill_name,
        "attacker": attacker.id,
        "target": target.id,
        "success": True,
        "damage": 0,
        "heal": 0,
        "effects": []
    }

    # 治疗技能
    if effect.get("damage_type") == "heal":
        heal_amount = effect.get("heal_amount", 50)
        actual_heal = min(heal_amount, attacker.max_hp - attacker.hp)
        attacker.hp += actual_heal
        result["heal"] = actual_heal
        result["effects"].append("heal")
        session.log.append(f"{attacker.name} 使用 {skill_name}，恢复了 {actual_heal} 点生命")
        return result

    # 增益技能
    if effect.get("damage_type") == "buff":
        if effect.get("attack_buff"):
            attacker.attack += effect["attack_buff"]
            result["effects"].append(f"attack+{effect['attack_buff']}")
        if effect.get("defense_buff"):
            attacker.defense += effect["defense_buff"]
            result["effects"].append(f"defense+{effect['defense_buff']}")
        if effect.get("speed_buff"):
            attacker.speed += effect["speed_buff"]
            result["effects"].append(f"speed+{effect['speed_buff']}")
        if effect.get("dodge_buff"):
            result["effects"].append(f"dodge+{effect['dodge_buff']}")
            attacker.buffs.append({"type": "dodge", "value": effect["dodge_buff"], "duration": 3})

        session.log.append(f"{attacker.name} 使用 {skill_name}，获得了增益效果")
        return result

    # 伤害技能
    targets = [target]
    if effect.get("aoe"):
        # AOE技能，攻击所有敌人
        if attacker.entity_type == "player":
            targets = [e for e in session.enemies if e.hp > 0]
        else:
            targets = [session.player] if session.player.hp > 0 else []

    for tgt in targets:
        if tgt.hp <= 0:
            continue

        damage = calculate_damage(attacker, tgt, effect.get("multiplier", 1.0))
        tgt.hp = max(0, tgt.hp - damage)

        if effect.get("lifesteal"):
            heal = int(damage * effect["lifesteal"])
            attacker.hp = min(attacker.max_hp, attacker.hp + heal)
            result["effects"].append(f"lifesteal_{heal}")

        result["damage"] += damage

        if effect.get("stun"):
            tgt.buffs.append({"type": "stun", "duration": 1})
            result["effects"].append("stun")

        if effect.get("slow"):
            tgt.buffs.append({"type": "slow", "duration": 2, "value": -10})
            result["effects"].append("slow")

        if effect.get("dot"):
            tgt.buffs.append({"type": "dot", "duration": 3, "value": damage // 3})
            result["effects"].append("dot")

    targets_str = "所有敌人" if effect.get("aoe") else target.name
    session.log.append(f"{attacker.name} 使用 {skill_name} 对 {targets_str} 造成 {result['damage']} 点伤害")

    return result


def process_enemy_turn(session: CombatSession) -> List[Dict]:
    """处理敌人回合"""
    actions = []
    player = session.player

    for enemy in session.enemies:
        if enemy.hp <= 0:
            continue

        # 检查是否被眩晕
        stun_buff = next((b for b in enemy.buffs if b.get("type") == "stun"), None)
        if stun_buff:
            session.log.append(f"{enemy.name} 被眩晕，无法行动")
            continue

        # AI决策：随机选择行动
        action_roll = random.random()

        if action_roll < 0.7 and player.hp > 0:
            # 70%概率攻击
            if enemy.skills and random.random() < 0.4:
                # 40%概率使用技能
                skill = random.choice(enemy.skills)
                action = execute_skill(enemy, player, skill, session)
            else:
                damage = calculate_damage(enemy, player)
                player.hp = max(0, player.hp - damage)
                action = {
                    "type": "attack",
                    "attacker": enemy.id,
                    "target": player.id,
                    "damage": damage
                }
                session.log.append(f"{enemy.name} 攻击了 {player.name}，造成 {damage} 点伤害")
        elif action_roll < 0.85:
            # 15%概率防御
            enemy.is_defending = True
            action = {"type": "defend", "entity": enemy.id}
            session.log.append(f"{enemy.name} 进入防御姿态")
        else:
            # 15%概率等待
            action = {"type": "wait", "entity": enemy.id}
            session.log.append(f"{enemy.name} 观察局势")

        actions.append(action)

    # 处理持续伤害效果
    for entity in [player] + session.enemies:
        if entity.hp <= 0:
            continue
        for buff in entity.buffs[:]:
            if buff.get("type") == "dot" and buff.get("duration", 0) > 0:
                entity.hp = max(0, entity.hp - buff.get("value", 0))
                buff["duration"] -= 1
                if buff["duration"] <= 0:
                    entity.buffs.remove(buff)
            elif buff.get("duration", 0) > 0 and buff.get("type") != "dot":
                buff["duration"] -= 1
                if buff["duration"] <= 0:
                    entity.buffs.remove(buff)

    return actions


def check_combat_end(session: CombatSession) -> Optional[str]:
    """检查战斗是否结束"""
    if session.player.hp <= 0:
        session.status = CombatStatus.DEFEAT.value
        return CombatStatus.DEFEAT.value

    if all(e.hp <= 0 for e in session.enemies):
        session.status = CombatStatus.VICTORY.value
        return CombatStatus.VICTORY.value

    return None


@combat_bp.route('/start', methods=['POST'])
def start_combat():
    """开始战斗"""
    player_name = session.get('player_name')
    if not player_name:
        return jsonify({'error': '未登录'}), 401

    data = request.json or {}
    enemy_type = data.get('enemy_type')
    difficulty = data.get('difficulty', 'normal')

    player_data = load_player_by_name(player_name)
    if not player_data:
        return jsonify({'error': '玩家不存在'}), 404

    player_level = player_data.get('level', 1)

    # 创建玩家实体
    player_entity = create_player_entity(player_data)

    # 根据难度确定敌人数量
    enemy_counts = {
        "easy": 1,
        "normal": 2,
        "hard": 3,
        "boss": 1
    }
    enemy_count = enemy_counts.get(difficulty, 2)

    # 生成敌人
    enemies = []
    for i in range(enemy_count):
        if difficulty == "boss" and i == 0:
            monster_data = get_monster_data("demon_king", player_level)
        else:
            monster_data = get_monster_data(enemy_type or "", player_level)

        enemy = CombatEntity(
            id=f"enemy_{i}",
            name=monster_data["name"],
            level=monster_data["level"],
            stage=monster_data["stage"],
            hp=monster_data["hp"],
            max_hp=monster_data["max_hp"],
            attack=monster_data["attack"],
            defense=monster_data["defense"],
            speed=monster_data["speed"],
            entity_type="enemy",
            skills=monster_data.get("skills", [])
        )
        enemies.append(enemy)

    # 确定行动顺序（按速度）
    all_entities = [player_entity] + enemies
    all_entities.sort(key=lambda e: e.speed, reverse=True)
    turn_order = [e.id for e in all_entities]

    # 创建战斗会话
    session_id = f"combat_{uuid.uuid4().hex[:12]}"
    combat_session = CombatSession(
        session_id=session_id,
        player=player_entity,
        enemies=enemies,
        turn_order=turn_order,
        status=CombatStatus.ACTIVE.value
    )
    combat_sessions[session_id] = combat_session

    combat_session.log.append(f"战斗开始！{player_entity.name} vs {', '.join(e.name for e in enemies)}")

    return jsonify({
        'success': True,
        'session_id': session_id,
        'player': player_entity.to_dict(),
        'enemies': [e.to_dict() for e in enemies],
        'turn_order': turn_order
    })


@combat_bp.route('/<session_id>/action', methods=['POST'])
def execute_action(session_id: str):
    """执行行动"""
    if session_id not in combat_sessions:
        return jsonify({'error': '战斗会话不存在'}), 404

    combat_session = combat_sessions[session_id]

    if combat_session.status != CombatStatus.ACTIVE.value:
        return jsonify({'error': '战斗已结束', 'status': combat_session.status}), 400

    data = request.json or {}
    action_type = data.get('action_type', 'attack')
    target_id = data.get('target_id')
    skill_id = data.get('skill_id')

    player = combat_session.player

    if player.hp <= 0:
        return jsonify({'error': '玩家已阵亡'}), 400

    action_result = {
        'action_type': action_type,
        'actor': player.id,
        'success': True
    }

    # 重置防御状态
    player.is_defending = False

    if action_type == 'attack':
        # 普通攻击
        if not target_id:
            # 自动选择第一个存活的敌人
            alive_enemies = [e for e in combat_session.enemies if e.hp > 0]
            if not alive_enemies:
                return jsonify({'error': '没有可攻击的目标'}), 400
            target_id = alive_enemies[0].id

        target = next((e for e in combat_session.enemies if e.id == target_id), None)
        if not target or target.hp <= 0:
            return jsonify({'error': '目标无效'}), 400

        damage = calculate_damage(player, target)
        target.hp = max(0, target.hp - damage)
        action_result['target'] = target_id
        action_result['damage'] = damage

        combat_session.log.append(f"{player.name} 攻击了 {target.name}，造成 {damage} 点伤害")

    elif action_type == 'skill':
        # 使用技能
        if not skill_id:
            return jsonify({'error': '请指定技能'}), 400
        if skill_id not in player.skills:
            return jsonify({'error': '未学会该技能'}), 400

        if not target_id:
            alive_enemies = [e for e in combat_session.enemies if e.hp > 0]
            if not alive_enemies:
                return jsonify({'error': '没有可攻击的目标'}), 400
            target_id = alive_enemies[0].id

        target = next((e for e in combat_session.enemies if e.id == target_id), None)
        if not target:
            return jsonify({'error': '目标无效'}), 400

        skill_result = execute_skill(player, target, skill_id, combat_session)
        action_result.update(skill_result)

    elif action_type == 'defend':
        # 防御
        player.is_defending = True
        combat_session.log.append(f"{player.name} 进入防御姿态")

    elif action_type == 'flee':
        # 逃跑
        flee_chance = 0.5 + (player.speed / 200)
        if random.random() < flee_chance:
            combat_session.status = CombatStatus.FLED.value
            combat_session.log.append(f"{player.name} 成功逃脱了战斗")
            return jsonify({
                'success': True,
                'action': action_result,
                'session': combat_session.to_dict(),
                'log': '成功逃脱'
            })
        else:
            combat_session.log.append(f"{player.name} 逃跑失败")
            action_result['success'] = False

    elif action_type == 'item':
        # 使用物品（简化处理，恢复HP）
        heal_amount = data.get('heal_amount', 50)
        actual_heal = min(heal_amount, player.max_hp - player.hp)
        player.hp += actual_heal
        action_result['heal'] = actual_heal
        combat_session.log.append(f"{player.name} 使用了物品，恢复了 {actual_heal} 点生命")

    # 检查战斗是否结束
    combat_end_status = check_combat_end(combat_session)

    # 敌人回合
    if combat_session.status == CombatStatus.ACTIVE.value:
        enemy_actions = process_enemy_turn(combat_session)
        action_result['enemy_actions'] = enemy_actions

        # 再次检查战斗结束
        combat_end_status = check_combat_end(combat_session)

    # 更新回合
    combat_session.turn_count += 1

    # 战斗结束处理
    if combat_end_status:
        if combat_end_status == CombatStatus.VICTORY.value:
            # 计算奖励
            total_xp = sum(e.get("level", 1) * 10 for e in [get_monster_data("", player.level)] * len(combat_session.enemies))
            total_stones = sum(e.get("level", 1) * 5 for e in [get_monster_data("", player.level)] * len(combat_session.enemies))

            # 更新玩家数据
            player_name = session.get('player_name')
            if player_name:
                player_data = load_player_by_name(player_name)
                if player_data:
                    player_data['xp'] = player_data.get('xp', 0) + total_xp
                    player_data['spirit_stones'] = player_data.get('spirit_stones', 0) + total_stones
                    save_player(player_data)

            combat_session.log.append(f"战斗胜利！获得 {total_xp} 经验和 {total_stones} 仙石")

    return jsonify({
        'success': True,
        'action': action_result,
        'session': combat_session.to_dict(),
        'log': combat_session.log[-5:] if combat_session.log else []
    })


@combat_bp.route('/<session_id>/auto', methods=['POST'])
def auto_combat(session_id: str):
    """自动战斗"""
    if session_id not in combat_sessions:
        return jsonify({'error': '战斗会话不存在'}), 404

    combat_session = combat_sessions[session_id]

    if combat_session.status != CombatStatus.ACTIVE.value:
        return jsonify({'error': '战斗已结束', 'status': combat_session.status}), 400

    data = request.json or {}
    max_turns = data.get('max_turns', 50)

    player = combat_session.player

    result_log = []

    for turn in range(max_turns):
        if combat_session.status != CombatStatus.ACTIVE.value:
            break

        # 玩家自动行动
        alive_enemies = [e for e in combat_session.enemies if e.hp > 0]
        if not alive_enemies:
            break

        # 简单AI：优先使用技能，否则攻击
        if player.skills and player.hp > player.max_hp * 0.3 and random.random() < 0.3:
            skill = random.choice(player.skills)
            target = alive_enemies[0]
            execute_skill(player, target, skill, combat_session)
        else:
            target = alive_enemies[0]
            damage = calculate_damage(player, target)
            target.hp = max(0, target.hp - damage)
            result_log.append(f"{player.name} 攻击 {target.name}，造成 {damage} 伤害")

        # 检查战斗结束
        if check_combat_end(combat_session):
            break

        # 敌人回合
        process_enemy_turn(combat_session)
        combat_session.turn_count += 1

    # 计算结果
    final_status = combat_session.status
    xp_gained = 0
    stones_gained = 0
    items_dropped = []

    if final_status == CombatStatus.VICTORY.value:
        xp_gained = sum(e.get("level", 1) * 10 for e in [get_monster_data("", player.level)] * len(combat_session.enemies))
        stones_gained = sum(e.get("level", 1) * 5 for e in [get_monster_data("", player.level)] * len(combat_session.enemies))

        # 更新玩家
        player_name = session.get('player_name')
        if player_name:
            player_data = load_player_by_name(player_name)
            if player_data:
                player_data['xp'] = player_data.get('xp', 0) + xp_gained
                player_data['spirit_stones'] = player_data.get('spirit_stones', 0) + stones_gained
                save_player(player_data)

    return jsonify({
        'success': True,
        'result': {
            'status': final_status,
            'turns': combat_session.turn_count,
            'xp_gained': xp_gained,
            'stones_gained': stones_gained,
            'items_dropped': items_dropped,
            'log': combat_session.log
        }
    })


@combat_bp.route('/<session_id>', methods=['GET'])
def get_combat_status(session_id: str):
    """获取战斗状态"""
    if session_id not in combat_sessions:
        return jsonify({'error': '战斗会话不存在'}), 404

    combat_session = combat_sessions[session_id]

    return jsonify({
        'success': True,
        'session': combat_session.to_dict()
    })


@combat_bp.route('/<session_id>/log', methods=['GET'])
def get_combat_log(session_id: str):
    """获取战斗日志"""
    if session_id not in combat_sessions:
        return jsonify({'error': '战斗会话不存在'}), 404

    combat_session = combat_sessions[session_id]

    return jsonify({
        'success': True,
        'log': combat_session.log
    })


@combat_bp.route('/monsters', methods=['GET'])
def get_monsters():
    """获取可战斗怪物列表"""
    monsters = []
    for monster_id, data in MONSTER_DATA.items():
        monsters.append({
            'id': monster_id,
            'name': data['name'],
            'level_range': data['level_range'],
            'difficulty': data['difficulty'],
            'description': data.get('description', ''),
            'skills': data.get('skills', [])
        })

    return jsonify({
        'success': True,
        'monsters': monsters
    })


@combat_bp.route('/pvp/challenge', methods=['POST'])
def pvp_challenge():
    """PVP挑战（可选功能）"""
    player_name = session.get('player_name')
    if not player_name:
        return jsonify({'error': '未登录'}), 401

    data = request.json or {}
    target_player = data.get('target_player')

    if not target_player:
        return jsonify({'error': '请指定目标玩家'}), 400

    target_data = load_player_by_name(target_player)
    if not target_data:
        return jsonify({'error': '目标玩家不存在'}), 404

    player_data = load_player_by_name(player_name)
    if not player_data:
        return jsonify({'error': '玩家不存在'}), 404

    # 创建PVP会话
    player_entity = create_player_entity(player_data)
    target_entity = create_player_entity(target_data)
    target_entity.id = "enemy_0"
    target_entity.entity_type = "enemy"

    session_id = f"pvp_{uuid.uuid4().hex[:12]}"
    combat_session = CombatSession(
        session_id=session_id,
        player=player_entity,
        enemies=[target_entity],
        turn_order=[player_entity.id, target_entity.id],
        status=CombatStatus.ACTIVE.value
    )
    combat_sessions[session_id] = combat_session

    combat_session.log.append(f"PVP战斗开始！{player_entity.name} vs {target_entity.name}")

    return jsonify({
        'success': True,
        'session_id': session_id,
        'player': player_entity.to_dict(),
        'enemies': [target_entity.to_dict()],
        'is_pvp': True
    })


@combat_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """列出活跃的战斗会话（调试用）"""
    active_sessions = [
        {
            'session_id': sid,
            'status': s.status,
            'turn_count': s.turn_count,
            'player': s.player.name,
            'enemies': [e.name for e in s.enemies if e.hp > 0]
        }
        for sid, s in combat_sessions.items()
    ]

    return jsonify({
        'success': True,
        'sessions': active_sessions
    })
