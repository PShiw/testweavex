# TestWeaveX — Phase 1 Foundation Design

**Date:** 2026-04-18
**Status:** Approved
**Scope:** Phase 1 only — data layer foundation (Weeks 1–2 of 18-week build order)
**Next phase:** Phase 2 — LLM Adapter + Skills Loader (separate spec)

---

## 1. Scope

Phase 1 delivers a working, importable Python package with a complete data layer. No CLI, no LLM, no web UI. Everything built in Phases 2–8 depends on this foundation.

### Files delivered

```
testweavex/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── models.py          # Pydantic v2 models, enums, stable ID function
│   ├── config.py          # YAML config loader with env var interpolation
│   └── exceptions.py      # Exception hierarchy
├── storage/
│   ├── __init__.py
│   ├── base.py            # Abstract StorageRepository (13 methods)
│   ├── models.py          # SQLAlchemy ORM models (5 tables)
│   └── sqlite.py          # SQLiteRepository — full implementation
tests/
├── __init__.py
├── test_models.py         # Stable ID, model validation, enum coverage
└── test_storage.py        # CRUD round-trips on in-memory SQLite
pyproject.toml             # Package config, entry points, dependencies
docs/
└── index.html             # GitHub Pages documentation site
```

### Explicitly excluded from Phase 1

`llm/`, `skills/`, `generation/`, `execution/`, `reporters/`, `gap/`, `tcm/`, `web/`, `cli.py`

---

## 2. Core Models (`core/models.py`)

### Enums

```python
class TestStatus(str, Enum):
    pending  = 'pending'
    passed   = 'passed'
    failed   = 'failed'
    skipped  = 'skipped'
    flaky    = 'flaky'

class TestType(str, Enum):
    smoke         = 'smoke'
    sanity        = 'sanity'
    happy_path    = 'happy_path'
    edge_cases    = 'edge_cases'
    data_driven   = 'data_driven'
    integration   = 'integration'
    system        = 'system'
    e2e           = 'e2e'
    accessibility = 'accessibility'
    cross_browser = 'cross_browser'

class GapStatus(str, Enum):
    open           = 'open'
    pending_review = 'pending_review'
    closed         = 'closed'
    dismissed      = 'dismissed'
```

### Stable ID

```python
def generate_stable_id(*parts: str) -> str:
    key = '|'.join(parts).encode('utf-8')
    return hashlib.sha256(key).hexdigest()  # full 64 chars — never truncate
```

**Algorithm is frozen.** Changing it invalidates all stable IDs in every deployed instance.

- `test_case_id = generate_stable_id(feature_path, scenario_name)`
- `feature_id   = generate_stable_id(feature_path)`

### Models

**TestCase**
```python
class TestCase(BaseModel):
    id: str                         # generate_stable_id(feature_path, scenario_name)
    title: str
    feature_id: str
    gherkin: str
    test_type: TestType
    skill: str
    status: TestStatus = TestStatus.pending
    is_automated: bool = False
    tcm_id: Optional[str] = None
    tags: list[str] = []
    priority: int = 2               # 1=critical, 2=high, 3=medium, 4=low
    source_file: Optional[str] = None
    created_at: datetime
    updated_at: datetime
```

**Feature**
```python
class Feature(BaseModel):
    id: str                         # generate_stable_id(feature_path)
    name: str
    description: str = ''
    acceptance_criteria: list[str] = []
    test_case_ids: list[str] = []
    source_file: Optional[str] = None
```

**TestRun**
```python
class TestRun(BaseModel):
    id: str                         # UUID generated at run start
    suite: str
    environment: str = 'local'      # local | ci | staging | prod
    browser: Optional[str] = None   # chromium | firefox | webkit
    triggered_by: str = 'tw'        # tw | pytest | api
    started_at: datetime
    completed_at: Optional[datetime] = None
    result_ids: list[str] = []
```

**TestResult**
```python
class TestResult(BaseModel):
    id: str
    run_id: str
    test_case_id: str
    status: TestStatus
    duration_ms: int
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    retry_count: int = 0
```

