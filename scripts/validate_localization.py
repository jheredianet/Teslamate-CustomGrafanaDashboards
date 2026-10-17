#!/usr/bin/env python3
"""Validate dashboard localization packs and generated dashboards."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARDS = ROOT / "dashboards"
PACK = ROOT / "i18n" / "it.json"
GENERATOR = ROOT / "scripts" / "generate_localized_dashboards.py"
LOCALIZABLE_KEYS = {"title", "description", "label", "displayName", "legendFormat", "tooltip", "noValue", "text", "alias"}
SQL_ALIAS_RE = re.compile(r'\bAS\s+["\']([^"\']+)["\']', re.I)
PLACEHOLDER_RE = re.compile(r'\$\{?[A-Za-z_][A-Za-z_0-9.:\[\]]*\}?')


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def add_visible(value, acc: set[str]):
    if not isinstance(value, str):
        return
    value = value.strip()
    if not value:
        return
    if re.match(r'^\$\{?[A-Za-z_][A-Za-z_0-9.:\[\]]*\}?$', value):
        return
    if re.match(r'^[0-9]+(?:\.[0-9]+)?(?:ms|s|m|h|d|w)?$', value):
        return
    if value in {"--", ".", "ID"}:
        return
    acc.add(value)


def collect_visible(value, acc: set[str]):
    if isinstance(value, list):
        for item in value:
            collect_visible(item, acc)
        return
    if not isinstance(value, dict):
        return
    for key, item in value.items():
        if key in LOCALIZABLE_KEYS and isinstance(item, str):
            add_visible(item, acc)
        elif key == "renameByName" and isinstance(item, dict):
            for target in item.values():
                add_visible(target, acc)
        elif key == "aliasColors" and isinstance(item, dict):
            for source in item.keys():
                add_visible(source, acc)
        elif key == "value" and value.get("id") == "displayName" and isinstance(item, str):
            add_visible(item, acc)
        elif key == "rawSql" and isinstance(item, str):
            for alias_name in SQL_ALIAS_RE.findall(item):
                add_visible(alias_name, acc)
        else:
            collect_visible(item, acc)


def query_values(dashboard: dict):
    result = []
    for var in dashboard.get("templating", {}).get("list", []) or []:
        options = var.get("options") or []
        result.append({
            "name": var.get("name"),
            "type": var.get("type"),
            "query": var.get("query"),
            "definition": var.get("definition"),
            "regex": var.get("regex"),
            "datasource": var.get("datasource"),
            "current_value": (var.get("current") or {}).get("value"),
            "option_values": [o.get("value") for o in options if isinstance(o, dict)],
        })
    return result


def collect_raw_sql(value, out: list[str]):
    if isinstance(value, list):
        for item in value:
            collect_raw_sql(item, out)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key == "rawSql" and isinstance(item, str):
                out.append(item)
            else:
                collect_raw_sql(item, out)


def import_generator():
    spec = importlib.util.spec_from_file_location("dashboard_localizer", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> int:
    pack = load(PACK)
    strings = pack.get("strings", {})
    passthrough = set(pack.get("passthrough", []))
    titles = pack.get("dashboard_titles", {})

    candidates: set[str] = set()
    dashboard_paths = sorted(DASHBOARDS.glob("*.json"))
    expected_stems = {p.stem for p in dashboard_paths}

    for path in dashboard_paths:
        dashboard = load(path)
        local = set()
        collect_visible(dashboard, local)
        local.discard(dashboard.get("title"))
        candidates |= local

    missing = sorted(candidates - set(strings) - passthrough)
    extra_titles = sorted(set(titles) - expected_stems)
    missing_titles = sorted(expected_stems - set(titles))
    if missing or missing_titles or extra_titles:
        if missing:
            print("Missing locale strings:")
            for item in missing:
                print(f"  - {item!r}")
        if missing_titles:
            print("Missing dashboard titles:", missing_titles)
        if extra_titles:
            print("Unknown dashboard titles:", extra_titles)
        return 1

    for source, target in strings.items():
        if sorted(PLACEHOLDER_RE.findall(source)) != sorted(PLACEHOLDER_RE.findall(target)):
            print(f"Placeholder mismatch: {source!r} -> {target!r}")
            return 1

    generator = import_generator()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        output = tmp_root / "dashboards"
        output.mkdir()
        for path in dashboard_paths:
            source = load(path)
            generated = generator.localize_dashboard(source, path.stem, pack)
            (output / path.name).write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            if generated.get("uid") != source.get("uid"):
                print(f"UID changed in {path.name}")
                return 1
            if query_values(generated) != query_values(source):
                print(f"Template variable technical values changed in {path.name}")
                return 1

            alias_map = generator.collect_alias_map(source, strings)
            source_sql: list[str] = []
            generated_sql: list[str] = []
            collect_raw_sql(source, source_sql)
            collect_raw_sql(generated, generated_sql)
            expected_sql = [generator.rewrite_sql_aliases(sql, alias_map) for sql in source_sql]
            if generated_sql != expected_sql:
                print(f"Unexpected SQL change in {path.name}")
                return 1

        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_dashboards.py"), "--root", str(tmp_root), "--no-sql"],
            text=True,
        )
        if result.returncode:
            return result.returncode

    print(f"localization OK: {len(dashboard_paths)} dashboards, {len(candidates)} visible strings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
