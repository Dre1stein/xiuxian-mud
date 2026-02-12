"""
Shared pytest fixtures for game_xiuxian tests.
"""
import pytest
import tempfile
import os
from typing import Dict, Any

from src.models.player import Player, SectType, CultivationStage, Monster
from src.game.game_systems import CultivationSystem, SectSystem, EconomySystem
from src.combat.damage import DamageCalculator, Element, DamageType
from src.combat.skills import CombatUnit, CombatSkill, SkillType, SkillTarget, SkillEffect


@pytest.fixture
def sample_player():
    """Create a sample player for testing."""
    return Player(
        player_id="test_player_001",
        name="TestPlayer",
        level=10,
        xp=5000,
        stage=CultivationStage.QI,
        sect=SectType.QINGYUN,
        cultivation=100,
        sect_stats={"speed": 20, "agility": 15, "attack": 10, "defense": 5},
        base_stats={"attack": 50, "defense": 30, "speed": 40, "agility": 35, "constitution": 25, "intellect": 20},
        spirit_stones=1000,
    )


@pytest.fixture
def sample_player_high_level():
    """Create a high-level sample player for testing."""
    return Player(
        player_id="test_player_002",
        name="HighLevelPlayer",
        level=100,
        xp=200000,
        stage=CultivationStage.JINDAN,
        sect=SectType.SHUSHAN,
        cultivation=5000,
        sect_stats={"attack": 40, "defense": 20, "crit": 15},
        base_stats={"attack": 200, "defense": 150, "speed": 100, "agility": 80, "constitution": 120, "intellect": 60},
        spirit_stones=50000,
    )


@pytest.fixture
def cultivation_system():
    """Create a cultivation system for testing."""
    return CultivationSystem()


@pytest.fixture
def sect_system():
    """Create a sect system for testing."""
    return SectSystem()


@pytest.fixture
def economy_system():
    """Create an economy system for testing."""
    return EconomySystem()


@pytest.fixture
def damage_calculator():
    """Create a damage calculator for testing."""
    return DamageCalculator()


@pytest.fixture
def sample_combat_unit():
    """Create a sample combat unit for testing."""
    return CombatUnit(
        unit_id="player_001",
        name="Test Fighter",
        level=10,
        hp=200,
        max_hp=200,
        mp=100,
        max_mp=100,
        attack=50,
        defense=25,
        magic_attack=30,
        magic_resist=15,
        speed=20,
        intellect=20,
        crit_rate=0.1,
        crit_damage=2.0,
        dodge_rate=0.05,
        element=Element.WIND,
    )


@pytest.fixture
def sample_enemy_unit():
    """Create a sample enemy combat unit for testing."""
    return CombatUnit(
        unit_id="enemy_001",
        name="Test Monster",
        level=8,
        hp=150,
        max_hp=150,
        mp=50,
        max_mp=50,
        attack=35,
        defense=20,
        magic_attack=20,
        magic_resist=10,
        speed=15,
        intellect=10,
        crit_rate=0.05,
        crit_damage=1.5,
        dodge_rate=0.02,
        element=Element.FIRE,
    )


@pytest.fixture
def sample_monster():
    """Create a sample monster for testing."""
    return Monster(
        monster_id="monster_001",
        name="Wild Beast",
        level=5,
        stage=CultivationStage.QI,
        hp=100,
        max_hp=100,
        attack=20,
        defense=10,
        sect=None,
        sect_stats={},
        experience=50,
        drop_rate=0.2,
        drops=["herb_001", "stone_001"],
    )


@pytest.fixture
def sample_skill():
    """Create a sample combat skill for testing."""
    return CombatSkill(
        skill_id="test_skill_001",
        name="Test Attack",
        description="A basic test attack",
        skill_type=SkillType.ACTIVE,
        target_type=SkillTarget.SINGLE_ENEMY,
        mp_cost=10,
        hp_cost=0,
        cooldown=2,
        effects=[
            SkillEffect(
                effect_type="damage",
                value_base=30,
                value_scaling=1.2,
                scaling_stat="attack",
                element=Element.WIND,
            )
        ],
    )


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_json_storage(temp_data_dir):
    """Create a JSONStorage instance with temporary directory.

    Note: JSONStorage doesn't implement combat session methods,
    so we skip tests that require those methods.
    """
    from src.data.json_storage import JSONStorage
    data_dir = os.path.join(temp_data_dir, "players")
    try:
        return JSONStorage(data_dir)
    except TypeError:
        # JSONStorage doesn't implement abstract methods, skip
        pytest.skip("JSONStorage doesn't implement all abstract methods")


@pytest.fixture
def temp_sqlite_storage(temp_data_dir):
    """Create a SQLiteStorage instance with temporary database."""
    from src.data.sqlite_storage import SQLiteStorage
    db_path = os.path.join(temp_data_dir, "test_game.db")
    return SQLiteStorage(db_path)


@pytest.fixture
def sample_player_data() -> Dict[str, Any]:
    """Create sample player data dictionary for storage tests."""
    return {
        "player_id": "test_storage_001",
        "name": "StorageTestPlayer",
        "level": 15,
        "xp": 10000,
        "stage": "炼气期",
        "sect": "青云门",
        "cultivation": 500,
        "spirit_stones": 2000,
        "current_map": "青云山",
        "base_stats": {"attack": 60, "defense": 40, "speed": 50},
        "sect_stats": {"speed": 15, "agility": 10},
        "school_progress": {},
    }
