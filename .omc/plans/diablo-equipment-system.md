# 暗黑风格装备系统 - 实现计划

**创建时间**: 2026-02-11
**状态**: DRAFT
**基于**: `.omc/autopilot/spec.md`

---

## 一、计划概述

### 目标
为修仙文字MUD游戏实现暗黑风格的装备系统，包含9级稀有度、词缀系统、套装系统、强化系统等核心功能。

### 范围
- **包含**: P0 核心功能（稀有度、词缀、装备槽位、生成、属性计算）+ P1 强化/套装
- **不包含**: P2 合成系统（后续迭代）

### 工作量估计
- **新增文件**: 13 个
- **修改文件**: 3 个
- **总任务数**: 16 个
- **复杂度**: MEDIUM-HIGH

---

## 二、阶段划分

```
阶段1: 基础设施 (配置、模型)     → T1-T5
阶段2: 核心逻辑 (生成器、计算器) → T6-T9
阶段3: 系统集成 (API、Player)   → T10-T13
阶段4: 测试验证                 → T14-T16
```

---

## 三、详细任务列表

### 阶段1: 基础设施

#### T1: 创建稀有度配置文件
- **任务ID**: T1
- **优先级**: P0
- **目标文件**: `config/equipment/rarities.yaml`
- **依赖**: 无
- **实现步骤**:
  1. 创建目录 `config/equipment/`
  2. 定义9级稀有度配置（名称、颜色、属性倍率、词缀槽数量）
  3. 添加掉落权重配置
- **验收标准**:
  - [ ] 9个稀有度级别完整定义
  - [ ] 每个稀有度包含：name, color, stat_multiplier, affix_slots, drop_weight
  - [ ] YAML格式正确，可通过 PyYAML 加载

**配置内容示例**:
```yaml
rarities:
  NORMAL:
    name: "普通"
    color: "#FFFFFF"
    stat_multiplier: 1.0
    affix_slots: 0
    drop_weight: 1000
  MAGIC:
    name: "魔法"
    color: "#4169E1"
    stat_multiplier: 1.2
    affix_slots: 1
    drop_weight: 500
  # ... 一直到 ETHEREAL
```

---

#### T2: 创建词缀池配置文件
- **任务ID**: T2
- **优先级**: P0
- **目标文件**: `config/equipment/affixes.yaml`
- **依赖**: 无
- **实现步骤**:
  1. 定义前缀词缀池（攻击向）
  2. 定义后缀词缀池（防御/辅助向）
  3. 定义传奇词缀池（特殊效果）
  4. 为每个词缀设置：ID、名称、属性范围、权重
- **验收标准**:
  - [ ] 至少10个前缀词缀
  - [ ] 至少10个后缀词缀
  - [ ] 至少5个传奇词缀
  - [ ] 每个词缀包含：id, name, type, stats(min/max), weight

**词缀示例**:
```yaml
prefixes:
  - id: "sharp"
    name: "锋利的"
    type: "PREFIX"
    stats:
      attack: { min: 5, max: 20 }
    weight: 100
    allowed_slots: ["WEAPON"]

suffixes:
  - id: "of_strength"
    name: "力量之"
    type: "SUFFIX"
    stats:
      constitution: { min: 3, max: 15 }
    weight: 100
    allowed_slots: ["*"]  # 所有槽位
```

---

#### T3: 创建套装和掉落表配置
- **任务ID**: T3
- **优先级**: P0
- **目标文件**:
  - `config/equipment/sets.yaml`
  - `config/equipment/drop_tables.yaml`
  - `config/equipment/affix_exclusions.yaml`
- **依赖**: 无
- **实现步骤**:
  1. 定义套装配置（2/4/6件奖励）
  2. 定义掉落表（按等级/怪物类型）
  3. 定义词缀互斥规则
- **验收标准**:
  - [ ] 至少3套套装定义
  - [ ] 掉落表按等级分层（1-10, 11-20, 21-30...）
  - [ ] 词缀互斥规则完整

---

#### T4: 实现核心数据模型
- **任务ID**: T4
- **优先级**: P0
- **目标文件**: `src/equipment/models.py`
- **依赖**: 无
- **实现步骤**:
  1. 定义 `Rarity` 枚举（9级）
  2. 定义 `EquipmentSlot` 枚举（10槽位）
  3. 定义 `AffixType` 枚举（前缀/后缀）
  4. 实现 `AffixInstance` Pydantic 模型
  5. 实现 `Equipment` Pydantic 模型
  6. 实现 `PlayerEquipment` Pydantic 模型
  7. 实现 `SetBonus` Pydantic 模型
