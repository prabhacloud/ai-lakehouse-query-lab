"""Deterministic controls for an AI-assisted analytics optimization lab."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Iterable, Mapping, Sequence


PROHIBITED_SQL = re.compile(
    r"\b(ALTER|CALL|CREATE|DELETE|DROP|GRANT|INSERT|MERGE|REVOKE|"
    r"TRUNCATE|UNLOAD|UPDATE)\b",
    re.IGNORECASE,
)
COMMENT_OR_SEPARATOR = re.compile(r"(--|/\*|\*/|;)")


@dataclass(frozen=True)
class Proposal:
    engine: str
    sql: str
    rationale: str
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class Measurement:
    engine: str
    data_scanned_bytes: int
    engine_millis: int
    result_hash: str
    row_count: int


@dataclass(frozen=True)
class Verdict:
    accepted: bool
    reasons: tuple[str, ...]
    savings_fraction: float


def parse_proposal(text: str) -> Proposal:
    """Parse the model's strict JSON response without accepting prose."""
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("proposal must be a JSON object")
    required = {"engine", "sql", "rationale", "assumptions"}
    if set(value) != required:
        raise ValueError(f"proposal keys must be exactly {sorted(required)}")
    assumptions = value["assumptions"]
    if not isinstance(assumptions, list) or not all(
        isinstance(item, str) for item in assumptions
    ):
        raise ValueError("assumptions must be a list of strings")
    return Proposal(
        engine=str(value["engine"]).lower(),
        sql=str(value["sql"]).strip(),
        rationale=str(value["rationale"]).strip(),
        assumptions=tuple(assumptions),
    )


def validate_read_only_sql(
    sql: str,
    *,
    allowed_tables: Iterable[str],
    allowed_engines: Iterable[str] = ("athena", "emr", "redshift"),
    engine: str,
) -> tuple[str, ...]:
    """Return rejection reasons for a candidate query."""
    reasons: list[str] = []
    normalized = " ".join(sql.strip().split())
    if not re.match(r"^(SELECT|WITH)\b", normalized, re.IGNORECASE):
        reasons.append("query must begin with SELECT or WITH")
    if PROHIBITED_SQL.search(normalized):
        reasons.append("query contains a prohibited operation")
    if COMMENT_OR_SEPARATOR.search(sql):
        reasons.append("comments and statement separators are prohibited")
    if engine.lower() not in {item.lower() for item in allowed_engines}:
        reasons.append("engine is not allow-listed")

    def normalize_identifier(value: str) -> str:
        return value.replace('"', "").lower()

    allowed = {normalize_identifier(item) for item in allowed_tables}
    referenced = {
        normalize_identifier(match)
        for match in re.findall(
            r"\b(?:FROM|JOIN)\s+([A-Za-z0-9_.$/\"-]+)",
            normalized,
            re.IGNORECASE,
        )
    }
    unknown = sorted(item for item in referenced if item not in allowed)
    if unknown:
        reasons.append(f"query references unknown tables: {', '.join(unknown)}")
    return tuple(reasons)


def canonical_result_hash(
    rows: Sequence[Sequence[object]], *, order_sensitive: bool = False
) -> str:
    """Hash a result set with stable JSON encoding and optional row sorting."""
    encoded = [
        json.dumps(list(row), sort_keys=True, separators=(",", ":"), default=str)
        for row in rows
    ]
    if not order_sensitive:
        encoded.sort()
    payload = "\n".join(encoded).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def decide(
    baseline: Measurement,
    candidate: Measurement,
    *,
    minimum_savings_fraction: float = 0.10,
) -> Verdict:
    reasons: list[str] = []
    if candidate.result_hash != baseline.result_hash:
        reasons.append("result hashes differ")
    if candidate.row_count != baseline.row_count:
        reasons.append("row counts differ")
    if baseline.data_scanned_bytes <= 0:
        savings = 0.0
        reasons.append("baseline has no measurable scan")
    else:
        savings = (
            baseline.data_scanned_bytes - candidate.data_scanned_bytes
        ) / baseline.data_scanned_bytes
        if savings < minimum_savings_fraction:
            reasons.append(
                f"scan savings {savings:.1%} are below "
                f"{minimum_savings_fraction:.1%}"
            )
    return Verdict(not reasons, tuple(reasons), savings)


def break_even_runs(
    *,
    ai_review_cost_usd: float,
    validation_cost_usd: float,
    savings_per_run_usd: float,
) -> int | None:
    """Return repeat executions required to recover review and validation cost."""
    if savings_per_run_usd <= 0:
        return None
    return math.ceil(
        (ai_review_cost_usd + validation_cost_usd) / savings_per_run_usd
    )


def proposal_prompt(
    *,
    sql: str,
    schema: Mapping[str, Sequence[str]],
    explain_plan: str,
) -> str:
    return (
        "You are proposing, not executing, a read-only analytics optimization. "
        "Return one JSON object with exactly these keys: engine, sql, rationale, "
        "assumptions. engine must be athena, emr, or redshift. Do not use DDL or "
        "DML. Never invent tables or columns.\n\n"
        f"Allowed schema:\n{json.dumps(schema, sort_keys=True)}\n\n"
        f"Original SQL:\n{sql}\n\n"
        f"Athena EXPLAIN plan:\n{explain_plan}"
    )

