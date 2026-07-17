"""
MindCore Memory Engine - v0.1.9 Production-Hardened Edition.

Hybrid search: BM25 keyword + FAISS semantic embedding = best precision + recall.
Security: instance-level FAISS, content limits, input validation, Fernet encryption.
Reliability: SLO tracking, circuit breaker, retry, BM25 degradation.
"""
from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import structlog

from .slo import track_latency
from .circuit_breaker import get_circuit
from .retry import retry_with_backoff

logger = structlog.get_logger()

# Circuit breakers for FAISS + embedding operations
_circuit_faiss = get_circuit("faiss_index", failure_threshold=3, recovery_timeout=60.0)
_circuit_embed = get_circuit("embedding", failure_threshold=3, recovery_timeout=60.0)

# ---------------------------------------------------------------------------
# Embedding provider (class-level shared cache — model is read-only & expensive)
# ---------------------------------------------------------------------------
class _EmbedderCache:
    """Thread-safe embedder cache shared across MemoryEngine instances."""
    _embedder = None
    _dim = None
    _load_failed = False

    @classmethod
    def get(cls) -> tuple[Optional[Any], Optional[int]]:
        if cls._embedder is not None:
            return cls._embedder, cls._dim
        if cls._load_failed:
            return None, None
        try:
            from sentence_transformers import SentenceTransformer
            import os
            model_path = os.environ.get("MINDCORE_MODEL_PATH")
            if model_path and os.path.isdir(model_path):
                model_name_or_path = model_path
                logger.info("embedder_loading_local", path=model_path)
            else:
                model_name_or_path = "all-MiniLM-L6-v2"
                logger.info("embedder_loading_hub")
            model = SentenceTransformer(model_name_or_path, device="cpu")
            cls._embedder = model
            cls._dim = model.get_sentence_embedding_dimension()
            logger.info("embedder_loaded", dim=cls._dim)
            return cls._embedder, cls._dim
        except Exception as e:
            cls._load_failed = True
            logger.error("embedder_load_failed_critical", error=str(e))
            return None, None


@retry_with_backoff(max_retries=3, base_delay=0.1)
def _embed_texts(texts: list[str]) -> Optional[list[list[float]]]:
    embedder, dim = _EmbedderCache.get()
    if embedder is None:
        return None
    try:
        embeddings = embedder.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.tolist()
    except Exception as e:
        logger.warning("embed_texts_failed", error=str(e))
        return None


# ---------------------------------------------------------------------------
# Tokenizer (English + Chinese, jieba optional)
# ---------------------------------------------------------------------------
_JIEBA_AVAILABLE = False
try:
    import jieba
    _JIEBA_AVAILABLE = True
except ImportError:
    pass


def _has_chinese(text: str) -> bool:
    """Check if text contains CJK characters."""
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff' or '\u3400' <= ch <= '\u4dbf':
            return True
    return False


def _tokenize(text: str) -> list[str]:
    """Tokenize text — jieba for Chinese, space-split for English."""
    if _JIEBA_AVAILABLE and _has_chinese(text):
        tokens = list(jieba.cut(text))
        return [t.lower().strip() for t in tokens if t.strip() and len(t.strip()) > 1]
    return [w.lower() for w in text.split() if w]


def _bm25_score(query_tokens: list[str], doc_tokens: list[str], doc_len: int, avgdl: float) -> float:
    k1 = 1.5
    b = 0.75
    score = 0.0
    word_freq = {}
    for w in doc_tokens:
        word_freq[w] = word_freq.get(w, 0) + 1
    for qw in query_tokens:
        f = word_freq.get(qw, 0)
        if f == 0:
            continue
        numerator = f * (k1 + 1)
        denominator = f + k1 * (1 - b + b * doc_len / max(avgdl, 1.0))
        score += numerator / max(denominator, 0.01)
    return score


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
class MemoryImportance(Enum):
    EPISODIC = 1
    WORKING = 2
    SEMANTIC = 3
    CRITICAL = 4


