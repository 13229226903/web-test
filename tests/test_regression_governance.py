#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Self-checks for the attempt recorder and summary classifier (no product site).

The probe test file must live inside the repository so the root conftest.py
(and thus the attempt recorder) loads.  It lives in a gitignored scratch dir
that is removed after each test.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def scratch() -> Path:
    path = ROOT / "reports" / "_governance_tmp"
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _run_probe(path: Path, attempt_log: Path, run_id: str, body: str) -> subprocess.CompletedProcess:
    path.write_text(body, encoding="utf-8")
    env = dict(os.environ)
    env["REGRESSION_RUN_ID"] = run_id
    env["PYTEST_ATTEMPT_LOG"] = str(attempt_log)
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(path), "-q", "-p", "no:cacheprovider"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def test_attempt_recorder_writes_clean_pass(scratch: Path):
    attempt_log = scratch / "attempts.jsonl"
    probe = scratch / "test_probe.py"
    proc = _run_probe(probe, attempt_log, "run-clean", "def test_clean():\n    assert True\n")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    records = [
        json.loads(line)
        for line in attempt_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert any(record.get("outcome") == "passed" and record.get("phase") == "call" for record in records)


def test_summary_distinguishes_clean_retry_failed(scratch: Path):
    attempt_log = scratch / "synthetic.jsonl"
    records = [
        {"run_id": "r1", "recorded_at": "2026-11-04T10:00:00+08:00", "test_id": "t1", "case_id": "P-1", "phase": "call", "attempt": 1, "outcome": "passed", "duration_s": 1, "worker": "master", "base_url": "http://test", "markers": [], "wasxfail": None},
        {"run_id": "r2", "recorded_at": "2026-11-04T10:01:00+08:00", "test_id": "t2", "case_id": "P-2", "phase": "call", "attempt": 1, "outcome": "failed", "duration_s": 1, "worker": "master", "base_url": "http://test", "markers": [], "wasxfail": None, "error": "first"},
        {"run_id": "r2", "recorded_at": "2026-11-04T10:01:02+08:00", "test_id": "t2", "case_id": "P-2", "phase": "call", "attempt": 2, "outcome": "passed", "duration_s": 1, "worker": "master", "base_url": "http://test", "markers": [], "wasxfail": None},
        {"run_id": "r3", "recorded_at": "2026-11-04T10:02:00+08:00", "test_id": "t3", "case_id": "P-3", "phase": "call", "attempt": 1, "outcome": "failed", "duration_s": 1, "worker": "master", "base_url": "http://test", "markers": [], "wasxfail": None, "error": "boom"},
    ]
    attempt_log.write_text("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n", encoding="utf-8")
    quarantine = scratch / "quarantine.yaml"
    quarantine.write_text("quarantine: []\n", encoding="utf-8")
    from scripts.regression_summary import build_summary

    clean = build_summary(attempt_log, quarantine, "r1")
    retry = build_summary(attempt_log, quarantine, "r2")
    failed = build_summary(attempt_log, quarantine, "r3")
    assert clean["counts"]["clean_pass"] == 1
    assert retry["counts"]["retry_pass"] == 1
    assert retry["counts"]["clean_pass"] == 0
    assert failed["counts"]["failed"] == 1


def test_quarantine_is_never_counted_as_pass(scratch: Path):
    attempt_log = scratch / "quarantine_case.jsonl"
    record = {"run_id": "rq", "recorded_at": "2026-11-04T10:03:00+08:00", "test_id": "tq", "case_id": "P-Q", "phase": "call", "attempt": 1, "outcome": "failed", "duration_s": 1, "worker": "master", "base_url": "http://test", "markers": [], "wasxfail": None, "error": "flaky"}
    attempt_log.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
    quarantine = scratch / "quarantine.yaml"
    quarantine.write_text(
        "quarantine:\n"
        "  - case_id: P-Q\n"
        "    reason: known flaky\n"
        "    owner: qa\n"
        "    opened_at: 2026-11-04\n"
        "    expires_at: 2026-12-31\n"
        "    evidence: reports/attempts/attempts.jsonl\n",
        encoding="utf-8",
    )
    from scripts.regression_summary import build_summary

    summary = build_summary(attempt_log, quarantine, "rq")
    assert summary["counts"]["quarantined"] == 1
    assert summary["counts"]["clean_pass"] == 0
    assert summary["counts"]["retry_pass"] == 0


def test_teardown_failure_is_broken_not_clean_pass(scratch: Path):
    attempt_log = scratch / "td.jsonl"
    records = [
        {"run_id": "rtd", "recorded_at": "2026-11-04T10:00:00+08:00", "test_id": "t1", "case_id": "P-TD", "phase": "call", "attempt": 1, "outcome": "passed", "duration_s": 1, "worker": "master", "base_url": "http://t", "markers": [], "wasxfail": None},
        {"run_id": "rtd", "recorded_at": "2026-11-04T10:00:01+08:00", "test_id": "t1", "case_id": "P-TD", "phase": "teardown", "attempt": 1, "outcome": "failed", "duration_s": 1, "worker": "master", "base_url": "http://t", "markers": [], "wasxfail": None, "error": "teardown boom"},
    ]
    attempt_log.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")
    quarantine = scratch / "q.yaml"
    quarantine.write_text("quarantine: []\n", encoding="utf-8")
    from scripts.regression_summary import build_summary

    summary = build_summary(attempt_log, quarantine, "rtd")
    case = summary["cases"][0]
    assert case["status"] == "broken", case
    assert summary["counts"]["clean_pass"] == 0


def test_case_id_label_is_authoritative(scratch: Path):
    probe = scratch / "test_label_probe.py"
    body = (
        "import allure\n"
        "class TestFoo:\n"
        "    @allure.label('case_id', 'L2-001')\n"
        "    def test_l2_001(self):\n"
        "        assert True\n"
    )
    attempt_log = scratch / "label.jsonl"
    proc = _run_probe(probe, attempt_log, "run-label", body)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    records = [
        json.loads(line)
        for line in attempt_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    call_records = [r for r in records if r.get("phase") == "call"]
    assert call_records, records
    assert call_records[0]["case_id"] == "L2-001", call_records[0]


def test_case_id_coverage_counts_only_resolved(scratch: Path):
    attempt_log = scratch / "cov.jsonl"
    records = [
        {"run_id": "rc", "recorded_at": "2026-11-04T10:00:00+08:00", "test_id": "t1", "case_id": "P-1", "phase": "call", "attempt": 1, "outcome": "passed", "duration_s": 1, "worker": "master", "base_url": "http://t", "markers": [], "wasxfail": None},
        {"run_id": "rc", "recorded_at": "2026-11-04T10:00:01+08:00", "test_id": "t2", "case_id": "MISSING_CASE_ID:t2", "phase": "call", "attempt": 1, "outcome": "passed", "duration_s": 1, "worker": "master", "base_url": "http://t", "markers": [], "wasxfail": None},
    ]
    attempt_log.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")
    quarantine = scratch / "q.yaml"
    quarantine.write_text("quarantine: []\n", encoding="utf-8")
    from scripts.regression_summary import build_summary

    summary = build_summary(attempt_log, quarantine, "rc")
    assert summary["case_id_coverage"]["resolved"] == 1
    assert summary["case_id_coverage"]["missing"] == 1
    assert summary["case_id_coverage"]["coverage_rate"] == 0.5


def test_dynamic_label_case_id_recovered_from_allure(scratch: Path):
    """allure.dynamic.label is runtime-only; summary must recover it from Allure JSON.

    Regression guard for the gap where case_id was read exclusively from pytest
    markers, silently dropping every allure.dynamic.label("case_id", ...) case.
    """
    attempt_log = scratch / "dynamic_attempts.jsonl"
    allure_dir = scratch / "allure"
    probe = scratch / "test_dynamic.py"
    probe.write_text(
        "import allure\n"
        "\n"
        "def test_dynamic_label_case():\n"
        "    allure.dynamic.label(\"case_id\", \"P-DYN-L2-777\")\n"
        "    allure.dynamic.title(\"P-DYN-L2-777: dynamic\")\n"
        "    assert True\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["REGRESSION_RUN_ID"] = "run-dynamic"
    env["PYTEST_ATTEMPT_LOG"] = str(attempt_log)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(probe), "-q", "-p", "no:cacheprovider",
         f"--alluredir={allure_dir}"],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    from scripts.regression_summary import build_summary

    quarantine = scratch / "quarantine.yaml"
    quarantine.write_text("quarantine: []\n", encoding="utf-8")
    summary = build_summary(attempt_log, quarantine, "run-dynamic", allure_dir)
    case = summary["cases"][0]
    assert case["case_id"] == "P-DYN-L2-777", case
    assert case["case_id_resolved"] is True, case
    assert summary["case_id_coverage"]["resolved"] == 1


def test_case_id_rules_global_prefix_used_verbatim():
    from scripts.case_id_rules import case_id_from_title

    assert case_id_from_title("TC-POR-L2-001 [P1] 维度切换", "tests/test_pokecut_portrait_detector.py") == "TC-POR-L2-001"
    assert case_id_from_title("PC-HOME-L1-001: hero", "tests/test_pokecut_pc_home_v6.py") == "PC-HOME-L1-001"
    assert case_id_from_title("P-AB-L1-001: batch", "tests/test_agent_batch_edit_panel.py") == "P-AB-L1-001"
    assert case_id_from_title("P-MX-L1-001: debug", "tests/test_create_chat_to_edit_model_matrix_v1.py") == "P-MX-L1-001"


def test_case_id_rules_short_id_is_namespaced():
    from scripts.case_id_rules import case_id_from_title

    # same short id in different suites must NOT collide
    a = case_id_from_title("L2-001: a", "tests/test_mobile_home.py")
    b = case_id_from_title("L2-001: b", "tests/test_help_page.py")
    assert a == "MH-L2-001", a
    assert b == "HELP-L2-001", b
    assert a != b


def test_case_id_rules_rejects_unknown_and_layer_only():
    from scripts.case_id_rules import case_id_from_title

    assert case_id_from_title("[L6][P0] 入口上传 + 左侧工具栏", "tests/test_infinite_canvas_text_layer_v2.py") == ""
    assert case_id_from_title("", "tests/test_x.py") == ""
    assert case_id_from_title("test_about_001_seo_title", "tests/test_about_page.py") == ""


def test_summary_extracts_case_id_from_title(scratch: Path):
    """Titles that already carry an id must resolve even without any label."""
    attempt_log = scratch / "title_attempts.jsonl"
    allure_dir = scratch / "title_allure"
    probe = scratch / "test_title.py"
    probe.write_text(
        "import allure\n"
        "\n"
        "@allure.title(\"TC-POR-L2-001 [P1] demo\")\n"
        "def test_with_title_id():\n"
        "    assert True\n"
        "\n"
        "@allure.title(\"[L6][P0] no id\")\n"
        "def test_without_title_id():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["REGRESSION_RUN_ID"] = "run-title"
    env["PYTEST_ATTEMPT_LOG"] = str(attempt_log)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(probe), "-q", "-p", "no:cacheprovider",
         f"--alluredir={allure_dir}"],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    from scripts.regression_summary import build_summary

    quarantine = scratch / "q.yaml"
    quarantine.write_text("quarantine: []\n", encoding="utf-8")
    summary = build_summary(attempt_log, quarantine, "run-title", allure_dir)
    by_test = {c["test_id"].split("::")[-1]: c for c in summary["cases"]}
    assert by_test["test_with_title_id"]["case_id"] == "TC-POR-L2-001"
    assert by_test["test_with_title_id"]["case_id_source"] == "title_extracted"
    assert by_test["test_without_title_id"]["case_id_resolved"] is False


def _write_run(directory, run_id, records):
    path = directory / (run_id + ".jsonl")
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )
    return path


def _rec(run_id, ts, test_id, case_id, outcome, attempt=1):
    return {
        "run_id": run_id, "recorded_at": ts, "test_id": test_id, "case_id": case_id,
        "title": "", "phase": "call", "attempt": attempt, "outcome": outcome,
        "duration_s": 1, "worker": "master", "base_url": "http://test",
        "markers": [], "wasxfail": None,
    }


def test_flaky_verdicts_across_runs(scratch: Path):
    runs = scratch / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    _write_run(runs, "r1", [
        _rec("r1", "2026-11-01T10:00:00+08:00", "t.stable", "C-STABLE", "passed"),
        _rec("r1", "2026-11-01T10:00:00+08:00", "t.flaky", "C-FLAKY", "passed"),
        _rec("r1", "2026-11-01T10:00:00+08:00", "t.fixed", "C-FIXED", "failed"),
        _rec("r1", "2026-11-01T10:00:00+08:00", "t.newfail", "C-NEWFAIL", "passed"),
    ])
    _write_run(runs, "r2", [
        _rec("r2", "2026-11-02T10:00:00+08:00", "t.stable", "C-STABLE", "passed"),
        _rec("r2", "2026-11-02T10:00:00+08:00", "t.flaky", "C-FLAKY", "failed"),
        _rec("r2", "2026-11-02T10:00:00+08:00", "t.fixed", "C-FIXED", "passed"),
        _rec("r2", "2026-11-02T10:00:00+08:00", "t.newfail", "C-NEWFAIL", "passed"),
    ])
    _write_run(runs, "r3", [
        _rec("r3", "2026-11-03T10:00:00+08:00", "t.stable", "C-STABLE", "passed"),
        _rec("r3", "2026-11-03T10:00:00+08:00", "t.flaky", "C-FLAKY", "passed"),
        _rec("r3", "2026-11-03T10:00:00+08:00", "t.fixed", "C-FIXED", "passed"),
        _rec("r3", "2026-11-03T10:00:00+08:00", "t.newfail", "C-NEWFAIL", "failed"),
    ])

    from scripts.flaky_report import build_report

    report = build_report(runs, None)
    verdicts = {c["case_id"]: c["verdict"] for c in report["cases"]}
    assert verdicts["C-STABLE"] == "stable_pass"
    assert verdicts["C-FLAKY"] == "flaky"
    assert verdicts["C-FIXED"] == "fixed"
    assert verdicts["C-NEWFAIL"] == "new_fail"
    action_ids = {c["case_id"] for c in report["needs_action"]}
    assert "C-FIXED" not in action_ids
    assert {"C-FLAKY", "C-NEWFAIL"} <= action_ids


def test_quarantine_lifecycle(scratch: Path):
    registry = scratch / "q.yaml"
    registry.write_text("schema_version: '1.0'\npolicy:\n  upgrade_after_consecutive_runs: 3\nquarantine: []\n", encoding="utf-8")

    from scripts.quarantine import main as qmain

    assert qmain(["--registry", str(registry), "add", "C-1",
                  "--reason", "flaky", "--owner", "qa", "--evidence", "e.json", "--days", "7"]) == 0
    data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    assert data["quarantine"][0]["case_id"] == "C-1"
    assert data["quarantine"][0]["status"] == "active"

    # duplicate add is rejected
    assert qmain(["--registry", str(registry), "add", "C-1",
                  "--reason", "x", "--owner", "qa", "--evidence", "e.json"]) == 2

    assert qmain(["--registry", str(registry), "extend", "C-1", "--days", "7"]) == 0
    assert qmain(["--registry", str(registry), "release", "C-1", "--reason", "fixed"]) == 0
    data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    entry = data["quarantine"][0]
    assert entry["status"] == "released"
    assert entry.get("released_at")
    # released entries are kept, not deleted
    assert len(data["quarantine"]) == 1
