# MCP Benchmark 1.0 数据集说明

当前版本的 benchmark 主要通过两个目录组织：

- `mcp_dataset/`：规范化后的 MCP 样本目录。
- `ground_truth/`：样本标签与元数据。

本 README 只说明这两个已经推送到仓库的数据目录。

## 目录结构

```text
mcp_dataset/
  benign_mcp/
    connor/                         # 130 个已确认 benign 的 Connor 样本
    sentinel/                       # 210 个已确认 benign 的 Sentinel 样本
    real_l0_l2_stress/              # 175 个 real_mcp 中的 L0-L2 压力测试样本
      devspace/                     # 35 个样本：L0, L1_*, L2_*
      docforge/                     # 35 个样本：L0, L1_*, L2_*
      keyvault/                     # 35 个样本：L0, L1_*, L2_*
      notevault/                    # 35 个样本：L0, L1_*, L2_*
      scaffoldkit/                  # 35 个样本：L0, L1_*, L2_*
  malicious_mcp/
    devspace/                       # 102 个 malicious L3 样本
    docforge/                       # 102 个 malicious L3 样本
    keyvault/                       # 102 个 malicious L3 样本
    notevault/                      # 102 个 malicious L3 样本
    scaffoldkit/                    # 102 个 malicious L3 样本

ground_truth/
  benign_connor/
  benign_sentinel/
  devspace/
  docforge/
  keyvault/
  notevault/
  scaffoldkit/
```

## 数据集划分

| 划分 | 样本目录 | 数量 | 标签 |
|---|---:|---:|---|
| Connor benign | `mcp_dataset/benign_mcp/connor/` | 130 | benign |
| Sentinel benign | `mcp_dataset/benign_mcp/sentinel/` | 210 | benign |
| real L0-L2 压力测试 | `mcp_dataset/benign_mcp/real_l0_l2_stress/` | 175 | benign / gray stress-test |
| real L3 malicious | `mcp_dataset/malicious_mcp/` | 510 | malicious |

当前 `mcp_dataset/` 共包含 1,025 个 MCP 样本。

## Ground truth 文件

`ground_truth/` 下每个子目录都包含：

- `labels.jsonl`：逐行 JSON，每行对应一个样本。
- `manifest.json`：该子集的汇总元数据。

## Benign ground truth

benign 子集包括：

```text
ground_truth/benign_connor/
ground_truth/benign_sentinel/
```

这两个子集均使用如下标签语义：

```json
{
  "label": "benign",
  "malicious_ground_truth": false,
  "risk_layer": "benign"
}
```

其中 Sentinel 样本的 `admission_policy` 为：

```text
confirmed_benign
```

对应的样本源码目录位于：

```text
mcp_dataset/benign_mcp/connor/<mcp_id>/
mcp_dataset/benign_mcp/sentinel/<mcp_id>/
```

注意：`benign_connor` 和 `benign_sentinel` 的 label 中可能保留了构建阶段的历史来源路径字段；实际使用时建议以 `mcp_dataset/benign_mcp/<connor|sentinel>/<mcp_id>/` 作为样本路径。

## Real-base ground truth

real-base 子集包括：

```text
ground_truth/devspace/
ground_truth/docforge/
ground_truth/keyvault/
ground_truth/notevault/
ground_truth/scaffoldkit/
```

每个 real-base 子集包含 137 条标签：

- `L0`：1 个 baseline 样本。
- `L1_*`：17 个 benign suggestion 样本。
- `L2_*`：17 个 gray / stress-test 样本。
- `L3_*`：102 个 malicious 样本。

这五个子集中的 `clean_path` 已经直接指向 `mcp_dataset/`：

```text
L0, L1_*, L2_* -> mcp_dataset/benign_mcp/real_l0_l2_stress/<base>/<sample_id>/
L3_*           -> mcp_dataset/malicious_mcp/<base>/<sample_id>/
```

## 主要字段说明

`labels.jsonl` 中常用字段如下：

| 字段 | 含义 |
|---|---|
| `base` | 数据子集名称，例如 `devspace` 或 `benign_sentinel`。 |
| `mcp_id` | 样本 ID。 |
| `clean_path` | 样本目录路径；real-base 子集中直接指向 `mcp_dataset/`。 |
| `label` | 标签名称。benign 子集使用 `benign`。 |
| `malicious_ground_truth` | 是否为恶意样本的布尔标签。 |
| `risk_layer` / `layer` | 风险层级或数据集层级。 |
| `expected_trigger` | 预期触发条件；如不适用则为 `null`。 |
| `evidence_endpoint` / `evidence_key` | 证据相关元数据；如不适用则为 `null`。 |

五个 real-base 子集中，`layer` 的含义为：

```text
L0  -> baseline
L1  -> benign_suggestion
L2  -> gray / stress-test
L3  -> malicious
```

## 推荐读取方式

1. 选择一个 `ground_truth/` 子集。
2. 读取该子集下的 `manifest.json`，获取总数、层级和路径信息。
3. 逐行读取 `labels.jsonl`。
4. 解析样本目录：
   - 对 `devspace`、`docforge`、`keyvault`、`notevault`、`scaffoldkit`，直接使用 `clean_path`。
   - 对 `benign_connor` 和 `benign_sentinel`，使用 `mcp_dataset/benign_mcp/<connor|sentinel>/<mcp_id>/`。
5. 从 `mcp_dataset/` 中读取对应样本的 MCP 配置和源码。

## 当前数量

| Ground truth 子集 | 标签数 | Benign / gray | Malicious |
|---|---:|---:|---:|
| `benign_connor` | 130 | 130 | 0 |
| `benign_sentinel` | 210 | 210 | 0 |
| `devspace` | 137 | 35 | 102 |
| `docforge` | 137 | 35 | 102 |
| `keyvault` | 137 | 35 | 102 |
| `notevault` | 137 | 35 | 102 |
| `scaffoldkit` | 137 | 35 | 102 |

总标签数：1,025。
