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
