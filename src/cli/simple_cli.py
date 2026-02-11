#!/usr/bin/env python3
"""
修仙文字MUD - 简化版CLI（无需数据库）
"""

import click
import sys
import os
from datetime import datetime
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.data.simple_storage import save_player, load_player, load_player_by_name
from src.models.player import Player, CultivationStage, SectType
from src.models.sect import SECT_PRESETS

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


@click.group()
def cli():
    pass


@cli.command()
@click.argument('name')
@click.option('--sect', type=click.Choice(['qingyun', 'danding', 'wanhua', 'xiaoyao', 'shushan']), default='qingyun')
def create(name: str, sect: str):
    global CURRENT_PLAYER
    
    existing = load_player_by_name(name)
    if existing:
        click.echo(f"❌ 角色 '{name}' 已存在")
        return
    
    sect_mapping = {
        'qingyun': SectType.QINGYUN,
        'danding': SectType.DANDING,
        'wanhua': SectType.WANHUA,
        'xiaoyao': SectType.XIAOYAO,
        'shushan': SectType.SHUSHAN
    }
    
    sect_type = sect_mapping[sect]
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
        CURRENT_PLAYER = player
        click.echo(f"✅ 角色 '{name}' 创建成功!")
        click.echo(f"   门派: {sect_preset['name']}")
        click.echo(f"   战斗力: {player.get_combat_power()}")
    else:
        click.echo("❌ 创建失败")


@cli.command()
@click.argument('name')
def login(name: str):
    global CURRENT_PLAYER
    
    player_data = load_player_by_name(name)
    if not player_data:
        click.echo(f"❌ 角色 '{name}' 不存在")
        click.echo("提示: 使用 'create <名字>' 创建新角色")
        return
    
    click.echo(f"✅ 登录成功: {name}")
    click.echo(f"等级: {player_data.get('level', 1)} | 境界: {player_data.get('stage', '炼气期')}")


@cli.command()
def status():
    if not CURRENT_PLAYER:
        click.echo("❌ 请先登录 (使用: login <名字>)")
        return
    
    player = CURRENT_PLAYER
    click.echo("\n" + "="*50)
    click.echo("👤 角色状态")
    click.echo("="*50)
    click.echo(f"姓名: {player.name}")
    click.echo(f"等级: {player.level}")
    click.echo(f"境界: {player.stage.value}")
    click.echo(f"门派: {player.sect.value if player.sect else '无'}")
    click.echo(f"仙石: {player.spirit_stones}")
    click.echo(f"战斗力: {player.get_combat_power()}")
    click.echo(f"经验: {player.xp}")


@cli.command()
@click.option('--hours', default=1, help='打坐时长（小时）')
def cultivate(hours: int):
    if not CURRENT_PLAYER:
        click.echo("❌ 请先登录")
        return
    
    if hours > 24:
        click.echo("❌ 单次打坐不能超过24小时")
        return
    
    player = CURRENT_PLAYER
    click.echo(f"🧘 {player.name} 开始打坐修炼...")
    
    xp_gain = 10 * hours
    player.xp += xp_gain
    
    stones_gain = sum(random.randint(10, 20) for _ in range(hours))
    player.spirit_stones += stones_gain
    
    old_level = player.level
    new_level = calculate_level_from_xp(player.xp)
    
    if new_level > old_level:
        player.level = new_level
        click.echo(f"⬆️ 等级提升: {old_level} → {new_level}")
        
        new_stage = get_stage_from_level(new_level)
        if new_stage != player.stage:
            player.stage = new_stage
            click.echo(f"🎭 突破境界: {new_stage.value}")
    
    save_player(player.__dict__)
    
    click.echo(f"\n📊 修炼成果:")
    click.echo(f"   获得经验: +{xp_gain}")
    click.echo(f"   获得仙石: +{stones_gain}")
    click.echo(f"   当前等级: {player.level}")
    click.echo(f"   当前境界: {player.stage.value}")


