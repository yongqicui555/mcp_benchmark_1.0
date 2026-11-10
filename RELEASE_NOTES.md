# MCP Benchmark 1.0 release candidate

Version: **1.0.0-rc.1**. This candidate prepares the existing private repository for review; it does not change repository visibility or create a public release.

## Included

- The existing 1,025 samples: 130 Connor, 210 Sentinel, 175 constructed L0–L2 and 510 constructed L3.
- Relocated sample and label directories, with corrected repository-relative metadata paths and a SHA-256 file inventory.
- English and Chinese method descriptions covering corpus design, the project's use of Codex and Hermes + GLM-5.2 for program generation and behavioral transformation, manual approval for stage progression, and the interpretation of verification evidence.
- Final implementation artifacts and controlled tests, with local machine paths removed from first-party input defaults.
- A standard-library catalog CLI and a baseline-only construction example that starts no servers.
- Research-use guidance, project citation, Apache-2.0 for original material and upstream attribution.

## Verification

The [verification summary](benchmark/metadata/verification.md) and machine-readable [release report](benchmark/metadata/release_verification.json) record completed checks, environment and limits. The baseline is commit `83bdeb9fa540f62722944f7ad844a8da9a7726d3`. Original sample content is preserved; label filesystem references and the repository organization change.

Verification covers file integrity, label correspondence, source/configuration parsing and controlled unit tests. Dynamic execution of the 510 final malicious samples and model API experiments are not part of release preparation. Intermediate tests and structural checks are not reported as final-behavior success rates.

## Reproduction limits

Original authoring instructions, prompts, conversations and raw process records are not released. The implementation can support documented code-level steps; it does not replay historical LLM coding sessions. Harness versions, the underlying Codex model and historical run counts are not inferred.

The additional local real-world test set, private environment settings, caches, virtual environments and local research logs are excluded. Existing third-party attribution is retained. No new per-sample license review or reconstruction of historical Sentinel review records is included.

## Before publication

Review this candidate's dataset, method account, code and verification report in the private repository. Repository visibility and the final version tag remain unchanged until the final review is complete.
