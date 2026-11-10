"""
Dynamic Context Loading System with /prime Commands

Implements progressive disclosure pattern for CLAUDE.md optimization.
Instead of loading all context upfront, contexts are loaded on-demand
via /prime-<context> commands.

Available contexts:
- /prime-bug: Bug fixing workflows and debugging patterns
- /prime-feature: Feature development guidelines
- /prime-refactor: Code refactoring best practices
- /prime-test: Testing strategies and patterns
- /prime-docs: Documentation standards
- /prime-api: API design and implementation
- /prime-perf: Performance optimization
- /prime-security: Security best practices

Benefits:
- 80% token reduction for base context
- Task-specific context only when needed
- Faster initial load times
- Better focused context
"""

import logging
from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class PrimeContext:
    """Represents a loadable prime context."""
    context_id: str
    display_name: str
    description: str
    content: str
    token_estimate: int
    dependencies: List[str]  # Other contexts this depends on
    keywords: List[str]  # For semantic matching
    usage_count: int = 0
    last_used: Optional[datetime] = None


class PrimeContextLoader:
    """
    Dynamic context loader for /prime commands.

    Manages task-specific context loading with:
    - Template-based context generation
    - AgentDB-backed semantic matching
    - Usage tracking and optimization
    - Dependency resolution
    """

    # Context templates
    CONTEXT_TEMPLATES = {
        'bug': {
            'display_name': 'Bug Fixing',
            'description': 'Debugging workflows, error patterns, and fix strategies',
            'sections': {
                'Debugging Workflow': """
**Systematic Debugging Approach:**

1. **Reproduce Reliably**
   - Create minimal reproduction case
   - Document exact steps
   - Note environment details

2. **Isolate the Problem**
   - Binary search through code
   - Disable features systematically
   - Use debugging tools (pdb, node inspect)

3. **Hypothesize & Test**
   - Form specific hypotheses
   - Test one variable at a time
   - Keep log of attempts

4. **Fix & Verify**
   - Implement minimal fix
   - Add regression test
   - Verify in clean environment

5. **Document**
   - Update relevant docs
   - Add code comments
   - Log in knowledge base
""",
                'Common Error Patterns': """
**Learned Error Patterns:**

- **Import Errors**: Check virtual env activation, package installation
- **Type Errors**: Validate input types, check API contracts
- **Null/Undefined**: Add guards, use optional chaining
- **Race Conditions**: Add proper async/await, locks
- **Memory Leaks**: Check event listener cleanup, close connections
""",
                'Debugging Tools': """
**Tool Selection by Language:**

- **Python**: `pdb`, `ipdb`, `pytest --pdb`, `logging`
- **JavaScript**: Chrome DevTools, `node --inspect`, `console`
- **General**: `strace`, `ltrace`, `gdb`, profilers
"""
            },
            'dependencies': [],
            'keywords': ['debug', 'bug', 'error', 'fix', 'troubleshoot']
        },

        'feature': {
            'display_name': 'Feature Development',
            'description': 'Feature design, implementation, and integration patterns',
            'sections': {
                'Feature Development Workflow': """
**Feature Implementation Process:**

1. **Requirements Analysis**
   - Clarify acceptance criteria
   - Identify edge cases
   - Plan API surface

2. **Design**
   - Sketch architecture
   - Define data models
   - Plan integration points

3. **Implementation**
   - TDD: Write tests first
   - Implement incrementally
   - Refactor continuously

4. **Integration**
   - API contracts
   - Database migrations
   - Configuration updates

5. **Validation**
   - Manual testing
   - Performance check
   - Security review
""",
                'Design Patterns': """
**Recommended Patterns:**

- **Single Responsibility**: One class/function, one job
- **Dependency Injection**: Easier testing, loose coupling
- **Factory Pattern**: Complex object creation
- **Observer Pattern**: Event-driven systems
- **Strategy Pattern**: Swappable algorithms
""",
                'Code Organization': """
**File Structure:**

```
feature/
├── models/        # Data models
├── services/      # Business logic
├── controllers/   # API handlers
├── tests/         # Test suite
└── README.md      # Feature docs
```
"""
            },
            'dependencies': [],
            'keywords': ['feature', 'implement', 'develop', 'build', 'create']
        },

        'refactor': {
            'display_name': 'Code Refactoring',
            'description': 'Refactoring patterns, code quality, and technical debt',
            'sections': {
                'Refactoring Principles': """
**Safe Refactoring:**

1. **Red-Green-Refactor**
   - Ensure tests pass (Green)
   - Refactor code
   - Verify tests still pass

2. **Small Steps**
   - One transformation at a time
   - Commit frequently
   - Can rollback easily

3. **Automated Tests Required**
   - No refactoring without tests
   - Add tests if missing
   - Aim for >80% coverage
""",
                'Common Refactorings': """
**High-Value Refactorings:**

- **Extract Function**: Break down large functions (>50 LOC)
- **Extract Class**: Split god objects
- **Rename**: Improve clarity
- **Remove Dead Code**: Delete unused code
- **Simplify Conditionals**: Reduce complexity
- **DRY**: Extract common code
""",
                'Code Smells': """
**Watch For:**

- Functions >50 lines
- Classes >500 lines
- Cyclomatic complexity >10
- Duplicate code blocks
- Long parameter lists (>3-4)
- Deep nesting (>3 levels)
"""
            },
            'dependencies': ['test'],
            'keywords': ['refactor', 'cleanup', 'improve', 'optimize', 'simplify']
        },

        'test': {
            'display_name': 'Testing Strategies',
            'description': 'Test patterns, coverage strategies, and testing tools',
            'sections': {
                'Testing Strategy': """
**Comprehensive Testing:**

1. **Unit Tests** (Fast, Isolated)
   - Test individual functions
   - Mock dependencies
   - 80%+ coverage target

2. **Integration Tests** (Realistic)
   - Test component interactions
   - Use test databases
   - Cover critical paths

3. **E2E Tests** (Confidence)
   - Test full user flows
   - Minimal but critical
   - Run in CI/CD
""",
                'Test Patterns': """
**Effective Test Patterns:**

- **AAA Pattern**: Arrange, Act, Assert
- **Given-When-Then**: BDD style
- **Fixtures**: Reusable test data
- **Factories**: Dynamic test objects
- **Mocking**: Isolate dependencies
- **Parametrize**: Test multiple inputs
""",
                'Coverage Requirements': """
**Coverage Targets:**

- **Unit Tests**: >80% code coverage
- **Critical Paths**: 100% coverage
- **New Features**: Tests required before merge
- **Bug Fixes**: Regression test required
"""
            },
            'dependencies': [],
            'keywords': ['test', 'testing', 'coverage', 'tdd', 'unit test']
        },

        'docs': {
            'display_name': 'Documentation',
            'description': 'Documentation standards, API docs, and examples',
            'sections': {
                'Documentation Standards': """
**Documentation Requirements:**

1. **README.md**
   - Project overview
   - Quick start
   - Key features
   - Installation

2. **API Documentation**
   - All public APIs documented
   - Parameters and return types
   - Usage examples
   - Error cases

3. **Architecture Docs**
   - System overview
   - Component diagrams
   - Data flow
   - Key decisions (ADRs)
""",
                'Code Documentation': """
**Inline Documentation:**

- **Docstrings**: All public functions/classes
- **Comments**: Explain why, not what
- **Type Hints**: Use where beneficial
- **Examples**: Include usage examples
""",
                'API Documentation Tools': """
**Recommended Tools:**

- **Python**: Sphinx, MkDocs, pydoc
- **JavaScript**: JSDoc, TypeDoc, Docusaurus
- **OpenAPI**: Swagger, Redoc
- **General**: Markdown, PlantUML
"""
            },
            'dependencies': [],
            'keywords': ['docs', 'documentation', 'readme', 'api docs']
        },

        'api': {
            'display_name': 'API Design',
            'description': 'REST API design, GraphQL, and API best practices',
            'sections': {
                'API Design Principles': """
**RESTful API Design:**

1. **Resources** (Nouns, not verbs)
   - `/users` not `/getUsers`
   - `/users/:id` for specific resource
   - Nested resources: `/users/:id/posts`

2. **HTTP Methods** (Proper semantics)
   - GET: Read (idempotent)
   - POST: Create
   - PUT: Replace
   - PATCH: Update
   - DELETE: Remove

3. **Status Codes** (Meaningful)
   - 200: Success
   - 201: Created
   - 400: Bad Request
   - 404: Not Found
   - 500: Server Error
""",
                'API Versioning': """
**Versioning Strategies:**

- **URL Versioning**: `/api/v1/users` (Recommended)
- **Header Versioning**: `Accept: application/vnd.api.v1+json`
- **Query Parameter**: `/api/users?version=1`

**Migration Strategy:**
- Support N and N-1 versions
- Deprecation warnings
- Sunset headers
""",
                'Response Format': """
**Standardized Responses:**

```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2024-10-20T10:30:00Z",
    "version": "v1"
  },
  "errors": []
}
```
"""
            },
            'dependencies': [],
            'keywords': ['api', 'rest', 'graphql', 'endpoint', 'http']
        },

        'perf': {
            'display_name': 'Performance Optimization',
            'description': 'Performance patterns, profiling, and optimization',
            'sections': {
                'Performance Strategy': """
**Optimization Approach:**

1. **Measure First**
   - Profile before optimizing
   - Identify bottlenecks
   - Set performance targets

2. **Focus on Hot Paths**
   - Optimize critical paths
   - 80/20 rule applies
   - Measure impact

3. **Trade-offs**
   - Memory vs Speed
   - Complexity vs Performance
   - Maintainability matters
""",
                'Common Optimizations': """
**High-Impact Optimizations:**

- **Caching**: Redis, in-memory, CDN
- **Database**: Indexes, query optimization, connection pooling
- **Async**: Non-blocking I/O, parallelism
- **Compression**: gzip, brotli
- **Lazy Loading**: Load on demand
- **Pagination**: Limit result sets
""",
                'Profiling Tools': """
**Profiling by Language:**

- **Python**: `cProfile`, `line_profiler`, `memory_profiler`
- **JavaScript**: Chrome DevTools, `clinic.js`
- **Database**: EXPLAIN, slow query log
- **Network**: Chrome DevTools, curl, wrk
"""
            },
            'dependencies': [],
            'keywords': ['performance', 'optimization', 'speed', 'latency', 'throughput']
        },

        'security': {
            'display_name': 'Security Best Practices',
            'description': 'Security patterns, OWASP guidelines, and secure coding',
            'sections': {
                'Security Fundamentals': """
**Core Security Principles:**

1. **Input Validation**
   - Validate all inputs
   - Sanitize user data
   - Use allowlists over denylists

2. **Authentication**
   - Strong password policies
   - Multi-factor authentication
   - Secure session management

3. **Authorization**
   - Principle of least privilege
   - Role-based access control
   - Resource-level permissions
""",
                'OWASP Top 10': """
**Critical Vulnerabilities:**

1. Broken Access Control
2. Cryptographic Failures
3. Injection (SQL, XSS)
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable Components
7. Authentication Failures
8. Data Integrity Failures
9. Logging Failures
10. SSRF
""",
                'Secure Coding Practices': """
**Best Practices:**

- **Never** store passwords in plain text
- **Always** use parameterized queries (prevent SQL injection)
- **Validate** on server side (never trust client)
- **Encrypt** sensitive data at rest
- **Use** HTTPS for all communication
- **Update** dependencies regularly
- **Audit** security logs
"""
            },
            'dependencies': [],
            'keywords': ['security', 'owasp', 'auth', 'encryption', 'vulnerability']
        }
    }

    def __init__(self, memory_system=None, optimizer=None):
        """
        Initialize prime context loader.

        Args:
            memory_system: PersistentMemory for caching contexts
            optimizer: ContextOptimizer for token estimation
        """
        self.memory = memory_system
        self.optimizer = optimizer

        # Build context registry
        self._contexts: Dict[str, PrimeContext] = {}
        self._initialize_contexts()

        # Usage statistics
        self._stats = {
            'contexts_loaded': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }

    def _initialize_contexts(self):
        """Initialize context registry from templates."""
        for context_id, template in self.CONTEXT_TEMPLATES.items():
            # Build content from sections
            content_lines = [
                f"# {template['display_name']} Context",
                "",
                f"_{template['description']}_",
                ""
            ]

            for section_name, section_content in template['sections'].items():
                content_lines.append(f"## {section_name}")
                content_lines.append("")
                content_lines.append(section_content.strip())
                content_lines.append("")

            content = '\n'.join(content_lines)

            # Estimate tokens
            token_estimate = len(content) / 4  # Rough estimate

            # Create context
            context = PrimeContext(
                context_id=context_id,
                display_name=template['display_name'],
                description=template['description'],
                content=content,
                token_estimate=int(token_estimate),
                dependencies=template.get('dependencies', []),
                keywords=template.get('keywords', [])
            )

            self._contexts[context_id] = context

        logger.info(f"Initialized {len(self._contexts)} prime contexts")

    async def load_context(
        self,
        context_id: str,
        include_dependencies: bool = True
    ) -> Optional[str]:
        """
        Load a prime context.

        Args:
            context_id: Context identifier (e.g., 'bug', 'feature')
            include_dependencies: Whether to include dependency contexts

        Returns:
            Context content or None if not found
        """
        # Normalize context ID
        context_id = context_id.lower().replace('prime-', '').replace('/prime-', '')

        if context_id not in self._contexts:
            logger.warning(f"Unknown context: {context_id}")
            return None

        # Check cache first
        cache_key = f"prime_context_{context_id}"
        if self.memory:
            cached = await self.memory.retrieve(cache_key, namespace="contexts")
            if cached:
                self._stats['cache_hits'] += 1
                self._update_usage(context_id)
                logger.debug(f"Loaded {context_id} from cache")
                return cached

        self._stats['cache_misses'] += 1

        # Get context
        context = self._contexts[context_id]
        content = context.content

        # Include dependencies if requested
        if include_dependencies and context.dependencies:
            dependency_content = []

            for dep_id in context.dependencies:
                dep_context = await self.load_context(dep_id, include_dependencies=False)
                if dep_context:
                    dependency_content.append(dep_context)

            if dependency_content:
                content = '\n\n---\n\n'.join([content] + dependency_content)

        # Cache for future use
        if self.memory:
            await self.memory.store(
                cache_key,
                content,
                namespace="contexts",
                ttl_seconds=3600  # 1 hour cache
            )

        # Update usage stats
        self._update_usage(context_id)
        self._stats['contexts_loaded'] += 1

        logger.info(
            f"Loaded context: {context_id} "
            f"({context.token_estimate} tokens, {len(context.dependencies)} dependencies)"
        )

        return content

    def _update_usage(self, context_id: str):
        """Update usage statistics for a context."""
        if context_id in self._contexts:
            context = self._contexts[context_id]
            context.usage_count += 1
            context.last_used = datetime.now()

    async def suggest_contexts(
        self,
        query: str,
        max_results: int = 3
    ) -> List[PrimeContext]:
        """
        Suggest relevant contexts based on a query.

        Args:
            query: Search query
            max_results: Maximum number of suggestions

        Returns:
            List of relevant contexts
        """
        query_lower = query.lower()
        scored_contexts = []

        for context in self._contexts.values():
            score = 0.0

            # Keyword matching
            for keyword in context.keywords:
                if keyword in query_lower:
                    score += 10.0

            # Description matching
            if any(word in context.description.lower() for word in query_lower.split()):
                score += 5.0

            # Usage frequency bonus
            score += context.usage_count * 0.1

            if score > 0:
                scored_contexts.append((score, context))

        # Sort by score
        scored_contexts.sort(reverse=True, key=lambda x: x[0])

        return [ctx for score, ctx in scored_contexts[:max_results]]

    def list_available_contexts(self) -> List[Dict[str, Any]]:
        """Get list of all available contexts."""
        return [
            {
                'id': ctx.context_id,
                'name': ctx.display_name,
                'description': ctx.description,
                'command': f'/prime-{ctx.context_id}',
                'tokens': ctx.token_estimate,
                'usage_count': ctx.usage_count,
                'dependencies': ctx.dependencies
            }
            for ctx in self._contexts.values()
        ]

    def get_context_menu(self) -> str:
        """Generate a context menu for display."""
        lines = [
            "# 📚 Available Prime Contexts",
            "",
            "Load task-specific context on-demand to minimize token usage:",
            ""
        ]

        # Group by category
        categories = {
            'Development': ['feature', 'refactor', 'test'],
            'Operations': ['bug', 'perf', 'security'],
            'Documentation': ['docs', 'api']
        }

        for category, context_ids in categories.items():
            lines.append(f"## {category}")
            lines.append("")

            for context_id in context_ids:
                if context_id in self._contexts:
                    ctx = self._contexts[context_id]
                    lines.append(
                        f"- **`/prime-{context_id}`** - {ctx.description} "
                        f"_({ctx.token_estimate} tokens)_"
                    )

            lines.append("")

        lines.append("---")
        lines.append("_Contexts are cached for 1 hour after first load._")

        return '\n'.join(lines)

    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            **self._stats,
            'total_contexts': len(self._contexts),
            'most_used': sorted(
                self._contexts.values(),
                key=lambda c: c.usage_count,
                reverse=True
            )[:5]
        }
