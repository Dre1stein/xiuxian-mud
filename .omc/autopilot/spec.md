# 暗黑风格装备系统 - 完整技术规格

## 项目概述

为修仙文字MUD游戏实现暗黑风格的装备系统，包含9级稀有度、词缀系统、套装系统、强化系统等核心功能。

---

## 一、功能需求摘要

### 核心功能
| 模块 | 描述 | 优先级 |
|------|------|--------|
| 稀有度系统 | 9级稀有度(普通→虚无)，颜色、词缀槽、属性倍率 | P0 |
| 词缀系统 | 前缀/后缀/传奇词缀，随机生成，互斥规则 | P0 |
| 装备槽位 | 10个槽位(武器/头盔/护甲/护手/战靴/腰带/项链/戒指×2/法宝) | P0 |
| 装备生成 | 基于等级/掉落源随机生成装备 | P0 |
| 属性计算 | 基础+词缀+强化+套装总属性 | P0 |
| 强化系统 | +0~+15强化，成功率递减，失败降级 | P1 |
| 套装系统 | 2/4/6件套装奖励 | P1 |
| 合成系统 | 3件同稀有度合成高阶装备 | P2 |

### 迁移需求
- 现有 `ItemQuality`(5级) → 新 `Rarity`(9级) 映射
- `Player.equipment: List[str]` → `Player.equipment_slots: Dict[str, Optional[str]]`

---

## 二、技术栈

| 组件 | 选择 | 理由 |
|------|------|------|
| Python | 3.10+ | 已有项目要求 |
| 数据模型 | Pydantic V2 | 已有依赖，支持验证和序列化 |
| 配置格式 | YAML | 人工可编辑，支持复杂结构 |
| 存储 | JSON文件 | 兼容现有架构 |

---

## 三、文件结构

```
src/equipment/
├── __init__.py           # 模块导出
├── models.py             # 核心枚举和数据类
├── generator.py          # 装备生成器
├── enhancer.py           # 强化系统
├── synthesizer.py        # 合成系统
├── calculator.py         # 属性计算器
├── validators.py         # 验证器
└── config_loader.py      # 配置加载

config/equipment/
├── rarities.yaml         # 稀有度配置
├── affixes.yaml          # 词缀池
├── sets.yaml             # 套装定义
├── drop_tables.yaml      # 掉落表
└── affix_exclusions.yaml # 词缀互斥

src/web/
└── equipment_routes.py   # Flask API路由

tests/test_equipment/
├── test_generator.py
├── test_enhancer.py
├── test_calculator.py
└── test_models.py
```

---

## 四、核心数据模型

### 4.1 枚举定义

```python
class Rarity(Enum):
    NORMAL = ("普通", "#FFFFFF", 1.0, 0)
    MAGIC = ("魔法", "#4169E1", 1.2, 1)
    RARE = ("稀有", "#FFD700", 1.5, 2)
    EPIC = ("史诗", "#A020F0", 2.0, 3)
    LEGENDARY = ("传说", "#FFA500", 3.0, 4)
    MYTHIC = ("神话", "#00CED1", 4.0, 5)
    DIVINE = ("神圣", "#FF69B4", 5.0, 6)
    IMMORTAL = ("不朽", "#FF0000", 7.0, 7)
    ETHEREAL = ("虚无", "#00FF00", 10.0, 8)

class EquipmentSlot(Enum):
    WEAPON = "武器"
    HELMET = "头盔"
    ARMOR = "护甲"
    GLOVES = "护手"
    BOOTS = "战靴"
    BELT = "腰带"
    AMULET = "项链"
    RING_LEFT = "左戒指"
    RING_RIGHT = "右戒指"
    ARTIFACT = "法宝"

class AffixType(Enum):
    PREFIX = "前缀"
    SUFFIX = "后缀"
```

### 4.2 核心类

```python
class AffixInstance(BaseModel):
    affix_id: str
    name: str
    affix_type: AffixType
    stat_modifiers: Dict[str, float]
    flat_modifiers: Dict[str, int]
    roll_value: float = 1.0

class Equipment(BaseModel):
    equipment_id: str
    base_item_id: str
    name: str
    slot: EquipmentSlot
    rarity: Rarity
    level: int = 1
    enhance_level: int = 0
    base_stats: Dict[str, int] = {}
    affixes: List[AffixInstance] = []
    set_id: Optional[str] = None
    identified: bool = True
    locked: bool = False
    created_at: datetime

class PlayerEquipment(BaseModel):
    player_id: str
    slots: Dict[EquipmentSlot, Optional[str]]
    inventory: List[str]
```

---

## 五、API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/equipment/generate` | POST | 生成随机装备 |
| `/api/equipment/<id>/enhance` | POST | 强化装备 |
| `/api/equipment/synthesize` | POST | 合成装备 |
| `/api/equipment/player/<id>/stats` | GET | 获取玩家装备总属性 |
| `/api/equipment/player/<id>/equip` | POST | 装备物品 |
| `/api/equipment/player/<id>/unequip` | POST | 卸下装备 |

---

## 六、实现阶段

### Phase 1: 核心框架 (P0)
1. 创建 `src/equipment/` 模块
2. 实现 `models.py` - 所有枚举和数据类
3. 实现 `config_loader.py` - YAML配置加载
4. 创建配置文件 `config/equipment/*.yaml`
5. 实现 `generator.py` - 装备生成器
6. 实现 `calculator.py` - 属性计算

### Phase 2: 系统集成 (P0)
1. 修改 `Player` 模型添加 `equipment_slots`
2. 实现 `equipment_routes.py` - Flask API
3. 集成到现有 Web 应用

### Phase 3: 进阶功能 (P1)
1. 实现 `enhancer.py` - 强化系统
2. 实现 `synthesizer.py` - 合成系统
3. 套装效果计算

### Phase 4: 测试与文档 (P1)
1. 单元测试
2. API文档
3. 数据迁移脚本

---

## 七、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 数据模型不兼容 | 高 | 提供迁移脚本，保留旧字段 |
| 词缀平衡性 | 中 | 配置外部化，便于调整 |
| 性能问题 | 中 | 属性计算缓存 |

---

**规格版本**: 1.0
**创建时间**: 2026-02-11
**状态**: EXPANSION_COMPLETE
