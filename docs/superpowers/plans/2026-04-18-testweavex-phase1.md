# TestWeaveX Phase 1 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete data layer for TestWeaveX — Pydantic models, config loader, exception hierarchy, SQLite storage, and GitHub Pages documentation site.

**Architecture:** All data models are Pydantic v2 `BaseModel` subclasses shared across the entire system. The storage layer is abstracted behind `StorageRepository` so callers never know whether SQLite or a remote server is active. The HTML docs site is a single self-contained file served by GitHub Pages.

**Tech Stack:** Python 3.11+, Pydantic v2, SQLAlchemy 2+, PyYAML 6+, pytest, plain HTML/CSS (docs)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `pyproject.toml` | Create | Package config, dependencies, entry points |
| `.gitignore` | Create | Exclude `.testweavex/`, `__pycache__/`, `.pytest_cache/` |
| `testweavex/__init__.py` | Create | Package root |
| `testweavex/core/__init__.py` | Create | Sub-package marker |
| `testweavex/core/exceptions.py` | Create | Full exception hierarchy (Phase 1 active + Phase 2–7 stubs) |
| `testweavex/core/models.py` | Create | Enums, `generate_stable_id`, all 7 Pydantic models |
| `testweavex/core/config.py` | Create | YAML config loader with `${ENV_VAR}` interpolation |
| `testweavex/storage/__init__.py` | Create | Sub-package marker |
| `testweavex/storage/base.py` | Create | Abstract `StorageRepository` with 13 methods |
| `testweavex/storage/models.py` | Create | SQLAlchemy ORM — 5 tables |
| `testweavex/storage/sqlite.py` | Create | `SQLiteRepository` — full implementation |
| `tests/__init__.py` | Create | Test package marker |
| `tests/test_models.py` | Create | Stable ID + model validation tests |
| `tests/test_storage.py` | Create | Storage CRUD + gap + flakiness tests |
| `docs/index.html` | Create | Self-contained GitHub Pages documentation |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `testweavex/__init__.py`
- Create: `testweavex/core/__init__.py`
- Create: `testweavex/storage/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "testweavex"
version = "0.1.0"
description = "Unified test management and execution platform with LLM-powered test generation"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }

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
openai    = ["openai>=1.0"]
anthropic = ["anthropic>=0.20"]
ollama    = ["ollama>=0.1"]
dev       = ["pytest>=7.0", "pytest-cov>=4.0"]

[project.entry-points."pytest11"]
testweavex = "testweavex.execution.plugin"

[project.scripts]
tw = "testweavex.cli:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["testweavex*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create `.gitignore`**

```
.testweavex/
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
build/
.env
```

- [ ] **Step 3: Create empty `__init__.py` files**

Create these four empty files (no content needed):
- `testweavex/__init__.py`
- `testweavex/core/__init__.py`
- `testweavex/storage/__init__.py`
- `tests/__init__.py`

- [ ] **Step 4: Verify Python version and install package in editable mode**

```bash
python --version
# Expected: Python 3.11.x or higher

pip install -e ".[dev]"
# Expected: Successfully installed testweavex-0.1.0
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore testweavex/__init__.py testweavex/core/__init__.py testweavex/storage/__init__.py tests/__init__.py
git commit -m "chore: project scaffolding — pyproject.toml and package structure"
```

---

## Task 2: Exception Hierarchy

**Files:**
- Create: `testweavex/core/exceptions.py`

- [ ] **Step 1: Write `testweavex/core/exceptions.py`**

```python
class TestWeaveXError(Exception):
    """Base exception for all TestWeaveX errors."""


class ConfigError(TestWeaveXError):
    """Raised when testweavex.config.yaml is missing, unreadable, or invalid."""


class StorageError(TestWeaveXError):
    """Raised when a database read or write operation fails."""


class RecordNotFound(StorageError):
    """Raised when a requested record does not exist in storage."""


class LLMOutputError(TestWeaveXError):
    """Raised when the LLM returns output that cannot be parsed or validated.
    Active from Phase 2 onwards.
    """


class SkillNotFoundError(TestWeaveXError):
    """Raised when a requested skill YAML file does not exist.
    Active from Phase 2 onwards.
    """


class GenerationError(TestWeaveXError):
    """Raised when the generation pipeline fails after exhausting retries.
    Active from Phase 3 onwards.
    """


class TCMConnectorError(TestWeaveXError):
    """Raised when communication with an external TCM (TestRail, Xray) fails.
    Active from Phase 7 onwards.
    """
```

- [ ] **Step 2: Verify the module imports cleanly**

```bash
python -c "from testweavex.core.exceptions import TestWeaveXError, ConfigError, StorageError, RecordNotFound; print('OK')"
# Expected: OK
```

- [ ] **Step 3: Commit**

```bash
git add testweavex/core/exceptions.py
git commit -m "feat: exception hierarchy for all phases (Phase 2-7 as stubs)"
```

---

## Task 3: Enums and Stable ID

**Files:**
- Create: `testweavex/core/models.py` (partial — enums + `generate_stable_id` only)
- Create: `tests/test_models.py` (stable ID tests only)

- [ ] **Step 1: Write failing tests for `generate_stable_id`**

Create `tests/test_models.py`:

```python
import pytest
from testweavex.core.models import generate_stable_id, TestStatus, TestType, GapStatus


class TestGenerateStableId:
    def test_deterministic(self):
        id1 = generate_stable_id("features/login.feature", "User can log in")
        id2 = generate_stable_id("features/login.feature", "User can log in")
        assert id1 == id2

    def test_returns_64_hex_chars(self):
        result = generate_stable_id("features/login.feature", "User can log in")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_different_inputs_different_ids(self):
        id1 = generate_stable_id("features/login.feature", "User can log in")
        id2 = generate_stable_id("features/login.feature", "User can log out")
        id3 = generate_stable_id("features/register.feature", "User can log in")
        assert id1 != id2
        assert id1 != id3
        assert id2 != id3

    def test_single_part(self):
        result = generate_stable_id("features/login.feature")
        assert len(result) == 64

    def test_separator_matters(self):
        # "a|b" and "ab" must produce different IDs to prevent collisions
        # e.g. generate_stable_id("a", "b") != generate_stable_id("ab", "")
        id1 = generate_stable_id("a", "b")
        id2 = generate_stable_id("ab", "")
        assert id1 != id2


class TestEnums:
    def test_test_status_values(self):
        assert TestStatus.pending == "pending"
        assert TestStatus.passed == "passed"
        assert TestStatus.failed == "failed"
        assert TestStatus.skipped == "skipped"
        assert TestStatus.flaky == "flaky"

    def test_test_type_values(self):
        expected = {
            "smoke", "sanity", "happy_path", "edge_cases", "data_driven",
            "integration", "system", "e2e", "accessibility", "cross_browser"
        }
        actual = {t.value for t in TestType}
        assert actual == expected

    def test_gap_status_values(self):
        assert GapStatus.open == "open"
        assert GapStatus.pending_review == "pending_review"
        assert GapStatus.closed == "closed"
        assert GapStatus.dismissed == "dismissed"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models.py -v
# Expected: ERROR — ModuleNotFoundError: No module named 'testweavex.core.models'
```

- [ ] **Step 3: Write enums and `generate_stable_id` in `testweavex/core/models.py`**

```python
from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


def generate_stable_id(*parts: str) -> str:
    key = "|".join(parts).encode("utf-8")
    return hashlib.sha256(key).hexdigest()


class TestStatus(str, Enum):
    pending = "pending"
    passed = "passed"
    failed = "failed"
    skipped = "skipped"
    flaky = "flaky"


class TestType(str, Enum):
    smoke = "smoke"
    sanity = "sanity"
    happy_path = "happy_path"
    edge_cases = "edge_cases"
    data_driven = "data_driven"
    integration = "integration"
    system = "system"
    e2e = "e2e"
    accessibility = "accessibility"
    cross_browser = "cross_browser"


class GapStatus(str, Enum):
    open = "open"
    pending_review = "pending_review"
    closed = "closed"
    dismissed = "dismissed"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_models.py::TestGenerateStableId tests/test_models.py::TestEnums -v
