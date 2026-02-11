from __future__ import annotations
"""
修仙文字MUD - 游戏逻辑核心系统
"""

from typing import Dict, List, Optional
from datetime import datetime


class CultivationSystem:
    """修仙境界系统"""
    
    def __init__(self):
        self.level: int = 1
        self.xp: int = 0
        self.stage: str = "炼气期"
        self.cultivation: int = 0
    
    def add_experience(self, amount: int) -> Dict[str, any]:
        """增加经验并检查升级"""
        self.xp += amount
        return self.check_level_up()
    
    def check_level_up(self) -> Dict[str, any]:
        """检查是否升级"""
        old_level = self.level
        new_level = self.calculate_level(self.xp)
        
        result = {
            "level_up": False,
            "stage_up": False,
            "old_level": old_level,
            "new_level": new_level,
            "xp": self.xp
        }
        
        if new_level > old_level:
            self.level = new_level
            result["level_up"] = True
            stage_change = self.check_stage_up(new_level)
            if stage_change:
                self.stage = stage_change
                result["stage_up"] = True
                result["new_stage"] = stage_change
        
        return result
    
    def calculate_level(self, xp: int) -> int:
        """根据经验计算等级"""
        # 炼气期（1-99级）：指数级增长
        if xp < 100000:
            return int((xp / 1000) ** 0.5)
        
        # 筑基期（100-199级）：线性增长
        elif xp < 1000000:
            return 100 + int((xp - 100000) / 10000)
        
        # 金丹期（200-299级）：对数级增长
        elif xp < 10000000:
            return 200 + int((xp - 1000000) / 50000)
        
        # 元婴期（300-499级）：对数级增长
        elif xp < 100000000:
            return 300 + int((xp - 10000000) / 200000)
        
        # 元神期（500-999级）：对数级增长
        else:
            return 500 + int((xp - 100000000) / 500000)
    
    def check_stage_up(self, level: int) -> Optional[str]:
        """检查是否突破境界"""
        if 1 <= level <= 99:
            return "筑基期"  # 炼气 → 筑基
        elif 100 <= level <= 199:
            return "金丹期"  # 筑基 → 金丹
        elif 200 <= level <= 299:
            return "元婴期"  # 金丹 → 元婴
        elif 300 <= level <= 499:
            return "元神期"  # 元婴 → 元神
        return None
    
    def get_stage_requirements(self) -> Dict[str, any]:
        """获取当前境界的突破要求"""
        if self.stage == "炼气期":
            return {
                "stage": "炼气期",
                "level_range": "1-99",
                "xp_required": 10000,
                "benefits": [
                    "灵压上限 +10%",
                    "气血防御 +5%",
                    "行动速度 +10%"
                ]
            }
        elif self.stage == "筑基期":
            return {
                "stage": "筑基期",
                "level_range": "100-199",
                "xp_required": 100000,
                "benefits": [
                    "真气上限 +20%",
                    "法术攻击 +10%",
                    "法术防御 +10%",
                    "内视能力 +5%"
                ]
            }
        elif self.stage == "金丹期":
            return {
                "stage": "金丹期",
                "level_range": "200-299",
                "xp_required": 1000000,
                "benefits": [
                    "金丹效果 +30%",
                    "火属性抗性 +15%",
                    "寿命上限 +10%"
                ]
            }
        elif self.stage == "元婴期":
            return {
                "stage": "元婴期",
                "level_range": "300-499",
                "xp_required": 10000000,
                "benefits": [
                    "元婴出窍 +30%",
                    "妖法护盾 +10%",
                    "通天法术 +20%",
                    "渡劫成功率 +20%"
                ]
            }
        elif self.stage == "元神期":
            return {
                "stage": "元神期",
                "level_range": "500-999",
                "xp_required": 100000000,
                "benefits": [
                    "神之力 +50%",
                    "通天法术 +20%",
                    "仙身不死 +10%",
                    "天道法则 +30%"
                ]
            }
        return {}


