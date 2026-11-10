# Release verification

The release candidate was checked in an independently cloned repository.

| Check | Result |
|---|---|
| Sample/label correspondence | 1,025 samples, matching counts and unique composite identities |
| Frozen file integrity | 11,421 of 11,421 data and label files match the SHA-256 inventory |
| Final constructed source/configuration | 685 server files parsed and 685 configurations decoded without executing samples |
| Controlled tests | 70 passed, 0 failed, 0 skipped, using a fresh locked dependency environment |
| Baseline example | Five L0 samples generated with synthetic data; no server or model API executed |
| Label preservation | No changes to non-path label fields |
| Documentation | Local links checked; provenance distinguishes manual approval for stage progression, the coding harness and the MCP test host |

The corpus sample files retain their pre-migration working-tree bytes. Two empty historical source-directory references and five stale manifest roots were corrected; the migration record preserves the omitted directory references. Inherited Git text rules are controlled at the repository level so supported clean checkouts pass the same inventory.

The credential-pattern check is a limited static scan, not a guarantee that every possible credential format is recognized. Its two findings are preserved upstream test fixtures. The author's local API configuration and private authoring materials are not tracked.

Dynamic execution of final malicious samples, model API experiments and historical LLM session replay were not performed. See [the machine-readable report](release_verification.json) for scope, checked revisions and environment.
