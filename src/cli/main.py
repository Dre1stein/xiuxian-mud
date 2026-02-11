#!/usr/bin/env python3
"""
修仙文字MUD - 命令行界面（CLI）
"""

import click
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.data.database import get_session, init_db
from src.models.player import Player, CultivationStage, SectType
from src.models.sect import Sect, SECT_PRESETS, get_sect_advantage
from src.models.item import Item, ItemQuality, ItemCategory
from src.game.game_systems import CultivationSystem, SectSystem, EconomySystem

SESSION = None
CURRENT_PLAYER: Optional[Player] = None
PLAYER_ID: Optional[str] = None


def get_player() -> Optional[Player]:
    global CURRENT_PLAYER, PLAYER_ID
    if PLAYER_ID and not CURRENT_PLAYER:
        with get_session() as session:
            CURRENT_PLAYER = session.query(Player).filter(Player.player_id == PLAYER_ID).first()
    return CURRENT_PLAYER


@click.group()
def cli():
    pass


@cli.command()
def init():
    click.echo("🚀 初始化修仙文字MUD数据库...")
    init_db()
    click.echo("✅ 数据库初始化完成")


@cli.command()
@click.argument('player_name')
@click.option('--sect', type=click.Choice(['qingyun', 'danding', 'wanhua', 'xiaoyao', 'shushan']), default='qingyun')
def create(player_name: str, sect: str):
    global PLAYER_ID
    click.echo(f"🧙 创建角色: {player_name}")
    
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
        name=player_name,
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
    
    try:
        with get_session() as session:
            session.add(player)
            session.commit()
            PLAYER_ID = player.player_id
            click.echo(f"✅ 角色创建成功!")
            click.echo(f"   姓名: {player.name}")
            click.echo(f"   门派: {player.sect.value}")
            click.echo(f"   战斗力: {player.get_combat_power()}")
    except Exception as e:
        click.echo(f"❌ 创建失败: {str(e)}")


@cli.command()
@click.argument('name')
def login(name: str):
    global PLAYER_ID
    with get_session() as session:
        player = session.query(Player).filter(Player.name == name).first()
        if player:
            PLAYER_ID = player.player_id
            click.echo(f"✅ 登录成功: {player.name}")
            click.echo(f"   等级: {player.level} | 境界: {player.stage.value}")
        else:
            click.echo(f"❌ 角色不存在: {name}")


@cli.command()
def logout():
    global PLAYER_ID, CURRENT_PLAYER
    if PLAYER_ID:
        click.echo("👋 已登出")
        PLAYER_ID = None
        CURRENT_PLAYER = None
    else:
        click.echo("❌ 未登录")


@cli.command()
@click.option('--hours', type=int, default=1)
def cultivate(hours: int):
    player = get_player()
    if not player:
        click.echo("❌ 请先登录")
        return
    
    if hours > 24:
        click.echo("❌ 单次打坐不能超过24小时")
        return
    
    click.echo(f"🧘 {player.name} 开始打坐修炼...")
    click.echo(f"   时长: {hours} 小时")
    
    try:
        with get_session() as session:
            player = session.query(Player).filter(Player.player_id == player.player_id).first()
            
            xp_gain = 10 * hours
            player.xp += xp_gain
            
            import random
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
            
            session.commit()
            
            click.echo(f"\n📊 修炼成果:")
            click.echo(f"   获得经验: +{xp_gain}")
            click.echo(f"   获得仙石: +{stones_gain}")
            click.echo(f"   当前等级: {player.level}")
            click.echo(f"   当前经验: {player.xp}")
            click.echo(f"   当前境界: {player.stage.value}")
            click.echo(f"   仙石余额: {player.spirit_stones}")
            
    except Exception as e:
        click.echo(f"❌ 修炼失败: {str(e)}")


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


@cli.command()
def status():
    player = get_player()
    if not player:
        click.echo("❌ 请先登录")
        return
    
    with get_session() as session:
        player = session.query(Player).filter(Player.player_id == player.player_id).first()
        
        click.echo("\n" + "="*50)
        click.echo("👤 角色信息")
        click.echo("="*50)
        click.echo(f"姓名: {player.name}")
        click.echo(f"等级: {player.level}")
        click.echo(f"境界: {player.stage.value}")
        click.echo(f"门派: {player.sect.value if player.sect else '无'}")
        click.echo(f"仙石: {player.spirit_stones}")
        click.echo(f"战斗力: {player.get_combat_power()}")
        
        next_stage_xp = get_next_stage_xp(player.stage)
        if next_stage_xp:
            progress = (player.xp / next_stage_xp) * 100
            click.echo(f"\n📊 境界进度: {progress:.1f}%")
            click.echo(f"   当前经验: {player.xp}")
            click.echo(f"   突破所需: {next_stage_xp}")


def get_next_stage_xp(stage: CultivationStage) -> int:
    requirements = {
        CultivationStage.QI: 10000,
        CultivationStage.ZHUJI: 100000,
        CultivationStage.JINDAN: 1000000,
        CultivationStage.YUANYING: 10000000,
        CultivationStage.YUANSHEN: 100000000
    }
    return requirements.get(stage, 0)


@cli.command()
@click.option('--name', prompt='角色名', help='角色名称')
@click.option('--sect', type=click.Choice(['qingyun', 'danding', 'wanhua', 'xiaoyao', 'shushan']), prompt='门派')
def play(name: str, sect: str):
    global PLAYER_ID, CURRENT_PLAYER
    
    with get_session() as session:
        player = session.query(Player).filter(Player.name == name).first()
        
        if not player:
            click.echo(f"角色 {name} 不存在，是否创建？(y/n)")
            if click.confirm('创建新角色?'):
                ctx = click.get_current_context()
                ctx.invoke(create, player_name=name, sect=sect)
                return
            else:
                return
        
        PLAYER_ID = player.player_id
        CURRENT_PLAYER = player
        
        click.echo(f"\n{'='*50}")
        click.echo(f"🎮 欢迎回来, {player.name}!")
        click.echo(f"{'='*50}")
        click.echo(f"等级: {player.level} | 境界: {player.stage.value}")
        click.echo(f"门派: {player.sect.value if player.sect else '无'}")
        click.echo(f"仙石: {player.spirit_stones}")
        click.echo(f"\n可用命令:")
        click.echo("  status    - 查看角色状态")
        click.echo("  cultivate - 打坐修炼")
        click.echo("  sect      - 查看门派信息")
        click.echo("  logout    - 退出登录")
        click.echo(f"{'='*50}\n")


if __name__ == '__main__':
    cli()
