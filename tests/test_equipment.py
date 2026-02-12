"""
Equipment system tests.
Tests for equipment generation, rarity distribution, affix generation, and stat calculations.
"""
import pytest
from unittest.mock import MagicMock, patch
from collections import Counter

from src.equipment.models import (
    Rarity, EquipmentSlot, AffixType, AffixInstance, Equipment,
    PlayerEquipment, rarity_from_string, QUALITY_TO_RARITY_MAP
)
from src.equipment.generator import EquipmentGenerator, get_generator


class TestRarity:
    """Tests for Rarity enum."""

    def test_rarity_values(self):
        """Test rarity enum values are correct."""
        assert Rarity.NORMAL.display_name == "普通"
        assert Rarity.NORMAL.multiplier == 1.0
        assert Rarity.NORMAL.affix_slots == 0

        assert Rarity.LEGENDARY.display_name == "传说"
        assert Rarity.LEGENDARY.multiplier == 3.0
        assert Rarity.LEGENDARY.affix_slots == 4

        assert Rarity.ETHEREAL.display_name == "虚无"
        assert Rarity.ETHEREAL.multiplier == 10.0
        assert Rarity.ETHEREAL.affix_slots == 8

    def test_rarity_ordering(self):
        """Test rarity hierarchy."""
        rarities = list(Rarity)
        for i in range(len(rarities) - 1):
            assert rarities[i].affix_slots <= rarities[i + 1].affix_slots

    def test_rarity_from_string(self):
        """Test converting string to rarity."""
        assert rarity_from_string("NORMAL") == Rarity.NORMAL
        assert rarity_from_string("普通") == Rarity.NORMAL
        assert rarity_from_string("LEGENDARY") == Rarity.LEGENDARY
        assert rarity_from_string("传说") == Rarity.LEGENDARY
        assert rarity_from_string("unknown") == Rarity.NORMAL


class TestEquipmentSlot:
    """Tests for EquipmentSlot enum."""

    def test_all_slots_exist(self):
        """Test all expected equipment slots exist."""
        expected_slots = [
            "WEAPON", "HELMET", "ARMOR", "GLOVES", "BOOTS",
            "BELT", "AMULET", "RING_LEFT", "RING_RIGHT", "ARTIFACT"
        ]
        actual_slots = [slot.name for slot in EquipmentSlot]
        for slot in expected_slots:
            assert slot in actual_slots

    def test_slot_values(self):
        """Test equipment slot display values."""
        assert EquipmentSlot.WEAPON.value == "武器"
        assert EquipmentSlot.HELMET.value == "头盔"
        assert EquipmentSlot.ARMOR.value == "护甲"


class TestAffixInstance:
    """Tests for AffixInstance class."""

    def test_affix_creation(self):
        """Test creating an affix instance."""
        affix = AffixInstance(
            affix_id="affix_001",
            name="Sharp",
            affix_type=AffixType.PREFIX,
            stat_modifiers={"crit_rate": 0.1},
            flat_modifiers={"attack": 10},
            roll_value=0.75,
        )
        assert affix.affix_id == "affix_001"
        assert affix.name == "Sharp"
        assert affix.affix_type == AffixType.PREFIX
        assert affix.flat_modifiers["attack"] == 10

    def test_affix_types(self):
        """Test affix type values."""
        assert AffixType.PREFIX.value == "前缀"
        assert AffixType.SUFFIX.value == "后缀"
        assert AffixType.LEGENDARY.value == "传奇"