@cli.command()
@click.option('--hours', default=1, help='探索时长（小时）')
def explore(hours: int):
    if not CURRENT_PLAYER:
        click.echo("❌ 请先登录")
        return
    
    if hours > 8:
        click.echo("❌ 单次探索不能超过8小时")
        return
    
    player = CURRENT_PLAYER
    click.echo(f"🗺️  {player.name} 开始探索秘境...")
    click.echo(f"   探索时长: {hours} 小时")
    
    events = []
    total_xp = 0
    total_stones = 0
    
    for hour in range(hours):
        event_roll = random.random()
        
        if event_roll < 0.4:
            # 遭遇妖兽
            monster_level = max(1, player.level + random.randint(-3, 3))
            monster_name = random.choice(['野狼', '山贼', '妖狐', '毒蝎', '野猪'])
            
            events.append(f"第{hour+1}小时: 遭遇 Lv.{monster_level} {monster_name}")
            
            # 简化战斗
            player_power = player.get_combat_power()
            monster_power = monster_level * 15 + random.randint(10, 50)
            
            if player_power > monster_power:
                xp_gain = monster_level * 5 + random.randint(10, 30)
                stone_gain = random.randint(5, 20)
                events.append(f"   ✅ 战斗胜利! 获得 {xp_gain} 经验, {stone_gain} 仙石")
                total_xp += xp_gain
                total_stones += stone_gain
            else:
                hp_loss = random.randint(10, 30)
                events.append(f"   ❌ 战斗失败! 损失 {hp_loss} HP")
        
        elif event_roll < 0.7:
            # 发现资源
            resource_type = random.choice(['灵草', '矿石', '遗迹', '宝箱'])
            events.append(f"第{hour+1}小时: 发现 {resource_type}")
            
            if resource_type == '宝箱':
                stone_gain = random.randint(20, 100)
                events.append(f"   🎁 打开宝箱获得 {stone_gain} 仙石")
                total_stones += stone_gain
            else:
                xp_gain = random.randint(5, 15)
                events.append(f"   📦 采集获得 {xp_gain} 经验")
                total_xp += xp_gain
        
        else:
            # 平安无事
            xp_gain = 5
            events.append(f"第{hour+1}小时: 平安无事, 获得 {xp_gain} 经验")
            total_xp += xp_gain
    
    # 显示探索结果
    click.echo("\n📜 探索日志:")
    click.echo("-" * 50)
    for event in events:
        click.echo(event)
    
    # 应用收益
    player.xp += total_xp
    player.spirit_stones += total_stones
    
    # 检查升级
    old_level = player.level
    new_level = calculate_level_from_xp(player.xp)
    
    if new_level > old_level:
        player.level = new_level
        click.echo(f"\n⬆️ 等级提升: {old_level} → {new_level}")
        
        new_stage = get_stage_from_level(new_level)
        if new_stage != player.stage:
            player.stage = new_stage
            click.echo(f"🎭 突破境界: {new_stage.value}")
    
    # 保存
    save_player(player.__dict__)
    
    click.echo(f"\n📊 探索总结 ({hours} 小时):")
    click.echo(f"   总经验: +{total_xp}")
    click.echo(f"   总仙石: +{total_stones}")
    click.echo(f"   当前等级: {player.level}")
    click.echo(f"   当前境界: {player.stage.value}")


@cli.command()
def quest():
    if not CURRENT_PLAYER:
        click.echo("❌ 请先登录")
        return
    
    player = CURRENT_PLAYER
    click.echo("\n" + "="*50)
    click.echo("📜 任务系统")
    click.echo("="*50)
    
    # 日常任务
    daily_quests = [
        {"name": "打坐修炼", "desc": "累计打坐修炼 8 小时", "reward_xp": 500, "reward_stones": 100},
        {"name": "秘境探索", "desc": "完成 3 次秘境探索", "reward_xp": 800, "reward_stones": 200},
        {"name": "降妖除魔", "desc": "击败 5 只妖兽", "reward_xp": 1000, "reward_stones": 300},
        {"name": "门派贡献", "desc": "完成门派任务 3 次", "reward_xp": 600, "reward_stones": 150},
    ]
    
    click.echo("\n📅 日常任务:")
    for i, quest in enumerate(daily_quests, 1):
        click.echo(f"\n  [{i}] {quest['name']}")
        click.echo(f"      描述: {quest['desc']}")
        click.echo(f"      奖励: {quest['reward_xp']} 经验, {quest['reward_stones']} 仙石")
    
    # 主线任务
    main_quests = [
        {"name": "初入修仙", "desc": "达到炼气期 10 级", "completed": player.level >= 10},
        {"name": "筑基成功", "desc": "突破到筑基期", "completed": player.stage.value in ['筑基期', '金丹期', '元婴期', '元神期']},
        {"name": "修仙有成", "desc": "达到金丹期", "completed": player.stage.value in ['金丹期', '元婴期', '元神期']},
        {"name": "元婴大成", "desc": "突破到元婴期", "completed": player.stage.value in ['元婴期', '元神期']},
        {"name": "元神归位", "desc": "达到元神期", "completed": player.stage.value == '元神期'},
    ]
    
    click.echo("\n🎯 主线任务:")
    for quest in main_quests:
        status = "✅" if quest['completed'] else "⬜"
        click.echo(f"  [{status}] {quest['name']}: {quest['desc']}")
    
    click.echo("\n" + "="*50)