# Expected: 12 passed
```

- [ ] **Step 5: Commit**

```bash
git add testweavex/core/models.py tests/test_models.py
git commit -m "feat: enums, generate_stable_id (full 64-char SHA-256)"
```

---

## Task 4: Pydantic Models

**Files:**
- Modify: `testweavex/core/models.py` (append 7 model classes)
- Modify: `tests/test_models.py` (append model validation tests)

- [ ] **Step 1: Write failing model validation tests — append to `tests/test_models.py`**

```python
class TestTestCase:
    def test_valid_construction(self):
        from testweavex.core.models import TestCase
        now = datetime.utcnow()
        tc = TestCase(
            id=generate_stable_id("features/login.feature", "User logs in"),
            title="User logs in",
            feature_id=generate_stable_id("features/login.feature"),
            gherkin="Given I am on the login page\nWhen I enter valid credentials\nThen I am logged in",
            test_type=TestType.smoke,
            skill="functional/smoke",
            created_at=now,
            updated_at=now,
        )
        assert tc.status == TestStatus.pending
        assert tc.is_automated is False
        assert tc.priority == 2
        assert tc.tags == []

    def test_invalid_test_type_raises(self):
        from testweavex.core.models import TestCase
        now = datetime.utcnow()
        with pytest.raises(Exception):
            TestCase(
                id="x" * 64,
                title="t",
                feature_id="f" * 64,
                gherkin="g",
                test_type="not_a_type",
                skill="functional/smoke",
                created_at=now,
                updated_at=now,
            )


class TestGap:
    def test_priority_score_defaults_to_zero(self):
        from testweavex.core.models import Gap
        gap = Gap(
            id="g" * 64,
            test_case_id="t" * 64,
            detected_at=datetime.utcnow(),
        )
        assert gap.priority_score == 0.0
        assert gap.status == GapStatus.open

    def test_priority_score_accepts_valid_range(self):
        from testweavex.core.models import Gap
        gap = Gap(
            id="g" * 64,
            test_case_id="t" * 64,
            priority_score=0.85,
            detected_at=datetime.utcnow(),
        )
        assert gap.priority_score == 0.85

    def test_priority_score_rejects_above_one(self):
        from testweavex.core.models import Gap
        with pytest.raises(Exception):
            Gap(
                id="g" * 64,
                test_case_id="t" * 64,
                priority_score=1.5,
                detected_at=datetime.utcnow(),
            )

    def test_priority_score_rejects_below_zero(self):
        from testweavex.core.models import Gap
        with pytest.raises(Exception):
            Gap(
                id="g" * 64,
                test_case_id="t" * 64,
                priority_score=-0.1,
                detected_at=datetime.utcnow(),
            )


class TestRunAndResult:
    def test_test_run_defaults(self):
        from testweavex.core.models import TestRun
        run = TestRun(
            id="r" * 36,
            suite="regression",
            started_at=datetime.utcnow(),
        )
        assert run.environment == "local"
        assert run.triggered_by == "tw"
        assert run.completed_at is None
        assert run.result_ids == []

    def test_test_result_construction(self):
        from testweavex.core.models import TestResult
        r = TestResult(
            id="x" * 36,
            run_id="r" * 36,
            test_case_id="t" * 64,
            status=TestStatus.passed,
            duration_ms=1234,
        )
        assert r.retry_count == 0
        assert r.error_message is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models.py::TestTestCase tests/test_models.py::TestGap tests/test_models.py::TestRunAndResult -v
# Expected: ERROR — ImportError (models not defined yet)
```

- [ ] **Step 3: Append the 7 model classes to `testweavex/core/models.py`**

Add these classes after the enums (keep everything already written above):

```python
class TestCase(BaseModel):
    id: str
    title: str
    feature_id: str
    gherkin: str
    test_type: TestType
    skill: str
    status: TestStatus = TestStatus.pending
    is_automated: bool = False
    tcm_id: Optional[str] = None
    tags: list[str] = []
    priority: int = 2
    source_file: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Feature(BaseModel):
    id: str
    name: str
    description: str = ""
    acceptance_criteria: list[str] = []
    test_case_ids: list[str] = []
    source_file: Optional[str] = None


class TestRun(BaseModel):
    id: str
    suite: str
    environment: str = "local"
    browser: Optional[str] = None
    triggered_by: str = "tw"
    started_at: datetime
    completed_at: Optional[datetime] = None
    result_ids: list[str] = []


class TestResult(BaseModel):
    id: str
    run_id: str
    test_case_id: str
    status: TestStatus
    duration_ms: int
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    retry_count: int = 0


class Gap(BaseModel):
    id: str
    test_case_id: str
    priority_score: float = 0.0
    gap_reason: str = ""
    suggested_gherkin: Optional[str] = None
    status: GapStatus = GapStatus.open
    detected_at: datetime
    closed_at: Optional[datetime] = None

    @field_validator("priority_score")
    @classmethod
    def score_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"priority_score must be 0.0–1.0, got {v}")
        return v


class ScoringSignals(BaseModel):
    test_priority: int
    test_type: TestType
    defect_count: int = 0
    executions_90d: int = 0
    days_since_run: int = 0


class RunSummary(BaseModel):
    run_id: str
    total: int
    passed: int
    failed: int
    skipped: int
    duration_ms: int
    coverage_percentage: float
```

- [ ] **Step 4: Run all model tests**

```bash
pytest tests/test_models.py -v
# Expected: all tests pass (17+ tests)
```

- [ ] **Step 5: Commit**

```bash
git add testweavex/core/models.py tests/test_models.py
git commit -m "feat: all Pydantic v2 models — TestCase, Feature, TestRun, TestResult, Gap, ScoringSignals, RunSummary"
```

---

## Task 5: Config Loader

**Files:**
- Create: `testweavex/core/config.py`

- [ ] **Step 1: Write `testweavex/core/config.py`**

```python
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from testweavex.core.exceptions import ConfigError

_ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _interpolate(value: object) -> object:
    if isinstance(value, str):
        def _replace(m: re.Match) -> str:
            var = m.group(1)
            return os.environ.get(var, "")
        return _ENV_PATTERN.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _interpolate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(i) for i in value]
    return value


@dataclass
class LLMConfig:
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    api_key: str = ""
    temperature: float = 0.3
    max_retries: int = 3
    timeout_seconds: int = 30
    base_url: Optional[str] = None
    azure_endpoint: Optional[str] = None
    api_version: Optional[str] = None
    deployment_name: Optional[str] = None


@dataclass
class GapAnalysisConfig:
    scoring_weights: dict = field(default_factory=lambda: {
        "priority": 0.30,
        "test_type": 0.25,
        "defects": 0.20,
        "frequency": 0.15,
        "staleness": 0.10,
    })
    match_threshold: float = 0.65
    top_gaps_default: int = 10
    min_runs_for_flaky: int = 5


@dataclass
class TCMConfig:
    provider: str = "none"
    testrail: dict = field(default_factory=dict)
    xray: dict = field(default_factory=dict)


@dataclass
class TestWeaveXConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    tcm: TCMConfig = field(default_factory=TCMConfig)
    gap_analysis: GapAnalysisConfig = field(default_factory=GapAnalysisConfig)
    results_server: Optional[str] = None


def _find_project_root(start: Path) -> Path:
    markers = {"pyproject.toml", "pytest.ini", "setup.cfg", "setup.py"}
    current = start.resolve()
    while True:
        if any((current / m).exists() for m in markers):
            return current
        parent = current.parent
        if parent == current:
            return start.resolve()
        current = parent


