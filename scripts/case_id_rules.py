#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Derive a stable case_id from an Allure title, with strict guardrails.

Design (see P1 plan):
  * Only titles whose leading token matches a known pattern are accepted.
  * A short id (L2-001) is namespaced by suite key to avoid cross-file clashes,
    because L2-001 appears in many suites.
  * A globally-prefixed id (TC-POR-..., PC-HOME-..., P-AB-...) is used as-is.
  * Anything unrecognised returns "" so the caller keeps a visible MISSING debt
    instead of inventing an identity.
"""
from __future__ import annotations

import re
from pathlib import Path

# Globally unique prefixes: use the token verbatim.
GLOBAL_ID_PATTERN = re.compile(r"^([A-Z][A-Z0-9]{0,7}(?:-[A-Z0-9]{1,8}){2,6})\b")
# Short layer ids such as L2-001 / L6-012: must be namespaced by suite.
SHORT_ID_PATTERN = re.compile(r"^(L[1-9])-([0-9]{2,4})\b")

# Suite key overrides (stable, human-readable). Falls back to a derived token.
SUITE_KEYS = {
    "test_mobile_home.py": "MH",
    "test_help_page.py": "HELP",
    "test_pokecut_pc_home_v6.py": "PCHOME",
    "test_pokecut_pc_batch_v1.py": "PCBATCH",
    "test_old_canvas_insert_panel_v3.py": "OCI",
    "test_old_canvas_text_panel_v1.py": "OCT",
    "test_old_canvas_sticker_panel_v1.py": "OCS",
    "test_infinite_canvas_enhance_v4.py": "ICE",
    "test_old_canvas_ai_tools_all.py": "OCAI",
    "test_infinite_canvas_sticker_v1.py": "ICS",
    "test_detection_ui_seo_l6.py": "L6DET",
    "test_create_chat_to_edit_auto_v1.py": "AUTO",
    "test_canvas_stats_all.py": "STATS",
    "test_infinite_canvas_text_layer_v2.py": "ICT",
}


def suite_key(nodeid: str) -> str:
    """Stable short key for a test file, used to namespace short ids."""
    file_part = str(nodeid).split("::", 1)[0].replace("\\", "/")
    name = Path(file_part).name
    if name in SUITE_KEYS:
        return SUITE_KEYS[name]
    # derive: strip test_ prefix and version suffix, uppercase, keep alnum
    stem = re.sub(r"^test_", "", name)
    stem = re.sub(r"\.py$", "", stem)
    stem = re.sub(r"_v\d+$", "", stem)
    return re.sub(r"[^A-Za-z0-9]", "", stem).upper()[:12] or "SUITE"


def case_id_from_title(title: str, nodeid: str) -> str:
    """Return a namespaced case id derived from an Allure title, or "".

    The returned value is safe for cross-file quarantine lookups and cross-run
    trend tracking.  Callers must treat "" as "no id", not as an error.
    """
    if not title:
        return ""
    text = str(title).strip()
    # Leading bracketed layer tags like "[L6][P0] ..." are not ids themselves.
    m_global = GLOBAL_ID_PATTERN.match(text)
    if m_global:
        return m_global.group(1).upper()
    m_short = SHORT_ID_PATTERN.match(text)
    if m_short:
        layer, num = m_short.group(1), m_short.group(2)
        return f"{suite_key(nodeid)}-{layer}-{num}"
    return ""