@dataclass
class MemoryEntry:
    id: str
    content: str
    importance: int
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    access_count: int = 0
    session_id: Optional[str] = None
    confidence: float = 0.5
    source: str = "agent"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "importance": self.importance,
            "tags": self.tags,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "session_id": self.session_id,
            "confidence": self.confidence,
            "source": self.source,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        # Validate and coerce types to prevent injection (H-004 fix)
        try:
            data["importance"] = max(1, min(4, int(data.get("importance", 2))))
        except (TypeError, ValueError):
            data["importance"] = 2
        try:
            data["confidence"] = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
        except (TypeError, ValueError):
            data["confidence"] = 0.5
        try:
            data["access_count"] = max(0, int(data.get("access_count", 0)))
        except (TypeError, ValueError):
            data["access_count"] = 0
        # Sanitize string fields
        if isinstance(data.get("content"), str) and len(data["content"]) > 100000:
            data["content"] = data["content"][:100000]
        if not isinstance(data.get("tags"), list):
            data["tags"] = []
        else:
            data["tags"] = [str(t)[:100] for t in data["tags"] if t is not None]
        if not isinstance(data.get("metadata"), dict):
            data["metadata"] = {}
        if "last_accessed" not in data:
            data["last_accessed"] = data.get("created_at", datetime.now(timezone.utc).isoformat())
        allowed_keys = {
            "id", "content", "importance", "tags", "created_at", "last_accessed",
            "access_count", "session_id", "confidence", "source", "metadata",
        }
        filtered = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered)


@dataclass
class RetrievalResult:
    memory: MemoryEntry
    relevance_score: float
    confidence: float
    snippet: str