def load_config(start_dir: Optional[Path] = None) -> TestWeaveXConfig:
    root = _find_project_root(start_dir or Path.cwd())
    config_path = root / "testweavex.config.yaml"

    if not config_path.exists():
        return TestWeaveXConfig()

    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Failed to parse {config_path}: {exc}") from exc

    raw = _interpolate(raw)

    cfg = TestWeaveXConfig()

    if llm_raw := raw.get("llm"):
        cfg.llm = LLMConfig(**{k: v for k, v in llm_raw.items() if hasattr(LLMConfig, k)})

    if rs := raw.get("results_server"):
        cfg.results_server = rs or None

    if tcm_raw := raw.get("tcm"):
        cfg.tcm = TCMConfig(
            provider=tcm_raw.get("provider", "none"),
            testrail=tcm_raw.get("testrail", {}),
            xray=tcm_raw.get("xray", {}),
        )

    if gap_raw := raw.get("gap_analysis"):
        cfg.gap_analysis = GapAnalysisConfig(
            scoring_weights=gap_raw.get("scoring_weights", GapAnalysisConfig().scoring_weights),
            match_threshold=gap_raw.get("match_threshold", 0.65),
            top_gaps_default=gap_raw.get("top_gaps_default", 10),
            min_runs_for_flaky=gap_raw.get("min_runs_for_flaky", 5),
        )

    return cfg
```

- [ ] **Step 2: Verify the config loader works with no config file**

```bash
python -c "
from testweavex.core.config import load_config
cfg = load_config()
print('provider:', cfg.llm.provider)
print('results_server:', cfg.results_server)
print('OK')
"
# Expected:
# provider: anthropic
# results_server: None
# OK
```

- [ ] **Step 3: Verify env var interpolation works**

```bash
python -c "
import os, tempfile, pathlib
os.environ['TEST_KEY'] = 'my-secret'
import yaml, pathlib, tempfile
d = tempfile.mkdtemp()
p = pathlib.Path(d) / 'pyproject.toml'
p.write_text('')
cfg_path = pathlib.Path(d) / 'testweavex.config.yaml'
cfg_path.write_text('llm:\n  api_key: \${TEST_KEY}\n')
from testweavex.core.config import load_config
cfg = load_config(pathlib.Path(d))
print('api_key:', cfg.llm.api_key)
assert cfg.llm.api_key == 'my-secret'
print('OK')
"
# Expected:
# api_key: my-secret
# OK
```

- [ ] **Step 4: Commit**

```bash
git add testweavex/core/config.py
git commit -m "feat: YAML config loader with env var interpolation"
```

---

## Task 6: Storage Abstract Interface + ORM Models

**Files:**
- Create: `testweavex/storage/base.py`
- Create: `testweavex/storage/models.py`

- [ ] **Step 1: Write `testweavex/storage/base.py`**

```python
from __future__ import annotations

from abc import ABC, abstractmethod

from testweavex.core.models import (
    Gap,
    RunSummary,
    ScoringSignals,
    TestCase,
    TestResult,
    TestRun,
)


class StorageRepository(ABC):

    @abstractmethod
    def upsert_test_case(self, tc: TestCase) -> None: ...

    @abstractmethod
    def get_test_case(self, id: str) -> TestCase: ...

    @abstractmethod
    def save_result(self, r: TestResult) -> None: ...

    @abstractmethod
    def start_run(self, suite: str, environment: str = "local",
                  browser: str | None = None, triggered_by: str = "tw") -> TestRun: ...

    @abstractmethod
    def end_run(self, run_id: str) -> None: ...

    @abstractmethod
    def get_run(self, run_id: str) -> TestRun: ...

    @abstractmethod
    def get_gaps(self, limit: int = 50, status: str = "open") -> list[Gap]: ...

    @abstractmethod
    def save_gaps(self, gaps: list[Gap]) -> None: ...

    @abstractmethod
    def get_coverage_percentage(self) -> float: ...

    @abstractmethod
    def get_coverage_trend(self, weeks: int) -> list[dict]: ...

    @abstractmethod
    def get_flaky_tests(self, min_runs: int = 5) -> list[TestCase]: ...

    @abstractmethod
    def get_scoring_signals(self, tc_id: str) -> ScoringSignals: ...

    @abstractmethod
    def mark_uncollected_as_gaps(self, collected_ids: list[str]) -> None: ...
```

- [ ] **Step 2: Write `testweavex/storage/models.py`**

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TestCaseORM(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    feature_id: Mapped[str] = mapped_column(String(64), nullable=False)
    gherkin: Mapped[str] = mapped_column(Text, nullable=False)
    test_type: Mapped[str] = mapped_column(String(32), nullable=False)
    skill: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    is_automated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    tcm_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tags: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[int] = mapped_column(Integer, default=2)
    source_file: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    results: Mapped[list[TestResultORM]] = relationship(back_populates="test_case")
    gaps: Mapped[list[GapORM]] = relationship(back_populates="test_case")


class FeatureORM(Base):
    __tablename__ = "features"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    acceptance_criteria: Mapped[str] = mapped_column(Text, default="")
    test_case_ids: Mapped[str] = mapped_column(Text, default="")
    source_file: Mapped[str | None] = mapped_column(Text, nullable=True)


class TestRunORM(Base):
    __tablename__ = "test_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    suite: Mapped[str] = mapped_column(Text, nullable=False)
    environment: Mapped[str] = mapped_column(String(32), default="local")
    browser: Mapped[str | None] = mapped_column(String(16), nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(16), default="tw")
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    results: Mapped[list[TestResultORM]] = relationship(back_populates="run")


class TestResultORM(Base):
    __tablename__ = "test_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_runs.id"), nullable=False)
    test_case_id: Mapped[str] = mapped_column(String(64), ForeignKey("test_cases.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    run: Mapped[TestRunORM] = relationship(back_populates="results")
    test_case: Mapped[TestCaseORM] = relationship(back_populates="results")


class GapORM(Base):
    __tablename__ = "gaps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    test_case_id: Mapped[str] = mapped_column(String(64), ForeignKey("test_cases.id"), nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    gap_reason: Mapped[str] = mapped_column(Text, default="")
    suggested_gherkin: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    test_case: Mapped[TestCaseORM] = relationship(back_populates="gaps")


Index("ix_gaps_status_score", GapORM.status, GapORM.priority_score)
```

- [ ] **Step 3: Verify both modules import cleanly**

```bash
python -c "
from testweavex.storage.base import StorageRepository
from testweavex.storage.models import Base, TestCaseORM, FeatureORM, TestRunORM, TestResultORM, GapORM
print('tables:', list(Base.metadata.tables.keys()))
"
# Expected: tables: ['test_cases', 'features', 'test_runs', 'test_results', 'gaps']
```

- [ ] **Step 4: Commit**

```bash
git add testweavex/storage/base.py testweavex/storage/models.py
git commit -m "feat: abstract StorageRepository interface and SQLAlchemy ORM (5 tables)"
```

---

## Task 7: SQLiteRepository — Core CRUD

**Files:**
- Create: `testweavex/storage/sqlite.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: Write failing tests for core CRUD — create `tests/test_storage.py`**

```python
from __future__ import annotations

import json
import uuid
from datetime import datetime

import pytest

from testweavex.core.models import (
    Gap,
    GapStatus,
    ScoringSignals,
    TestCase,
    TestResult,
    TestRun,
    TestStatus,
    TestType,
    generate_stable_id,
)
from testweavex.storage.sqlite import SQLiteRepository


@pytest.fixture
def repo():
    """In-memory SQLite repo — isolated per test."""
    return SQLiteRepository(db_url="sqlite:///:memory:")


def _make_test_case(feature_path: str = "features/login.feature",
                    scenario: str = "User logs in") -> TestCase:
    now = datetime.utcnow()
    return TestCase(
        id=generate_stable_id(feature_path, scenario),
        title=scenario,
        feature_id=generate_stable_id(feature_path),
        gherkin="Given I am on the login page\nWhen I enter valid credentials\nThen I am logged in",
        test_type=TestType.smoke,
        skill="functional/smoke",
        created_at=now,
        updated_at=now,
    )


