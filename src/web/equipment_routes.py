"""
装备系统 API 路由
"""
from flask import Blueprint, request, jsonify, session
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.equipment import (
    Equipment, EquipmentSlot, Rarity,
    get_generator, get_calculator, get_enhancer, get_validator,
    rarity_from_string
)
from src.data.simple_storage import load_player_by_name, save_player

equipment_bp = Blueprint('equipment', __name__, url_prefix='/api/equipment')


@equipment_bp.route('/generate', methods=['POST'])
def generate_equipment():
    """生成随机装备

    Body: {
        "level": 10,
        "slot": "WEAPON",
        "source": "normal_monster",
        "forced_rarity": "RARE"  # optional
    }
    """
    try:
        data = request.json or {}
        level = data.get('level', 1)
        slot_name = data.get('slot', 'WEAPON')
        source = data.get('source', 'normal_monster')
        forced_rarity = data.get('forced_rarity')

        slot = EquipmentSlot[slot_name]
        rarity = rarity_from_string(forced_rarity) if forced_rarity else None

        generator = get_generator()
        equipment = generator.generate(
            level=level,
            slot=slot,
            source=source,
            forced_rarity=rarity
        )

        return jsonify({
            'success': True,
            'equipment': equipment.model_dump()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@equipment_bp.route('/<equipment_id>/enhance', methods=['POST'])
def enhance_equipment(equipment_id: str):
    """强化装备

    Body: {
        "equipment": {...},
        "use_protection": false,
        "luck_bonus": 0.0
    }
    """
    try:
        data = request.json or {}
        equipment_data = data.get('equipment')
        use_protection = data.get('use_protection', False)
        luck_bonus = data.get('luck_bonus', 0.0)

        if not equipment_data:
            return jsonify({'success': False, 'error': '缺少装备数据'}), 400

        equipment = Equipment(**equipment_data)
        enhancer = get_enhancer()
        result = enhancer.enhance(equipment, use_protection, luck_bonus)

        return jsonify({
            'success': True,
            'result': {
                'success': result.success,
                'old_level': result.old_level,
                'new_level': result.new_level,
                'message': result.message,
                'materials_consumed': result.materials_consumed
            },
            'equipment': equipment.model_dump()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@equipment_bp.route('/calculate', methods=['POST'])
def calculate_stats():
    """计算装备属性

    Body: {"equipment": {...}}
    """
    try:
        data = request.json or {}
        equipment_data = data.get('equipment')

        if not equipment_data:
            return jsonify({'success': False, 'error': '缺少装备数据'}), 400

        equipment = Equipment(**equipment_data)
        calculator = get_calculator()
        stats = calculator.calculate_equipment_stats(equipment)
        combat_power = calculator.calculate_combat_power(stats)

        return jsonify({
            'success': True,
            'stats': stats,
            'combat_power': combat_power
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@equipment_bp.route('/player/<player_name>/equip', methods=['POST'])
def equip_item(player_name: str):
    """装备物品

    Body: {
        "equipment_id": "equip_xxx",
        "slot": "WEAPON",
        "equipment": {...}  # 装备数据用于存储
    }
    """
    try:
        player_data = load_player_by_name(player_name)
        if not player_data:
            return jsonify({'success': False, 'error': '玩家不存在'}), 404

        data = request.json or {}
        equipment_id = data.get('equipment_id')
        slot = data.get('slot')
        equipment_data = data.get('equipment')

        if not equipment_id or not slot:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        # 初始化 equipment_slots 如果不存在
        if 'equipment_slots' not in player_data:
            player_data['equipment_slots'] = {
                "WEAPON": None, "HELMET": None, "ARMOR": None,
                "GLOVES": None, "BOOTS": None, "BELT": None,
                "AMULET": None, "RING_LEFT": None, "RING_RIGHT": None,
                "ARTIFACT": None
            }

        # 初始化 inventory 如果不存在
        if 'inventory' not in player_data:
            player_data['inventory'] = []

        # 获取旧装备
        old_equipment = player_data['equipment_slots'].get(slot)

        # 装备新物品
        player_data['equipment_slots'][slot] = equipment_id

        # 从背包移除
        if equipment_id in player_data['inventory']:
            player_data['inventory'].remove(equipment_id)

        # 旧装备放入背包
        if old_equipment:
            player_data['inventory'].append(old_equipment)

        # 存储装备数据 (简化处理，实际应该有单独的装备存储)
        if 'equipment_storage' not in player_data:
            player_data['equipment_storage'] = {}
        player_data['equipment_storage'][equipment_id] = equipment_data

        save_player(player_data)

        return jsonify({
            'success': True,
            'slot': slot,
            'equipment_id': equipment_id,
            'replaced': old_equipment
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@equipment_bp.route('/player/<player_name>/unequip', methods=['POST'])
def unequip_item(player_name: str):
    """卸下装备

    Body: {"slot": "WEAPON"}
    """
    try:
        player_data = load_player_by_name(player_name)
        if not player_data:
            return jsonify({'success': False, 'error': '玩家不存在'}), 404

        data = request.json or {}
        slot = data.get('slot')

        if not slot:
            return jsonify({'success': False, 'error': '缺少槽位参数'}), 400

        equipment_slots = player_data.get('equipment_slots', {})
        equipment_id = equipment_slots.get(slot)

        if not equipment_id:
            return jsonify({'success': False, 'error': '该槽位没有装备'}), 400

        # 卸下装备
        player_data['equipment_slots'][slot] = None

        # 放入背包
        inventory = player_data.get('inventory', [])
        inventory.append(equipment_id)
        player_data['inventory'] = inventory

        save_player(player_data)

        return jsonify({
            'success': True,
            'slot': slot,
            'equipment_id': equipment_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@equipment_bp.route('/player/<player_name>/inventory', methods=['GET'])
def get_inventory(player_name: str):
    """获取玩家装备背包"""
    try:
        player_data = load_player_by_name(player_name)
        if not player_data:
            return jsonify({'success': False, 'error': '玩家不存在'}), 404

        inventory = player_data.get('inventory', [])
        equipment_storage = player_data.get('equipment_storage', {})
        equipment_slots = player_data.get('equipment_slots', {})

        # 计算总属性
        equipped_items = []
        for slot, eid in equipment_slots.items():
            if eid and eid in equipment_storage:
                equipped_items.append(Equipment(**equipment_storage[eid]))

        calculator = get_calculator()
        total_stats = calculator.calculate_player_total_stats(equipped_items)
        combat_power = calculator.calculate_combat_power(total_stats)

        return jsonify({
            'success': True,
            'inventory': inventory,
            'equipment_slots': equipment_slots,
            'total_stats': total_stats,
            'combat_power': combat_power
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@equipment_bp.route('/slots', methods=['GET'])
def get_slots():
    """获取所有装备槽位"""
    return jsonify({
        'success': True,
        'slots': [{'name': slot.name, 'display': slot.value} for slot in EquipmentSlot]
    })


@equipment_bp.route('/rarities', methods=['GET'])
def get_rarities():
    """获取所有稀有度"""
    return jsonify({
        'success': True,
        'rarities': [
            {
                'name': rarity.name,
                'display': rarity.display_name,
                'color': rarity.color,
                'multiplier': rarity.multiplier,
                'affix_slots': rarity.affix_slots
            }
            for rarity in Rarity
        ]
    })