- **验收标准**:
  - [ ] 所有枚举定义完整
  - [ ] Pydantic V2 模型支持序列化/反序列化
  - [ ] 包含必要的验证器
  - [ ] 添加 `__init__.py` 导出

**关键模型**:
```python
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
```

---

#### T5: 实现配置加载器
- **任务ID**: T5
- **优先级**: P0
- **目标文件**: `src/equipment/config_loader.py`
- **依赖**: T1, T2, T3
- **实现步骤**:
  1. 实现 `EquipmentConfig` 类
  2. 加载所有 YAML 配置文件
  3. 提供配置缓存机制
  4. 实现配置热重载支持
- **验收标准**:
  - [ ] 成功加载所有配置文件
  - [ ] 提供便捷的查询方法（如 get_rarity, get_affix）
  - [ ] 配置加载失败时抛出明确异常

---

### 阶段2: 核心逻辑

#### T6: 实现装备生成器
- **任务ID**: T6
- **优先级**: P0
- **目标文件**: `src/equipment/generator.py`
- **依赖**: T4, T5
- **实现步骤**:
  1. 实现 `EquipmentGenerator` 类
  2. 实现稀有度随机选择（基于权重）
  3. 实现词缀随机生成（基于槽位限制）
  4. 实现词缀值随机滚动
  5. 实现基础属性生成（基于稀有度倍率）
  6. 实现套装关联
- **验收标准**:
  - [ ] `generate(level, slot, source)` 方法可用
  - [ ] 词缀互斥规则生效
  - [ ] 生成的装备符合配置的概率分布
  - [ ] 支持指定稀有度生成

**核心方法签名**:
```python
class EquipmentGenerator:
    def generate(
        self,
        level: int,
        slot: EquipmentSlot,
        source: str = "monster",
        forced_rarity: Optional[Rarity] = None
    ) -> Equipment:
        ...
```

---

#### T7: 实现属性计算器
- **任务ID**: T7
- **优先级**: P0
- **目标文件**: `src/equipment/calculator.py`
- **依赖**: T4
- **实现步骤**:
  1. 实现 `EquipmentCalculator` 类
  2. 计算单件装备总属性 = 基础 + 词缀 + 强化
  3. 计算玩家装备总属性（遍历所有槽位）
  4. 实现套装效果计算（2/4/6件）
  5. 实现属性缓存机制
- **验收标准**:
  - [ ] `calculate_equipment_stats(equipment)` 返回属性字典
  - [ ] `calculate_player_total_stats(player_id)` 返回总属性
  - [ ] 套装效果正确叠加
  - [ ] 强化加成正确计算

---

#### T8: 实现强化系统 (P1)
- **任务ID**: T8
- **优先级**: P1
- **目标文件**: `src/equipment/enhancer.py`
- **依赖**: T4
- **实现步骤**:
  1. 实现强化成功率表（+0~+15）
  2. 实现 `EquipmentEnhancer` 类
  3. 实现 `enhance(equipment)` 方法
  4. 实现失败降级逻辑
  5. 实现强化保护道具支持
- **验收标准**:
  - [ ] 成功率随强化等级递减
  - [ ] 失败时等级-1（可配置）
  - [ ] 返回强化结果（成功/失败/新等级）
  - [ ] 支持锁定保护

**成功率表示例**:
```python
ENHANCE_SUCCESS_RATE = {
    0: 1.0,   # +0 → +1: 100%
    1: 0.9,   # +1 → +2: 90%
    2: 0.8,
    # ...
    14: 0.1,  # +14 → +15: 10%
}
```

---

#### T9: 实现验证器
- **任务ID**: T9
- **优先级**: P0
- **目标文件**: `src/equipment/validators.py`
- **依赖**: T4
- **实现步骤**:
  1. 实现装备槽位验证
  2. 实现词缀数量验证
  3. 实现稀有度-词缀槽位匹配验证
  4. 实现套装完整性验证
- **验收标准**:
  - [ ] `validate_equipment(equipment)` 返回验证结果
  - [ ] `validate_affix_compatibility(affixes)` 检查互斥
  - [ ] 异常信息清晰明确

---

### 阶段3: 系统集成

#### T10: 创建模块初始化文件
- **任务ID**: T10
- **优先级**: P0
- **目标文件**: `src/equipment/__init__.py`
- **依赖**: T4-T9
- **实现步骤**:
  1. 导出所有公共类和函数
  2. 定义模块版本
  3. 添加便捷工厂函数
