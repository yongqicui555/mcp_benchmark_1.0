# Support

## Getting Help

### Documentation
- [README.md](README.md) — Installation, configuration, and API reference
- [docs/comparison.md](docs/comparison.md) — Competitive comparison and migration guides
- [docs/boundary-algorithm.md](docs/boundary-algorithm.md) — 3D Boundary Balance Algorithm deep dive
- [CHANGELOG.md](CHANGELOG.md) — Version history and release notes

### Community
- [GitHub Discussions](https://github.com/woshilaohei/mindcore-memory-mcp/discussions) — Q&A, ideas, and community support
- [GitHub Issues](https://github.com/woshilaohei/mindcore-memory-mcp/issues) — Bug reports and feature requests

### Direct Contact
- Email: **1410770089@qq.com**

## FAQ

### How is this different from Mem0 / Letta?
See our [competitive comparison](docs/comparison.md) for a detailed breakdown. In short: MindCore is the only MCP memory server with production-grade resilience (circuit breaker, retry, SLO tracking, Prometheus metrics).

### Does this require an API key or cloud service?
No. MindCore runs entirely locally with zero external dependencies. Your memory data never leaves your machine.

### How do I enable semantic (FAISS) search?
```bash
pip install mindcore-memory[semantic]
```
FAISS vector search activates automatically when sentence-transformers is available. Falls back to BM25-only gracefully.

### How do I enable encryption?
Set the `MINDCORE_ENCRYPT_KEY` environment variable (a base64-encoded Fernet key):
```bash
export MINDCORE_ENCRYPT_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

### Can I use this in production?
Yes. The project passes 118/118 tests, has circuit breaker + retry + SLO tracking, and follows MCP protocol standards. See [SECURITY.md](SECURITY.md) for our security posture.

## Commercial Support

For enterprise deployment, custom integrations, or priority support, contact: **1410770089@qq.com**
