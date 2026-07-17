"""
End-to-end real world test: inject memories, test recall flow.
Simulates actual usage patterns — bugs, preferences, project context.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mindcore_memory.memory_engine import MemoryEngine
import time, json

# Use a clean test storage
TEST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tmp_e2e")
import shutil
shutil.rmtree(TEST_DIR, ignore_errors=True)

eng = MemoryEngine(storage_path=TEST_DIR)
print("=" * 60)
print("PHASE 0: 空库状态")
print("=" * 60)
print(json.dumps(eng.get_stats(), indent=2))

# =========================================================================
# PHASE 1: 注入——今天发现的真实错误 (Critical, SESSION_BUGS)
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 1: 注入「今天老犯的错误」（4 条 Critical Bug）")
print("=" * 60)

bug_ids = {}
bug_session = "SESSION_BUGS_2026-06-14"

bugs = [
    ("tag_no_truncation", "发现 bug：store() 方法未截断 tag 到 100 字符。from_dict() 里做了但 store() 直接用 raw tags 构建 MemoryEntry，会导致超长 tag 写入磁盘。已修复：在 store() 加入 [:100] + strip 清洗。", ["bug", "tag", "sanitize"]),
    ("tag_no_dedup", "发现 bug：store() 方法未对 tag 去重。传入 ['a','a','b','a'] 会原样存储 4 个重复 tag。已修复：加入 seen_tags set 去重逻辑。", ["bug", "tag", "sanitize"]),
    ("importance_ranking_faiss", "发现：test_high_importance_ranks_higher 在纯 BM25 模式下失败。语义搜索需要 sentence-transformers，否则 'important note' 无法匹配 'Critical fact: server is down'。已标记为 skip（需 FAISS）。", ["bug", "faiss", "test"]),
    ("mcp_config_stale", "发现：run_dev_server.py 指向不存在的 pylib 目录，MCP 连接器启动失败。venv 中有完整依赖。已修复：更新路径指向 .venv/Lib/site-packages。", ["bug", "mcp", "config"]),
]

for i, (tag, content, tags) in enumerate(bugs):
    mid = eng.store(
        content=content,
        importance=4,  # Critical
        tags=tags,
        session_id=bug_session,
        confidence=0.95,
        source="agent"
    )
    bug_ids[tag] = mid
    print(f"  [{i+1}] Stored: {tag} → {mid}")

# =========================================================================
# PHASE 2: 注入——被多次纠正的"老习惯" (Critical, SESSION_HABITS)
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 2: 注入「反复纠正的老习惯」（5 条 Critical）")
print("=" * 60)

habits_session = "SESSION_HABITS_2026-06-14"

habits = [
    ("先认知后动手是铁律。不是知识，是认知——知识是别人告诉你的，认知是自己筛出来的。任何任务到手，先调研→判断对错→筛掉错的→整合最优→再动手。急躁的直接后果就是返工。", ["habit", "workflow", "cognition"]),
    ("大哥纠正过：不要急于动手，先做认知工作。两天里纠正的本质问题，如果在动手前先做认知，大部分都能避免。这条永远记住。", ["habit", "大哥", "correction"]),
    ("代码写完必须逐行带行号分析，用 ✅/⚠️ 标注验证状态。不能只给结论不给依据。", ["habit", "code_review", "verification"]),
    ("回答风格必须简洁直接。不需要冗长解释，用户要的是结果不是过程。中文优先。", ["habit", "style", "short"]),
    ("不要自作主张扩展架构。已经被纠正过——零道门和小脑引擎之间不需要桥接层，它们是并行路线。做减法不是加法。", ["habit", "architecture", "大哥"]),
]

for i, (content, tags) in enumerate(habits):
    mid = eng.store(
        content=content,
        importance=4,  # Critical
        tags=tags,
        session_id=habits_session,
        confidence=0.9,
        source="agent"
    )
    print(f"  [{i+1}] Stored habit: {mid}")

# =========================================================================
# PHASE 3: 注入——项目核心事实 (Semantic, SESSION_PROJECTS)
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 3: 注入项目事实（6 条 Semantic）")
print("=" * 60)

proj_session = "SESSION_PROJECTS_2026-06-14"

projects = [
    ("零道门 v4.3.3 三分离架构：引擎≠骨架≠黑金9.1。三循环机制，TIC 为骨架层，经历轨迹库为个体专属，边界库独立。", ["project", "零道门", "architecture"]),
    ("Bee Memory v5.x：五维记忆池(EXP/TRJ/COG/BND/CTX) + 虚空引擎(碰撞择优) + BND 版本链。当前 v1.4.0+，MCP Server 已上线，5 个工具。", ["project", "bee_memory", "architecture"]),
    ("小脑引擎 v4.0：安全壳/中心化架构，与零道门构成两条并行 AI 安全路线。已完成 GitHub 开源发布，含英文 README.md。", ["project", "小脑引擎", "github"]),
    ("VSOS Guard v0.7.0：纯规则安全插件，编码层 14/14 拦截率。定位为 AI 工具安全适配器，与零道门完全独立。", ["project", "vsos", "security"]),
    ("mindcore-memory-mcp：层级记忆 STM→LTM→Deduction，SQLite+FAISS 混合检索。GitHub 开源 + PyPI 发布 v0.1.8，6 个 MCP 工具。", ["project", "mindcore", "opensource"]),
    ("确信性路由+过滤管道替代 RRF v2.0：时间/COG 噪声信号污染 BM25 结果。新方案确定性更强，无调参依赖。", ["project", "mindcore", "retrieval"]),
]

for i, (content, tags) in enumerate(projects):
    mid = eng.store(
        content=content,
        importance=3,  # Semantic
        tags=tags,
        session_id=proj_session,
        confidence=0.85,
        source="agent"
    )
    print(f"  [{i+1}] Stored project: {mid}")

# =========================================================================
# PHASE 4: 注入——用户偏好 (Working, SESSION_USER)
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 4: 注入用户偏好（4 条 Working）")
print("=" * 60)

user_session = "SESSION_USER_2026-06-14"

user_prefs = [
    ("用户自称老黑(Lao Hei)，应尊称大哥。沟通风格直接、自信、善用生动类比。要求 AI 执行而非推理。", ["user", "identity", "大哥"]),
    ("用户邮箱 1410770089@qq.com。AI 身体为受限外部壳 WorkBuddy。该 AI 具备文件、命令、浏览器等本地控制能力，但严禁自主交易或控制金融账户。", ["user", "contact", "security"]),
    ("工作日 D 盘为重点。D:\\WorkBuddy\\2026-06-14-00-55-34 为当前工作目录。所有代码、测试、产出物存此。", ["user", "workspace", "path"]),
    ("编码乱码问题已修复：mindcore-memory 中英文混合存储使用 utf-8 编码，确保中文 content 不乱码。", ["user", "encoding", "fix"]),
]

for i, (content, tags) in enumerate(user_prefs):
    mid = eng.store(
        content=content,
        importance=2,  # Working
        tags=tags,
        session_id=user_session,
        confidence=0.9,
        source="user"
    )
    print(f"  [{i+1}] Stored pref: {mid}")

# =========================================================================
# PHASE 5: 统计——看总览
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 5: 记忆库总览")
print("=" * 60)
stats = eng.get_stats()
print(json.dumps(stats, indent=2))
print(f"\n  Total: {stats['total_memories']} 条记忆, {stats['tag_count']} 个标签")
print(f"  By importance: {stats['by_importance']}")
print(f"  FAISS available: {stats['faiss_available']}")

# =========================================================================
# PHASE 6: 召回验证——各种维度
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 6: 召回验证（多维度查询）")
print("=" * 60)

test_queries = [
    ("今天发现的 bug", None, "🔍 关键词召回：bug"),
    ("tag 截断和去重", None, "🔍 语义召回：tag 安全"),
    ("先认知后动手", None, "🔍 老习惯召回"),
    ("零道门架构", None, "🔍 项目架构召回"),
    ("用户是怎么称呼自己的", None, "🔍 用户偏好召回"),
]

for query, tag_filter, label in test_queries:
    results = eng.recall(query, tags=tag_filter, limit=5)
    print(f"\n{label} query='{query}'")
    print(f"  Results: {len(results)}")
    for r in results:
        print(f"  [{r.relevance_score:.3f}|conf={r.confidence:.2f}|★{r.memory.importance}] {r.snippet}")

# =========================================================================
# PHASE 7: Session 隔离测试
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 7: Session 隔离与衔接")
print("=" * 60)

sessions = [bug_session, habits_session, proj_session, user_session]
for sid in sessions:
    results = eng.recall("memory", session_id=sid, limit=2)
    if results:
        tag_sample = results[0].memory.tags[:2]
        print(f"  {sid}: {len(results)}+ 条记忆, 标签样例: {tag_sample}")

# Session 交叉查询：查今天错误的时候不该出现项目事实
results_bugs = eng.recall("bug", session_id=bug_session, limit=5)
results_all = eng.recall("bug", limit=5)
print(f"\n  Session 过滤: bug 会话内 {len(results_bugs)} 条 vs 全库 {len(results_all)} 条")
for r in results_all:
    print(f"    [{r.relevance_score:.3f}] session={r.memory.session_id} {r.snippet[:60]}")

# =========================================================================
# PHASE 8: Context Window 构建
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 8: Context Window — LLM 输入")
print("=" * 60)

ctx_queries = [
    ("今天写了哪些代码，有什么 bug", "现在需要做什么"),
    ("用户老黑有什么习惯需要遵守", "对话风格和规则"),
]

for query, task in ctx_queries:
    ctx = eng.get_context_window(query=query, max_tokens=1500, session_id=None)
    print(f"\n📋 Task: {task}")
    print(f"  Query: {query}")
    print(f"  Context length: {len(ctx)} chars")
    # Show first 200 chars
    print(f"  Preview: {ctx[:300]}...")

# =========================================================================
# PHASE 9: 置信度更新 + 持久化验证
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 9: 置信度更新 + 持久化验证")
print("=" * 60)

# Update a bug memory confidence (we fixed it, so lower confidence might apply)
sample_id = bug_ids.get("tag_no_truncation")
if sample_id:
    old_mem = eng._memories.get(sample_id)
    print(f"  Before: {sample_id} confidence={old_mem.confidence}")
    eng.update_confidence(sample_id, 0.5)  # We found the fix, bug is less critical now
    updated = eng._memories[sample_id]
    print(f"  After:  confidence={updated.confidence}")

# Verify persistence: reload engine and check
eng2 = MemoryEngine(storage_path=TEST_DIR)
stats2 = eng2.get_stats()
print(f"  Reloaded: total={stats2['total_memories']}, avg_conf={stats2['avg_confidence']}")
for mid in bug_ids.values():
    if mid in eng2._memories:
        mem = eng2._memories[mid]
        print(f"  ✓ Persisted: {mid[:8]}... conf={mem.confidence:.2f}")
    else:
        print(f"  ✗ LOST: {mid[:8]}...")

# =========================================================================
# PHASE 10: Tag 系统验证
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 10: Tag 系统 — 去重 + 截断验证")
print("=" * 60)

# Test tag dedup and truncation
mid_test = eng.store(
    content="tag 测试内容：验证去重和截断功能",
    tags=["bug", "bug", "BUG", "a" * 200, "valid_tag"],
    importance=2,
)
mem = eng._memories[mid_test]
print(f"  Tags: {mem.tags}")
print(f"  Tag count: {len(mem.tags)} (expected <=4: bug, valid_tag, and truncated 'a'*100)")
assert len(mem.tags) <= 4, f"Too many tags: {len(mem.tags)}"
assert "bug" in mem.tags
assert "valid_tag" in mem.tags
# Check truncation
for t in mem.tags:
    assert len(t) <= 100, f"Tag too long: {len(t)} chars"
print("  ✅ Tag 去重 + 截断验证通过")

# =========================================================================
# FINAL STATS
# =========================================================================
print("\n" + "=" * 60)
print("PHASE 11: 最终状态")
print("=" * 60)
final = eng.get_stats()
print(json.dumps(final, indent=2))

# Cleanup
shutil.rmtree(TEST_DIR, ignore_errors=True)
print("\n🎉 ALL E2E TESTS COMPLETED")