- **验收标准**:
  - [ ] `from src.equipment import Equipment, EquipmentGenerator, ...` 可用
  - [ ] 模块文档字符串完整

---

#### T11: 修改 Player 模型
- **任务ID**: T11
- **优先级**: P0
- **目标文件**: `src/models/player.py`
- **依赖**: T4
- **实现步骤**:
  1. 添加 `equipment_slots: Dict[str, Optional[str]]` 字段
  2. 保留 `equipment: List[str]` 用于向后兼容
  3. 添加 `inventory: List[str]` 字段（装备背包）
  4. 添加 `equip(item_id)` 方法
  5. 添加 `unequip(slot)` 方法
  6. 实现数据迁移逻辑
- **验收标准**:
  - [ ] 新字段在数据库中正确存储
  - [ ] 旧数据可以正确迁移
  - [ ] 装备/卸载方法工作正常

**Player 模型修改**:
```python
# 添加到 Player 类
equipment_slots: Dict[str, Optional[str]] = field(
    default_factory=lambda: {slot: None for slot in EquipmentSlot}
)
inventory: List[str] = field(default_factory=list)
```

---

#### T12: 实现装备 API 路由
- **任务ID**: T12
- **优先级**: P0
- **目标文件**: `src/web/equipment_routes.py`
- **依赖**: T6, T7, T10
- **实现步骤**:
  1. 创建 Flask Blueprint
  2. 实现 `POST /api/equipment/generate` - 生成装备
  3. 实现 `POST /api/equipment/<id>/enhance` - 强化装备
  4. 实现 `GET /api/equipment/player/<id>/stats` - 获取玩家装备属性
  5. 实现 `POST /api/equipment/player/<id>/equip` - 装备物品
  6. 实现 `POST /api/equipment/player/<id>/unequip` - 卸下装备
  7. 实现 `GET /api/equipment/player/<id>/inventory` - 获取背包
- **验收标准**:
  - [ ] 所有端点返回正确的 JSON 格式
  - [ ] 错误处理完善
  - [ ] API 文档字符串完整

**API 端点设计**:
```
POST /api/equipment/generate
  Body: { "level": 10, "slot": "WEAPON", "source": "monster" }
  Response: { "equipment": {...} }

POST /api/equipment/player/<id>/equip
  Body: { "equipment_id": "eq_123" }
  Response: { "success": true, "slot": "WEAPON" }
```

---

#### T13: 集成到主应用
- **任务ID**: T13
- **优先级**: P0
- **目标文件**: `src/web/app.py`
- **依赖**: T12
- **实现步骤**:
  1. 导入 equipment_routes Blueprint
  2. 注册到 Flask app
  3. 更新 API 状态端点
  4. 添加装备系统初始化逻辑
- **验收标准**:
  - [ ] 装备 API 可通过主应用访问
  - [ ] `/api/status` 显示装备端点

---

### 阶段4: 测试验证

#### T14: 单元测试 - 模型和生成器
- **任务ID**: T14
- **优先级**: P1
- **目标文件**:
  - `tests/test_equipment/test_models.py`
  - `tests/test_equipment/test_generator.py`
- **依赖**: T4, T6
- **实现步骤**:
  1. 测试所有枚举值
  2. 测试 Equipment 模型序列化
  3. 测试装备生成器的稀有度分布
  4. 测试词缀生成逻辑
  5. 测试词缀互斥规则
- **验收标准**:
  - [ ] 测试覆盖率 > 80%
  - [ ] 所有测试通过

---

#### T15: 单元测试 - 计算器和强化
- **任务ID**: T15
- **优先级**: P1
- **目标文件**:
  - `tests/test_equipment/test_calculator.py`
  - `tests/test_equipment/test_enhancer.py`
- **依赖**: T7, T8
- **实现步骤**:
  1. 测试单件装备属性计算
  2. 测试玩家总属性计算
  3. 测试套装效果
  4. 测试强化成功率
  5. 测试强化失败降级
- **验收标准**:
  - [ ] 测试覆盖率 > 80%
  - [ ] 所有测试通过

---

#### T16: 集成测试和数据迁移
- **任务ID**: T16
- **优先级**: P1
- **目标文件**:
  - `tests/test_equipment/test_api.py`
  - `scripts/migrate_equipment.py`
- **依赖**: T11, T12
- **实现步骤**:
  1. 测试所有 API 端点
  2. 测试装备/卸载流程
  3. 创建数据迁移脚本
  4. 测试旧数据迁移
