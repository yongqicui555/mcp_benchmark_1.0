# Changelog

## [0.1.11] — 2026-06-14

### Added
- **GitHub Releases**: 首次创建 GitHub Release 页面
- **MCP Registry 发布**: 正式发布到 [MCP Official Registry](https://registry.modelcontextprotocol.io/servers/io.github.woshilaohei/mindcore-memory)

### Changed
- CI 流水线分离: `ci.yml` 纯测试（push + PR + workflow_dispatch），`publish-mcp.yml` 统一处理 PyPI + MCP Registry 发布（tag push）
- `twine upload` 直接上传 PyPI，移除中间仓库依赖

### Fixed
- Tag push 同一 SHA 不触发 CI → 确保新 commit 再打 tag

## [0.1.10] — 2026-06-14

### Fixed
- **P0** CI `test_security.py`: `/tmp` 路径保护 → `TMPDIR` 环境变量指定安全目录
- **P0** CI 表达式错误: `${{ runner.temp }}` 无效 → `${{ github.workspace }}/_temp`
- **P0** Tag push 不触发 CI: GitHub Actions 相同 SHA 去重

### Changed
- `ci.yml` + `publish-mcp.yml` 流程重构，分阶段修复
- 版本号 0.1.9 → 0.1.10，确保新 commit + tag 触发 CI

## [0.1.9] — 2026-06-14

### Added
- **SLO 跟踪** (`slo.py`): 6 operations P95/P99 latency targets + `@track_latency` decorator
- **Prometheus 指标** (`metrics.py`): 零依赖 Prometheus 兼容收集器 + `/metrics` endpoint
- **熔断器** (`circuit_breaker.py`): CLOSED→OPEN→HALF_OPEN 状态机，保护 FAISS/embedding 操作
- **重试机制** (`retry.py`): 指数退避+jitter，瞬态错误自动重试
- **单元测试** (`test_v019_modules.py`): 4 新模块 45 个测试用例全覆盖

### Fixed
- **P0** JSONL 无限膨胀: `update_confidence()` 从追加模式改为 `_rewrite_jsonl()` 原子覆盖
- **P0** Evict 假删除: `_evict_low_importance()` 删除后写入磁盘，避免重启僵尸复活
- **P0** http_app.py: 单例化 `MemoryEngine`，避免每次请求创建实例
- **P1** 无内容去重: `store()` 前精确匹配去重，相同内容合并重要性/置信度
- **P1** BM25 重要性污染: 无 FAISS 时 importance boost 从 35% 降至 1%
- **P1** metrics.py `render()`: 原子快照替代分步锁调用，消除数据竞争
- **P1** metrics.py gauge 精度: `int` 截断改为 `round` 四舍五入
- **P1** circuit_breaker.py: 模块级 structlog import，消除方法内重复 import
- **P1** retry.py: 重构 `for-else` 为显式循环后处理，消除歧义
- **P2** `_load()` 加载时自动去重+压缩重写

### Changed
- slo.py: p95=0 时跳过 SLO 日志（无 SLO 定义的操作不记录）
- metrics.py: SLO violation 计数器独立于 total/errors 展示

### Performance
- 全部 6 operations 远超 SLO 目标（最低 8x 余量）
- 回归测试: 117/118 passed (99.2%)
- 全景真实测试: 146/146 (100%) — 15 Phase 全链路覆盖
- 测试覆盖从 73 case → 118 case (+62%)，含 45 个新模块测试

## [0.1.8] — 2026-06-13

### Added
- Tag 处理: 截断到 100 字符 + strip + 去重
- store() 中 tag 自动清洗

### Fixed
- BM25 重要性污染（完整修复在 0.1.9）

## [0.1.7] — 2026-06-12

### Added
- Hybrid search: BM25(40%) + FAISS(50%) + importance(5%) + recency(5%)
- IVF 索引: 500+ 记忆自动切换
- 路径遍历保护
- 输入净化层

## [0.1.6] — 2026-06-11

### Added
- Fernet 加密支持
- Session ID 验证
- Context window 管理
