#!/usr/bin/env python3
"""Generate localized copies of TeslaMate Custom Grafana Dashboards.

The source dashboards remain untouched. Only user-visible strings are translated;
query values, variables, datasource identifiers and other technical fields remain
unchanged. SQL aliases are translated together with Grafana field references that
point to those aliases.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path

LOCALIZABLE_KEYS = {
    "title", "description", "label", "displayName", "legendFormat",
    "tooltip", "noValue", "text", "alias",
}
SQL_ALIAS_RE = re.compile(r'(?i)(\bAS\s+)(["\'])([^"\']+)(\2)')


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def translate_exact(value: str, strings: dict[str, str], passthrough: set[str]) -> str:
    if value in strings:
        return strings[value]
    if value in passthrough:
        return value
    return value


def collect_alias_map(value, strings: dict[str, str]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "rawSql" and isinstance(item, str):
                for match in SQL_ALIAS_RE.finditer(item):
                    source = match.group(3)
                    target = strings.get(source)
                    if target and target != source:
                        aliases[source] = target
            else:
                aliases.update(collect_alias_map(item, strings))
    elif isinstance(value, list):
        for item in value:
            aliases.update(collect_alias_map(item, strings))
    return aliases


def rewrite_sql_aliases(value: str, alias_map: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        source = match.group(3)
        target = alias_map.get(source, source)
        return f"{match.group(1)}{match.group(2)}{target}{match.group(4)}"
    return SQL_ALIAS_RE.sub(replace, value)


def rewrite_alias_ref(value, alias_map: dict[str, str]):
    if isinstance(value, str):
        return alias_map.get(value, value)
    if isinstance(value, list):
        return [rewrite_alias_ref(item, alias_map) for item in value]
    return value


def rewrite(value, strings: dict[str, str], passthrough: set[str], alias_map: dict[str, str]):
    if isinstance(value, list):
        return [rewrite(item, strings, passthrough, alias_map) for item in value]

    if not isinstance(value, dict):
        # Unknown scalar contexts are technical by default and are left intact.
        return value

    localized = {}
    for key, item in value.items():
        if key == "rawSql" and isinstance(item, str):
            localized[key] = rewrite_sql_aliases(item, alias_map)

        elif key in LOCALIZABLE_KEYS and isinstance(item, str):
            localized[key] = translate_exact(item, strings, passthrough)

        elif key == "renameByName" and isinstance(item, dict):
            localized[key] = {
                alias_map.get(source, source): (
                    translate_exact(target, strings, passthrough)
                    if isinstance(target, str)
                    else rewrite(target, strings, passthrough, alias_map)
                )
                for source, target in item.items()
            }

        elif key == "aliasColors" and isinstance(item, dict):
            localized[key] = {
                alias_map.get(source, source): rewrite(target, strings, passthrough, alias_map)
                for source, target in item.items()
            }

        elif key == "matcher" and isinstance(item, dict):
            matcher = copy.deepcopy(item)
            if matcher.get("id") in {"byName", "byNames"} and "options" in matcher:
                matcher["options"] = rewrite_alias_ref(matcher["options"], alias_map)
            localized[key] = rewrite(matcher, strings, passthrough, alias_map)

        elif key == "names" and isinstance(item, list):
            # Grafana transformations commonly keep a list of field/series names.
            localized[key] = [alias_map.get(name, name) if isinstance(name, str) else name for name in item]

        elif key == "value" and value.get("id") == "displayName" and isinstance(item, str):
            localized[key] = translate_exact(item, strings, passthrough)

        else:
            localized[key] = rewrite(item, strings, passthrough, alias_map)

    return localized


def localize_dashboard(source: dict, stem: str, pack: dict) -> dict:
    strings = pack.get("strings", {})
    passthrough = set(pack.get("passthrough", []))
    alias_map = collect_alias_map(source, strings)
    localized = rewrite(copy.deepcopy(source), strings, passthrough, alias_map)
    title = (pack.get("dashboard_titles") or {}).get(stem)
    if title:
        localized["title"] = title
    return localized


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="dashboards", help="source dashboard directory")
    parser.add_argument("--pack", default="i18n/it.json", help="locale JSON pack")
    parser.add_argument("--output", required=True, help="directory for localized dashboard JSON files")
    args = parser.parse_args(argv)

    source_dir = Path(args.source)
    pack_path = Path(args.pack)
    output_dir = Path(args.output)
    pack = load_json(pack_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = sorted(source_dir.glob("*.json"))
    if not paths:
        parser.error(f"no dashboard JSON files found in {source_dir}")

    for path in paths:
        dashboard = load_json(path)
        localized = localize_dashboard(dashboard, path.stem, pack)
        (output_dir / path.name).write_text(
            json.dumps(localized, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"generated {len(paths)} {pack.get('locale', 'localized')} dashboards in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
