"""Review API configuration helper.

Loads local env sources and resolves the review model/provider config.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from typing import Tuple

ROOT = Path(__file__).resolve().parent.parent


def load_local_env() -> None:
    """Load project .env and Codex settings env into process env."""
    env_path = ROOT / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k not in os.environ:
                        os.environ[k] = v

    settings_path = Path.home() / ".codex" / "settings.json"
    if settings_path.exists():
        try:
            cfg = json.loads(settings_path.read_text(encoding="utf-8"))
            env_cfg = cfg.get("env") or {}
            if isinstance(env_cfg, dict):
                for k, v in env_cfg.items():
                    if k not in os.environ and isinstance(v, str):
                        os.environ[k] = v
        except Exception:
            pass


def get_review_api_config() -> Tuple[str, str, str]:
    """Resolve API key / base URL / model for review calls."""
    load_local_env()

    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if openai_key:
        return (
            openai_key,
            _normalize_api_base(os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")),
            os.getenv("OPENAI_MODEL", "gpt-4.1"),
        )

    anthropic_key = (
        os.getenv("ANTHROPIC_AUTH_TOKEN")
        or os.getenv("ANTHROPIC_API_KEY")
        or ""
    ).strip()
    if anthropic_key:
        model = (
            os.getenv("ANTHROPIC_MODEL")
            or os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL")
            or os.getenv("ANTHROPIC_DEFAULT_OPUS_MODEL")
            or os.getenv("ANTHROPIC_DEFAULT_HAIKU_MODEL")
            or "gpt-4.1"
        )
        return (
            anthropic_key,
            _normalize_api_base(os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")),
            model,
        )

    return "", "", ""


def _normalize_api_base(base_url: str) -> str:
    """Ensure OpenAI-compatible base URL points to the API root."""
    base = (base_url or "").strip().rstrip("/")
    if not base:
        return ""
    parsed = urlparse(base)
    path = (parsed.path or "").rstrip("/")
    if path.endswith("/v1"):
        return base
    if not path:
        return base + "/v1"
    return urlunparse(parsed._replace(path=f"{path}/v1")).rstrip("/")