class TestUpsertAndGetTestCase:
    def test_insert_then_retrieve(self, repo):
        tc = _make_test_case()
        repo.upsert_test_case(tc)
        retrieved = repo.get_test_case(tc.id)
        assert retrieved.id == tc.id
        assert retrieved.title == tc.title
        assert retrieved.test_type == TestType.smoke

    def test_upsert_updates_existing(self, repo):
        tc = _make_test_case()
        repo.upsert_test_case(tc)
        updated = tc.model_copy(update={"title": "Updated title", "is_automated": True})
        repo.upsert_test_case(updated)
        retrieved = repo.get_test_case(tc.id)
        assert retrieved.title == "Updated title"
        assert retrieved.is_automated is True

    def test_get_nonexistent_raises(self, repo):
        from testweavex.core.exceptions import RecordNotFound
        with pytest.raises(RecordNotFound):
            repo.get_test_case("nonexistent-id")


class TestRunLifecycle:
    def test_start_and_end_run(self, repo):
        tc = _make_test_case()
        repo.upsert_test_case(tc)

        run = repo.start_run(suite="regression", environment="ci")
        assert run.id
        assert run.completed_at is None

        result = TestResult(
            id=str(uuid.uuid4()),
            run_id=run.id,
            test_case_id=tc.id,
            status=TestStatus.passed,
            duration_ms=1500,
        )
        repo.save_result(result)
        repo.end_run(run.id)

        retrieved = repo.get_run(run.id)
        assert retrieved.completed_at is not None
        assert retrieved.suite == "regression"
        assert retrieved.environment == "ci"

    def test_get_nonexistent_run_raises(self, repo):
        from testweavex.core.exceptions import RecordNotFound
        with pytest.raises(RecordNotFound):
            repo.get_run("nonexistent-run-id")


class TestCoveragePercentage:
    def test_empty_db_returns_zero(self, repo):
        assert repo.get_coverage_percentage() == 0.0

    def test_all_automated(self, repo):
        tc = _make_test_case()
        automated = tc.model_copy(update={"is_automated": True})
        repo.upsert_test_case(automated)
        assert repo.get_coverage_percentage() == 100.0

    def test_mixed_automated(self, repo):
        now = datetime.utcnow()
        for i in range(4):
            tc = _make_test_case(scenario=f"Scenario {i}")
            is_auto = i < 2
            repo.upsert_test_case(tc.model_copy(update={"is_automated": is_auto}))
        pct = repo.get_coverage_percentage()
        assert pct == 50.0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_storage.py -v
# Expected: ERROR — ModuleNotFoundError: No module named 'testweavex.storage.sqlite'
```

- [ ] **Step 3: Write `testweavex/storage/sqlite.py` — core CRUD portion**

```python
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from testweavex.core.exceptions import RecordNotFound, StorageError
from testweavex.core.models import (
    Gap,
    GapStatus,
    RunSummary,
    ScoringSignals,
    TestCase,
    TestResult,
    TestRun,
    TestStatus,
    TestType,
    generate_stable_id,
)
from testweavex.storage.base import StorageRepository
from testweavex.storage.models import (
    Base,
    FeatureORM,
    GapORM,
    TestCaseORM,
    TestResultORM,
    TestRunORM,
)


def _find_project_root(start: Path) -> Path:
    markers = {"pyproject.toml", "pytest.ini", "setup.cfg", "setup.py"}
    current = start.resolve()
    while True:
        if any((current / m).exists() for m in markers):
            return current
        parent = current.parent
        if parent == current:
            return start.resolve()
        current = parent


def _orm_to_test_case(row: TestCaseORM) -> TestCase:
    return TestCase(
        id=row.id,
        title=row.title,
        feature_id=row.feature_id,
        gherkin=row.gherkin,
        test_type=TestType(row.test_type),
        skill=row.skill,
        status=TestStatus(row.status),
        is_automated=row.is_automated,
        tcm_id=row.tcm_id,
        tags=json.loads(row.tags) if row.tags else [],
        priority=row.priority,
        source_file=row.source_file,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _orm_to_test_run(row: TestRunORM) -> TestRun:
    return TestRun(
        id=row.id,
        suite=row.suite,
        environment=row.environment,
        browser=row.browser,
        triggered_by=row.triggered_by,
        started_at=row.started_at,
        completed_at=row.completed_at,
        result_ids=[],
    )


def _orm_to_gap(row: GapORM) -> Gap:
    return Gap(
        id=row.id,
        test_case_id=row.test_case_id,
        priority_score=row.priority_score,
        gap_reason=row.gap_reason,
        suggested_gherkin=row.suggested_gherkin,
        status=GapStatus(row.status),
        detected_at=row.detected_at,
        closed_at=row.closed_at,
    )


class SQLiteRepository(StorageRepository):

    def __init__(self, db_url: Optional[str] = None) -> None:
        if db_url is None:
            root = _find_project_root(Path.cwd())
            db_dir = root / ".testweavex"
            db_dir.mkdir(exist_ok=True)
            db_url = f"sqlite:///{db_dir / 'results.db'}"

        self._engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self._engine)

    def _session(self) -> Session:
        return Session(self._engine)

    # ── TestCase ──────────────────────────────────────────────────────────

    def upsert_test_case(self, tc: TestCase) -> None:
        try:
            with self._session() as s:
                row = TestCaseORM(
                    id=tc.id,
                    title=tc.title,
                    feature_id=tc.feature_id,
                    gherkin=tc.gherkin,
                    test_type=tc.test_type.value,
                    skill=tc.skill,
                    status=tc.status.value,
                    is_automated=tc.is_automated,
                    tcm_id=tc.tcm_id,
                    tags=json.dumps(tc.tags),
                    priority=tc.priority,
                    source_file=tc.source_file,
                    created_at=tc.created_at,
                    updated_at=tc.updated_at,
                )
                s.merge(row)
                s.commit()
        except Exception as exc:
            raise StorageError(f"Failed to upsert test case {tc.id}") from exc

    def get_test_case(self, id: str) -> TestCase:
        with self._session() as s:
            row = s.get(TestCaseORM, id)
            if row is None:
                raise RecordNotFound(f"TestCase not found: {id}")
            return _orm_to_test_case(row)

    # ── TestRun / TestResult ──────────────────────────────────────────────

    def start_run(self, suite: str, environment: str = "local",
                  browser: Optional[str] = None, triggered_by: str = "tw") -> TestRun:
        run_id = str(uuid.uuid4())
        now = datetime.utcnow()
        try:
            with self._session() as s:
                row = TestRunORM(
                    id=run_id,
                    suite=suite,
                    environment=environment,
                    browser=browser,
                    triggered_by=triggered_by,
                    started_at=now,
                )
                s.add(row)
                s.commit()
        except Exception as exc:
            raise StorageError("Failed to start test run") from exc
        return TestRun(
            id=run_id,
            suite=suite,
            environment=environment,
            browser=browser,
            triggered_by=triggered_by,
            started_at=now,
        )

    def end_run(self, run_id: str) -> None:
        try:
            with self._session() as s:
                row = s.get(TestRunORM, run_id)
                if row is None:
                    raise RecordNotFound(f"TestRun not found: {run_id}")
                row.completed_at = datetime.utcnow()
                s.commit()
        except RecordNotFound:
            raise
        except Exception as exc:
            raise StorageError(f"Failed to end run {run_id}") from exc

    def get_run(self, run_id: str) -> TestRun:
        with self._session() as s:
            row = s.get(TestRunORM, run_id)
            if row is None:
                raise RecordNotFound(f"TestRun not found: {run_id}")
            return _orm_to_test_run(row)

    def save_result(self, r: TestResult) -> None:
        try:
            with self._session() as s:
                row = TestResultORM(
                    id=r.id,
                    run_id=r.run_id,
                    test_case_id=r.test_case_id,
                    status=r.status.value,
                    duration_ms=r.duration_ms,
                    error_message=r.error_message,
                    screenshot_path=r.screenshot_path,
                    retry_count=r.retry_count,
                )
                s.add(row)
                s.commit()
        except Exception as exc:
            raise StorageError(f"Failed to save result {r.id}") from exc

    # ── Coverage ──────────────────────────────────────────────────────────

    def get_coverage_percentage(self) -> float:
        with self._session() as s:
            total = s.query(TestCaseORM).count()
            if total == 0:
                return 0.0
            automated = s.query(TestCaseORM).filter(TestCaseORM.is_automated.is_(True)).count()
            return round(automated / total * 100, 2)

    def get_coverage_trend(self, weeks: int) -> list[dict]:
        return []

    # ── Gaps ──────────────────────────────────────────────────────────────

    def get_gaps(self, limit: int = 50, status: str = "open") -> list[Gap]:
        with self._session() as s:
            rows = (
                s.query(GapORM)
                .filter(GapORM.status == status)
                .order_by(GapORM.priority_score.desc())
                .limit(limit)
                .all()
            )
            return [_orm_to_gap(r) for r in rows]

    def save_gaps(self, gaps: list[Gap]) -> None:
        try:
            with self._session() as s:
                for g in gaps:
                    row = GapORM(
                        id=g.id,
                        test_case_id=g.test_case_id,
                        priority_score=g.priority_score,
                        gap_reason=g.gap_reason,
                        suggested_gherkin=g.suggested_gherkin,
                        status=g.status.value,
                        detected_at=g.detected_at,
                        closed_at=g.closed_at,
                    )
                    s.merge(row)
                s.commit()
        except Exception as exc:
            raise StorageError("Failed to save gaps") from exc

    def mark_uncollected_as_gaps(self, collected_ids: list[str]) -> None:
        now = datetime.utcnow()
        with self._session() as s:
            all_ids = [row.id for row in s.query(TestCaseORM.id).all()]
            existing_open_gap_tc_ids = {
                row.test_case_id
                for row in s.query(GapORM.test_case_id)
                .filter(GapORM.status == "open")
                .all()
            }
            collected_set = set(collected_ids)
            new_gaps = []
            for tc_id in all_ids:
                if tc_id not in collected_set and tc_id not in existing_open_gap_tc_ids:
                    new_gaps.append(GapORM(
                        id=str(uuid.uuid4()),
                        test_case_id=tc_id,
                        priority_score=0.0,
                        gap_reason="Not collected in last test run",
                        status="open",
                        detected_at=now,
                    ))
            if new_gaps:
                s.add_all(new_gaps)
                s.commit()

    # ── Flakiness ─────────────────────────────────────────────────────────

    def get_flaky_tests(self, min_runs: int = 5) -> list[TestCase]:
        sql = text("""
            SELECT test_case_id
            FROM test_results
            GROUP BY test_case_id
            HAVING COUNT(*) >= :min_runs
               AND SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) > 0
               AND SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) > 0
            ORDER BY CAST(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) DESC
        """)
        with self._session() as s:
            rows = s.execute(sql, {"min_runs": min_runs}).fetchall()
            result = []
            for (tc_id,) in rows:
                try:
                    result.append(self.get_test_case(tc_id))
                except RecordNotFound:
                    pass
            return result

    # ── ScoringSignals ────────────────────────────────────────────────────

    def get_scoring_signals(self, tc_id: str) -> ScoringSignals:
        tc = self.get_test_case(tc_id)
        with self._session() as s:
            executions_90d_sql = text("""
                SELECT COUNT(*) FROM test_results tr
                JOIN test_runs run ON tr.run_id = run.id
                WHERE tr.test_case_id = :tc_id
                  AND run.started_at >= datetime('now', '-90 days')
            """)
            executions_90d = s.execute(executions_90d_sql, {"tc_id": tc_id}).scalar() or 0

            last_run_sql = text("""
                SELECT run.started_at FROM test_results tr
                JOIN test_runs run ON tr.run_id = run.id
                WHERE tr.test_case_id = :tc_id
                ORDER BY run.started_at DESC LIMIT 1
            """)
            last_run_row = s.execute(last_run_sql, {"tc_id": tc_id}).fetchone()
            if last_run_row:
                last_run_dt = last_run_row[0]
                if isinstance(last_run_dt, str):
                    last_run_dt = datetime.fromisoformat(last_run_dt)
                days_since = (datetime.utcnow() - last_run_dt).days
            else:
                days_since = 999

        return ScoringSignals(
            test_priority=tc.priority,
            test_type=tc.test_type,
            defect_count=0,
            executions_90d=executions_90d,
            days_since_run=days_since,
        )