- **验收标准**:
  - [ ] API 集成测试通过
  - [ ] 迁移脚本可重复执行
  - [ ] 迁移后数据完整

---

## 四、依赖关系图

```
T1 (rarities.yaml) ─────┐
T2 (affixes.yaml) ──────┼──→ T5 (config_loader) ──→ T6 (generator)
T3 (sets/drop_tables) ─┘                           │
                                                   ↓
T4 (models) ──────────────────────────────────→ T7 (calculator)
         │                                      │
         ├──────────────────────────────────→ T8 (enhancer)
         │                                      │
         └──────────────────────────────────→ T9 (validators)
                                                │
                                                ↓
                    T10 (__init__.py) ←─────────┘
                         │
                         ↓
T11 (Player model) ──→ T12 (API routes) ──→ T13 (integration)
                         │
                         ↓
                    T14-T16 (tests)
```

---

## 五、文件清单

### 新增文件 (13个)

| 文件路径 | 描述 | 任务 |
|---------|------|------|
| `config/equipment/rarities.yaml` | 稀有度配置 | T1 |
| `config/equipment/affixes.yaml` | 词缀池配置 | T2 |
| `config/equipment/sets.yaml` | 套装配置 | T3 |
| `config/equipment/drop_tables.yaml` | 掉落表配置 | T3 |
| `config/equipment/affix_exclusions.yaml` | 词缀互斥规则 | T3 |
| `src/equipment/__init__.py` | 模块初始化 | T10 |
| `src/equipment/models.py` | 核心数据模型 | T4 |
| `src/equipment/config_loader.py` | 配置加载器 | T5 |
| `src/equipment/generator.py` | 装备生成器 | T6 |
| `src/equipment/calculator.py` | 属性计算器 | T7 |
| `src/equipment/enhancer.py` | 强化系统 | T8 |
| `src/equipment/validators.py` | 验证器 | T9 |
| `src/web/equipment_routes.py` | API路由 | T12 |

### 修改文件 (3个)

| 文件路径 | 修改内容 | 任务 |
|---------|---------|------|
| `src/models/player.py` | 添加装备槽位字段 | T11 |
| `src/web/app.py` | 注册装备API蓝图 | T13 |
| `src/data/database.py` | 更新模型导入 | T11 |

### 测试文件 (4个)

| 文件路径 | 描述 | 任务 |
|---------|------|------|
| `tests/test_equipment/__init__.py` | 测试包初始化 | T14 |
| `tests/test_equipment/test_models.py` | 模型测试 | T14 |
| `tests/test_equipment/test_generator.py` | 生成器测试 | T14 |
| `tests/test_equipment/test_calculator.py` | 计算器测试 | T15 |
| `tests/test_equipment/test_enhancer.py` | 强化测试 | T15 |
| `tests/test_equipment/test_api.py` | API测试 | T16 |

---

## 六、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Player 模型迁移破坏现有数据 | 高 | 保留旧字段，提供迁移脚本 |
| 词缀平衡性问题 | 中 | 配置外部化，便于热修复 |
| 属性计算性能 | 中 | 实现缓存机制 |
| Pydantic V2 兼容性 | 低 | 使用正确的模型定义语法 |

---

## 七、验收标准总览

### 功能验收
- [ ] 9级稀有度系统完整实现
- [ ] 词缀系统支持前缀/后缀/传奇词缀
- [ ] 10个装备槽位正常工作
- [ ] 装备生成符合配置的概率分布
- [ ] 属性计算正确（基础+词缀+强化+套装）
- [ ] 强化系统成功率正确

### 质量验收
- [ ] 所有单元测试通过
- [ ] 测试覆盖率 > 80%
- [ ] API 端点文档完整
- [ ] 数据迁移脚本可重复执行

### 兼容性验收
- [ ] 现有 Player 数据可正常迁移
- [ ] 旧 API 端点不受影响

---

## 八、执行建议

### 推荐执行顺序
1. **阶段1** (T1-T5): 完成基础设施，确保配置和模型正确
2. **阶段2** (T6-T9): 实现核心逻辑，先不急于集成
3. **阶段3** (T10-T13): 系统集成，逐步接入现有系统
4. **阶段4** (T14-T16): 测试验证，确保质量

### 时间估计
- 阶段1: 2-3 小时
- 阶段2: 3-4 小时
- 阶段3: 2-3 小时
- 阶段4: 2-3 小时
- **总计**: 约 10-13 小时

---

**下一步**: 用户确认后，使用 `/oh-my-claudecode:start-work diablo-equipment-system` 开始执行
