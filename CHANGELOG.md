# Changelog

## 1.0.0-rc.1

- Organize the existing 1,025-sample snapshot under `benchmark/`, preserving sample bytes and class labels.
- Correct published paths, including the 340 imported benign label rows.
- Describe the corpus design and harness + LLM method in English and Chinese, explaining my use of Codex for construction and Hermes + GLM-5.2 for behavioral transformation.
- Include final implementation artifacts, configuration and controlled tests under `construction/`.
- Add standard-library catalog checks, a frozen checksum inventory and a baseline-only example.
- Keep authoring prompts, conversations, raw process logs and the separate local real-world test set out of the release.
- Document research use, source attribution and reproduction boundaries.

This is a release candidate. Preparation does not change repository visibility or establish dynamic validation of final malicious behavior.