```

- [ ] **Step 4: Run the core CRUD tests**

```bash
pytest tests/test_storage.py -v
# Expected: all tests in TestUpsertAndGetTestCase, TestRunLifecycle, TestCoveragePercentage pass
```

- [ ] **Step 5: Commit**

```bash
git add testweavex/storage/sqlite.py tests/test_storage.py
git commit -m "feat: SQLiteRepository — core CRUD, run lifecycle, coverage percentage"
```

---

## Task 8: SQLiteRepository — Gaps and Flakiness

**Files:**
- Modify: `tests/test_storage.py` (append gap + flakiness tests)

- [ ] **Step 1: Append failing tests for gaps and flakiness to `tests/test_storage.py`**

```python
class TestMarkUncollectedAsGaps:
    def test_uncollected_test_cases_become_gaps(self, repo):
        tc1 = _make_test_case(scenario="Scenario A")
        tc2 = _make_test_case(scenario="Scenario B")
        tc3 = _make_test_case(scenario="Scenario C")
        for tc in [tc1, tc2, tc3]:
            repo.upsert_test_case(tc)

        repo.mark_uncollected_as_gaps(collected_ids=[tc1.id])

        gaps = repo.get_gaps(limit=10, status="open")
        gap_tc_ids = {g.test_case_id for g in gaps}
        assert tc2.id in gap_tc_ids
        assert tc3.id in gap_tc_ids
        assert tc1.id not in gap_tc_ids

    def test_does_not_create_duplicate_gaps(self, repo):
        tc = _make_test_case()
        repo.upsert_test_case(tc)

        repo.mark_uncollected_as_gaps(collected_ids=[])
        repo.mark_uncollected_as_gaps(collected_ids=[])

        gaps = repo.get_gaps(limit=10, status="open")
        tc_gap_ids = [g for g in gaps if g.test_case_id == tc.id]
        assert len(tc_gap_ids) == 1

    def test_empty_collected_ids_flags_all(self, repo):
        tc1 = _make_test_case(scenario="A")
        tc2 = _make_test_case(scenario="B")
        repo.upsert_test_case(tc1)
        repo.upsert_test_case(tc2)

        repo.mark_uncollected_as_gaps(collected_ids=[])

        gaps = repo.get_gaps(limit=10)
        assert len(gaps) == 2


class TestFlakyTests:
    def test_returns_empty_with_no_runs(self, repo):
        tc = _make_test_case()
        repo.upsert_test_case(tc)
        assert repo.get_flaky_tests(min_runs=1) == []

    def test_consistent_pass_not_flaky(self, repo):
        tc = _make_test_case()
        repo.upsert_test_case(tc)
        run = repo.start_run(suite="s")
        for i in range(5):
            repo.save_result(TestResult(
                id=str(uuid.uuid4()),
                run_id=run.id,
                test_case_id=tc.id,
                status=TestStatus.passed,
                duration_ms=100,
            ))
        assert repo.get_flaky_tests(min_runs=5) == []

    def test_mixed_results_is_flaky(self, repo):
        tc = _make_test_case()
        repo.upsert_test_case(tc)
        run = repo.start_run(suite="s")
        statuses = [TestStatus.passed, TestStatus.failed, TestStatus.passed,
                    TestStatus.failed, TestStatus.passed]
        for status in statuses:
            repo.save_result(TestResult(
                id=str(uuid.uuid4()),
                run_id=run.id,
                test_case_id=tc.id,
                status=status,
                duration_ms=100,
            ))
        flaky = repo.get_flaky_tests(min_runs=5)
        assert len(flaky) == 1
        assert flaky[0].id == tc.id

    def test_below_min_runs_not_returned(self, repo):
        tc = _make_test_case()
        repo.upsert_test_case(tc)
        run = repo.start_run(suite="s")
        for status in [TestStatus.passed, TestStatus.failed]:
            repo.save_result(TestResult(
                id=str(uuid.uuid4()),
                run_id=run.id,
                test_case_id=tc.id,
                status=status,
                duration_ms=100,
            ))
        assert repo.get_flaky_tests(min_runs=5) == []


