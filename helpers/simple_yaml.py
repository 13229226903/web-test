"""Very small YAML reader for the SEO config files.

This project only needs a tiny subset of YAML:
  - top-level key/value pairs
  - a single list under ``seo_pages``
  - list items that are either plain strings or small dicts

The helper avoids depending on PyYAML in environments where it is absent.
"""

from __future__ import annotations

from pathlib import Path


def _parse_scalar(value: str):
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if lower in {"null", "~"}:
        return None
    try:
        return int(value)
    except ValueError:
        return value


def load_simple_yaml(path: str | Path) -> dict:
    path = Path(path)
    data: dict = {}
    current_key = None
    current_item = None
    current_list = None

    def flush_item():
        nonlocal current_item
        if current_key == "seo_pages" and current_item is not None:
            current_list.append(current_item)
            current_item = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not line.startswith(" "):
            flush_item()
            current_item = None
            current_list = None
            current_key = None
            if ":" not in stripped:
                continue
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key == "seo_pages" and not value:
                current_key = key
                current_list = []
                data[key] = current_list
            else:
                data[key] = _parse_scalar(value)
            continue

        if current_key != "seo_pages":
            continue

        indent_stripped = stripped
        if indent_stripped.startswith("- "):
            flush_item()
            item_text = indent_stripped[2:].strip()
            if not item_text:
                current_item = {}
            elif ":" in item_text:
                key, value = item_text.split(":", 1)
                current_item = {key.strip(): _parse_scalar(value.strip())}
            else:
                current_item = _parse_scalar(item_text)
            continue

        if isinstance(current_item, dict) and ":" in indent_stripped:
            key, value = indent_stripped.split(":", 1)
            current_item[key.strip()] = _parse_scalar(value.strip())

    flush_item()
    return data