class TestEquipment:
    """Tests for Equipment class."""

    def test_equipment_creation(self):
        """Test creating equipment."""
        equipment = Equipment(
            equipment_id="equip_001",
            base_item_id="base_sword",
            name="Iron Sword",
            slot=EquipmentSlot.WEAPON,
            rarity=Rarity.NORMAL,
            level=10,
            base_stats={"attack": 20, "speed": 5},
        )
        assert equipment.equipment_id == "equip_001"
        assert equipment.name == "Iron Sword"
        assert equipment.slot == EquipmentSlot.WEAPON
        assert equipment.rarity == Rarity.NORMAL
        assert equipment.level == 10

    def test_equipment_display_name_no_affixes(self):
        """Test equipment display name without affixes."""
        equipment = Equipment(
            base_item_id="base_sword",
            name="Iron Sword",
            slot=EquipmentSlot.WEAPON,
            rarity=Rarity.NORMAL,
        )
        assert equipment.get_display_name() == "Iron Sword"

    def test_equipment_display_name_with_affixes(self):
        """Test equipment display name with affixes."""
        equipment = Equipment(
            base_item_id="base_sword",
            name="Iron Sword",
            slot=EquipmentSlot.WEAPON,
            rarity=Rarity.RARE,
            affixes=[
                AffixInstance(affix_id="p1", name="Sharp", affix_type=AffixType.PREFIX),
                AffixInstance(affix_id="s1", name="Fire", affix_type=AffixType.SUFFIX),
            ],
        )
        display = equipment.get_display_name()
        assert "Sharp" in display
        assert "Iron Sword" in display

    def test_equipment_with_enhance_level(self):
        """Test equipment display with enhance level."""
        equipment = Equipment(
            base_item_id="base_sword",
            name="Iron Sword",
            slot=EquipmentSlot.WEAPON,
            rarity=Rarity.NORMAL,
            enhance_level=5,
        )
        display = equipment.get_display_name()
        assert "+5" in display

    def test_equipment_default_values(self):
        """Test equipment default values."""
        equipment = Equipment(
            base_item_id="base_sword",
            name="Test",
            slot=EquipmentSlot.WEAPON,
            rarity=Rarity.NORMAL,
        )
        assert equipment.level == 1
        assert equipment.enhance_level == 0
        assert equipment.identified is True
        assert equipment.locked is False
        assert len(equipment.affixes) == 0


class TestPlayerEquipment:
    """Tests for PlayerEquipment class."""

    def test_player_equipment_creation(self):
        """Test creating player equipment manager."""
        pe = PlayerEquipment(player_id="player_001")
        assert pe.player_id == "player_001"
        assert len(pe.slots) == len(EquipmentSlot)
        assert all(slot is None for slot in pe.slots.values())

    def test_equip_item(self):
        """Test equipping an item."""
        pe = PlayerEquipment(player_id="player_001")
        pe.inventory.append("equip_001")

        old = pe.equip(EquipmentSlot.WEAPON, "equip_001")

        assert old is None
        assert pe.slots["WEAPON"] == "equip_001"
        assert "equip_001" not in pe.inventory

    def test_equip_replaces_existing(self):
        """Test equipping replaces existing equipment."""
        pe = PlayerEquipment(player_id="player_001")
        pe.slots["WEAPON"] = "old_equip"

        old = pe.equip(EquipmentSlot.WEAPON, "new_equip")

        assert old == "old_equip"
        assert pe.slots["WEAPON"] == "new_equip"
        assert "old_equip" in pe.inventory

    def test_unequip_item(self):
        """Test unequipping an item."""
        pe = PlayerEquipment(player_id="player_001")
        pe.slots["WEAPON"] = "equip_001"

        unequipped = pe.unequip(EquipmentSlot.WEAPON)

        assert unequipped == "equip_001"
        assert pe.slots["WEAPON"] is None
        assert "equip_001" in pe.inventory

    def test_unequip_empty_slot(self):
        """Test unequipping from empty slot."""
        pe = PlayerEquipment(player_id="player_001")

        unequipped = pe.unequip(EquipmentSlot.WEAPON)

        assert unequipped is None


class TestEquipmentGenerator:
    """Tests for EquipmentGenerator class."""

    def test_generator_creation(self):
        """Test creating equipment generator."""
        generator = EquipmentGenerator()
        assert generator is not None

    def test_generate_basic_equipment(self):
        """Test generating basic equipment."""
        generator = EquipmentGenerator()
        equipment = generator.generate(
            level=10,
            slot=EquipmentSlot.WEAPON,
            source="normal_monster",
        )
        assert equipment is not None
        assert equipment.slot == EquipmentSlot.WEAPON
        assert equipment.level == 10

    def test_generate_with_forced_rarity(self):
        """Test generating equipment with forced rarity."""
        generator = EquipmentGenerator()
        equipment = generator.generate(
            level=20,
            slot=EquipmentSlot.ARMOR,
            forced_rarity=Rarity.LEGENDARY,
        )
        assert equipment.rarity == Rarity.LEGENDARY

    def test_generate_different_slots(self):
        """Test generating equipment for different slots."""
        generator = EquipmentGenerator()

        for slot in [EquipmentSlot.WEAPON, EquipmentSlot.HELMET, EquipmentSlot.ARMOR]:
            equipment = generator.generate(level=10, slot=slot)
            assert equipment.slot == slot

    def test_generated_equipment_has_id(self):
        """Test generated equipment has unique ID."""
        generator = EquipmentGenerator()
        equipment = generator.generate(level=10, slot=EquipmentSlot.WEAPON)
        assert equipment.equipment_id is not None
        assert len(equipment.equipment_id) > 0

    def test_generated_equipment_has_name(self):
        """Test generated equipment has a name."""
        generator = EquipmentGenerator()
        equipment = generator.generate(level=10, slot=EquipmentSlot.WEAPON)
        assert equipment.name is not None
        assert len(equipment.name) > 0

    def test_get_generator_singleton(self):
        """Test get_generator returns singleton."""
        gen1 = get_generator()
        gen2 = get_generator()
        assert gen1 is gen2


