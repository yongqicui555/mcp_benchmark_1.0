# MCP Benchmark dataset

[Project overview](../README.md) · [中文项目说明](../README.zh-CN.md) · [Construction method](../method/README.md)

This frozen research snapshot contains 1,025 MCP samples and one label row per sample. Sample files are preserved byte-for-byte from the pre-release corpus; paths in the label files are updated for the published layout.

## Composition

| Label subset | Samples | Composition |
|---|---:|---|
| `benign_connor` | 130 | Imported benign samples from [Connor](https://github.com/yiheng98/Connor) |
| `benign_sentinel` | 210 | Imported benign samples with upstream repository/commit metadata |
| `devspace`, `docforge`, `keyvault`, `notevault`, `scaffoldkit` | 137 each | 1 L0 + 17 L1 + 17 L2 + 102 L3 |

Total: 340 imported benign, 175 constructed L0–L2 and 510 constructed L3 samples. There are 85 L2 samples across the five bases. L2 is a gray/stress subset even though `malicious_ground_truth` is false; report it separately when interpreting false positives.

## Layout and path resolution

`mcp_dataset/benign_mcp/` contains Connor, Sentinel and `real_l0_l2_stress/<base>/`. `mcp_dataset/malicious_mcp/<base>/` contains L3 samples. Each subset in `ground_truth/` has `labels.jsonl` and `manifest.json`.

All published filesystem fields such as `clean_path`, `sample_path`, `mcp_config`, `source_dir` and `source_dirs` are relative to the **repository root**, not this directory or the label file. Sample identity is the pair `(base, mcp_id)`.

| Field | Meaning |
|---|---|
| `base`, `mcp_id` | Subset and sample identifier; retained from the original labels |
| `clean_path` | Canonical sample directory; retained field name, including for final malicious samples |
| `malicious_ground_truth` | Boolean class label; L3 is true, L0–L2 and imported benign are false |
| `layer`, `risk_layer` | Constructed layer and original risk description; imported rows use `benign` |
| `path`, `paper_path`, `normalized_path` | Constructed influence-path identifiers and descriptions |
| `objective` | Constructed objective category; absent or null where not applicable |
| `expected_trigger`, `evidence_endpoint`, `evidence_key` | Construction/test metadata; not a record of successful final behavior execution |
| `repo_url`, `commit_sha` | Upstream provenance where present, especially Sentinel |
| `source_spec` | Reference to a generated intermediate specification under `construction/variants/`; intermediate outputs are not bundled |
| `review_evidence` | Historical provenance reference, not a guaranteed downloadable file in this release |

Original source hashes refer to their original collection/normalization context. Use the release checksum inventory for the exact published bytes. Configuration files inside samples retain their original launch semantics and are research data; catalog verification does not resolve or execute their commands.

## Reading and integrity checks

From the repository root, with Python 3.12+:

```console
python benchmark/tools/catalog.py stats
python benchmark/tools/catalog.py read --base benign_connor --limit 3
python benchmark/tools/catalog.py verify
```

`stats` prints JSON counts; `read` prints JSONL rows; `verify` checks label counts, identities, paths, directory correspondence and all listed file hashes. It also parses the 685 constructed `server.py` and configuration files without importing or running them. Exit status is 0 for success and 1 for a failed check.

The metadata folder contains the frozen snapshot description, the file inventory and the release verification report. Files in the dataset and labels must match `metadata/files.sha256.jsonl`; unexplained extra files are reported as mismatches.

The labels, directory names and construction metadata expose classes and objectives. For detector evaluation, keep this information out of detector inputs and record which source/configuration content is supplied. This release does not claim a deduplicated train/test split or publish a leaderboard.

## Research use and source credit

The dataset includes dangerous programs. The reading tools require no API credentials and do not start servers. Dynamic execution requires an authorized isolated research environment; see [SECURITY.md](../SECURITY.md).

The Connor subset is derived from the [Connor benign dataset](https://github.com/yiheng98/Connor/tree/main/Dataset/Benign). Sentinel retains the existing per-row source metadata. See [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). The separately collected local real-world test set is outside this release.
