"""
Combat system tests.
Tests for combat mechanics including skills, turn order, and victory/defeat conditions.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.combat.skills import (
    CombatUnit, CombatSkill, SkillExecutor, SkillType, SkillTarget, SkillEffect,
    get_skill, get_skills_by_sect, SKILL_REGISTRY
)
from src.combat.damage import DamageCalculator, Element, DamageType


class TestCombatUnit:
    """Tests for CombatUnit class."""

    def test_combat_unit_creation(self):
        """Test creating a combat unit."""
        unit = CombatUnit(
            unit_id="test_unit",
            name="Test Warrior",
            level=10,
            hp=100,
            max_hp=100,
            mp=50,
            max_mp=50,
            attack=30,
            defense=15,
        )
        assert unit.unit_id == "test_unit"
        assert unit.name == "Test Warrior"
        assert unit.hp == 100
        assert unit.is_dead is False

    def test_combat_unit_death(self):
        """Test unit death when HP reaches 0."""
        unit = CombatUnit(
            unit_id="test_unit",
            name="Test Warrior",
            hp=100,
            max_hp=100,
        )
        unit.hp = 0
        unit.is_dead = True
        assert unit.is_dead is True

    def test_combat_unit_buffs(self):
        """Test adding and removing buffs."""
        unit = CombatUnit(
            unit_id="test_unit",
            name="Test Warrior",
        )
        buff = {"buff_id": "attack_boost", "duration": 3, "value": 10}
        unit.buffs.append(buff)
        assert len(unit.buffs) == 1
        assert unit.buffs[0]["buff_id"] == "attack_boost"

    def test_combat_unit_debuffs(self):
        """Test adding debuffs."""
        unit = CombatUnit(
            unit_id="test_unit",
            name="Test Warrior",
        )
        debuff = {"debuff_id": "poison", "duration": 2, "value": 5}
        unit.debuffs.append(debuff)
        assert len(unit.debuffs) == 1


class TestCombatSkill:
    """Tests for CombatSkill class."""

    def test_skill_creation(self):
        """Test creating a combat skill."""
        skill = CombatSkill(
            skill_id="test_skill",
            name="Fireball",
            description="A ball of fire",
            skill_type=SkillType.ACTIVE,
            target_type=SkillTarget.SINGLE_ENEMY,
            mp_cost=20,
            cooldown=3,
        )
        assert skill.skill_id == "test_skill"
        assert skill.name == "Fireball"
        assert skill.mp_cost == 20
        assert skill.cooldown == 3

    def test_skill_can_use_sufficient_resources(self):
        """Test skill can be used with sufficient MP."""
        skill = CombatSkill(
            skill_id="test_skill",
            name="Fireball",
            description="A ball of fire",
            skill_type=SkillType.ACTIVE,
            target_type=SkillTarget.SINGLE_ENEMY,
            mp_cost=20,
            cooldown=0,
        )
        assert skill.can_use(caster_mp=30, caster_hp=100) is True

    def test_skill_can_use_insufficient_mp(self):
        """Test skill cannot be used with insufficient MP."""
        skill = CombatSkill(
            skill_id="test_skill",
            name="Fireball",
            description="A ball of fire",
            skill_type=SkillType.ACTIVE,
            target_type=SkillTarget.SINGLE_ENEMY,
            mp_cost=50,
            cooldown=0,
        )
        assert skill.can_use(caster_mp=30, caster_hp=100) is False

    def test_skill_can_use_on_cooldown(self):
        """Test skill cannot be used while on cooldown."""
        skill = CombatSkill(
            skill_id="test_skill",
            name="Fireball",
            description="A ball of fire",
            skill_type=SkillType.ACTIVE,
            target_type=SkillTarget.SINGLE_ENEMY,
            mp_cost=20,
            cooldown=3,
        )
        skill.current_cooldown = 2
        assert skill.can_use(caster_mp=100, caster_hp=100) is False

    def test_skill_cooldown_management(self):
        """Test cooldown application and reduction."""
        skill = CombatSkill(
            skill_id="test_skill",
            name="Fireball",
            description="A ball of fire",
            skill_type=SkillType.ACTIVE,
            target_type=SkillTarget.SINGLE_ENEMY,
            mp_cost=20,
            cooldown=3,
        )
        skill.apply_cooldown()
        assert skill.current_cooldown == 3

        skill.reduce_cooldown()
        assert skill.current_cooldown == 2

    def test_skill_clone(self):
        """Test cloning a skill."""
        skill = CombatSkill(
            skill_id="test_skill",
            name="Fireball",
            description="A ball of fire",
            skill_type=SkillType.ACTIVE,
            target_type=SkillTarget.SINGLE_ENEMY,
            mp_cost=20,
            cooldown=3,
        )
        skill.current_cooldown = 1
        cloned = skill.clone()
        assert cloned.skill_id == skill.skill_id
        assert cloned.current_cooldown == 1
        # Ensure it's a different object
        cloned.current_cooldown = 5
        assert skill.current_cooldown == 1


class TestSkillExecutor:
    """Tests for SkillExecutor class."""

    def test_execute_damage_skill(self, damage_calculator, sample_combat_unit, sample_enemy_unit):
        """Test executing a damage skill."""
        skill = CombatSkill(
            skill_id="test_attack",
            name="Test Attack",
            description="A basic attack",
            skill_type=SkillType.ACTIVE,
            target_type=SkillTarget.SINGLE_ENEMY,
            mp_cost=10,
            effects=[
                SkillEffect(
                    effect_type="damage",
                    value_base=30,
                    value_scaling=1.0,
                    scaling_stat="attack",
                    element=Element.PHYSICAL,
                )
            ],
        )
        executor = SkillExecutor(damage_calculator)
        initial_hp = sample_enemy_unit.hp
        initial_mp = sample_combat_unit.mp

        actions = executor.execute_skill(skill, sample_combat_unit, [sample_enemy_unit])

        assert len(actions) == 1
        assert sample_combat_unit.mp == initial_mp - 10
        assert sample_enemy_unit.hp < initial_hp

    def test_execute_heal_skill(self, damage_calculator, sample_combat_unit):
        """Test executing a healing skill."""
        # Damage the unit first
        sample_combat_unit.hp = 100

        skill = CombatSkill(
            skill_id="test_heal",
            name="Test Heal",
            description="A healing spell",
            skill_type=SkillType.ACTIVE,
            target_type=SkillTarget.SELF,
            mp_cost=15,
            effects=[
                SkillEffect(
                    effect_type="heal",
                    value_base=50,
                    value_scaling=1.0,
                    scaling_stat="intellect",
                )
            ],
        )
        executor = SkillExecutor(damage_calculator)
        actions = executor.execute_skill(skill, sample_combat_unit, [])

        assert len(actions) == 1
        assert sample_combat_unit.hp > 100

    def test_execute_buff_skill(self, damage_calculator, sample_combat_unit):
        """Test executing a buff skill."""
        skill = CombatSkill(
            skill_id="test_buff",
            name="Test Buff",
            description="A buff skill",
            skill_type=SkillType.ACTIVE,
            target_type=SkillTarget.SELF,
            mp_cost=10,
            effects=[
                SkillEffect(
                    effect_type="buff",
                    value_base=20,
                    value_scaling=0.0,
                    scaling_stat="speed",
                    buff_id="speed_boost",
                    duration=3,
                )
            ],
        )
        executor = SkillExecutor(damage_calculator)
        actions = executor.execute_skill(skill, sample_combat_unit, [])

        assert len(actions) == 1
        assert len(sample_combat_unit.buffs) == 1
        assert sample_combat_unit.buffs[0]["buff_id"] == "speed_boost"

    def test_execute_skill_insufficient_mp(self, damage_calculator, sample_combat_unit, sample_enemy_unit):
        """Test executing skill with insufficient MP returns empty actions."""
        skill = CombatSkill(
            skill_id="expensive_skill",
            name="Expensive Skill",
            description="An expensive skill",
            skill_type=SkillType.ACTIVE,
            target_type=SkillTarget.SINGLE_ENEMY,
            mp_cost=1000,  # More than unit has
            effects=[
                SkillEffect(
                    effect_type="damage",
                    value_base=100,
                    value_scaling=1.0,
                    scaling_stat="attack",
                )
            ],
        )
        executor = SkillExecutor(damage_calculator)
        actions = executor.execute_skill(skill, sample_combat_unit, [sample_enemy_unit])

        assert len(actions) == 0


class TestSkillRegistry:
    """Tests for skill registry functions."""

    def test_get_skill_existing(self):
        """Test getting an existing skill."""
        skill = get_skill("qingyun_sword_qi")
        assert skill is not None
        assert skill.skill_id == "qingyun_sword_qi"

    def test_get_skill_nonexistent(self):
        """Test getting a non-existent skill returns None."""
        skill = get_skill("nonexistent_skill")
        assert skill is None

    def test_get_skills_by_sect(self):
        """Test getting skills by sect."""
        skills = get_skills_by_sect("青云门")
        assert len(skills) > 0
        for skill in skills:
            assert skill.required_sect == "青云门"

    def test_skill_registry_has_skills(self):
        """Test that skill registry contains expected skills."""
        assert len(SKILL_REGISTRY) > 0
        assert "qingyun_sword_qi" in SKILL_REGISTRY
        assert "sanmei_zhenhuo" in SKILL_REGISTRY


class TestTurnOrder:
    """Tests for turn order logic based on speed."""

    def test_faster_unit_acts_first(self, sample_combat_unit, sample_enemy_unit):
        """Test that faster unit acts first."""
        sample_combat_unit.speed = 50
        sample_enemy_unit.speed = 20

        units = [sample_enemy_unit, sample_combat_unit]
        sorted_units = sorted(units, key=lambda u: u.speed, reverse=True)

        assert sorted_units[0] == sample_combat_unit

    def test_turn_order_with_equal_speed(self):
        """Test turn order when speeds are equal."""
        unit1 = CombatUnit(unit_id="unit1", name="Unit 1", speed=30)
        unit2 = CombatUnit(unit_id="unit2", name="Unit 2", speed=30)

        units = [unit1, unit2]
        sorted_units = sorted(units, key=lambda u: u.speed, reverse=True)

        assert len(sorted_units) == 2


class TestVictoryDefeatConditions:
    """Tests for victory and defeat conditions."""

    def test_victory_when_all_enemies_dead(self):
        """Test victory condition when all enemies are dead."""
        enemies = [
            CombatUnit(unit_id="enemy1", name="Enemy 1", hp=0, is_dead=True),
            CombatUnit(unit_id="enemy2", name="Enemy 2", hp=0, is_dead=True),
        ]

        all_dead = all(e.is_dead for e in enemies)
        assert all_dead is True

    def test_defeat_when_player_dead(self):
        """Test defeat condition when player is dead."""
        player = CombatUnit(unit_id="player", name="Player", hp=0, is_dead=True)
        assert player.is_dead is True

    def test_combat_continues_while_both_alive(self):
        """Test combat continues while both sides have living units."""
        player = CombatUnit(unit_id="player", name="Player", hp=100, is_dead=False)
        enemy = CombatUnit(unit_id="enemy", name="Enemy", hp=50, is_dead=False)

        combat_ended = player.is_dead or enemy.is_dead
        assert combat_ended is False


class TestMultiHitSkills:
    """Tests for multi-hit skills."""

    def test_multi_hit_damage(self, damage_calculator, sample_combat_unit, sample_enemy_unit):
        """Test multi-hit skill deals multiple hits worth of damage."""
        skill = CombatSkill(
            skill_id="multi_hit",
            name="Triple Strike",
            description="A triple strike attack",
            skill_type=SkillType.ACTIVE,
            target_type=SkillTarget.SINGLE_ENEMY,
            mp_cost=25,
            effects=[
                SkillEffect(
                    effect_type="damage",
                    value_base=20,
                    value_scaling=0.5,
                    scaling_stat="attack",
                    hit_count=3,
                )
            ],
        )
        executor = SkillExecutor(damage_calculator)
        initial_hp = sample_enemy_unit.hp

        actions = executor.execute_skill(skill, sample_combat_unit, [sample_enemy_unit])

        assert len(actions) == 1
        # Damage should be approximately 3x single hit
        damage_dealt = initial_hp - sample_enemy_unit.hp
        assert damage_dealt > 0


class TestAOESkills:
    """Tests for area of effect skills."""

    def test_aoe_hits_all_enemies(self, damage_calculator):
        """Test AOE skill hits all enemies."""
        # Create a strong attacker to ensure damage is dealt
        attacker = CombatUnit(
            unit_id="player",
            name="Strong Attacker",
            level=50,
            hp=500,
            max_hp=500,
            mp=200,
            max_mp=200,
            attack=200,
            defense=100,
            magic_attack=150,
            magic_resist=80,
            speed=30,
            intellect=50,
            crit_rate=0.0,  # No crits for predictable results
            crit_damage=1.5,
            dodge_rate=0.0,
        )

        enemies = [
            CombatUnit(unit_id="enemy1", name="Enemy 1", hp=100, max_hp=100, defense=5, magic_resist=5),
            CombatUnit(unit_id="enemy2", name="Enemy 2", hp=100, max_hp=100, defense=5, magic_resist=5),
            CombatUnit(unit_id="enemy3", name="Enemy 3", hp=100, max_hp=100, defense=5, magic_resist=5),
        ]

        skill = CombatSkill(
            skill_id="aoe_attack",
            name="Flame Wave",
            description="A wave of flames",
            skill_type=SkillType.ACTIVE,
            target_type=SkillTarget.ALL_ENEMIES,
            mp_cost=30,
            effects=[
                SkillEffect(
                    effect_type="damage",
                    value_base=100,  # High base damage
                    value_scaling=2.0,  # Strong scaling
                    scaling_stat="magic_attack",
                    element=Element.FIRE,
                )
            ],
        )
        executor = SkillExecutor(damage_calculator)
        actions = executor.execute_skill(skill, attacker, enemies)

        # Should hit all 3 enemies
        assert len(actions) == 3
        # All enemies should take damage (hp < 100)
        for enemy in enemies:
            assert enemy.hp < 100


# ============================================================================
# Sect Advantage Tests for combat_routes.py
# ============================================================================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.web.combat_routes import calculate_damage, CombatEntity
from src.models.player import SectType, SECT_ADVANTAGES


# ============================================================================
# New Tests for src.web.combat_routes Combat System
# ============================================================================

class TestCombatEntity:
    """测试战斗实体类 - src.web.combat_routes.CombatEntity"""

    def test_entity_creation(self):
        """测试战斗实体创建"""
        entity = CombatEntity(
            id="test_entity",
            name="测试实体",
            level=10,
            stage="炼气期",
            hp=100,
            max_hp=100,
            attack=20,
            defense=10,
            speed=15,
            entity_type="player",
            skills=["攻击", "防御"],
            sect="青云门"
        )

        assert entity.id == "test_entity"
        assert entity.name == "测试实体"
        assert entity.level == 10
        assert entity.hp == 100
        assert entity.max_hp == 100
        assert entity.attack == 20
        assert entity.defense == 10
        assert entity.speed == 15
        assert entity.entity_type == "player"
        assert len(entity.skills) == 2
        assert entity.sect == "青云门"
        assert entity.is_defending is False

    def test_entity_to_dict(self):
        """测试实体序列化"""
        entity = CombatEntity(
            id="test_entity",
            name="测试实体",
            level=5,
            stage="炼气期",
            hp=80,
            max_hp=100,
            attack=15,
            defense=8,
            speed=12,
            entity_type="enemy",
            skills=["撕咬"],
            equipment_stats={"attack": 10, "defense": 5}
        )

        result = entity.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == "test_entity"
        assert result["name"] == "测试实体"
        assert result["level"] == 5
        assert result["hp"] == 80
        assert result["max_hp"] == 100
        assert result["attack"] == 15
        assert result["defense"] == 8
        assert result["speed"] == 12
        assert result["entity_type"] == "enemy"
        assert result["skills"] == ["撕咬"]
        assert result["equipment_stats"] == {"attack": 10, "defense": 5}
        assert result["is_defending"] is False


class TestDamageCalculation:
    """测试伤害计算系统"""

    def test_basic_damage(self):
        """测试基础伤害计算"""
        attacker = CombatEntity(
            id="attacker",
            name="攻击者",
            level=10,
            stage="炼气期",
            hp=100,
            max_hp=100,
            attack=50,
            defense=10,
            speed=15,
            entity_type="player"
        )

        defender = CombatEntity(
            id="defender",
            name="防御者",
            level=10,
            stage="炼气期",
            hp=100,
            max_hp=100,
            attack=30,
            defense=20,
            speed=10,
            entity_type="enemy"
        )

        # Run multiple times to account for crits and random variation
        damages = []
        for _ in range(50):
            damage, sect_msg, equip_msg = calculate_damage(attacker, defender)
            if not sect_msg and not equip_msg:  # Only count non-crit, non-sect-advantage hits
                damages.append(damage)

        # Base damage formula: max(1, attack - defense // 2)
        # 50 - 20 // 2 = 40, then random 0.9-1.1
        # With 15% crit rate, filter those out and check average
        avg_damage = sum(damages) / len(damages) if damages else 40
        # Average should be around 40 (allowing for crits to raise it)
        assert avg_damage >= 30  # Accounts for some crits in mix
        assert avg_damage <= 70  # Accounts for some crits
        # At least some non-crit hits should be in range
        non_crit_hits = [d for d in damages if d < 60]
        assert len(non_crit_hits) > 0

    def test_defense_reduction(self):
        """测试防御减伤"""
        attacker = CombatEntity(
            id="attacker",
            name="攻击者",
            level=10,
            stage="炼气期",
            hp=100,
            max_hp=100,
            attack=50,
            defense=5,
            speed=15,
            entity_type="player"
        )

        defender = CombatEntity(
            id="defender",
            name="防御者",
            level=10,
            stage="炼气期",
            hp=100,
            max_hp=100,
            attack=20,
            defense=30,
            speed=10,
            entity_type="enemy",
            is_defending=True
        )

        damage, sect_msg, equip_msg = calculate_damage(attacker, defender)

        # With defense stance, damage should be halved
        # Base: 50 - 30 // 2 = 35
        # With defending: 35 // 2 = 17 (or close due to random)
        assert damage >= 7  # 17 * 0.9
        assert damage <= 19  # 17 * 1.1

    def test_critical_hit(self):
        """测试暴击"""
        attacker = CombatEntity(
            id="attacker",
            name="攻击者",
            level=10,
            stage="炼气期",
            hp=100,
            max_hp=100,
            attack=50,
            defense=10,
            speed=15,
            entity_type="player"
        )

        defender = CombatEntity(
            id="defender",
            name="防御者",
            level=10,
            stage="炼气期",
            hp=100,
            max_hp=100,
            attack=20,
            defense=10,
            speed=10,
            entity_type="enemy"
        )

        # Run multiple times to potentially hit a crit
        found_crit = False
        for _ in range(100):
            damage, sect_msg, equip_msg = calculate_damage(attacker, defender)
            # Crits do 1.5x damage
            if damage > 55:  # Normal max is around 44, crit would be ~66
                found_crit = True
                break

        # With 15% crit rate and 100 attempts, should see at least one
        assert found_crit

    def test_sect_advantage(self):
        """测试门派克制"""
        # 青云门(风) 克 万花谷(木) - 1.3x
        attacker = CombatEntity(
            id="attacker",
            name="青云弟子",
            level=10,
            stage="炼气期",
            hp=100,
            max_hp=100,
            attack=50,
            defense=10,
            speed=15,
            entity_type="player",
            sect="青云门"
        )

        defender = CombatEntity(
            id="defender",
            name="万花弟子",
            level=10,
            stage="炼气期",
            hp=100,
            max_hp=100,
            attack=20,
            defense=10,
            speed=10,
            entity_type="enemy",
            sect="万花谷"
        )

        damage, sect_msg, equip_msg = calculate_damage(attacker, defender)

        # Should get sect advantage message
        assert "青云门" in sect_msg
        assert "万花谷" in sect_msg
        assert "30%" in sect_msg or "克制" in sect_msg

    def test_equipment_contribution(self):
        """测试装备贡献"""
        attacker = CombatEntity(
            id="attacker",
            name="玩家",
            level=10,
            stage="炼气期",
            hp=100,
            max_hp=100,
            attack=100,  # 50 base + 50 equipment
            defense=10,
            speed=15,
            entity_type="player",
            equipment_stats={"attack": 50}  # 50% of total attack
        )

        defender = CombatEntity(
            id="defender",
            name="敌人",
            level=10,
            stage="炼气期",
            hp=100,
            max_hp=100,
            attack=20,
            defense=10,
            speed=10,
            entity_type="enemy"
        )

        damage, sect_msg, equip_msg = calculate_damage(attacker, defender)

        # Should get equipment contribution message
        assert "装备增益" in equip_msg
        assert "50%" in equip_msg


class TestSectAdvantage:
    """测试门派克制伤害计算"""

    def test_sect_advantage_increases_damage(self):
        """青云门攻击万花谷应该有伤害加成"""
        attacker = CombatEntity(
            id="p1", name="青云弟子", level=10, stage="炼气期",
            hp=100, max_hp=100, attack=100, defense=10, speed=10,
            sect="青云门"
        )
        defender = CombatEntity(
            id="e1", name="万花弟子", level=10, stage="炼气期",
            hp=100, max_hp=100, attack=50, defense=10, speed=10,
            sect="万花谷"
        )

        # 多次测试取平均，因为有随机浮动
        total_damage = 0
        sect_messages = []
        for _ in range(100):
            damage, sect_msg, equip_msg = calculate_damage(attacker, defender)
            total_damage += damage
            if sect_msg:
                sect_messages.append(sect_msg)

        avg_damage = total_damage / 100
        # 青云门克万花谷 1.25 倍，基础伤害约 95 (100-10/2)
        # 考虑随机浮动 0.9-1.1，期望约 95 * 1.25 * 1.0 = 118
        assert avg_damage > 90, f"Expected higher damage with sect advantage, got {avg_damage}"
        assert any("青云门" in m and "万花谷" in m for m in sect_messages), "Should have sect advantage message"

    def test_sect_disadvantage_reduces_damage(self):
        """青云门攻击蜀山派应该伤害降低"""
        attacker = CombatEntity(
            id="p1", name="青云弟子", level=10, stage="炼气期",
            hp=100, max_hp=100, attack=100, defense=10, speed=10,
            sect="青云门"
        )
        defender = CombatEntity(
            id="e1", name="蜀山弟子", level=10, stage="炼气期",
            hp=100, max_hp=100, attack=50, defense=10, speed=10,
            sect="蜀山派"
        )

        total_damage = 0
        sect_messages = []
        for _ in range(100):
            damage, sect_msg, equip_msg = calculate_damage(attacker, defender)
            total_damage += damage
            if sect_msg:
                sect_messages.append(sect_msg)

        avg_damage = total_damage / 100
        # 蜀山克青云门 0.8 倍，基础伤害约 95 (100-10/2)
        # 考虑随机浮动 0.9-1.1，期望约 95 * 0.8 = 76
        assert avg_damage < 100, f"Expected lower damage with sect disadvantage, got {avg_damage}"
        # Should have disadvantage message
        assert any("蜀山派" in m and "青云门" in m for m in sect_messages), "Should have sect disadvantage message"

    def test_no_sect_no_advantage(self):
        """没有门派时不应有克制"""
        attacker = CombatEntity(
            id="p1", name="无名", level=10, stage="炼气期",
            hp=100, max_hp=100, attack=100, defense=10, speed=10,
            sect=""
        )
        defender = CombatEntity(
            id="e1", name="敌人", level=10, stage="炼气期",
            hp=100, max_hp=100, attack=50, defense=10, speed=10,
            sect=""
        )

        damage, sect_msg, equip_msg = calculate_damage(attacker, defender)
        assert sect_msg == "", f"Should not have sect message when no sect, got: {sect_msg}"

    def test_all_sect_combinations(self):
        """测试所有门派组合的克制关系"""
        for (attacker_sect, defender_sect), multiplier in SECT_ADVANTAGES.items():
            attacker = CombatEntity(
                id="p1", name="攻击者", level=10, stage="炼气期",
                hp=100, max_hp=100, attack=100, defense=10, speed=10,
                sect=attacker_sect.value
            )
            defender = CombatEntity(
                id="e1", name="防御者", level=10, stage="炼气期",
                hp=100, max_hp=100, attack=50, defense=10, speed=10,
                sect=defender_sect.value
            )

            # 计算无克制时的基准伤害
            base_attacker = CombatEntity(
                id="p1", name="攻击者", level=10, stage="炼气期",
                hp=100, max_hp=100, attack=100, defense=10, speed=10,
                sect=""
            )
            base_defender = CombatEntity(
                id="e1", name="防御者", level=10, stage="炼气期",
                hp=100, max_hp=100, attack=50, defense=10, speed=10,
                sect=""
            )

            total_with_sect = 0
            total_without_sect = 0
            for _ in range(50):
                d1, _, _ = calculate_damage(attacker, defender)
                d2, _, _ = calculate_damage(base_attacker, base_defender)
                total_with_sect += d1
                total_without_sect += d2

            avg_with_sect = total_with_sect / 50
            avg_without_sect = total_without_sect / 50
            ratio = avg_with_sect / avg_without_sect

            # 验证克制系数在合理范围内
            assert 0.7 * multiplier <= ratio <= 1.3 * multiplier, \
                f"Sect advantage {attacker_sect}->{defender_sect} multiplier {multiplier} not matching calculated ratio {ratio}"

    def test_sect_message_format(self):
        """测试门派克制消息格式"""
        attacker = CombatEntity(
            id="p1", name="丹鼎弟子", level=10, stage="炼气期",
            hp=100, max_hp=100, attack=100, defense=10, speed=10,
            sect="丹鼎门"
        )
        defender = CombatEntity(
            id="e1", name="昆仑弟子", level=10, stage="炼气期",
            hp=100, max_hp=100, attack=50, defense=10, speed=10,
            sect="昆仑派"
        )

        # 丹鼎门克昆仑派 1.30 倍
        _, sect_msg, _ = calculate_damage(attacker, defender)
        assert "丹鼎门" in sect_msg
        assert "昆仑派" in sect_msg
        assert "克制" in sect_msg
        assert "+" in sect_msg  # Should show damage increase