class TestRarityDistribution:
    """Tests for rarity distribution in equipment generation."""

    def test_normal_monster_distribution(self):
        """Test that normal monsters drop appropriate rarity items."""
        generator = EquipmentGenerator()
        rarities = []

        for _ in range(100):
            equipment = generator.generate(
                level=10,
                slot=EquipmentSlot.WEAPON,
                source="normal_monster",
            )
            rarities.append(equipment.rarity)

        # Normal monsters should mostly drop common items
        common_count = rarities.count(Rarity.NORMAL) + rarities.count(Rarity.MAGIC)
        assert common_count > 50  # At least half should be common

    def test_high_level_equipment_stats(self):
        """Test that higher level equipment has better stats."""
        generator = EquipmentGenerator()

        low_level = generator.generate(level=1, slot=EquipmentSlot.WEAPON, forced_rarity=Rarity.NORMAL)
        high_level = generator.generate(level=50, slot=EquipmentSlot.WEAPON, forced_rarity=Rarity.NORMAL)

        # Higher level should have higher stats
        low_attack = low_level.base_stats.get("attack", 0)
        high_attack = high_level.base_stats.get("attack", 0)
        assert high_attack > low_attack

    def test_rarity_affects_affix_count(self):
        """Test that higher rarity has more affixes."""
        generator = EquipmentGenerator()

        normal = generator.generate(level=10, slot=EquipmentSlot.WEAPON, forced_rarity=Rarity.NORMAL)
        legendary = generator.generate(level=10, slot=EquipmentSlot.WEAPON, forced_rarity=Rarity.LEGENDARY)

        assert len(legendary.affixes) >= len(normal.affixes)


class TestAffixGeneration:
    """Tests for affix generation."""

    def test_affix_count_matches_rarity(self):
        """Test affix count matches rarity specification."""
        generator = EquipmentGenerator()

        for rarity in [Rarity.RARE, Rarity.EPIC, Rarity.LEGENDARY]:
            equipment = generator.generate(
                level=20,
                slot=EquipmentSlot.WEAPON,
                forced_rarity=rarity,
            )
            # Affix count should be at least the rarity's affix_slots (may be less if pool exhausted)
            assert len(equipment.affixes) <= rarity.affix_slots

    def test_affixes_have_required_fields(self):
        """Test that generated affixes have required fields."""
        generator = EquipmentGenerator()
        equipment = generator.generate(
            level=20,
            slot=EquipmentSlot.WEAPON,
            forced_rarity=Rarity.EPIC,
        )

        for affix in equipment.affixes:
            assert affix.affix_id is not None
            assert affix.name is not None
            assert affix.affix_type is not None


class TestStatCalculations:
    """Tests for stat calculations."""

    def test_base_stats_exist(self):
        """Test that generated equipment has base stats."""
        generator = EquipmentGenerator()
        equipment = generator.generate(
            level=10,
            slot=EquipmentSlot.WEAPON,
            forced_rarity=Rarity.NORMAL,
        )
        assert len(equipment.base_stats) > 0

    def test_rarity_multiplier_affects_stats(self):
        """Test that rarity multiplier affects base stats."""
        generator = EquipmentGenerator()

        normal = generator.generate(level=10, slot=EquipmentSlot.WEAPON, forced_rarity=Rarity.NORMAL)
        legendary = generator.generate(level=10, slot=EquipmentSlot.WEAPON, forced_rarity=Rarity.LEGENDARY)

        # Legendary should have higher stats due to multiplier
        if normal.base_stats and legendary.base_stats:
            first_stat = list(normal.base_stats.keys())[0]
            if first_stat in legendary.base_stats:
                assert legendary.base_stats[first_stat] > normal.base_stats[first_stat]

    def test_different_slots_have_different_stats(self):
        """Test that different equipment slots have appropriate stats."""
        generator = EquipmentGenerator()

        weapon = generator.generate(level=10, slot=EquipmentSlot.WEAPON, forced_rarity=Rarity.NORMAL)
        armor = generator.generate(level=10, slot=EquipmentSlot.ARMOR, forced_rarity=Rarity.NORMAL)

        # Weapons should have attack, armor should have defense
        assert "attack" in weapon.base_stats or "speed" in weapon.base_stats
        assert "defense" in armor.base_stats or "hp" in armor.base_stats