@cli.command()
@click.argument('target', required=False)
def battle(target):
    if not CURRENT_PLAYER:
        click.echo("❌ 请先登录")
        return
    
    player = CURRENT_PLAYER
    
    # 生成敌人
    if target:
        enemy_name = target
    else:
        enemies = ['野狼', '山贼', '妖狐', '毒蝎', '野猪', '恶霸', '魔修', '妖兽']
        enemy_name = random.choice(enemies)
    
    enemy_level = max(1, player.level + random.randint(-2, 3))
    enemy_hp = enemy_level * 20 + random.randint(10, 50)
    enemy_max_hp = enemy_hp
    enemy_attack = enemy_level * 5 + random.randint(5, 15)
    enemy_defense = enemy_level * 3 + random.randint(2, 8)
    
    # 玩家属性
    player_hp = player.level * 25 + 100
    player_max_hp = player_hp
    player_attack = player.get_combat_power() // 5 + 10
    player_defense = player.level * 4 + 5
    
    click.echo("\n" + "="*60)
    click.echo("⚔️  战斗开始!")
    click.echo("="*60)
    click.echo(f"\n👤 {player.name} (Lv.{player.level})")
    click.echo(f"   HP: {player_hp}/{player_max_hp}")
    click.echo(f"   攻击: {player_attack} | 防御: {player_defense}")
    click.echo(f"\n👹 {enemy_name} (Lv.{enemy_level})")
    click.echo(f"   HP: {enemy_hp}/{enemy_max_hp}")
    click.echo(f"   攻击: {enemy_attack} | 防御: {enemy_defense}")
    
    click.echo("\n" + "-"*60)
    
    # 战斗回合
    round_num = 1
    while player_hp > 0 and enemy_hp > 0:
        click.echo(f"\n🔄 第 {round_num} 回合")
        
        # 玩家攻击
        damage = max(1, player_attack - enemy_defense)
        damage = int(damage * random.uniform(0.8, 1.2))  # 随机波动
        
        # 暴击判定 (10%概率)
        is_crit = random.random() < 0.1
        if is_crit:
            damage = int(damage * 1.5)
            click.echo(f"   💥 {player.name} 发动暴击!")
        
        enemy_hp -= damage
        enemy_hp = max(0, enemy_hp)
        click.echo(f"   ⚔️  {player.name} 造成 {damage} 伤害 ({enemy_name} HP: {enemy_hp})")
        
        if enemy_hp <= 0:
            break
        
        # 敌人攻击
        damage = max(1, enemy_attack - player_defense)
        damage = int(damage * random.uniform(0.8, 1.2))
        
        # 敌人暴击 (5%概率)
        if random.random() < 0.05:
            damage = int(damage * 1.5)
            click.echo(f"   💢 {enemy_name} 发动暴击!")
        
        player_hp -= damage
        player_hp = max(0, player_hp)
        click.echo(f"   🗡️  {enemy_name} 造成 {damage} 伤害 ({player.name} HP: {player_hp})")
        
        round_num += 1
        
        if round_num > 50:  # 防止无限战斗
            click.echo("\n⏱️  战斗超时!")
            break
    
    # 战斗结果
    click.echo("\n" + "="*60)
    if player_hp > 0 and enemy_hp <= 0:
        click.echo("🎉 战斗胜利!")
        
        # 奖励
        xp_reward = enemy_level * 10 + random.randint(20, 50)
        stone_reward = enemy_level * 3 + random.randint(5, 15)
        
        player.xp += xp_reward
        player.spirit_stones += stone_reward
        
        click.echo(f"   获得 {xp_reward} 经验")
        click.echo(f"   获得 {stone_reward} 仙石")
        
        # 升级检查
        old_level = player.level
        new_level = calculate_level_from_xp(player.xp)
        if new_level > old_level:
            player.level = new_level
            click.echo(f"\n⬆️ 等级提升: {old_level} → {new_level}")
            
            new_stage = get_stage_from_level(new_level)
            if new_stage != player.stage:
                player.stage = new_stage
                click.echo(f"🎭 突破境界: {new_stage.value}")
        
        save_player(player.__dict__)
        
    elif player_hp <= 0:
        click.echo("💀 战斗失败!")
        click.echo("   你受了重伤，需要休息恢复...")
        # 惩罚：损失一些仙石
        penalty = min(player.spirit_stones // 10, 100)
        player.spirit_stones -= penalty
        click.echo(f"   损失 {penalty} 仙石作为医疗费")
        save_player(player.__dict__)
    else:
        click.echo("🏳️ 战斗平局")
    
    click.echo("="*60)


if __name__ == '__main__':
    cli()
