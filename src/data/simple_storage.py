import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data/players')

os.makedirs(DATA_DIR, exist_ok=True)

def get_player_file(player_id: str) -> str:
    return os.path.join(DATA_DIR, f'{player_id}.json')

def serialize_player(player_data: Dict[str, Any]) -> Dict[str, Any]:
    """将玩家数据序列化为可JSON存储的格式"""
    data = player_data.copy()
    
    # 处理枚举类型
    if 'stage' in data and hasattr(data['stage'], 'value'):
        data['stage'] = data['stage'].value
    elif 'stage' in data and isinstance(data['stage'], str):
        # 已经是字符串形式，保留
        pass
        
    if 'sect' in data and hasattr(data['sect'], 'value'):
        data['sect'] = data['sect'].value
    elif 'sect' in data and isinstance(data['sect'], str):
        # 已经是字符串形式，保留
        pass
    
    # 处理datetime
    for key in ['created_at', 'last_active']:
        if key in data and hasattr(data[key], 'isoformat'):
            data[key] = data[key].isoformat()
    
    return data


def save_player(player_data: Dict[str, Any]) -> bool:
    try:
        player_id = player_data.get('player_id')
        if not player_id:
            return False
        
        # 序列化数据
        serializable_data = serialize_player(player_data)
        
        file_path = get_player_file(player_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_player(player_id: str) -> Optional[Dict[str, Any]]:
    try:
        file_path = get_player_file(player_id)
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载失败: {e}")
        return None

def load_player_by_name(name: str) -> Optional[Dict[str, Any]]:
    try:
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.json'):
                with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('name') == name:
                        return data
        return None
    except Exception as e:
        print(f"查找失败: {e}")
        return None

def list_all_players() -> list:
    players = []
    try:
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.json'):
                with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
                    players.append(json.load(f))
    except:
        pass
    return players