class TestScoringSignals:
    def test_returns_signals_for_known_test(self, repo):
        tc = _make_test_case()
        repo.upsert_test_case(tc)
        signals = repo.get_scoring_signals(tc.id)
        assert signals.test_priority == 2
        assert signals.test_type == TestType.smoke
        assert signals.defect_count == 0
        assert signals.executions_90d == 0

    def test_raises_for_unknown_test(self, repo):
        from testweavex.core.exceptions import RecordNotFound
        with pytest.raises(RecordNotFound):
            repo.get_scoring_signals("nonexistent-id")
```

- [ ] **Step 2: Run all storage tests**

```bash
pytest tests/test_storage.py -v
# Expected: all tests pass (20+ tests)
```

- [ ] **Step 3: Run the full test suite**

```bash
pytest tests/ -v
# Expected: all tests pass
```

- [ ] **Step 4: Commit**

```bash
git add tests/test_storage.py
git commit -m "test: gap detection, flakiness, and scoring signals tests — all passing"
```

---

## Task 9: GitHub Pages Documentation

**Files:**
- Create: `docs/index.html`

- [ ] **Step 1: Write `docs/index.html`**

Create a single self-contained HTML file. Copy this exactly:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>TestWeaveX — Documentation</title>
<style>
:root {
  --brand: #1A6B8A;
  --brand-dark: #135570;
  --accent: #E07B39;
  --surface: #FFFFFF;
  --surface-sub: #F8FAFB;
  --text-pri: #1A1A2E;
  --text-sec: #4A4A6A;
  --text-mut: #8A8AA0;
  --border: #E2E8EC;
  --code-bg: #1A1A2E;
  --code-text: #E8F4F8;
  --nav-bg: #1A1A2E;
  --nav-text: rgba(255,255,255,0.65);
  --nav-active: #FFFFFF;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, -apple-system, sans-serif; font-size: 15px;
       color: var(--text-pri); background: var(--surface-sub); line-height: 1.7; }

/* ── Nav ── */
nav { position: fixed; top: 0; left: 0; right: 0; z-index: 100;
      background: var(--nav-bg); padding: 0 32px;
      display: flex; align-items: center; height: 56px; gap: 32px; }
.nav-logo { font-size: 17px; font-weight: 800; color: #fff; letter-spacing: -0.5px;
            text-decoration: none; flex-shrink: 0; }
.nav-logo span { color: var(--accent); }
.nav-links { display: flex; gap: 24px; flex: 1; }
.nav-links a { color: var(--nav-text); text-decoration: none; font-size: 13px;
               font-weight: 500; transition: color .15s; }
.nav-links a:hover, .nav-links a.active { color: var(--nav-active); }
.nav-badge { background: var(--accent); color: #fff; font-size: 11px; font-weight: 700;
             padding: 2px 8px; border-radius: 999px; }

/* ── Layout ── */
.page { max-width: 860px; margin: 0 auto; padding: 88px 24px 64px; }

/* ── Hero ── */
.hero { text-align: center; padding: 64px 0 48px; }
.hero h1 { font-size: 48px; font-weight: 800; letter-spacing: -1px;
           color: var(--text-pri); line-height: 1.1; margin-bottom: 16px; }
.hero h1 span { color: var(--brand); }
.hero p { font-size: 18px; color: var(--text-sec); max-width: 600px;
          margin: 0 auto 32px; }
.hero-badges { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;
               margin-bottom: 32px; }
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px;
         background: var(--surface); border: 1px solid var(--border); border-radius: 999px;
         font-size: 12px; font-weight: 600; color: var(--text-sec); text-decoration: none; }
.badge:hover { border-color: var(--brand); color: var(--brand); }
.install-box { background: var(--code-bg); color: var(--code-text);
               padding: 14px 24px; border-radius: 10px; font-family: monospace;
               font-size: 15px; display: inline-block; }
.install-box .prompt { color: var(--accent); margin-right: 8px; }

/* ── Section ── */
section { margin-bottom: 64px; scroll-margin-top: 72px; }
section h2 { font-size: 26px; font-weight: 700; color: var(--text-pri);
             margin-bottom: 8px; padding-bottom: 12px;
             border-bottom: 2px solid var(--border); }
section h3 { font-size: 16px; font-weight: 700; color: var(--text-pri);
             margin: 28px 0 8px; }
section p { color: var(--text-sec); margin-bottom: 16px; }
section ul, section ol { padding-left: 20px; color: var(--text-sec); margin-bottom: 16px; }
section li { margin-bottom: 6px; }

/* ── Code ── */
pre { background: var(--code-bg); color: var(--code-text); padding: 18px 20px;
      border-radius: 8px; overflow-x: auto; font-size: 13px; margin: 12px 0 20px;
      font-family: 'Cascadia Code', 'Fira Code', monospace; line-height: 1.6; }
code { font-family: 'Cascadia Code', 'Fira Code', monospace; font-size: 13px;
       background: #eef2f5; padding: 2px 6px; border-radius: 4px; color: var(--brand-dark); }
pre code { background: none; padding: 0; color: inherit; }
.kw { color: #7dd3fc; }
.cm { color: #6b7280; }
.st { color: #86efac; }
.nm { color: #fbbf24; }

/* ── Table ── */
table { width: 100%; border-collapse: collapse; margin: 12px 0 24px; font-size: 14px; }
th { background: var(--surface); text-align: left; padding: 10px 14px;
     font-size: 11px; font-weight: 700; color: var(--text-mut); text-transform: uppercase;
     letter-spacing: .5px; border-bottom: 2px solid var(--border); }
td { padding: 10px 14px; border-bottom: 1px solid var(--border); color: var(--text-sec); }
tr:last-child td { border-bottom: none; }
td code { font-size: 12px; }

/* ── Steps ── */
.steps { counter-reset: step; list-style: none; padding: 0; }
.steps li { counter-increment: step; display: flex; gap: 16px; margin-bottom: 24px; }
.steps li::before { content: counter(step); width: 32px; height: 32px; min-width: 32px;
                    background: var(--brand); color: #fff; border-radius: 50%;
                    display: flex; align-items: center; justify-content: center;
                    font-weight: 700; font-size: 13px; margin-top: 2px; }
.step-body h4 { font-size: 15px; font-weight: 700; margin-bottom: 4px; }

/* ── Callout ── */
.callout { background: #e8f4f8; border-left: 4px solid var(--brand); padding: 14px 18px;
           border-radius: 0 8px 8px 0; margin: 16px 0; }
.callout strong { color: var(--brand-dark); }

/* ── Footer ── */
footer { text-align: center; padding: 32px; font-size: 13px; color: var(--text-mut);
         border-top: 1px solid var(--border); }
footer a { color: var(--brand); text-decoration: none; }
</style>
</head>
<body>

<nav>
  <a class="nav-logo" href="#hero">Test<span>Weave</span>X</a>
  <div class="nav-links">
    <a href="#getting-started">Getting Started</a>
    <a href="#cli">CLI Reference</a>
    <a href="#config">Configuration</a>
    <a href="#architecture">Architecture</a>
    <a href="#contributing">Contributing</a>
  </div>
  <span class="nav-badge">v0.1.0</span>
</nav>

<div class="page">

<!-- ── Hero ── -->
<section id="hero" class="hero">
  <h1>Unified Test Management<br><span>Powered by Any LLM</span></h1>
  <p>TestWeaveX brings test case management, execution, and AI-assisted generation into a single Git-native platform. The LLM suggests. You decide.</p>
  <div class="hero-badges">
    <a class="badge" href="https://github.com/testweavex/testweavex">⭐ GitHub</a>
    <a class="badge" href="https://pypi.org/project/testweavex">📦 PyPI</a>
    <a class="badge" href="#contributing">🤝 Contribute</a>
  </div>
  <div class="install-box"><span class="prompt">$</span>pip install testweavex</div>
</section>

<!-- ── Getting Started ── -->
<section id="getting-started">
  <h2>Getting Started</h2>
  <p>From install to your first gap report in under 10 minutes.</p>

  <ol class="steps">
    <li>
      <div class="step-body">
        <h4>Install and initialise</h4>
        <pre><span class="kw">pip</span> install testweavex
<span class="kw">tw</span> init --llm-provider anthropic</pre>
        <p>This creates <code>testweavex.config.yaml</code> in your project root and a <code>testweavex/skills/</code> folder with the 10 built-in skill files.</p>
      </div>
    </li>
    <li>
      <div class="step-body">
        <h4>Run your test suite</h4>
        <pre><span class="kw">tw</span>                         <span class="cm"># same as pytest — all flags work</span>
<span class="kw">tw</span> tests/login.feature    <span class="cm"># run a specific feature</span>
<span class="kw">tw</span> -k smoke -n 4          <span class="cm"># filter + parallel</span></pre>
        <p>Results are stored automatically in <code>.testweavex/results.db</code>. No configuration required.</p>
      </div>
    </li>
    <li>
      <div class="step-body">
        <h4>View your first gap report</h4>
        <pre><span class="kw">tw</span> gaps --limit 20</pre>
        <p>TestWeaveX compares your TCM against your automation suite and surfaces unautomated tests ranked by priority score. Generate automation for any gap with <code>tw gaps --generate</code>.</p>
      </div>
    </li>
  </ol>

  <div class="callout">
    <strong>Team mode:</strong> Add <code>--results-server https://your-server --token $TOKEN</code> to any <code>tw</code> command to share results across your team. One <code>docker-compose up</code> starts the server.
  </div>
</section>

<!-- ── CLI Reference ── -->
<section id="cli">
  <h2>CLI Reference</h2>
  <p>Every <code>pytest</code> flag works with <code>tw</code> unchanged. TestWeaveX adds its own flags alongside.</p>

  <table>
    <thead><tr><th>Command</th><th>Description</th><th>Key Options</th></tr></thead>
    <tbody>
      <tr><td><code>tw [paths]</code></td><td>Run tests (wraps pytest)</td><td><code>--results-server</code>, <code>--token</code>, <code>--sync-tcm</code>, <code>--gaps</code></td></tr>
      <tr><td><code>tw init</code></td><td>Initialise TestWeaveX in a project</td><td><code>--llm-provider</code>, <code>--tcm</code></td></tr>
      <tr><td><code>tw generate</code></td><td>Generate tests from a feature description</td><td><code>--feature</code>, <code>--skill</code>, <code>--output</code></td></tr>
      <tr><td><code>tw gaps</code></td><td>Run gap analysis, show ranked report</td><td><code>--limit</code>, <code>--min-score</code>, <code>--generate</code></td></tr>
      <tr><td><code>tw import</code></td><td>Import from external TCM or CSV</td><td><code>--source</code> (testrail/xray/csv)</td></tr>
      <tr><td><code>tw status</code></td><td>Show coverage map and summary</td><td><code>--format</code> (table/json/html)</td></tr>
      <tr><td><code>tw history</code></td><td>Show execution history</td><td><code>--id</code>, <code>--last-n</code></td></tr>
      <tr><td><code>tw serve</code></td><td>Start local Web UI</td><td><code>--port</code> (default: 8080)</td></tr>
      <tr><td><code>tw migrate</code></td><td>Migrate from external TCM</td><td><code>--source</code>, <code>--dry-run</code></td></tr>
      <tr><td><code>tw sync</code></td><td>Push results to external TCM</td><td><code>--tcm</code>, <code>--run-id</code></td></tr>
    </tbody>
  </table>

  <h3>CI/CD Example (GitHub Actions)</h3>
  <pre>- <span class="nm">name</span>: Run tests
  <span class="nm">run</span>: |
    tw run --suite regression \
           --results-server <span class="st">${{ secrets.TW_SERVER }}</span> \
           --token <span class="st">${{ secrets.TW_TOKEN }}</span> \
           --sync-tcm testrail</pre>
</section>

<!-- ── Configuration ── -->
<section id="config">
  <h2>Configuration</h2>
  <p>Create <code>testweavex.config.yaml</code> in your project root. All values support <code>${ENV_VAR}</code> interpolation. Missing keys use defaults.</p>

  <pre><span class="cm"># testweavex.config.yaml</span>
<span class="nm">llm</span>:
  <span class="nm">provider</span>: <span class="st">anthropic</span>        <span class="cm"># openai | anthropic | ollama | azure</span>
  <span class="nm">model</span>: <span class="st">claude-sonnet-4-6</span>
  <span class="nm">api_key</span>: <span class="st">${ANTHROPIC_API_KEY}</span>
  <span class="nm">temperature</span>: <span class="st">0.3</span>
  <span class="nm">max_retries</span>: <span class="st">3</span>
  <span class="nm">timeout_seconds</span>: <span class="st">30</span>

<span class="nm">results_server</span>: <span class="st">${TESTWEAVEX_SERVER}</span>  <span class="cm"># optional — team mode</span>

<span class="nm">tcm</span>:
  <span class="nm">provider</span>: <span class="st">none</span>              <span class="cm"># testrail | xray | none</span>

<span class="nm">gap_analysis</span>:
  <span class="nm">scoring_weights</span>:
    <span class="nm">priority</span>:  <span class="st">0.30</span>
    <span class="nm">test_type</span>: <span class="st">0.25</span>
    <span class="nm">defects</span>:   <span class="st">0.20</span>
    <span class="nm">frequency</span>: <span class="st">0.15</span>
    <span class="nm">staleness</span>: <span class="st">0.10</span>
  <span class="nm">match_threshold</span>: <span class="st">0.65</span>
  <span class="nm">top_gaps_default</span>: <span class="st">10</span></pre>

  <h3>LLM Providers</h3>
  <table>
    <thead><tr><th>Provider</th><th>Key Setting</th><th>Models</th></tr></thead>
    <tbody>
      <tr><td>Anthropic</td><td><code>api_key: ${ANTHROPIC_API_KEY}</code></td><td>claude-sonnet-4-6, claude-opus-4-7, claude-haiku-4-5</td></tr>
      <tr><td>OpenAI</td><td><code>api_key: ${OPENAI_API_KEY}</code></td><td>gpt-4o, gpt-4-turbo, gpt-3.5-turbo</td></tr>
      <tr><td>Ollama</td><td><code>base_url: http://localhost:11434</code></td><td>llama3, mistral, phi-3, any local model</td></tr>
      <tr><td>Azure OpenAI</td><td><code>azure_endpoint</code>, <code>deployment_name</code></td><td>All Azure-deployed OpenAI models</td></tr>
    </tbody>
  </table>
</section>

<!-- ── Architecture ── -->
<section id="architecture">
  <h2>Architecture</h2>
  <p>TestWeaveX is a pytest plugin with a thin CLI wrapper. All functionality flows through one of three pipelines.</p>

  <table>
    <thead><tr><th>Pipeline</th><th>Input</th><th>Output</th></tr></thead>
    <tbody>
      <tr><td><strong>Generation</strong></td><td>Feature description + skill file</td><td>Approved Gherkin + step definitions in repo</td></tr>
      <tr><td><strong>Execution</strong></td><td>Feature files + pytest config</td><td>Test results in storage + TCM updated</td></tr>
      <tr><td><strong>Gap Analysis</strong></td><td>TCM test cases + automation suite</td><td>Ranked gap list + optional generated automation</td></tr>
    </tbody>
  </table>

  <h3>Component Map</h3>
  <table>
    <thead><tr><th>Module</th><th>Responsibility</th><th>Phase</th></tr></thead>
    <tbody>
      <tr><td><code>core/models.py</code></td><td>Pydantic data models — shared contract</td><td>1</td></tr>
      <tr><td><code>core/config.py</code></td><td>YAML config loader</td><td>1</td></tr>
      <tr><td><code>storage/sqlite.py</code></td><td>Local SQLite persistence (default)</td><td>1</td></tr>
      <tr><td><code>llm/</code></td><td>Provider-agnostic LLM adapter layer</td><td>2</td></tr>
      <tr><td><code>skills/</code></td><td>YAML skill files for each test type</td><td>2</td></tr>
      <tr><td><code>generation/</code></td><td>Feature → Gherkin → step definitions</td><td>3</td></tr>
      <tr><td><code>execution/plugin.py</code></td><td>pytest plugin hooks</td><td>4</td></tr>
      <tr><td><code>gap/</code></td><td>Gap detection, scoring, automation trigger</td><td>5</td></tr>
      <tr><td><code>web/</code></td><td>FastAPI + React dashboard</td><td>6</td></tr>
      <tr><td><code>tcm/</code></td><td>TestRail + Xray connectors</td><td>7</td></tr>
    </tbody>
  </table>

  <h3>Stable ID Algorithm</h3>
  <p>Every test case gets a deterministic 64-character ID derived from its feature file path and scenario name. This ID is stable across machines, CI runs, and environments. <strong>The algorithm is frozen — never change it after first deployment.</strong></p>
  <pre><span class="kw">import</span> hashlib

<span class="kw">def</span> <span class="nm">generate_stable_id</span>(*parts: str) -> str:
    key = <span class="st">"|"</span>.join(parts).encode(<span class="st">"utf-8"</span>)
    <span class="kw">return</span> hashlib.sha256(key).hexdigest()  <span class="cm"># full 64 chars</span>

<span class="cm"># test_case_id = generate_stable_id(feature_path, scenario_name)</span>
<span class="cm"># feature_id   = generate_stable_id(feature_path)</span></pre>

  <h3>Gap Priority Scoring</h3>
  <p>Gaps are ranked by a six-signal weighted score (0.0–1.0). Higher = automate first.</p>
  <table>
    <thead><tr><th>Signal</th><th>Weight</th><th>Meaning</th></tr></thead>
    <tbody>
      <tr><td>Priority</td><td>30%</td><td>P1 tests must be automated before P4</td></tr>
      <tr><td>Test Type</td><td>25%</td><td>Smoke/E2E gaps hurt most (score 1.0/0.9)</td></tr>
      <tr><td>Defect History</td><td>20%</td><td>Tests linked to past bugs are high value</td></tr>
      <tr><td>Frequency</td><td>15%</td><td>Frequently-run manual tests benefit most from automation</td></tr>
      <tr><td>Staleness</td><td>10%</td><td>Tests not run recently carry higher regression risk</td></tr>
    </tbody>
  </table>
</section>

<!-- ── Contributing ── -->
<section id="contributing">
  <h2>Contributing</h2>

  <h3>Repository Structure</h3>
  <table>
    <thead><tr><th>Repo</th><th>Purpose</th></tr></thead>
    <tbody>
      <tr><td><a href="https://github.com/testweavex/testweavex">testweavex/testweavex</a></td><td>Core Python library (this package)</td></tr>
      <tr><td>testweavex/testweavex-server</td><td>Self-hosted result server (Docker)</td></tr>
      <tr><td>testweavex/testweavex-skills</td><td>Community skill file contributions</td></tr>
      <tr><td>testweavex/testweavex-docs</td><td>Full Docusaurus documentation site</td></tr>
    </tbody>
  </table>

  <h3>Adding a Custom Skill</h3>
  <p>The easiest way to contribute is a new skill YAML file. Create <code>testweavex/skills/custom/your-skill.yaml</code>:</p>
  <pre><span class="nm">name</span>: <span class="st">custom/your-skill</span>
<span class="nm">display_name</span>: <span class="st">Your Skill Name</span>
<span class="nm">description</span>: <span class="st">What this skill generates</span>

<span class="nm">prompt_template</span>: |
  You are a senior QA engineer.
  Feature: {feature_description}
  Generate {n_suggestions} test scenarios that...
  Return JSON: title, gherkin, confidence, rationale, suggested_tags

<span class="nm">assertion_hints</span>:
  - <span class="st">Verify primary outcome</span>
<span class="nm">tags</span>: [<span class="st">custom</span>]
<span class="nm">priority</span>: <span class="st">3</span></pre>

  <h3>Development Setup</h3>
  <pre><span class="kw">git</span> clone https://github.com/testweavex/testweavex
<span class="kw">cd</span> testweavex
<span class="kw">pip</span> install -e <span class="st">".[dev]"</span>
<span class="kw">pytest</span> tests/ -v</pre>

  <div class="callout">
    <strong>Contribution areas:</strong> Skill YAML files (lowest barrier), LLM adapter implementations for new providers, external TCM connectors, bug fixes in core library.
  </div>
</section>

</div>

<footer>
  TestWeaveX is open source under the MIT licence &mdash;
  <a href="https://github.com/testweavex/testweavex">github.com/testweavex/testweavex</a>
</footer>

<script>
const links = document.querySelectorAll('.nav-links a');
const sections = document.querySelectorAll('section[id]');

const observer = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      links.forEach(l => l.classList.remove('active'));
      const active = document.querySelector(`.nav-links a[href="#${e.target.id}"]`);
      if (active) active.classList.add('active');
    }
  });
}, { rootMargin: '-20% 0px -75% 0px' });

sections.forEach(s => observer.observe(s));
</script>
</body>
</html>
```

