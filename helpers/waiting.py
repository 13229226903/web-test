#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared wait helpers for Playwright tests.

Purpose (P3): replace fixed `page.wait_for_timeout(ms)` with waits that resolve
as soon as the target state is observable, while keeping a bounded fallback so a
slow render never turns into a hang.

Design rules
------------
- Prefer a positive, observable condition (`ready`) over "just wait longer".
- Always keep a timeout; never wait forever.
- Record which strategy fired so flaky waits become visible in evidence.
- This module does NOT install global monkeypatching. Callers opt in explicitly.
"""
from __future__ import annotations

from typing import Any, Callable
from urllib.parse import urlparse

from playwright.sync_api import Page, TimeoutError as PWTimeout

DEFAULT_SETTLE_MS = 250


def wait_ready(
    page: Page,
    ready: Callable[[], Any] | None = None,
    *,
    timeout: int = 8000,
    poll: int = 100,
    settle_ms: int = DEFAULT_SETTLE_MS,
) -> bool:
    """Wait until `ready()` is truthy, then give the UI `settle_ms` to stabilise.

    Returns True if `ready()` became truthy, False on timeout.  Never raises: a
    missing condition must not mask the real assertion failure that follows.

    `ready=None` means "no observable condition" -> a bounded settle wait.
    Every such call site should carry a comment explaining why the state cannot
    be observed.
    """
    if ready is None:
        page.wait_for_timeout(settle_ms)
        return True

    import time

    deadline = time.monotonic() + timeout / 1000.0
    while True:
        try:
            if ready():
                if settle_ms:
                    page.wait_for_timeout(settle_ms)
                return True
        except Exception:
            pass
        if time.monotonic() >= deadline:
            return False
        page.wait_for_timeout(min(poll, 100))


def poll_until(
    page: Page,
    ready: Callable[[], Any],
    *,
    timeout: int = 10000,
    interval: int = 500,
) -> bool:
    """Poll `ready()` until truthy or timeout; returns the final truthiness.

    This is the explicit primitive for the "call a page probe repeatedly" loops
    that used to be written as `while ...: page.wait_for_timeout(interval)`.
    It keeps the same semantics (no settle step, caller inspects final state)
    while making the poll interval and deadline greppable.
    """
    import time

    deadline = time.monotonic() + timeout / 1000.0
    while True:
        try:
            if ready():
                return True
        except Exception:
            pass
        if time.monotonic() >= deadline:
            return False
        page.wait_for_timeout(interval)


def wait_visible(page: Page, locator, *, timeout: int = 8000, settle_ms: int = DEFAULT_SETTLE_MS) -> bool:
    """Wait for a locator to become visible. Returns True/False, never raises."""
    try:
        locator.first.wait_for(state="visible", timeout=timeout)
        if settle_ms:
            page.wait_for_timeout(settle_ms)
        return True
    except PWTimeout:
        return False
    except Exception:
        return False


def wait_attached(page: Page, locator, *, timeout: int = 8000, settle_ms: int = DEFAULT_SETTLE_MS) -> bool:
    """Wait for a locator to be attached (may be hidden)."""
    try:
        locator.first.wait_for(state="attached", timeout=timeout)
        if settle_ms:
            page.wait_for_timeout(settle_ms)
        return True
    except Exception:
        return False


def wait_url_contains(page: Page, fragment: str, *, timeout: int = 10000, settle_ms: int = DEFAULT_SETTLE_MS) -> bool:
    """Wait until the URL contains a fragment."""
    try:
        page.wait_for_url(f"**{fragment}**", timeout=timeout)
        if settle_ms:
            page.wait_for_timeout(settle_ms)
        return True
    except Exception:
        return False


def wait_network_quiet(page: Page, *, timeout: int = 2000, idle_ms: int = 500) -> bool:
    """Best-effort network settle. CSR pages may never reach networkidle.

    This is deliberately capped low: it is a smoothing step, not a correctness
    gate.  Long "networkidle" waits are an anti-pattern for streaming pages.
    """
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass
    if idle_ms:
        page.wait_for_timeout(idle_ms)
    return True


def wait_canvas_ready(page: Page, *, timeout: int = 30000, settle_ms: int = 300) -> bool:
    """等待编辑器画布真正渲染完成（URL 变化 != 内容就绪）。

    2026-11-05: SPA 路由切换先于内容渲染；仅等 URL 会截到空白加载页。
    以「可见 canvas 或大尺寸图层图片」+（移动端）底部主面板为就绪信号。
    """
    import time

    deadline = time.monotonic() + timeout / 1000.0
    while True:
        try:
            ready = page.evaluate("""() => {
                const canvasN = [...document.querySelectorAll('canvas')].filter(c => {
                    const r = c.getBoundingClientRect();
                    return r.width > 50 && r.height > 50;
                }).length;
                const imgN = [...document.querySelectorAll('img')].filter(i => {
                    const r = i.getBoundingClientRect();
                    return r.width > 150 && r.height > 150;
                }).length;
                return canvasN > 0 || imgN > 0;
            }""")
            if ready:
                if settle_ms:
                    page.wait_for_timeout(settle_ms)
                return True
        except Exception:
            pass
        if time.monotonic() >= deadline:
            return False
        page.wait_for_timeout(200)


def settle(page: Page, ms: int = DEFAULT_SETTLE_MS) -> None:
    """Explicit bounded settle for cases where no observable condition exists.

    Use sparingly; every call site should carry a comment explaining WHY the
    state cannot be observed.  Kept as a named helper so the debt is greppable.
    """
    page.wait_for_timeout(ms)


def same_origin(page: Page) -> str:
    parsed = urlparse(page.url)
    return f"{parsed.scheme}://{parsed.netloc}"
