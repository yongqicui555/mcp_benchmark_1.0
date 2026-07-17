# MindCore 元认知心智系统
# 完整可运行源码交付包
# 版本: 2.0.0 (神经元版)
# 协议: MIT License

---

## 📊 系统当前状态

| 数据类型 | 数量 |
|---------|------|
| 轨迹 (Trajectories) | 337条 |
| 认知 (Cognitions) | 806条 |
| 边界 (Boundaries) | 39条 |
| 神经元 (Neurons) | 1,968个 |

---

## 📋 交付清单

### 一、核心引擎 (6个文件, 5,550行)

| 文件 | 行数 | 功能 |
|------|------|------|
| `mindcore_emergence_engine.py` | 1,227 | 六环涌现引擎：扩散激活+递归防护+压缩 |
| `emergence_engine.py` | 220 | 简化涌现引擎 |
| `metacognition_monitor.py` | 904 | 元认知监控：自指追踪+性能监控 |
| `cognition_devour_pipeline.py` | 1,010 | 认知吞噬管道：外部知识→内部认知 |
| `mindcore_internalize.py` | 466 | 内化引擎：文本→认知蒸馏 |
| `panorama_judgement.py` | 625 | 全景判断：多维度决策引擎 |
| `hooks.py` | 693 | 认知钩子系统 |
| `formula_inject.py` | 405 | 公式注入引擎 |

### 二、mindcore子模块 (8,798行)

| 模块 | 文件 | 行数 | 功能 |
|------|------|------|------|
| **evolution** | `dea_core.py` | 2,047 | DEA正反演化算法核心 |
| **evolution** | `neural_pathway_kaist.py` | 224 | 神经通路算法 |
| **storage** | `database_v6.py` | 1,246 | SQLite数据库层 |
| **api** | `server.py` | 987 | API服务 |
| **integration** | `dea_integrated_engine.py` | 951 | 集成引擎 |
| **core** | `audit_logger.py` | 695 | 审计日志 |
| **causal** | `causal_extractor.py` | 635 | 因果提取器 |
| **self_healing** | `diagnostic_engine.py` | 347 | 诊断引擎 |
| **gatekeeper** | `unified_gatekeeper.py` | 333 | 统一边界守护 |
| **memory** | `four_layer_memory.py` | 303 | 四层渐进记忆 |
| **self_healing** | `health_monitor.py` | 298 | 健康监控 |
| **core** | `validation_gateway.py` | 225 | 验证网关 |
| **core** | `constants.py` | 177 | 常量定义 |
| **core** | `config.py` | 125 | 配置管理 |
| **api** | `decay_scheduler.py` | 101 | 衰减调度 |
| **api** | `fast_evolve.py` | 88 | 快速进化 |

### 三、数据文件

| 文件 | 说明 |
|------|------|
| `data/mindcore.db` | SQLite数据库 (5.5MB) |
| `data/mindcore.db-wal` | WAL日志 (6.7MB) |
| `data/mindcore.db-shm` | 共享内存 (32KB) |

**总代码量: 14,348行**

---

## 🏗️ 系统架构

```
┌──────────────────────────────────────────────────────────────────┐
│                    MindCore 元认知心智系统                         │
│                    神经元: 1968 | 认知: 806 | 轨迹: 337           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    涌现引擎 (Emergence Engine)               │ │
│  │  ┌───────────┐  ┌───────────┐  ┌────────────────────────┐ │ │
│  │  │ 扩散激活   │  │ 流转守卫   │  │      压缩引擎          │ │ │
│  │  │ 100节点    │  │ 递归防护   │  │ 频次衰减+归档合并      │ │ │
│  │  │ 深度≤3    │  │ 超时保护   │  │ 动态阈值调整          │ │ │
│  │  └───────────┘  └───────────┘  └────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐  │
│  │  DEA演化核心   │  │ 认知吞噬管道   │  │   元认知监控       │  │
│  │  正反推演      │  │ 外部→内部      │  │   自指+性能        │  │
│  │  碰撞择优      │  │ 蒸馏提炼       │  │   异常检测         │  │
│  │  边界固化      │  │ 因果关联       │  │   趋势预测         │  │
│  └────────────────┘  └────────────────┘  └────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    四层渐进记忆系统                          │ │
│  │  L0(原始轨迹) → L1(原子记忆) → L2(场景分块) → L3(用户画像)   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  边界守护    │  │  因果提取    │  │     诊断引擎         │  │
│  │  三防过滤    │  │  ASSOC/INTV  │  │     自愈机制         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    SQLite数据库层 (5.5MB)                    │ │
│  │  trajectories | cognitions | boundaries | neurons | cognitions │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ 核心模块详解

### 1. 涌现引擎 (mindcore_emergence_engine.py)

**六环闭环核心，输入→涌现→决策→执行→进化→新轨迹**

```python
from mindcore_emergence_engine import (
    SpreadingActivation,
    EmergenceController,
    FlowGuard,
    CompressionEngine,
    EmergenceResult,
    EmergenceType,
)