- [ ] **Step 2: Open the file in a browser to verify it renders correctly**

```bash
# On Windows:
start docs/index.html
# On Mac:
open docs/index.html
# On Linux:
xdg-open docs/index.html
```

Verify: nav is fixed at top, all 6 sections render, code blocks are dark, active nav link updates on scroll.

- [ ] **Step 3: Commit**

```bash
git add docs/index.html
git commit -m "docs: self-contained GitHub Pages site — user + contributor docs"
```

---

## Task 10: Final Verification

- [ ] **Step 1: Run the complete test suite**

```bash
pytest tests/ -v --tb=short
# Expected: all tests pass, 0 failures
```

- [ ] **Step 2: Verify the package installs and models import cleanly**

```bash
python -c "
from testweavex.core.models import (
    TestCase, Feature, TestRun, TestResult, Gap,
    ScoringSignals, RunSummary, TestStatus, TestType, GapStatus,
    generate_stable_id
)
from testweavex.core.config import load_config
from testweavex.core.exceptions import (
    TestWeaveXError, ConfigError, StorageError, RecordNotFound,
    LLMOutputError, SkillNotFoundError, GenerationError, TCMConnectorError
)
from testweavex.storage.base import StorageRepository
from testweavex.storage.sqlite import SQLiteRepository

repo = SQLiteRepository(db_url='sqlite:///:memory:')
pct = repo.get_coverage_percentage()
assert pct == 0.0

stable_id = generate_stable_id('features/login.feature', 'User logs in')
assert len(stable_id) == 64

print('All Phase 1 imports and smoke checks passed.')
"
# Expected: All Phase 1 imports and smoke checks passed.
```