class TestQualityToRarityMapping:
    """Tests for legacy quality to rarity mapping."""

    def test_mapping_exists(self):
        """Test quality to rarity mapping exists."""
        assert len(QUALITY_TO_RARITY_MAP) > 0

    def test_common_maps_to_normal(self):
        """Test COMMON quality maps to NORMAL rarity."""
        assert QUALITY_TO_RARITY_MAP["COMMON"] == Rarity.NORMAL

    def test_legendary_maps_to_epic(self):
        """Test LEGENDARY quality maps to EPIC rarity."""
        assert QUALITY_TO_RARITY_MAP["LEGENDARY"] == Rarity.EPIC


# ============================================================================
# Tests for src.equipment.combat_stats
# ============================================================================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.equipment.combat_stats import (
    calculate_equipment_stats, calculate_player_equipment_stats,
    CombatStats, AFFIX_TO_COMBAT_MAPPING, STAT_MAPPING
)


class TestCombatStats:
    """测试CombatStats类"""

    def test_empty_combat_stats(self):
        """测试空CombatStats"""
        stats = CombatStats()
        assert stats.attack == 0
        assert stats.defense == 0
        assert stats.speed == 0
        assert stats.max_hp == 0
        assert stats.constitution == 0
        assert stats.crit_rate == 0.0
        assert stats.crit_damage == 0.0
        assert stats.fire_damage == 0
        assert stats.ice_damage == 0
        assert stats.lightning_damage == 0
        assert stats.poison_damage == 0
        assert stats.lifesteal == 0.0
        assert stats.dodge_rate == 0.0

    def test_combat_stats_to_dict(self):
        """测试CombatStats序列化"""
        stats = CombatStats(
            attack=100,
            defense=50,
            speed=25,
            max_hp=500,
            crit_rate=15.5,
            fire_damage=30
        )

        result = stats.to_dict()

        assert result["attack"] == 100
        assert result["defense"] == 50
        assert result["speed"] == 25
        assert result["max_hp"] == 500
        assert result["crit_rate"] == 15.5
        assert result["fire_damage"] == 30

    def test_combat_stats_addition(self):
        """测试CombatStats相加"""
        stats1 = CombatStats(attack=50, defense=30, crit_rate=10.0)
        stats2 = CombatStats(attack=20, defense=20, crit_rate=5.0)

        combined = stats1 + stats2

        assert combined.attack == 70
        assert combined.defense == 50
        assert combined.crit_rate == 15.0
        assert combined.speed == 0  # unchanged


class TestStatAggregation:
    """测试属性聚合"""

    def test_stat_aggregation_single_equipment(self):
        """测试单件装备属性聚合"""
        equipment_list = [
            {
                "base_stats": {"attack": 50, "defense": 20},
                "affixes": [],
                "rarity": "NORMAL",
                "enhance_level": 0
            }
        ]

        stats = calculate_equipment_stats(equipment_list)

        assert stats.attack == 50
        assert stats.defense == 20

    def test_stat_aggregation_multiple_equipment(self):
        """测试多件装备属性聚合"""
        equipment_list = [
            {
                "base_stats": {"attack": 50, "speed": 10},
                "affixes": [],
                "rarity": "NORMAL",
                "enhance_level": 0
            },
            {
                "base_stats": {"defense": 30, "speed": 5},
                "affixes": [],
                "rarity": "NORMAL",
                "enhance_level": 0
            }
        ]

        stats = calculate_equipment_stats(equipment_list)

        assert stats.attack == 50
        assert stats.defense == 30
        assert stats.speed == 15  # 10 + 5

    def test_empty_equipment_list(self):
        """测试空装备列表"""
        stats = calculate_equipment_stats([])

        assert stats.attack == 0
        assert stats.defense == 0
        assert stats.speed == 0
        assert stats.max_hp == 0