**Gap**
```python
class Gap(BaseModel):
    id: str
    test_case_id: str
    priority_score: float = 0.0     # 0.0 – 1.0, higher = automate first
    gap_reason: str = ''
    suggested_gherkin: Optional[str] = None
    status: GapStatus = GapStatus.open
    detected_at: datetime
    closed_at: Optional[datetime] = None
```

**ScoringSignals** (consumed by gap scorer in Phase 5)
```python
class ScoringSignals(BaseModel):
    test_priority: int              # 1–4
    test_type: TestType
    defect_count: int = 0
    executions_90d: int = 0
    days_since_run: int = 0
```

**RunSummary** (consumed by reporters in Phase 4)
```python
class RunSummary(BaseModel):
    run_id: str
    total: int
    passed: int
    failed: int
    skipped: int
    duration_ms: int
    coverage_percentage: float
```

---

## 3. Configuration (`core/config.py`)

Loads `testweavex.config.yaml` from the project root (same directory as `pyproject.toml`). Supports `${ENV_VAR}` interpolation anywhere in values.

```yaml
# testweavex.config.yaml — full V1 schema
llm:
  provider: anthropic           # openai | anthropic | ollama | azure
  model: claude-sonnet-4-6
  api_key: ${ANTHROPIC_API_KEY}
  temperature: 0.3
  max_retries: 3
  timeout_seconds: 30

results_server: ${TESTWEAVEX_SERVER}   # optional — enables team mode

tcm:
  provider: none                # testrail | xray | none

gap_analysis:
  scoring_weights:
    priority:  0.30
    test_type: 0.25
    defects:   0.20
    frequency: 0.15
    staleness: 0.10
  match_threshold: 0.65
  top_gaps_default: 10
  min_runs_for_flaky: 5
```

Config object is a plain dataclass. Missing keys return defaults. Unknown keys are ignored (forward compatibility).

---

## 4. Exceptions (`core/exceptions.py`)

```
TestWeaveXError (base)
├── ConfigError          # Invalid or missing config
├── StorageError         # DB read/write failure
│   └── RecordNotFound   # Specific missing-record case
├── LLMOutputError       # LLM returned invalid/unparseable output (Phase 2+)
├── SkillNotFoundError   # Requested skill YAML not found (Phase 2+)
├── GenerationError      # Generation pipeline failure (Phase 3+)
└── TCMConnectorError    # External TCM API failure (Phase 7+)
```

Phase 1 only raises `ConfigError`, `StorageError`, and `RecordNotFound`. The rest are stubs with docstrings, ready for later phases.

---

## 5. Storage Layer

### Abstract interface (`storage/base.py`)

13 abstract methods. Callers never know whether SQLite or ServerRepository is active.

```python
class StorageRepository(ABC):
    def upsert_test_case(self, tc: TestCase): ...
    def get_test_case(self, id: str) -> TestCase: ...
    def save_result(self, r: TestResult): ...
    def start_run(self) -> TestRun: ...
    def end_run(self, run_id: str): ...
    def get_run(self, run_id: str) -> TestRun: ...
    def get_gaps(self, limit=50, status='open') -> list[Gap]: ...
    def save_gaps(self, gaps: list[Gap]): ...
    def get_coverage_percentage(self) -> float: ...
    def get_coverage_trend(self, weeks: int) -> list[dict]: ...
    def get_flaky_tests(self, min_runs=5) -> list[TestCase]: ...
    def get_scoring_signals(self, tc_id: str) -> ScoringSignals: ...
    def mark_uncollected_as_gaps(self, collected_ids: list[str]): ...
```

### ORM models (`storage/models.py`)

5 SQLAlchemy tables. Primary keys match the Pydantic model IDs (stable hash or UUID — never autoincrement).

| Table | Primary Key | Notes |
|-------|-------------|-------|
| `test_cases` | 64-char stable hash | `is_automated` indexed for gap queries |
| `features` | 64-char stable hash | |
| `test_runs` | UUID string | `completed_at` nullable |
| `test_results` | UUID string | FK → test_runs, test_cases |
| `gaps` | UUID string | FK → test_cases; `status` + `priority_score` indexed |