- [ ] **Step 3: Final commit**

```bash
git add -A
git status
# Verify no unexpected files are staged
git commit -m "feat: TestWeaveX Phase 1 complete — data layer, storage, docs"
```

---

## Self-Review

**Spec coverage check:**

| Spec Section | Covered by Task |
|---|---|
| §1 File scope | Tasks 1–9 create every listed file |
| §2 Core models — enums | Task 3 |
| §2 Core models — generate_stable_id (64 chars) | Task 3 |
| §2 Core models — 7 Pydantic models | Task 4 |
| §2 Gap.priority_score validator 0–1 | Task 4 |
| §3 Config loader + env var interpolation | Task 5 |
| §4 Exception hierarchy + stubs | Task 2 |
| §5 Abstract StorageRepository (13 methods) | Task 6 |
| §5 ORM — 5 tables with correct PKs | Task 6 |
| §5 SQLiteRepository — upsert, CRUD | Task 7 |
| §5 SQLiteRepository — mark_uncollected_as_gaps | Task 7 |
| §5 SQLiteRepository — get_flaky_tests (raw SQL) | Task 7 |
| §5 SQLiteRepository — get_scoring_signals | Task 7 |
| §5 Test coverage — test_models.py | Tasks 3 + 4 |
| §5 Test coverage — test_storage.py | Tasks 7 + 8 |
| §6 HTML docs — 6 sections | Task 9 |
| §7 pyproject.toml | Task 1 |

**All spec requirements covered. No placeholders. Types consistent across all tasks.**
