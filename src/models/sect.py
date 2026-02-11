from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from src.models.player import SectType


@dataclass
class Sect:
    sect_id: str
    name: str
    type: SectType
    description: str
    cultivation: int = 999
    title: str = "掌门"
    color: str = "#FFFFFF"
    skills: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)


SECT_PRESETS = {
    SectType.QINGYUN: {
        "name": "青云门",
        "type": SectType.QINGYUN,
        "description": "以风清静、逍遥自在著称",
        "cultivation": 999,
        "title": "青云掌门",
        "color": "#87CEEB",
        "stats": {
            "speed": 20,
            "agility": 15,
            "attack": 10,
            "defense": 5
        },
        "skills": ["青云剑诀", "清风诀", "流云步法"]
    },
    SectType.DANDING: {
        "name": "丹鼎门",
        "type": SectType.DANDING,
        "description": "以炼丹、鼎炉、火属性著称",
        "cultivation": 999,
        "title": "丹鼎掌门",
        "color": "#FF5733",
        "stats": {
            "attack": 30,
            "defense": 25,
            "constitution": 15,
            "intellect": 5
        },
        "skills": ["金鼎诀", "三昧真火", "九鼎炼术"]
    },
    SectType.WANHUA: {
        "name": "万花谷",
        "type": SectType.WANHUA,
        "description": "以灵药、医术、疗愈著称",
        "cultivation": 999,
        "title": "万花谷主",
        "color": "#FFB6C1",
        "stats": {
            "constitution": 30,
            "healing": 25,
            "resistance": 20,
            "poison_resist": 20
        },
        "skills": ["万花医术", "炼金散", "回春术", "毒术精通"]
    },
    SectType.XIAOYAO: {
        "name": "逍遥宗",
        "type": SectType.XIAOYAO,
        "description": "以逍遥自在、潇洒不羁著称",
        "cultivation": 999,
        "title": "逍遥仙尊",
        "color": "#9B59B6",
        "stats": {
            "dodge": 25,
            "stealth": 10,
            "movement": 20,
            "crit": 10
        },
        "skills": ["逍遥步", "无相功法", "逍遥心法", "逍遥游身"]
    },
    SectType.SHUSHAN: {
        "name": "蜀山派",
        "type": SectType.SHUSHAN,
        "description": "以武力、坚韧、忠诚著称",
        "cultivation": 999,
        "title": "蜀山掌门",
        "color": "#FFD700",
        "stats": {
            "attack": 40,
            "defense": 20,
            "constitution": 15,
            "crit": 15
        },
        "skills": ["蜀山剑法", "八卦掌法", "金刚伏魔功", "内功心法"]
    }
}


SECT_ADVANTAGES = {
    (SectType.QINGYUN, SectType.WANHUA): 1.2,
    (SectType.QINGYUN, SectType.XIAOYAO): 1.5,
    (SectType.QINGYUN, SectType.SHUSHAN): 0.8,
    (SectType.QINGYUN, SectType.DANDING): 0.9,
}


def get_sect_advantage(attacker: SectType, defender: SectType) -> float:
    return SECT_ADVANTAGES.get((attacker, defender), 1.0)