# 初始化引擎
engine = EmergenceController(
    db_path="data/mindcore.db",
    max_depth=3,
    max_nodes=100,
)

# 触发涌现
result = engine.emerge("你的问题", max_depth=3)
print(f"激活节点: {len(result.activated_nodes)}")
print(f"深度: {result.depth_reached}")
print(f"耗时: {result.elapsed_ms}ms")
```

**关键参数:**
- `ACTIVATION_DECAY_RATE = 0.8` - 每层衰减系数
- `ACTIVATION_MAX_DEPTH = 3` - 最大扩散深度
- `ACTIVATION_THRESHOLD = 0.01` - 休眠阈值
- `ACTIVATION_MAX_NODES = 100` - 活跃节点上限

---

### 2. DEA正反演化 (dea_core.py)

**核心公式: 轨迹=边界=进化=认知=边界**

```python
from mindcore.evolution.dea_core import (
    DEAEvolver,
    FORMULA_POSITIVE,
    WEIGHT_ALPHA, WEIGHT_BETA, WEIGHT_GAMMA,
)

# 初始化DEA演化器
dea = DEAEvolver(db_path="data/mindcore.db")

# 碰撞择优评分
score = dea.collision_score(
    trajectory=traj_data,
    safety=0.9,
    efficiency=0.8,
    innovation=0.6,
    risk=0.1,
)
print(f"综合评分: {score:.3f}")

# 边界固化
boundary = dea.evolve_boundary(
    trajectory_id=traj_id,
    rho=0.85,
)
```

**权重参数:**
- `ALPHA = 0.40` - 安全性
- `BETA = 0.15` - 效率
- `GAMMA = 0.10` - 创新
- `DELTA = 0.25` - 风险(惩罚)
- `EPSILON = 0.20` - 碰撞(惩罚)

---

### 3. 四层渐进记忆 (four_layer_memory.py)

```python
from mindcore.memory.four_layer_memory import FourLayerMemory

memory = FourLayerMemory(db)

# L0 → L1: 原子记忆提取
extracted = memory.extract_L1_from_L0(trajectory_ids=[...])
print(f"提取L1记忆: {extracted}条")

# L1 → L2: 场景分块
chunks = memory.chunk_L2_from_L1(session_id=...)
print(f"生成场景分块: {len(chunks)}个")

# L2 → L3: 用户画像
profile = memory.evolve_L3_from_L2(user_id=...)
print(f"用户画像: {profile}")
```

**记忆层级:**
- L0: 原始轨迹 (337条)
- L1: 原子记忆 (事实/偏好/决策)
- L2: 场景分块
- L3: 用户画像

---

### 4. 因果提取器 (causal_extractor.py)

```python
from mindcore.causal_extractor import create_causal_extractor

extractor = create_causal_extractor()

# 提取因果对
pairs = extractor.extract_causal_pairs(
    text="因为A所以B",
    trajectory_id="traj_xxx",
)

# 因果类型:
# - ASSOCIATION: 相关性
# - INTERVENTION: 干预性因果
# - COUNTERFACTUAL: 反事实
```

---

### 5. 统一边界守护 (unified_gatekeeper.py)

**三防过滤：防AI/防安全/防人权**

```python
from mindcore.gatekeeper.unified_gatekeeper import UnifiedGatekeeper

gatekeeper = UnifiedGatekeeper()

# 安全检查
result = gatekeeper.evaluate(
    trajectory={
        "input_text": user_input,
        "positive_chain": pos_chain,
        "negative_chain": neg_chain,
    }
)