# ---------------------------------------------------------------------------
# Memory Engine
# ---------------------------------------------------------------------------
class MemoryEngine:
    """
    Hybrid search memory engine.
    Score = 0.40 * BM25 keyword + 0.50 * FAISS semantic + 0.05 * importance + 0.05 * recency.
    """

    MAX_CONTENT_LENGTH = 100_000  # Prevent disk/memory DoS (C-002 fix)

    # Dangerous system paths that storage should never target (M-001 fix)
    _FORBIDDEN_PATHS = {
        "/", "/etc", "/boot", "/sys", "/proc", "/dev", "/run",
        "/var/log", "/var/run", "/tmp",  # Unix
        "C:\\Windows", "C:\\Windows\\System32",  # Windows
    }

    def __init__(
        self,
        storage_path: Optional[str] = None,
        max_memories: int = 10000,
        recall_limit: int = 20,
        encrypt_key: Optional[bytes] = None,
        bnd_manager=None,
    ):
        if storage_path:
            self.storage_path = Path(storage_path).resolve()
        else:
            self.storage_path = (Path.home() / ".mindcore" / "memory").resolve()

        # M-001 fix: validate storage path is safe
        self._validate_storage_path()

        self.max_memories = max_memories
        self.recall_limit = recall_limit
        self._memories: dict[str, MemoryEntry] = {}
        self._index: dict[str, set] = {}  # tag -> set of memory ids
        self._lock = threading.Lock()  # Concurrency safety for HTTP mode
        self._faiss_dirty = True
        # Per-instance FAISS state — eliminates cross-instance data leak (C-001 fix)
        self._faiss_index = None
        self._faiss_id_map: list[str] = []
        self._faiss_index_type: str = "none"  # "Flat" | "IVF" | "none"

        # L-003 fix: optional Fernet encryption for PII protection
        self._fernet = None
        if encrypt_key:
            from cryptography.fernet import Fernet
            self._fernet = Fernet(encrypt_key)
            logger.info("encryption_enabled")
        self._encrypt_key = encrypt_key

        # BND Boundary Manager (optional 3D balance evaluation)
        self._bnd_manager = bnd_manager

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.storage_path / "memories.jsonl"

        self._load()
        logger.info("memory_engine_initialized", storage_path=str(self.storage_path),
                     count=len(self._memories), encrypted=self._fernet is not None)

    def set_bnd_manager(self, mgr):
        """Inject BND manager; subsequent store() calls auto-execute 3D boundary evaluation."""
        self._bnd_manager = mgr

    def _validate_storage_path(self) -> None:
        """M-001 fix: prevent path traversal into system directories."""
        resolved = str(self.storage_path)
        for forbidden in self._FORBIDDEN_PATHS:
            rp = str(Path(forbidden).resolve())
            if resolved == rp or resolved.startswith(rp + "/") or resolved.startswith(rp + "\\"):
                raise ValueError(
                    f"Storage path '{self.storage_path}' resolves to a protected system "
                    f"directory '{forbidden}'. Please use a safe user directory."
                )
        # Reject relative path traversal via ..
        if ".." in str(self.storage_path):
            # Already resolved, but double-check the resolved path is within a valid root
            home = str(Path.home().resolve())
            cwd = str(Path.cwd().resolve())
            if not (resolved.startswith(home) or resolved.startswith(cwd)):
                raise ValueError(
                    f"Storage path '{self.storage_path}' is outside the home directory. "
                    f"Please use a path under '{home}'."
                )

    # -- persistence ----------------------------------------------------------
    def _load(self) -> None:
        if not self.memory_file.exists():
            return
        count = 0
        dups = 0
        content_dups = 0
        # Track normalized content → best entry for merging
        seen_content: dict[str, str] = {}  # normalized_content → memory_id
        to_remove: set[str] = set()
        with open(self.memory_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        # L-003 fix: decrypt content if encrypted
                        if "content" in data and isinstance(data["content"], str):
                            data["content"] = self._decrypt_content(data["content"])
                        entry = MemoryEntry.from_dict(data)

                        # ID dedup: last line wins, but skip processing (no merge needed)
                        if entry.id in self._memories:
                            dups += 1
                            continue

                        # P2 fix: content dedup — merge entries with identical content
                        norm = entry.content.strip()
                        if norm in seen_content:
                            content_dups += 1
                            best_id = seen_content[norm]
                            best = self._memories[best_id]
                            # Merge: keep highest importance/confidence, sum access counts
                            best.importance = max(best.importance, entry.importance)
                            best.confidence = max(best.confidence, entry.confidence)
                            best.access_count += entry.access_count
                            for tag in entry.tags:
                                if tag not in best.tags:
                                    best.tags.append(tag)
                            to_remove.add(entry.id)
                        else:
                            self._memories[entry.id] = entry
                            seen_content[norm] = entry.id
                            # Rebuild tag index for this entry
                            for tag in entry.tags:
                                self._index.setdefault(tag, set()).add(entry.id)
                            count += 1
                    except Exception as e:
                        logger.warning("failed_to_load_memory", error=str(e))

        # Clean up merged-away entries from index
        for mid in to_remove:
            if mid in self._memories:
                del self._memories[mid]

        self._faiss_dirty = True
        logger.info("memories_loaded", count=count, id_duplicates=dups, content_duplicates=content_dups)

        # P2 fix: auto-compact jsonl if duplicates were found during load
        if dups > 0 or content_dups > 0:
            self._rewrite_jsonl()
            logger.info("jsonl_compacted", removed_duplicates=dups + content_dups)

    def _encrypt_content(self, content: str) -> str:
        """L-003 fix: encrypt content field if Fernet key is configured."""
        if self._fernet is None:
            return content
        return "ENC:" + self._fernet.encrypt(content.encode("utf-8")).decode("ascii")

    def _decrypt_content(self, content: str) -> str:
        """L-003 fix: decrypt content field if prefixed with 'ENC:'."""
        if not content.startswith("ENC:") or self._fernet is None:
            return content
        try:
            return self._fernet.decrypt(content[4:].encode("ascii")).decode("utf-8")
        except Exception:
            logger.warning("decrypt_failed", content_len=len(content))
            return content  # Fall back to raw (may be garbage)

    def _save(self, entry: MemoryEntry) -> None:
        # L-003: encrypt content before writing (if key configured)
        data = entry.to_dict()
        data["content"] = self._encrypt_content(data["content"])
        # Append with fsync — _load handles partial lines gracefully
        import os as _os
        with open(self.memory_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
            f.flush()
            _os.fsync(f.fileno())
        self._faiss_dirty = True

    # -- FAISS (per-instance, no global state — C-001 fix) -------------------
    def _rebuild_faiss_if_needed(self) -> None:
        if not self._faiss_dirty:
            return
        self._ensure_faiss_index()
        self._faiss_dirty = False

    def _ensure_faiss_index(self) -> bool:
        if not self._memories:
            self._faiss_index = None
            self._faiss_id_map = []
            return False

        def _build():
            embeddings = _embed_texts([m.content for m in self._memories.values()])
            if embeddings is None:
                return False
            import faiss
            import numpy as np
            import math
            dim = len(embeddings[0])
            np_embeddings = np.array(embeddings, dtype="float32")
            n = len(np_embeddings)

            # C-003 fix: use IVF for >500 memories, FlatIP for small sets
            if n >= 500:
                nlist = max(4, min(256, int(math.sqrt(n))))
                quantizer = faiss.IndexFlatIP(dim)
                index = faiss.IndexIVFFlat(quantizer, dim, nlist)
                index.train(np_embeddings)
                index.add(np_embeddings)
                index.nprobe = max(1, nlist // 8)
                self._faiss_index_type = "IVF"
                logger.info("faiss_index_built", n=n, dim=dim, index_type="IVF",
                           nlist=nlist, nprobe=index.nprobe)
            else:
                index = faiss.IndexFlatIP(dim)
                index.add(np_embeddings)
                self._faiss_index_type = "Flat"
                logger.info("faiss_index_built", n=n, dim=dim, index_type="Flat")

            self._faiss_index = index
            self._faiss_id_map = list(self._memories.keys())
            return True

        def _faiss_fallback():
            """Degradation: FAISS unavailable → mark as unbuilt, rely on BM25 only."""
            logger.warning("faiss_circuit_open_degraded", reason="BM25-only fallback active")
            self._faiss_index = None
            self._faiss_id_map = []
            return False

        try:
            return _circuit_faiss.call(_build, fallback=_faiss_fallback)
        except Exception as e:
            logger.error("faiss_index_build_failed", error=str(e))
            self._faiss_index = None
            self._faiss_id_map = []
            return False

    def _semantic_search(self, query: str, top_k: int = 50) -> dict[str, float]:
        self._rebuild_faiss_if_needed()
        if self._faiss_index is None or not self._faiss_id_map:
            return {}
        query_emb = _embed_texts([query])
        if query_emb is None:
            return {}
        try:
            import numpy as np
            import faiss
            q = np.array(query_emb, dtype="float32")
            scores, indices = self._faiss_index.search(q, min(top_k, len(self._faiss_id_map)))
            result = {}
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0:
                    continue
                mem_id = self._faiss_id_map[idx]
                result[mem_id] = float(score)
            return result
        except Exception as e:
            logger.warning("semantic_search_failed", error=str(e))
            return {}

    # -- public API -----------------------------------------------------------
    @staticmethod
    def _validate_session_id(session_id: Optional[str]) -> Optional[str]:
        """L-008 fix: validate session_id format."""
        if session_id is None:
            return None
        import re
        session_id = session_id.strip()
        if not session_id:
            return None
        if len(session_id) > 128:
            raise ValueError(f"session_id too long (max 128 chars, got {len(session_id)})")
        if not re.match(r'^[a-zA-Z0-9:_\-]+$', session_id):
            raise ValueError(
                f"session_id contains invalid characters. "
                f"Only alphanumeric, colon, underscore and hyphen allowed."
            )
        return session_id

    @track_latency("memory_store")
    def store(
        self,
        content: str,
        importance: int = 2,
        tags: Optional[list[str]] = None,
        session_id: Optional[str] = None,
        confidence: float = 0.5,
        source: str = "agent",
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        # C-002 fix: reject oversized content to prevent disk DoS
        if not isinstance(content, str):
            raise TypeError(f"content must be a string, got {type(content).__name__}")
        if len(content) > self.MAX_CONTENT_LENGTH:
            raise ValueError(
                f"Content exceeds maximum length of {self.MAX_CONTENT_LENGTH} characters "
                f"(got {len(content)}). Please split into smaller memories."
            )
        if not content.strip():
            raise ValueError("Content cannot be empty")

        # L-008 fix: validate session_id format
        session_id = self._validate_session_id(session_id)

        # Sanitize tags: truncate, deduplicate, strip
        cleaned_tags: list[str] = []
        seen_tags: set[str] = set()
        for t in (tags or []):
            if t is None:
                continue
            s = str(t)[:100].strip()
            if s and s.lower() not in seen_tags:
                cleaned_tags.append(s)
                seen_tags.add(s.lower())

        # P1 fix: content dedup — identical content should merge, not duplicate
        existing_id = self._find_duplicate_content(content, session_id)
        if existing_id is not None:
            with self._lock:
                mem = self._memories[existing_id]
                mem.importance = max(mem.importance, importance)
                mem.confidence = max(mem.confidence, confidence)
                mem.access_count += 1
                mem.last_accessed = datetime.now(timezone.utc).isoformat()
                # Merge new tags
                for tag in cleaned_tags:
                    if tag not in mem.tags:
                        mem.tags.append(tag)
                        self._index.setdefault(tag, set()).add(existing_id)
                self._faiss_dirty = True
                self._rewrite_jsonl()
            logger.info("memory_merged", memory_id=existing_id, importance=mem.importance, confidence=mem.confidence)
            return existing_id

        if len(self._memories) >= self.max_memories:
            self._evict_low_importance()

        with self._lock:
            entry = MemoryEntry(
                id=str(uuid.uuid4()),
                content=content,
                importance=max(1, min(4, importance)),
                tags=cleaned_tags,
                session_id=session_id,
                confidence=confidence,
                source=source,
                metadata=metadata or {},
            )

            self._memories[entry.id] = entry
            for tag in entry.tags:
                self._index.setdefault(tag, set()).add(entry.id)

        # BND auto-evaluation: every memory auto-passes 3D boundary algorithm
        bnd_eval = None
        if self._bnd_manager:
            try:
                bnd_eval = self._bnd_manager.evaluate(
                    content=content,
                    importance=entry.importance,
                    confidence=confidence,
                    tags=entry.tags,
                )
                entry.metadata["bnd_score"] = bnd_eval.bnd_score
                entry.metadata["bnd_accepted"] = bnd_eval.accepted
                entry.metadata["bnd_dimensions"] = bnd_eval.dimensions
                entry.metadata["bnd_balance"] = bnd_eval.balance
                entry.metadata["bnd_anti_chain"] = bnd_eval.anti_chain_triggered
                if not bnd_eval.accepted:
                    logger.info("bnd_rejected", memory_id=entry.id,
                               bnd_score=round(bnd_eval.bnd_score, 3),
                               dimensions=bnd_eval.dimensions)
            except Exception as e:
                logger.warning("bnd_eval_error", error=str(e))

        self._save(entry)
        logger.info("memory_stored", memory_id=entry.id, importance=entry.importance,
                     tags=entry.tags, bnd_accepted=bnd_eval.accepted if bnd_eval else None)
        try:
            from .metrics import get_collector
            c = get_collector(); c.record_success("store") if c else None
            c.set_gauge("memories_total", len(self._memories)) if c else None
        except Exception:
            pass
        return entry.id

    @track_latency("memory_recall")
    def recall(
        self,
        query: str,
        tags: Optional[list[str]] = None,
        session_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[RetrievalResult]:
        limit = limit or self.recall_limit
        limit = max(1, min(limit, 100))  # Hard cap to prevent abuse
        # L-008 fix: validate session_id format
        session_id = self._validate_session_id(session_id)
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        # Semantic search (FAISS)
        semantic_scores = self._semantic_search(query, top_k=limit * 3)

        # BM25 keyword search
        all_mems = list(self._memories.values())
        avg_dl = sum(len(m.content.split()) for m in all_mems) / max(len(all_mems), 1)

        candidates: list[tuple[str, float, MemoryEntry]] = []

        for mem_id, mem in self._memories.items():
            if session_id and mem.session_id and mem.session_id != session_id:
                continue
            if tags and not any(t in mem.tags for t in tags):
                continue

            content_tokens = _tokenize(mem.content)
            bm25 = _bm25_score(query_tokens, content_tokens, len(content_tokens), avg_dl)
            keyword_score = min(bm25 / 10.0, 1.0)

            semantic_score = semantic_scores.get(mem_id, 0.0)

            # FAISS availability determines bias scaling.
            # Without FAISS, importance/recency boosts must shrink to
            # prevent ★4 Critical items from polluting all queries.
            has_faiss = len(semantic_scores) > 0
            bias_scale = 0.05 if has_faiss else 0.01

            # Importance boost: scaled by FAISS presence
            importance_boost = bias_scale * (mem.importance / 4.0)

            # Recency boost: scaled by FAISS presence
            recency_boost = 0.0
            try:
                last = datetime.fromisoformat(mem.last_accessed.replace("Z", "+00:00"))
                age_h = (datetime.now(timezone.utc) - last).total_seconds() / 3600
                if age_h < 1:
                    recency_boost = bias_scale
                elif age_h < 24:
                    recency_boost = bias_scale * 0.4
            except Exception:
                pass

            final_score = 0.40 * keyword_score + 0.50 * semantic_score + importance_boost + recency_boost
            final_score = min(final_score, 1.0)

            if final_score > 0.01:
                candidates.append((mem_id, final_score, mem))

        candidates.sort(key=lambda x: x[1], reverse=True)

        results = []
        for mem_id, score, mem in candidates[:limit]:
            mem.access_count += 1
            mem.last_accessed = datetime.now(timezone.utc).isoformat()
            snippet = (mem.content[:200] + "...") if len(mem.content) > 200 else mem.content
            results.append(RetrievalResult(
                memory=mem,
                relevance_score=round(score, 4),
                confidence=mem.confidence,
                snippet=snippet,
            ))

        logger.info("memory_recalled", query_hash=hash(query) & 0xFFFF, count=len(results),
                     top_score=results[0].relevance_score if results else 0)
        try:
            from .metrics import get_collector
            c = get_collector(); c.record_success("recall") if c else None
        except Exception:
            pass
        return results

    @track_latency("memory_context")
    def get_context_window(
        self,
        query: str,
        max_tokens: int = 4000,
        session_id: Optional[str] = None,
    ) -> str:
        results = self.recall(query, session_id=session_id, limit=50)
        context_parts = []
        current_tokens = 0
        sorted_results = sorted(results, key=lambda r: (r.memory.importance, r.relevance_score), reverse=True)
        for result in sorted_results:
            mem = result.memory
            # M-006 fix: better token estimate (Chinese ~1.5 tokens/char, English ~0.25)
            chinese_count = sum(1 for ch in mem.content if '\u4e00' <= ch <= '\u9fff')
            other_count = len(mem.content) - chinese_count
            mem_tokens = int(chinese_count * 1.5 + other_count * 0.25)
            if current_tokens + mem_tokens > max_tokens:
                continue
            context_parts.append(f"[{mem.importance}★] {mem.content}")
            current_tokens += mem_tokens
        result = "\n\n".join(context_parts) if context_parts else ""
        try:
            from .metrics import get_collector
            c = get_collector(); c.record_success("context") if c else None
        except Exception:
            pass
        return result

    def _find_duplicate_content(self, content: str, session_id: Optional[str]) -> Optional[str]:
        """P1 fix: check if identical content already exists.
        
        Exact-match only — no fuzzy matching to avoid false merges.
        Returns the existing memory_id if found, None otherwise.
        """
        normalized = content.strip()
        with self._lock:
            for mid, mem in self._memories.items():
                if mem.content.strip() == normalized:
                    return mid
        return None

    def _evict_low_importance(self) -> None:
        with self._lock:
            if not self._memories:
                return
            sorted_mems = sorted(self._memories.items(), key=lambda x: (x[1].importance, -x[1].access_count))
            evict_count = max(1, len(self._memories) // 10)
            to_evict = [mid for mid, _ in sorted_mems[:evict_count]]
            for mid in to_evict:
                del self._memories[mid]
            self._index.clear()
            for mem_id, mem in self._memories.items():
                for tag in mem.tags:
                    self._index.setdefault(tag, set()).add(mem_id)
            self._faiss_dirty = True
            # P0 fix: persist eviction to disk, prevent zombie revival on restart
            self._rewrite_jsonl()
        logger.warning("memories_evicted", count=evict_count, remaining=len(self._memories))

    @track_latency("memory_update_confidence")
    def update_confidence(self, memory_id: str, confidence: float) -> bool:
        with self._lock:
            if memory_id not in self._memories:
                return False
            mem = self._memories[memory_id]
            mem.confidence = max(0.0, min(1.0, confidence))
            mem.last_accessed = datetime.now(timezone.utc).isoformat()
            self._faiss_dirty = True
            try:
                self._rewrite_jsonl()
            except Exception as e:
                logger.warning("confidence_persist_failed", memory_id=memory_id, error=str(e))
        logger.info("memory_confidence_updated", memory_id=memory_id, confidence=confidence)
        try:
            from .metrics import get_collector
            c = get_collector(); c.record_success("update_confidence") if c else None
        except Exception:
            pass
        return True

    @track_latency("memory_delete")
    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID. Returns True if found and deleted."""
        with self._lock:
            if memory_id not in self._memories:
                return False
            mem = self._memories.pop(memory_id)
            for tag in mem.tags:
                if tag in self._index:
                    self._index[tag].discard(memory_id)
                    if not self._index[tag]:
                        del self._index[tag]
            self._faiss_dirty = True
            self._rewrite_jsonl()
            logger.info("memory_deleted", memory_id=memory_id)
            try:
                from .metrics import get_collector
                c = get_collector(); c.record_success("delete") if c else None
                c.set_gauge("memories_total", len(self._memories)) if c else None
            except Exception:
                pass
            return True

    def _rewrite_jsonl(self) -> None:
        import tempfile
        tmp = self.memory_file.with_suffix(".rewrite_tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                for entry in self._memories.values():
                    data = entry.to_dict()
                    # L-003 fix: encrypt content during rewrite too
                    data["content"] = self._encrypt_content(data["content"])
                    f.write(json.dumps(data, ensure_ascii=False) + "\n")
                f.flush()
                import os as _os
                _os.fsync(f.fileno())
            tmp.replace(self.memory_file)
        except Exception:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            raise

    @track_latency("memory_stats")
    def get_stats(self) -> dict[str, Any]:
        total = len(self._memories)
        embedder_available = _EmbedderCache.get()[0] is not None
        faiss_has_index = self._faiss_index is not None
        if total == 0:
            result = {
                "total_memories": 0,
                "max_memories": self.max_memories,
                "by_importance": {i: 0 for i in range(1, 5)},
                "avg_confidence": 0.0,
                "tag_count": 0,
                "storage_path": str(self.storage_path),
                "faiss_available": embedder_available,
                "faiss_index_type": self._faiss_index_type,
            }
        else:
            by_importance = {i: sum(1 for m in self._memories.values() if m.importance == i) for i in range(1, 5)}
            avg_conf = sum(m.confidence for m in self._memories.values()) / total
            result = {
                "total_memories": total,
                "max_memories": self.max_memories,
                "by_importance": by_importance,
                "avg_confidence": round(avg_conf, 3),
                "tag_count": len(self._index),
                "storage_path": str(self.storage_path),
                "faiss_available": embedder_available,
                "faiss_index_type": self._faiss_index_type,
            }
        # Update gauges
        try:
            from .metrics import get_collector
            c = get_collector()
            if c:
                c.record_success("stats")
                c.set_gauge("memories_total", total)
                c.set_gauge("embedder_available", 1 if embedder_available else 0)
                c.set_gauge("faiss_available", 1 if faiss_has_index else 0)
                c.set_gauge("encryption_enabled", 1 if self._fernet else 0)
        except Exception:
            pass
        return result

    # -- H-005 fix: expose embedder health status for monitoring ----------
    def embedder_available(self) -> bool:
        """Check if semantic search (embedding model) is available."""
        return _EmbedderCache.get()[0] is not None