class SectSystem:
    """门派系统"""
    
    def __init__(self):
        self.sect_type: Optional[str] = None
        self.sect_stats: Dict[str, int] = {}
        self.skills: List[str] = []
        self.reputation: int = 0
    
    def join_sect(self, sect_type: str) -> Dict[str, any]:
        """加入门派"""
        self.sect_type = sect_type
        
        # 根据门派设置属性加成
        if sect_type == "青云门":
            self.sect_stats = {
                "speed": 20,
                "agility": 15,
                "dodge": 10
            }
            self.skills = ["青云剑诀", "清风诀", "流云步法"]
        elif sect_type == "丹鼎门":
            self.sect_stats = {
                "attack": 30,
                "defense": 25,
                "constitution": 15
            }
            self.skills = ["金鼎诀", "三昧真火", "九鼎炼术"]
        elif sect_type == "万花谷":
            self.sect_stats = {
                "constitution": 30,
                "healing": 25,
                "resistance": 20,
                "poison_resist": 20
            }
            self.skills = ["万花医术", "炼金散", "回春术", "毒术精通"]
        elif sect_type == "逍遥宗":
            self.sect_stats = {
                "dodge": 25,
                "stealth": 10,
                "movement": 20
            }
            self.skills = ["逍遥步", "无相功法", "逍遥心法", "逍遥游身"]
        elif sect_type == "蜀山派":
            self.sect_stats = {
                "attack": 40,
                "defense": 20,
                "crit": 15
            }
            self.skills = ["蜀山剑法", "八卦掌法", "金刚伏魔功", "内功心法"]
        
        return {
            "sect_type": sect_type,
            "stats": self.sect_stats,
            "skills": self.skills
        }
    
    def add_reputation(self, amount: int) -> int:
        """增加门派声望"""
        self.reputation += amount
        return self.reputation
    
    def get_sect_benefits(self) -> Dict[str, any]:
        """获取门派特权"""
        benefits = []
        
        if self.reputation >= 1000:
            benefits.append("高级门派任务")
        
        if self.reputation >= 5000:
            benefits.append("门派专属商店")
        
        if self.reputation >= 10000:
            benefits.append("门派长老称号")
        
        return {
            "reputation": self.reputation,
            "benefits": benefits,
            "next_tier": self.get_next_tier(self.reputation)
        }
    
    def get_next_tier(self, current_rep: int) -> Dict[str, any]:
        """获取下一声望层级"""
        if current_rep < 1000:
            return {"tier": "新手", "required": 1000}
        elif current_rep < 5000:
            return {"tier": "初级", "required": 5000}
        elif current_rep < 10000:
            return {"tier": "中级", "required": 10000}
        elif current_rep < 50000:
            return {"tier": "高级", "required": 50000}
        else:
            return {"tier": "精英", "required": 100000}


class EconomySystem:
    """仙石经济系统"""
    
    def __init__(self):
        self.spirit_stones: int = 0
        self.transaction_history: List[Dict] = []
    
    def earn_stones(self, amount: int, source: str) -> Dict[str, any]:
        """获取仙石"""
        self.spirit_stones += amount
        self.transaction_history.append({
            "type": "earn",
            "amount": amount,
            "source": source,
            "timestamp": datetime.now()
        })
        
        return {
            "amount": amount,
            "source": source,
            "total": self.spirit_stones
        }
    
    def spend_stones(self, amount: int, purpose: str) -> bool:
        """消耗仙石"""
        if self.spirit_stones < amount:
            return False
        
        self.spirit_stones -= amount
        self.transaction_history.append({
            "type": "spend",
            "amount": amount,
            "purpose": purpose,
            "timestamp": datetime.now()
        })
        
        return True
    
    def get_balance(self) -> Dict[str, any]:
        """获取仙石余额"""
        return {
            "spirit_stones": self.spirit_stones,
            "transaction_count": len(self.transaction_history)
        }
    
    def get_daily_income(self) -> Dict[str, any]:
        """获取日收入"""
        # 打坐：10-20仙石/小时
        # 任务：50-2000仙石
        # 门派福利：100-5000仙石
        
        return {
            "mediation": "10-20 仙石/小时",
            "tasks": "50-2000 仙石",
            "sect_welfare": "100-5000 仙石",
            "total_daily": "120-240 仙石（打坐） + 任务 + 福利"
        }


if __name__ == "__main__":
    # 测试游戏系统
    print("🧪 修仙文字MUD游戏系统测试")
    
    # 测试修仙境界系统
    print("\n--- 修仙境界系统 ---")
    cult = CultivationSystem()
    cult.level = 1
    cult.xp = 0
    
    print(f"初始状态: 等级 {cult.level}, 经验 {cult.xp}")
    
    # 模拟增加经验
    result = cult.add_experience(5000)
    print(f"增加5000经验后: {result}")
    
    # 测试门派系统
    print("\n--- 门派系统 ---")
    sect = SectSystem()
    sect_result = sect.join_sect("青云门")
    print(f"加入门派: {sect_result}")
    
    # 测试经济系统
    print("\n--- 仙石经济系统 ---")
    eco = EconomySystem()
    
    # 打坐获取仙石
    earn = eco.earn_stones(15, "打坐1.5小时")
    print(f"获取仙石: {earn}")
    
    # 消耗仙石
    spend = eco.spend_stones(100, "传送费用")
    print(f"消耗仙石: {spend}")
    
    # 查看余额
    balance = eco.get_balance()
    print(f"仙石余额: {balance}")