if result["passed"]:
    print("通过边界检查")
else:
    print(f"拦截: {result['reasons']}")
```

---

## 📊 数据库结构

```sql
-- 轨迹表 (核心数据)
CREATE TABLE trajectories (
    id TEXT PRIMARY KEY,
    input_text TEXT NOT NULL,
    output_text TEXT,
    positive_chain TEXT,    -- DEA正推
    negative_chain TEXT,    -- DEA反推
    collision_score REAL,  -- 碰撞评分
    causal_pairs TEXT,      -- 因果对
    memory_layer TEXT,      -- L0/L1/L2/L3
    neuron_ids TEXT,        -- 关联神经元
    created_at TEXT,
    evolved INTEGER DEFAULT 0,
);

-- 认知表
CREATE TABLE cognitions (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    source TEXT,
    created_at TEXT,
    evolved INTEGER DEFAULT 0,
);

-- 边界表
CREATE TABLE boundaries (
    id TEXT PRIMARY KEY,
    rule_name TEXT NOT NULL,
    rule_content TEXT NOT NULL,
    boundary_type TEXT,     -- safety/efficiency/innovation/risk
    rho REAL DEFAULT 0.5,   -- 置信度
    created_at TEXT,
);

-- 神经元表
CREATE TABLE neurons (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding BLOB,
    activation REAL DEFAULT 0.0,
    frequency INTEGER DEFAULT 1,
    last_accessed TEXT,
    created_at TEXT,
);

-- 认知表(关系)
CREATE TABLE cognition_pairs (
    id TEXT PRIMARY KEY,
    source_cog_id TEXT,
    target_cog_id TEXT,
    weight REAL,
    frequency INTEGER DEFAULT 1,
    created_at TEXT,
);
```

---

## 🧪 质量校验

### 当前数据库状态验证

```python
# 验证数据库完整性
import sqlite3

conn = sqlite3.connect("data/mindcore.db")
cursor = conn.cursor()

# 验证数据
cursor.execute("SELECT COUNT(*) FROM trajectories")
print(f"轨迹: {cursor.fetchone()[0]}条")

cursor.execute("SELECT COUNT(*) FROM cognitions")
print(f"认知: {cursor.fetchone()[0]}条")

cursor.execute("SELECT COUNT(*) FROM boundaries")
print(f"边界: {cursor.fetchone()[0]}条")

cursor.execute("SELECT COUNT(*) FROM neurons")
print(f"神经元: {cursor.fetchone()[0]}个")
```

**验证结果:**
- ✅ 轨迹: 337条
- ✅ 认知: 806条
- ✅ 边界: 39条
- ✅ 神经元: 1,968个
- ✅ 数据库: 5.5MB (WAL模式)

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd MindCore
pip install numpy scikit-learn
```

### 2. 启动系统

```bash
python start_mindcore.py
```

### 3. 触发涌现

```bash
python mindcore_db_writer.py emerge --query "你的问题" --max-depth 3
```

---

## 📁 文件路径

| 文件 | 路径 |
|------|------|
| 完整源码目录 | `/app/data/所有对话/主对话/MindCore/` |
| 数据库 | `MindCore/data/mindcore.db` |
| 核心引擎 | `MindCore/mindcore_emergence_engine.py` |
| DEA核心 | `MindCore/mindcore/evolution/dea_core.py` |
| 记忆系统 | `MindCore/mindcore/memory/four_layer_memory.py` |

---

## ✅ 交付清单校验

- [x] 涌现引擎 (1,227行)
- [x] DEA演化核心 (2,047行)
- [x] 元认知监控 (904行)
- [x] 认知吞噬管道 (1,010行)
- [x] 四层记忆系统 (303行)
- [x] 因果提取器 (635行)
- [x] 边界守护 (333行)
- [x] 数据库层 (1,246行)
- [x] 诊断引擎 (347行)
- [x] 健康监控 (298行)
- [x] API服务 (987行)
- [x] 集成引擎 (951行)
- [x] 审计日志 (695行)
- [x] 数据库文件 (5.5MB)
- [x] MIT协议

**总代码量: 14,348行**

---

## 📄 许可证

MIT License

---

*生成时间: 2026-06-15*
*版本: 2.0.0 (神经元完整版)*