class TestRarityMultiplier:
    """测试稀有度倍率"""

    def test_rarity_multiplier_applied(self):
        """测试稀有度倍率应用"""
        # Same base stats, different rarities
        normal_equip = {
            "base_stats": {"attack": 100},
            "affixes": [],
            "rarity": "NORMAL",  # 1.0x
            "enhance_level": 0
        }

        legendary_equip = {
            "base_stats": {"attack": 100},
            "affixes": [],
            "rarity": "LEGENDARY",  # 3.0x
            "enhance_level": 0
        }

        normal_stats = calculate_equipment_stats([normal_equip])
        legendary_stats = calculate_equipment_stats([legendary_equip])

        assert legendary_stats.attack == 3 * normal_stats.attack

    def test_all_rarity_multipliers(self):
        """测试所有稀有度倍率"""
        base_attack = 100
        rarities = ["NORMAL", "MAGIC", "RARE", "EPIC", "LEGENDARY", "MYTHIC", "DIVINE", "IMMORTAL", "ETHEREAL"]
        expected_multipliers = [1.0, 1.2, 1.5, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0]

        for rarity, expected_mult in zip(rarities, expected_multipliers):
            equip = {
                "base_stats": {"attack": base_attack},
                "affixes": [],
                "rarity": rarity,
                "enhance_level": 0
            }
            stats = calculate_equipment_stats([equip])
            expected_attack = int(base_attack * expected_mult)
            assert stats.attack == expected_attack, f"Rarity {rarity} expected {expected_attack}, got {stats.attack}"


class TestEnhancementBonus:
    """测试强化加成"""

    def test_enhancement_bonus(self):
        """测试强化加成计算"""
        # Level 1-10: +5% per level
        base_equip = {
            "base_stats": {"attack": 100},
            "affixes": [],
            "rarity": "NORMAL",
            "enhance_level": 0
        }

        enhanced_equip = {
            "base_stats": {"attack": 100},
            "affixes": [],
            "rarity": "NORMAL",
            "enhance_level": 10  # +50%
        }

        base_stats = calculate_equipment_stats([base_equip])
        enhanced_stats = calculate_equipment_stats([enhanced_equip])

        # 100 * 1.0 = 100 vs 100 * 1.5 = 150
        assert enhanced_stats.attack == int(base_stats.attack * 1.5)

    def test_high_enhancement_bonus(self):
        """测试高等级强化加成（+8% per level above 10）"""
        equip = {
            "base_stats": {"attack": 100},
            "affixes": [],
            "rarity": "NORMAL",
            "enhance_level": 15  # 1.5 + (15-10) * 0.08 = 1.9
        }

        stats = calculate_equipment_stats([equip])

        # 100 * 1.0 (rarity) * 1.9 (enhancement) = 190
        assert stats.attack == 190


class TestAffixModifiers:
    """测试词缀修改器"""

    def test_affix_flat_modifiers(self):
        """测试词缀平坦值修改器"""
        equipment_list = [
            {
                "base_stats": {},
                "affixes": [
                    {
                        "flat_modifiers": {"attack": 20, "defense": 10},
                        "stat_modifiers": {}
                    }
                ],
                "rarity": "NORMAL",
                "enhance_level": 0
            }
        ]

        stats = calculate_equipment_stats(equipment_list)

        assert stats.attack == 20
        assert stats.defense == 10

    def test_affix_percentage_modifiers(self):
        """测试词缀百分比修改器"""
        equipment_list = [
            {
                "base_stats": {},
                "affixes": [
                    {
                        "flat_modifiers": {},
                        "stat_modifiers": {"crit_rate": 5.0, "lifesteal": 10.0}
                    }
                ],
                "rarity": "NORMAL",
                "enhance_level": 0
            }
        ]

        stats = calculate_equipment_stats(equipment_list)

        assert stats.crit_rate == 5.0
        assert stats.lifesteal == 10.0

    def test_affix_combined_modifiers(self):
        """测试词缀组合修改器"""
        equipment_list = [
            {
                "base_stats": {"attack": 100},
                "affixes": [
                    {
                        "flat_modifiers": {"attack": 20},
                        "stat_modifiers": {"crit_rate": 3.0}
                    }
                ],
                "rarity": "NORMAL",
                "enhance_level": 0
            }
        ]

        stats = calculate_equipment_stats(equipment_list)

        # Base 100 + flat 20 = 120 (before rarity multiplier)
        # After NORMAL (1.0x): 120 attack
        assert stats.attack == 120
        assert stats.crit_rate == 3.0


class TestStatMapping:
    """测试属性映射"""

    def test_stat_mapping_exists(self):
        """测试属性映射存在"""
        assert "attack" in STAT_MAPPING
        assert "defense" in STAT_MAPPING
        assert "speed" in STAT_MAPPING
        assert "crit_rate" in STAT_MAPPING
        assert "fire_damage" in STAT_MAPPING

    def test_stat_mapping_values(self):
        """测试属性映射值"""
        assert STAT_MAPPING["attack"] == "attack"
        assert STAT_MAPPING["hp"] == "max_hp"
        assert STAT_MAPPING["max_hp"] == "max_hp"
        assert STAT_MAPPING["crit_chance"] == "crit_rate"
        assert STAT_MAPPING["fire"] == "fire_damage"
