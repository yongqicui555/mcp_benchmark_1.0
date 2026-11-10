# Reproduction and working outputs

## Environment and checks

Use Python 3.12+ and [uv](https://docs.astral.sh/uv/). From the repository root:

Clone with byte-preserving line-ending settings: `git clone -c core.autocrlf=false -c core.longpaths=true <repository-url>`. Some preserved upstream filenames are long; the catalog handles extended Windows paths internally.

```console
uv sync --locked
uv run --locked python benchmark/tools/catalog.py verify
uv run --locked pytest
```

Dataset reading needs only the Python standard library. The locked environment is for the first-party implementation and tests; it does not install the dependencies of every third-party sample. No model key is needed for catalog checks or the controlled test suite.

Tests generate synthetic fixtures under temporary directories instead of requiring unpublished keys or local seed folders. They inspect generated sources and exercise controlled intermediate helpers. Passing these tests does not establish successful execution of final malicious behaviors.

## Controlled construction example

From the repository root, a baseline-only example can be generated without starting a server:

```console
uv run --locked python construction/examples/build_baseline.py --output .cache/baseline-example
```

The example produces one L0 intermediate sample per base and a summary. It uses a new or empty output directory, synthetic data and existing construction functions. It does not invoke Hermes, Codex, GLM-5.2 or a model API. It does not regenerate the final malicious dataset.

## Existing stage artifacts and output locations

The existing stage scripts operate relative to `construction/`. Their intermediate outputs include `variants/`, `clean_mcp/`, `real_mcp/`, `ground_truth/`, `mcp_dataset/` and `interaction_logs/` inside that directory. These are working outputs and are not the published `benchmark/` tree. Preserve a stage's inputs before using historical overwrite options.

The intermediate interaction runner accepts its existing per-base variants and model configuration. Optional settings are documented in `.env.example`; never use personal or production credentials for research sample execution. Its model settings belong to MCP interaction tests, not the historical authoring provenance.

The original transformation stages require their preceding stage outputs; their source and structural verification code are retained for inspection. The release does not add an automatic launcher for dangerous artifacts. Dynamic experiments require the conditions in [SECURITY.md](../SECURITY.md).

The layered exporter consumes the constructed stage outputs, imported benign trees and corresponding generated labels, and writes a separate working export. Historical benign-collection scripts additionally require external registry inputs and collection records. The frozen 340 benign samples and labels are already included for dataset use; recollecting live upstream projects is not guaranteed to reproduce that snapshot.

## What can be reproduced

The frozen published dataset is identified by its file-checksum inventory. The final code allows the supported data-reading, checking and controlled construction steps to be executed. Intermediate fixtures may contain random keys and timestamps, so a new build is not promised to reproduce the frozen bytes.

The method account describes the project's staged use of Codex and Hermes + GLM-5.2, with manual approval for stage progression. Private task instructions and process records are outside the release scope. Exact model-session replay is outside the reproduction claim. The release report lists the checks actually performed and the dynamic checks not performed.
