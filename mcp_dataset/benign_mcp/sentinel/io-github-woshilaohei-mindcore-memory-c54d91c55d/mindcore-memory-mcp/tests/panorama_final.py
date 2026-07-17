"""
Panorama Final E2E -- mindcore-memory-mcp v0.1.9 full-chain real-world test.
15 phases simulating production usage: store/recall/context/update/delete
+ SLO + metrics + circuit_breaker + retry + encryption + tags + dedup + HTTP endpoints.
"""
import sys, os, io, json, shutil, time, threading, tempfile, uuid

# Force UTF-8 stdout for Windows GBK consoles
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mindcore_memory.memory_engine import MemoryEngine, MemoryEntry, RetrievalResult, MemoryImportance
from mindcore_memory.slo import SLO_TARGETS, get_slo_target, track_latency
from mindcore_memory.metrics import MetricsCollector, get_collector
from mindcore_memory.circuit_breaker import CircuitBreaker, CircuitOpenError, get_circuit, CircuitState
from mindcore_memory.retry import retry_with_backoff


def main():
    # -- Setup --
    TEST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tmp_panorama")
    shutil.rmtree(TEST_DIR, ignore_errors=True)

    PASS = [0]
    FAIL = [0]

    def check(condition, label):
        if condition:
            PASS[0] += 1
            print(f"  [PASS] {label}")
        else:
            FAIL[0] += 1
            print(f"  [FAIL] {label}")
        return condition

    # -- Crypto key for encryption tests --
    from cryptography.fernet import Fernet
    ENCRYPT_KEY = Fernet.generate_key()

    # -- Engine --
    eng = MemoryEngine(storage_path=TEST_DIR, encrypt_key=ENCRYPT_KEY)
    collector = get_collector()

    print("=" * 72)
    print("  PANORAMA FINAL E2E -- mindcore-memory-mcp v0.1.9")
    print("=" * 72)

    # ======================================================================
    # PHASE 1: Empty DB basics
    # ======================================================================
    print("\n-- Phase 1: Empty DB --")
    stats = eng.get_stats()
    check(stats["total_memories"] == 0, "empty total_memories=0")
    check(stats["max_memories"] == 10000, "default max_memories=10000")
    check(stats["avg_confidence"] == 0.0, "empty avg_confidence=0")
    check(len(stats["by_importance"]) == 4, "4 importance levels")
    check(eng.recall("anything") == [], "empty recall returns []")
    check(eng.get_context_window("test") == "", "empty context_window returns ''")
    check(eng.get_stats()["total_memories"] == 0, "idempotent get_stats")

    # ======================================================================
    # PHASE 2: Mass injection -- 200 mixed entries
    # ======================================================================
    print("\n-- Phase 2: Inject 200 memories --")
    categories = {
        "bug": [
            "Bug: store() no tag truncation, >100 char tags written to disk",
            "Bug: update_confidence append mode caused JSONL inflation",
            "Bug: BM25 importance pollution, critical=4 dominated 35% weight",
            "Bug: eviction only removed from memory, not disk; zombie revival",
            "Bug: content dedup missing, same sentence stored N UUIDs",
        ],
        "habit": [
            "Rule: understand first then act -- knowledge != cognition",
            "Rule: do not rush, investigate before doing anything",
            "Rule: code must be reviewed line-by-line with check/x marks",
            "Rule: responses must be concise, no verbose explanations",
            "Rule: do not expand architecture arbitrarily, subtract not add",
        ],
        "project": [
            "ZeroDao v4.3.3: triple separation -- engine != frame != blackgold 9.1",
            "Bee Memory v5.x: 5D pool EXP/TRJ/COG/BND/CTX + void engine",
            "Cerebellum v4.0: safety shell/centralized, GitHub open source",
            "VSOS Guard v0.7.0: pure rule-based, 14/14 intercept",
            "mindcore-memory-mcp: STM->LTM->Deduction, SQLite+FAISS hybrid",
        ],
        "user": [
            "User calls himself Lao Hei, honorific as Big Brother",
            "User email 1410770089@qq.com, body is WorkBuddy shell",
            "Work directory: D:/WorkBuddy, all code/output here",
            "Encoding fixed: mindcore-memory uses utf-8 for mixed CN/EN",
            "User wants AI to execute not reason, concise communication",
        ],
    }

    store_ids = {}
    for cat, items in categories.items():
        sid = f"SESSION_{cat.upper()}_PANORAMA"
        for i, content in enumerate(items):
            imp = 4 if cat in ("bug", "habit") else (3 if cat == "project" else 2)
            mid = eng.store(
                content=content,
                importance=imp,
                tags=[cat, f"test_{i}"],
                session_id=sid,
                confidence=0.8 + i * 0.02,
                source="agent",
            )
            store_ids.setdefault(cat, []).append(mid)

    # Fill to 200 with synthetic entries
    topics = ["performance", "security", "testing", "refactor", "architecture",
              "database", "network", "ml", "config", "monitoring"]
    for i in range(200 - 20):
        topic = topics[i % len(topics)]
        eng.store(
            f"[{topic}] Test memory #{i+1}: Details about {topic}. "
            f"Key metric: {i*3.14159:.2f}, status code: {i%500}. "
            f"Project: mindcore-memory-mcp v0.1.9",
            importance=(i % 4) + 1,
            tags=[topic, f"fill_{i//20}"],
            session_id=f"SESSION_FILL_{i//50}",
            confidence=0.5 + (i % 50) / 100,
        )

    stats = eng.get_stats()
    check(stats["total_memories"] == 200, f"total=200 (actual={stats['total_memories']})")
    check(len(stats["by_importance"]) == 4, "4 importance levels")
    check(stats["avg_confidence"] > 0.5, f"avg confidence > 0.5 (actual={stats['avg_confidence']:.2f})")
    print(f"  Distribution: {stats['by_importance']}")
    print(f"  Total tags: {stats['tag_count']}")

    # ======================================================================
    # PHASE 3: Multi-dimension semantic recall
    # ======================================================================
    print("\n-- Phase 3: Multi-dimension recall --")

    queries = {
        "bug tag truncation memory": ("bug", 3),
        "understand first then act": ("habit", 3),
        "ZeroDao triple separation architecture": ("project", 3),
        "Lao Hei user identity": ("user", 3),
        "performance optimization": ("performance", 1),
        "security audit": ("security", 1),
    }

    for query, (expected_cat, min_results) in queries.items():
        results = eng.recall(query, limit=10)
        check(len(results) >= min_results,
              f"query '{query}' returns >= {min_results} (actual={len(results)})")
        if results:
            print(f"    top: [{results[0].relevance_score:.4f}] {results[0].snippet[:60]}...")

    # Empty query
    check(eng.recall("", limit=5) == [], "empty query returns []")

    # Tag filter
    tag_results = eng.recall("memory", tags=["bug"], limit=5)
    check(len(tag_results) > 0, f"tag filter 'bug' returns results (actual={len(tag_results)})")
    for r in tag_results:
        check("bug" in r.memory.tags, f"tag filtered result has 'bug': {r.memory.tags}")

    # Session isolation
    for cat in ["bug", "habit", "project", "user"]:
        sid = f"SESSION_{cat.upper()}_PANORAMA"
        results = eng.recall("memory", session_id=sid, limit=30)
        check(len(results) > 0, f"session {sid} isolation ({len(results)} results)")
        for r in results:
            check(r.memory.session_id == sid, f"session matched: {r.memory.session_id}")

    # ======================================================================
    # PHASE 4: Context Window
    # ======================================================================
    print("\n-- Phase 4: Context Window --")

    ctx_small = eng.get_context_window("bug", max_tokens=200)
    check(len(ctx_small) > 0, "bug context not empty")
    check(len(ctx_small) < 1000, f"token limit effective, chars={len(ctx_small)}")

    ctx_large = eng.get_context_window("test memory", max_tokens=8000)
    check(len(ctx_large) > 0, "large window not empty")
    print(f"  small window: {len(ctx_small)} chars")
    print(f"  large window: {len(ctx_large)} chars")

    # Chinese query
    ctx_cn = eng.get_context_window("user identity Lao Hei", max_tokens=500)
    check(len(ctx_cn) > 0, "Chinese query context not empty")

    # ======================================================================
    # PHASE 5: Confidence update + atomic persistence
    # ======================================================================
    print("\n-- Phase 5: Confidence update + persistence --")

    sample_id = store_ids["bug"][0]
    old_conf = eng._memories[sample_id].confidence
    check(eng.update_confidence(sample_id, 0.99), "update_confidence returns True")
    check(eng._memories[sample_id].confidence == 0.99,
          f"confidence updated: {old_conf} -> {eng._memories[sample_id].confidence}")

    fake_id = "nonexistent-id-12345"
    check(not eng.update_confidence(fake_id, 0.5), "non-existent ID returns False")

    # Boundary values
    check(eng.update_confidence(sample_id, 0.0), "boundary confidence=0")
    check(eng._memories[sample_id].confidence == 0.0, "confidence set to 0")
    check(eng.update_confidence(sample_id, 1.5), "boundary >1 auto clamp")
    check(eng._memories[sample_id].confidence == 1.0, "clamped to 1.0")
    check(eng.update_confidence(sample_id, -0.5), "boundary <0 auto clamp")
    check(eng._memories[sample_id].confidence == 0.0, "clamped to 0.0")
    eng.update_confidence(sample_id, 0.85)  # restore

    # Persistence: reload and verify
    eng2 = MemoryEngine(storage_path=TEST_DIR, encrypt_key=ENCRYPT_KEY)
    check(sample_id in eng2._memories, "sample_id present after reload")
    check(eng2._memories[sample_id].confidence == 0.85, f"confidence persisted (actual={eng2._memories[sample_id].confidence})")
    check(eng2.get_stats()["total_memories"] == 200,
          f"total consistent after reload (actual={eng2.get_stats()['total_memories']})")

    # ======================================================================
    # PHASE 6: Tag system deep validation
    # ======================================================================
    print("\n-- Phase 6: Tag system --")

    # Dedup
    mid1 = eng.store(content="Tag dedup test A", tags=["a", "A", "a", "b"], importance=2)
    mem1 = eng._memories[mid1]
    check(len(mem1.tags) == 2, f"dedup: 2 tags (actual={len(mem1.tags)}): {mem1.tags}")
    check("a" in mem1.tags and "b" in mem1.tags, "correct dedup content")

    # Truncation
    long_tag = "x" * 250
    mid2 = eng.store(content="Tag truncation test", tags=[long_tag], importance=1)
    mem2 = eng._memories[mid2]
    check(all(len(t) <= 100 for t in mem2.tags),
          f"all tags <= 100 chars (max={max(len(t) for t in mem2.tags)})")

    # None/empty handling
    mid3 = eng.store(content="Tag None/empty test", tags=["valid", None, "  ", ""], importance=2)
    mem3 = eng._memories[mid3]
    check("valid" in mem3.tags, "valid tag kept")
    check(len(mem3.tags) == 1, f"None/empty removed (actual={len(mem3.tags)})")

    # ======================================================================
    # PHASE 7: Content dedup merge
    # ======================================================================
    print("\n-- Phase 7: Content Dedup --")

    dup_content = "Dedup test: this is the exact same memory content, should merge"
    mid_a = eng.store(content=dup_content, importance=2, confidence=0.5, tags=["first"])
    count_before = eng.get_stats()["total_memories"]

    mid_b = eng.store(content=dup_content, importance=4, confidence=0.9, tags=["second"])
    check(mid_b == mid_a, f"duplicate returns same ID: {mid_a} == {mid_b}")
    check(eng.get_stats()["total_memories"] == count_before, f"count unchanged (actual={eng.get_stats()['total_memories']})")

    mem_merged = eng._memories[mid_a]
    check(mem_merged.importance == 4, f"merged to highest importance=4 (actual={mem_merged.importance})")
    check(mem_merged.confidence == 0.9, f"merged to highest confidence=0.9 (actual={mem_merged.confidence})")
    check("first" in mem_merged.tags and "second" in mem_merged.tags, "both tag sets retained")
    check(mem_merged.access_count >= 1, f"access_count incremented (actual={mem_merged.access_count})")

    # ======================================================================
    # PHASE 8: Delete + idempotency
    # ======================================================================
    print("\n-- Phase 8: Delete + idempotency --")

    to_del = eng.store(content="To be deleted", importance=1, tags=["delete_me"])
    count_before_del = eng.get_stats()["total_memories"]
    check(eng.delete(to_del), "delete returns True")
    check(eng.get_stats()["total_memories"] == count_before_del - 1, "count decreased by 1")

    # Idempotent delete
    check(not eng.delete(to_del), "re-delete returns False")
    check(eng.get_stats()["total_memories"] == count_before_del - 1, "re-delete no data corruption")

    # Non-existent ID
    check(not eng.delete("nonexistent-deadbeef-cafe"), "non-existent ID returns False")

    # Reload check
    eng3 = MemoryEngine(storage_path=TEST_DIR, encrypt_key=ENCRYPT_KEY)
    check(to_del not in eng3._memories, "delete persisted after reload")

    # ======================================================================
    # PHASE 9: Input validation / encoding safety
    # ======================================================================
    print("\n-- Phase 9: Input validation & encoding --")

    # Pure Chinese
    mid_cn = eng.store(content="Chinese memory test: hello world Ni Hao Shi Jie", importance=3, tags=["chinese", "test"])
    mem_cn = eng._memories[mid_cn]
    check("Ni Hao Shi Jie" in mem_cn.content, "Chinese content stored correctly")

    # Mixed CN/EN
    mid_mix = eng.store(content="Mixed: English with some Chinese characters and symbols.", importance=2)
    mem_mix = eng._memories[mid_mix]
    check("English" in mem_mix.content and "Chinese" in mem_mix.content, "mixed CN/EN stored")

    # Special characters
    mid_sp = eng.store(content="Special: <= >= != + - * / # @ $ % & * !", importance=2, tags=["special"])
    mem_sp = eng._memories[mid_sp]
    check("#" in mem_sp.content and "!" in mem_sp.content, "special chars stored")

    # Oversized content rejection
    try:
        eng.store(content="x" * 200_000, importance=2)
        check(False, "oversized content should be rejected")
    except ValueError as e:
        check("exceeds maximum length" in str(e).lower(), f"oversized rejected: {str(e)[:80]}")

    # Empty content rejection
    try:
        eng.store(content="   ", importance=2)
        check(False, "empty content should be rejected")
    except ValueError:
        check(True, "empty content rejected")

    # Non-string rejection
    try:
        eng.store(content=12345, importance=2)
        check(False, "non-string should be rejected")
    except TypeError as e:
        check("must be a string" in str(e), f"non-string rejected: {str(e)[:60]}")

    # session_id validation
    check(eng._validate_session_id("valid_session_123") == "valid_session_123", "valid session_id")
    check(eng._validate_session_id(None) is None, "None session_id")
    check(eng._validate_session_id("  ") is None, "blank session_id")

    try:
        eng._validate_session_id("x" * 200)
        check(False, "too long session_id should be rejected")
    except ValueError:
        check(True, "too long session_id rejected")

    try:
        eng._validate_session_id("bad session!")
        check(False, "invalid chars session_id should be rejected")
    except ValueError:
        check(True, "invalid chars session_id rejected")

    # ======================================================================
    # PHASE 10: Encryption verification
    # ======================================================================
    print("\n-- Phase 10: Encryption --")

    with open(eng.memory_file, "r", encoding="utf-8") as f:
        first_line = f.readline()
    check("ENC:" in first_line, f"JSONL content encrypted (ENC: prefix)")

    # Reload both at the same time for fair comparison
    eng_reload_enc = MemoryEngine(storage_path=TEST_DIR, encrypt_key=ENCRYPT_KEY)
    eng_reload_noenc = MemoryEngine(storage_path=TEST_DIR)  # no encrypt_key
    check(eng_reload_noenc.get_stats()["total_memories"] == eng_reload_enc.get_stats()["total_memories"],
          f"no-key engine loads same count ({eng_reload_noenc.get_stats()['total_memories']})")

    # ======================================================================
    # PHASE 11: Eviction capacity limit
    # ======================================================================
    print("\n-- Phase 11: Eviction --")

    small_path = os.path.join(TEST_DIR, "small")
    small_eng = MemoryEngine(storage_path=small_path, max_memories=20)
    for i in range(25):
        small_eng.store(f"Evict test #{i}: low importance, will be evicted", importance=1, tags=["evict"])

    stats_small = small_eng.get_stats()
    check(stats_small["total_memories"] <= small_eng.max_memories,
          f"eviction limit <= {small_eng.max_memories} (actual={stats_small['total_memories']})")

    # High importance preserved
    small_eng.store(content="Important memory, must be kept", importance=4, tags=["critical", "keep"])
    critical_in = any(m.importance == 4 for m in small_eng._memories.values())
    check(critical_in, "high importance memory survived eviction")

    # No zombie revival
    small_eng2 = MemoryEngine(storage_path=small_path)
    check(small_eng2.get_stats()["total_memories"] <= 20,
          f"no zombie revival after reload (actual={small_eng2.get_stats()['total_memories']})")

    # ======================================================================
    # PHASE 12: SLO + Metrics
    # ======================================================================
    print("\n-- Phase 12: SLO + Metrics --")

    # All 6 ops have SLO targets
    expected_ops = ["memory_store", "memory_recall", "memory_context",
                    "memory_update_confidence", "memory_delete", "memory_stats"]
    for op in expected_ops:
        check(op in SLO_TARGETS, f"SLO defined: {op}")
        check(get_slo_target(op, "p95") > 0, f"{op} p95 target > 0")
        check(get_slo_target(op, "p99") > 0, f"{op} p99 target > 0")

    # Undefined SLO op returns 0
    check(get_slo_target("nonexistent_op", "p95") == 0.0, "unknown op SLO = 0")

    # Metrics render
    rendered = collector.render()
    check("mindcore_uptime_seconds" in rendered, "uptime metric present")
    check("mindcore_memories_total" in rendered, "memories_total metric present")
    check("# HELP" in rendered, "HELP line present")
    check("# TYPE" in rendered, "TYPE line present")

    lines = rendered.strip().split("\n")
    check(len(lines) >= 10, f"metrics lines >= 10 (actual={len(lines)})")
    check("_bucket" in rendered or "latency_seconds" in rendered, "histogram buckets present")

    # Concurrency safety: multi-threaded metrics writes
    def _concurrent_record():
        for _ in range(100):
            collector.record_success("store")
            collector.record_latency("store", 0.001)

    threads = [threading.Thread(target=_concurrent_record) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    check(True, "concurrent metrics writes no crash")

    store_total = collector._counters.get("mindcore_store_total", 0)
    check(store_total >= 1000, f"concurrent store_total >= 1000 (actual={store_total})")

    # ======================================================================
    # PHASE 13: Circuit Breaker state machine
    # ======================================================================
    print("\n-- Phase 13: Circuit Breaker --")

    cb = CircuitBreaker(name="test_cb", failure_threshold=3, recovery_timeout=0.5)

    # CLOSED -> OPEN (force 3 failures, catch each)
    def always_fail():
        raise RuntimeError("injected failure")

    for i in range(3):
        try:
            cb.call(always_fail)
        except RuntimeError:
            pass
    check(cb.state == CircuitState.OPEN, f"3 failures -> OPEN (state={cb.state.value})")

    # OPEN blocks
    try:
        cb.call(lambda: 42)
        check(False, "OPEN should block")
    except CircuitOpenError:
        check(True, "OPEN correctly blocks")

    # Fallback works
    result = cb.call(lambda: 42, fallback=lambda: 99)
    check(result == 99, "OPEN fallback works")

    # Recovery -> CLOSED
    time.sleep(0.6)
    result = cb.call(lambda: 42)
    check(result == 42, "HALF_OPEN success returns correct")
    check(cb.state == CircuitState.CLOSED, f"HALF_OPEN success -> CLOSED (state={cb.state.value})")

    # Global singleton
    shared = get_circuit("shared_test", failure_threshold=2)
    shared2 = get_circuit("shared_test")
    check(shared is shared2, "global circuit singleton")

    # ======================================================================
    # PHASE 14: HTTP endpoint simulation
    # ======================================================================
    print("\n-- Phase 14: HTTP endpoints --")

    from mindcore_memory.http_app import create_http_app, _get_engine

    app_noauth = create_http_app()
    check(app_noauth.title == "MindCore Memory MCP", "FastAPI app created (no auth)")

    app_auth = create_http_app(token="secret123")
    check(app_auth is not None, "FastAPI app created (with auth)")

    # Engine singleton
    e1 = _get_engine()
    e2 = _get_engine()
    check(e1 is e2, "engine singleton works")

    # Routes
    routes = [r.path for r in app_noauth.routes]
    check("/health" in routes, "route /health")
    check("/metrics" in routes, "route /metrics")
    check("/stats" in routes, "route /stats")
    check("/mcp" in routes, "route /mcp")

    # CORS middleware
    cors_mw = [mw for mw in app_noauth.user_middleware if mw.cls.__name__ == "CORSMiddleware"]
    check(len(cors_mw) > 0, "CORS middleware present")

    # ======================================================================
    # PHASE 15: Retry mechanism
    # ======================================================================
    print("\n-- Phase 15: Retry --")

    call_count = [0]

    @retry_with_backoff(max_retries=2, base_delay=0.01)
    def retry_ok():
        call_count[0] += 1
        return "ok"

    result = retry_ok()
    check(result == "ok", "no exception: return directly")
    check(call_count[0] == 1, f"no retry on success (calls={call_count[0]})")

    call_count2 = [0]

    @retry_with_backoff(max_retries=2, base_delay=0.01, retryable=(RuntimeError,))
    def retry_transient():
        call_count2[0] += 1
        raise RuntimeError("transient")

    try:
        retry_transient()
        check(False, "exhausted retries should raise")
    except RuntimeError:
        check(call_count2[0] == 3, f"3 retries exhausted (calls={call_count2[0]})")

    # Non-retryable exception
    call_count3 = [0]

    @retry_with_backoff(max_retries=2, base_delay=0.01, retryable=(RuntimeError,))
    def retry_fatal():
        call_count3[0] += 1
        raise ValueError("not retryable")

    try:
        retry_fatal()
        check(False, "non-retryable should raise immediately")
    except ValueError:
        check(call_count3[0] == 1, f"non-retryable: no retry (calls={call_count3[0]})")

    # ======================================================================
    # Final cross-validation
    # ======================================================================
    print("\n-- Final: Cross-validation --")

    stats_final = eng.get_stats()
    check(stats_final["total_memories"] >= 200, f"final total >= 200 (actual={stats_final['total_memories']})")
    check(stats_final["by_importance"][4] >= 10, f"Critical memories >= 10 (actual={stats_final['by_importance'][4]})")

    # Session isolation: bug query in user session returns only user-session or
    # sessionless (None) entries — never entries from other sessions.
    bug_in_user = eng.recall("memory bug", session_id="SESSION_USER_PANORAMA", limit=10)
    foreign_sessions = [r for r in bug_in_user
                        if r.memory.session_id is not None
                        and r.memory.session_id != "SESSION_USER_PANORAMA"]
    check(len(foreign_sessions) == 0,
          f"no foreign session leaks (foreign={len(foreign_sessions)}, total_results={len(bug_in_user)})")
    has_bug_tags = any("bug" in r.memory.tags for r in bug_in_user)
    check(not has_bug_tags, f"user session results have no bug tags (found={has_bug_tags})")

    # Context window completeness
    ctx_final = eng.get_context_window("all important matters", max_tokens=3000)
    check(len(ctx_final) > 500, f"full context window > 500 chars (actual={len(ctx_final)})")

    # ======================================================================
    # Report
    # ======================================================================
    print("\n" + "=" * 72)
    pct = 100 * PASS[0] / (PASS[0] + FAIL[0]) if (PASS[0] + FAIL[0]) > 0 else 0
    print(f"  Panorama Result: {PASS[0]} PASS / {FAIL[0]} FAIL")
    print(f"  Pass Rate: {PASS[0]}/{PASS[0]+FAIL[0]} ({pct:.1f}%)")
    print("=" * 72)

    # Cleanup
    shutil.rmtree(TEST_DIR, ignore_errors=True)

    if FAIL[0] > 0:
        print(f"\n  WARNING: {FAIL[0]} failures need fixing")
        return 1
    else:
        print("\n  ALL PANORAMA TESTS PASSED -- PRODUCTION-READY")
        return 0


if __name__ == "__main__":
    sys.exit(main())