### SQLiteRepository (`storage/sqlite.py`)

**DB location:** Walks up from `cwd` searching for `pyproject.toml` or `pytest.ini`. Creates `.testweavex/results.db` in that directory. Add `.testweavex/` to `.gitignore`.

**Key implementation details:**
- All writes use a session context manager with rollback on exception
- `upsert_test_case` uses SQLAlchemy `merge()` — insert or update by primary key
- `get_flaky_tests` uses raw SQL for the window query (reproduced from architecture spec)
- `get_coverage_percentage` = `automated_count / max(total_count, 1) * 100`
- `mark_uncollected_as_gaps` bulk-inserts Gap rows for any TestCase ID not in the provided list; skips IDs that already have an open gap

---

## 6. HTML Documentation (`docs/index.html`)

Single self-contained file. No build step. GitHub Pages serves it from `docs/index.html`. Embedded CSS only — no CDN, no external fonts. Offline-capable.

### Page sections

| Section | Audience | Content source |
|---------|----------|----------------|
| Hero | All | Tagline, install snippet, GitHub + PyPI badges |
| Getting Started | Users | 3-step quick-start: install → init → first gap report |
| CLI Reference | Users | All 10 `tw` commands with flags, from PRD §10 |
| Configuration | Users | Full `testweavex.config.yaml` reference |
| Architecture | Contributors | Component map, three pipelines, build order table |
| Contributing | Contributors | Custom skill format, repo structure, PR guide |

Fixed top nav with anchor links. Active section highlighted on scroll. Dark theme consistent with `testweavex_ui_design.html`.

---

## 7. Package Config (`pyproject.toml`)

```toml
[project]
name = "testweavex"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "pyyaml>=6.0",
    "pytest>=7.0",
    "pytest-bdd>=7.0",
    "pytest-playwright>=0.4",
    "pytest-xdist>=3.0",
    "typer>=0.9",
    "httpx>=0.24",
    "fastapi>=0.110",
    "uvicorn>=0.27",
    "rich>=13.0",
]

[project.optional-dependencies]
openai     = ["openai>=1.0"]
anthropic  = ["anthropic>=0.20"]
ollama     = ["ollama>=0.1"]

[project.entry-points."pytest11"]
testweavex = "testweavex.execution.plugin"

[project.scripts]
tw = "testweavex.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

## 8. Test Coverage (Phase 1)

**`tests/test_models.py`**
- `generate_stable_id` is deterministic (same inputs → same output)
- `generate_stable_id` produces exactly 64 hex characters
- Different inputs never produce the same ID (spot-checks)
- `TestCase` rejects invalid `TestType` enum values
- `Gap.priority_score` rejects values outside 0.0–1.0

**`tests/test_storage.py`**
- Round-trip: upsert TestCase → get_test_case → fields match
- Round-trip: start_run → save_result → end_run → get_run
- `get_coverage_percentage` returns 0.0 on empty DB
- `mark_uncollected_as_gaps` creates Gap records for non-collected IDs
- `get_flaky_tests` returns only tests with both pass and fail results

All tests use an in-memory SQLite instance (`sqlite:///:memory:`) — no filesystem required.

---

## Decisions made during design

| Decision | Rationale |
|----------|-----------|
| Stable ID uses full 64-char SHA-256 (not truncated) | 16-char truncation has non-zero collision risk; 32-char is UUID-equivalent; 64-char is the full hash with zero collision risk. Algorithm frozen at first deployment. |
| 5 ORM tables (not 4) | Gap table added alongside the 4 originally listed — needed by `mark_uncollected_as_gaps` in Phase 1 storage interface |
| Future-phase exceptions defined as stubs now | Lets Phase 2+ code import from `core.exceptions` without circular dependency or refactoring |
| `ScoringSignals` and `RunSummary` in Phase 1 models | Storage interface methods reference them; defining them now avoids a breaking model change when Phase 4/5 land |
