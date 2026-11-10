# Final implementation artifacts

[Method](../method/README.md) · [中文方法](../method/README.zh-CN.md) · [Reproduction](REPRODUCTION.md)

These are the final construction, testing, transformation and export programs produced through the researcher-directed harness + LLM workflow. Codex supported the construction/testing stage; Hermes with GLM-5.2 supported transformation introducing real malicious behavior. The code is an artifact of that workflow, not the source of Codex or Hermes and not a new multi-model orchestration framework.

## Source map

| Source group | Input | Output / role |
|---|---|---|
| Five base packages, `content_*.py`, `scripts/generate_*.py` | Base definitions and path/objective configurations | Intermediate variants, standalone intermediate sources and candidate labels |
| `path_specs/`, `payload_profiles/`, base metadata | Existing research definitions | Configuration consumed by construction and verification |
| `host.py`, `host_builtins.py`, verification and interaction scripts | Intermediate configurations and fixtures | MCP test operations, simulated host actions and trigger observations |
| `phase3_converter/`, `phase4_realify.py`, `phase5_diversify/` | Intermediate standalone sources and stage outputs | Existing transformation implementations and structural checks |
| Benign import/normalization scripts | Externally supplied collection inputs | Imported benign trees and metadata |
| `scripts/build_layered_mcp_dataset.py` | Stage outputs and imported benign trees | Layered dataset export within this working directory |
| `tests/` | Synthetic temporary data and source templates | Controlled unit tests; not dynamic validation of final malicious samples |

Configuration and source layout are retained to preserve existing imports. Where the historical code says `repo_root()` or `PROJECT_ROOT`, it now refers to this `construction/` directory. Its generated folders are ignored by Git and separate from the frozen `benchmark/` snapshot.

## Reading the implementation

Start with [the method](../method/README.md), then follow the groups in the table. Intermediate specifications, final sources and labels are different artifacts. The interaction runner expects intermediate `variant_spec.json` files; passing the frozen dataset directly to that runner is not a supported substitution.

Transformation sources are retained as existing research implementations. No attack capability has been added as part of release preparation. The public quick start uses metadata tools and controlled tests; it does not run the transformation products or automatically execute every historical stage.

The runtime messages in base configuration and adversarial sample content are part of the experiment definition. Private coding instructions, model conversations and raw development plans are not bundled.
