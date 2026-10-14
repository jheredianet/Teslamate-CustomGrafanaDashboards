#!/usr/bin/env python3
"""Validate the dashboards of this repository.

Two levels of checking, both usable on their own:

1. Static checks (always run, no database needed):

   * every JSON file parses;
   * dashboard uids and titles are unique;
   * every datasource reference points to a provisioned datasource uid;
   * the ``${base_url:raw}`` link is present and interpolation-safe;
   * every ``$variable`` used in a query is declared in the dashboard;
   * ``$__timezone`` is always quoted, and a stored (UTC) column is never
     passed straight to the dashboard time zone (see the README section
     "Dates and time zones in the queries");
   * every panel declares the same ``pluginVersion``, so that editing with
     a newer Grafana does not silently stamp a different version on some
     panels.

2. SQL checks (only with ``--dsn`` or ``--docker``):

   * every query and every query variable is prepared against a real
     TeslaMate database with ``PREPARE``, which parses and plans it
     without executing it. Template variables and Grafana macros are
     interpolated first, the same way Grafana does it.

The SQL level catches the mistakes that are otherwise only visible when a
panel is opened: renamed or removed columns, bad joins, type errors,
dialect mistakes.

Usage::

    # static checks only (what CI runs)
    python3 scripts/validate_dashboards.py

    # full check against a running TeslaMate database
    python3 scripts/validate_dashboards.py --docker database
    python3 scripts/validate_dashboards.py --dsn postgres://user:pass@host:5432/teslamate

Exit code is 0 when there is no error (warnings are allowed unless
``--strict`` is passed).
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

DEFAULT_DSN = os.environ.get("DASHBOARDS_DSN") or os.environ.get("DATABASE_URL")
DEFAULT_DOCKER = os.environ.get("DASHBOARDS_DOCKER")

#: Datasource references available in any Grafana install: the one that the
#: stock TeslaMate provisioning creates, plus Grafana's own built-in
#: datasources (rows, mixed panels, dashboard-to-dashboard references).
KNOWN_DATASOURCE_TYPES = {
    "grafana-postgresql-datasource", "postgres",
    "datasource",  # -- Dashboard --
    "grafana",     # -- Grafana --
    "mixed",       # -- Mixed --
}
KNOWN_DATASOURCE_UIDS = {"TeslaMate", "-- Dashboard --", "-- Grafana --", "-- Mixed --"}

#: Built-in Grafana variables, they are not declared in ``templating``.
BUILTIN_VARS = {
    "__dashboard", "__from", "__to", "__interval", "__interval_ms", "__timezone",
    "__org", "__user", "__range", "__range_ms", "__range_s", "__url_time_range",
    "__rate_interval", "__rate_interval_ms", "__name",
}

#: Columns stored by TeslaMate as naive UTC.
UTC_COLUMNS = (
    "start_date", "end_date", "date", "inserted_at", "updated_at",
    "start_position_date", "end_position_date",
)

#: Value and SQL type used for each template variable when no real value can
#: be resolved from an available database. Keep in sync with the dashboards.
FALLBACK_VALUES = {
    "alternative_length_unit": ("mi", "text"),
    "BatteryCapacity": ("75", "numeric"),
    "car_cost": ("40000", "numeric"),
    "car_id": ("1", "integer"),
    "carrier": ("", "text"),
    "charging_processes": ("1", "integer"),
    "current_capacity": ("58.4", "numeric"),
    "current_charge_time": (str(int(dt.datetime(2026, 1, 1).timestamp() * 1000)), "bigint"),
    "current_drive": ("1", "integer"),
    "current_drive_end_time": (str(int(dt.datetime(2026, 12, 31).timestamp() * 1000)), "bigint"),
    "current_drive_start_time": (str(int(dt.datetime(2026, 1, 1).timestamp() * 1000)), "bigint"),
    "current_end_time": (str(int(dt.datetime(2026, 12, 31).timestamp() * 1000)), "bigint"),
    "datapoints": ("100", "integer"),
    "Day": ("01", "text"),
    "depreciated_value": ("20", "numeric"),
    "distance_driven": ("1000", "numeric"),
    "DCCost": ("0.5", "numeric"),
    "efficiency": ("150", "numeric"),
    "filter_power_from": ("0", "numeric"),
    "filter_power_to": ("260", "numeric"),
    "filter_soc_from": ("0", "numeric"),
    "filter_soc_to": ("100", "numeric"),
    "fuel_price": ("0.108", "numeric"),
    "geofence": ("", "text"),
    "interval": ("15d", "text"),
    "journey": ("1", "integer"),
    "length_unit": ("km", "text"),
    "loss_rate": ("0.20", "numeric"),
    "min_avg_speed": ("0", "numeric"),
    "min_dist": ("0", "numeric"),
    "min_distance": ("25", "numeric"),
    "min_speed_segment": ("50", "numeric"),
    "Month": ("01", "text"),
    "period": ("month", "text"),
    "preferred_range": ("rated", "text"),
    "pressure_unit": ("bar", "text"),
    "speed_step": ("10", "numeric"),
    "SucCost": ("0.4", "numeric"),
    "temp_unit": ("C", "text"),
    "temperature_step": ("5", "numeric"),
    "terrain_type": ("Flat", "text"),
    "TotalCost": ("100", "numeric"),
    "Year": ("2026", "text"),
    "ACCost": ("0.3", "numeric"),
    "base_url": ("http://localhost:4000", "text"),
}

MACROS_SQL = {
    "$__timezone": "'UTC'",
    "$__interval": "'1 hour'",
    "$__interval_ms": "3600000",
    "$__timeFrom": "TIMESTAMP '2026-01-01 00:00:00'",
    "$__timeTo": "TIMESTAMP '2026-12-31 00:00:00'",
    "$__from": str(int(dt.datetime(2026, 1, 1).timestamp() * 1000)),
    "$__to": str(int(dt.datetime(2026, 12, 31).timestamp() * 1000)),
}

PSQL_ARGS = ["-X", "-q", "-A", "-t", "-v", "ON_ERROR_STOP=1"]


# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------

ERROR, WARNING = "error", "warning"


class Report:
    def __init__(self) -> None:
        self.findings: list[tuple[str, str, str, str]] = []

    def add(self, level: str, where: str, message: str, detail: str = "") -> None:
        self.findings.append((level, where, message, detail))

    def error(self, where: str, message: str, detail: str = "") -> None:
        self.add(ERROR, where, message, detail)

    def warning(self, where: str, message: str, detail: str = "") -> None:
        self.add(WARNING, where, message, detail)

    @property
    def errors(self) -> list[tuple[str, str, str, str]]:
        return [f for f in self.findings if f[0] == ERROR]

    @property
    def warnings(self) -> list[tuple[str, str, str, str]]:
        return [f for f in self.findings if f[0] == WARNING]


# --------------------------------------------------------------------------
# Reading the dashboards
# --------------------------------------------------------------------------

def walk_panels(panels):
    for panel in panels or []:
        yield panel
        yield from walk_panels(panel.get("panels"))


def panel_queries(dashboard):
    """Yield (panel title, raw SQL) for every panel target with SQL."""
    for panel in walk_panels(dashboard.get("panels")):
        if panel.get("type") == "row":
            continue
        for target in panel.get("targets") or []:
            sql = target.get("rawSql") or target.get("rawQuery")
            if isinstance(sql, str) and sql.strip():
                yield panel.get("title") or "(untitled panel)", sql


def variable_queries(dashboard):
    """Yield (variable name, raw SQL) for every query variable."""
    for var in dashboard.get("templating", {}).get("list", []) or []:
        query = var.get("query")
        if var.get("type") == "query" and isinstance(query, str) and re.search(r"\bselect\b", query, re.I):
            yield var.get("name"), query


def datasource_refs(dashboard):
    """Yield (where, reference) for every datasource reference in the file."""
    for panel in walk_panels(dashboard.get("panels")):
        title = panel.get("title") or "(untitled panel)"
        ref = panel.get("datasource")
        if isinstance(ref, dict):
            yield f"{title}", ref
        for target in panel.get("targets") or []:
            ref = target.get("datasource")
            if isinstance(ref, dict):
                yield f"{title}", ref
    for var in dashboard.get("templating", {}).get("list", []) or []:
        ref = var.get("datasource")
        if isinstance(ref, dict):
            yield f"variable {var.get('name')}", ref
    if isinstance(dashboard.get("datasource"), dict):
        yield "dashboard", dashboard["datasource"]


def all_sql(dashboard):
    for title, sql in panel_queries(dashboard):
        yield f"panel '{title}'", sql
    for name, sql in variable_queries(dashboard):
        yield f"variable '{name}'", sql


# --------------------------------------------------------------------------
# Static checks
# --------------------------------------------------------------------------

VAR_PATTERN = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)(?::[a-z:]+)?\}|([A-Za-z_][A-Za-z0-9_]*))")


def used_variables(sql: str) -> set[str]:
    names = set()
    for braced, plain in VAR_PATTERN.findall(sql):
        name = braced or plain
        if not name:
            continue
        if name.startswith("__"):
            if name not in BUILTIN_VARS and not name.startswith("__time") and not name.startswith("__unixEpoch"):
                names.add(name)
            continue
        if name in ("__data", "data"):
            continue
        names.add(name)
    # ${__data.fields.x} style references are links, not query variables
    return {n for n in names if "." not in n}


def check_panel_plugin_versions(loaded, report: Report) -> None:
    """Every panel should declare the same Grafana version.

    ``pluginVersion`` is metadata that Grafana stamps when a panel is saved
    and never uses to migrate anything, but when the dashboards are edited
    with different Grafana versions it drifts: a panel saved long ago keeps
    an old value, which is misleading and turns a one line change into a
    diff over many panels. See the README section on contributing.
    """
    versions: dict[str, list[str]] = {}
    for name, dashboard in loaded:
        for panel in walk_panels(dashboard.get("panels")):
            version = panel.get("pluginVersion")
            if version:
                versions.setdefault(version, []).append(f"{name}: {panel.get('title')}")

    if len(versions) <= 1:
        return

    majority = max(versions, key=lambda v: len(versions[v]))
    for version, panels in sorted(versions.items()):
        if version == majority:
            continue
        report.error(
            "dashboards",
            f"{len(panels)} panel(s) declare pluginVersion {version!r}, expected {majority!r}",
            "panels: " + "; ".join(panels[:5]) + (" ..." if len(panels) > 5 else ""),
        )


def static_checks(root: str, report: Report) -> list[tuple[str, dict]]:
    files = sorted(glob.glob(os.path.join(root, "dashboards", "*.json")))
    if not files:
        report.error("dashboards", f"no dashboard JSON files found under {root}")
        return []

    loaded = []
    seen_uids: dict[str, str] = {}
    seen_titles: dict[str, str] = {}

    for path in files:
        name = os.path.basename(path)
        try:
            with open(path, encoding="utf-8") as handle:
                dashboard = json.load(handle)
        except json.JSONDecodeError as exc:
            report.error(name, "invalid JSON", str(exc))
            continue
        loaded.append((name, dashboard))

        uid = dashboard.get("uid")
        title = dashboard.get("title")
        if not uid:
            report.error(name, "dashboard has no uid")
        elif uid in seen_uids:
            report.error(name, f"duplicated uid {uid!r}", f"also used by {seen_uids[uid]}")
        else:
            seen_uids[uid] = name
        if title in seen_titles:
            report.warning(name, f"duplicated title {title!r}", f"also used by {seen_titles[title]}")
        else:
            seen_titles[title] = name

        if not dashboard.get("panels"):
            report.warning(name, "dashboard has no panels")

        # datasource references
        for where, ref in datasource_refs(dashboard):
            ref_type, ref_uid = ref.get("type"), ref.get("uid")
            if ref_type and ref_type not in KNOWN_DATASOURCE_TYPES:
                report.warning(name, f"{where}: unexpected datasource type {ref_type!r}")
            if ref_uid is None:
                report.warning(name, f"{where}: datasource has no uid")
            elif ref_uid not in KNOWN_DATASOURCE_UIDS:
                report.warning(
                    name,
                    f"{where}: datasource uid {ref_uid!r} is not one of {sorted(KNOWN_DATASOURCE_UIDS)}",
                    "the stock TeslaMate provisioning names the datasource 'TeslaMate'",
                )

        # navigation link to the TeslaMate web interface
        urls = [link.get("url") for link in dashboard.get("links", []) or [] if isinstance(link, dict)]
        if "${base_url:raw}" not in urls:
            report.warning(name, "no ${base_url:raw} navigation link")

        # declared variables vs used variables
        declared = {v.get("name") for v in dashboard.get("templating", {}).get("list", []) or []}
        undeclared = {}
        for where, sql in all_sql(dashboard):
            for variable in used_variables(sql):
                if variable not in declared:
                    undeclared.setdefault(variable, where)
        for variable, where in sorted(undeclared.items()):
            report.error(name, f"$'{variable}' used in {where} but not declared", "add it to templating.list")

        # time zone conventions (see README, "Dates and time zones in the queries")
        for where, sql in all_sql(dashboard):
            for match in re.finditer(r"timezone\(\s*\$__timezone", sql):
                report.error(
                    name,
                    f"{where}: $__timezone used without quotes",
                    "Grafana substitutes the zone name without quotes; write '$__timezone'",
                )
            for column in UTC_COLUMNS:
                wrong = re.compile(
                    r"date_trunc\([^,]+,(?:\s*)timezone\(\s*'\$__timezone'\s*,\s*" + column + r"\b"
                )
                if wrong.search(sql):
                    report.error(
                        name,
                        f"{where}: {column} (stored in UTC) is passed straight to the dashboard time zone",
                        f"wrap it first: timezone('UTC', {column})",
                    )

    check_panel_plugin_versions(loaded, report)
    return loaded


# --------------------------------------------------------------------------
# SQL checks
# --------------------------------------------------------------------------

class Database:
    """Runs SQL through psql, locally or inside a container."""

    def __init__(self, dsn: str | None = None, container: str | None = None,
                 user: str = "teslamate", database: str = "teslamate") -> None:
        self.dsn = dsn
        self.container = container
        self.user = user
        self.database = database

    @property
    def label(self) -> str:
        if self.dsn:
            return self.dsn.split("@")[-1]
        return f"docker:{self.container} ({self.user}@{self.database})"

    def _base(self) -> list[str]:
        if self.container:
            return ["docker", "exec", "-i", self.container,
                    "psql", "-U", self.user, "-d", self.database]
        return ["psql", self.dsn]

    def query(self, sql: str, timeout: int = 60) -> tuple[bool, str]:
        """Run SQL through psql stdin. Nothing is ever committed."""
        cmd = self._base() + PSQL_ARGS + ["-f", "-"]
        try:
            result = subprocess.run(cmd, input=sql, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError:
            return False, "psql not found (use --docker CONTAINER instead of --dsn)"
        except subprocess.TimeoutExpired:
            return False, f"timed out after {timeout}s"
        if result.returncode != 0:
            return False, (result.stderr or result.stdout).strip()
        return True, result.stdout

    def prepare(self, statements: list[str]) -> tuple[bool, str]:
        """PREPARE (parse + plan, no execution) inside a rolled back transaction."""
        body = "\n".join(s.rstrip().rstrip(";") + ";" for s in statements)
        return self.query("BEGIN;\n" + body + "\nROLLBACK;")

    def explain(self, sql: str) -> tuple[bool, str]:
        return self.query("EXPLAIN " + sql, timeout=120)

    def alive(self) -> tuple[bool, str]:
        return self.query("SELECT 1;")


def render(sql: str, values: dict[str, tuple[str, str]]) -> tuple[str, list[str]]:
    """Interpolate Grafana macros and template variables, as Grafana does."""
    unresolved = []

    def macro(match: re.Match) -> str:
        name = match.group(1)
        replacement = MACROS_SQL.get(name)
        if replacement is None:
            return match.group(0)
        # $__timeFrom / $__timeTo exist both as a value and as a call,
        # and MACROS_SQL already gives a ready to use literal in both cases.
        return replacement

    # macros first, they also start with $. A macro may be written already
    # quoted in the SQL (the convention for '$__timezone'), so that spelling
    # is replaced variant first; \b keeps $__timeFilter from matching $__time.
    for name in sorted(MACROS_SQL, key=len, reverse=True):
        quoted = f"'{name}'"
        if quoted in sql:
            sql = sql.replace(quoted, f"'{MACROS_SQL[name].strip(chr(39))}'")
    sql = re.sub(
        r"(\$__[A-Za-z_]+)(\(\s*\))?",
        macro,
        sql,
    )
    sql = re.sub(r"\$__timeFilter\(\s*([^)]+?)\s*\)",
                 r"\1 BETWEEN TIMESTAMP '2026-01-01 00:00:00' AND TIMESTAMP '2026-12-31 00:00:00'", sql)
    sql = re.sub(r"\$__unixEpochFilter\(\s*([^)]+?)\s*\)",
                 r"\1 BETWEEN 1767225600 AND 1798761600", sql)
    sql = re.sub(r"\$__timeGroupAlias\(\s*([^,]+?)\s*,\s*[^)]+?\)",
                 r'\1 AS "time"', sql)
    sql = re.sub(r"\$__timeGroup\(\s*([^,]+?)\s*,\s*[^)]+?\)", r"\1", sql)
    sql = re.sub(r"\$__timeEpoch\(\s*([^)]+?)\s*\)", r"\1", sql)
    sql = re.sub(r"\$__time\(\s*([^)]+?)\s*\)", r'\1 AS "time"', sql)

    def replace(match: re.Match) -> str:
        name = match.group(1) or match.group(2)
        # time range built-ins are epoch milliseconds in Grafana
        if name in ("__from", "__to"):
            return MACROS_SQL[f"${name}"]
        if name in values:
            return values[name][0]
        if name in BUILTIN_VARS:
            return "NULL"
        unresolved.append(name)
        return "NULL"

    sql = VAR_PATTERN.sub(replace, sql)
    return sql, unresolved


def resolve_values(dashboard: dict, db: Database | None, report: Report, name: str) -> dict[str, tuple[str, str]]:
    """Work out a value and a type for every variable of the dashboard."""
    values: dict[str, tuple[str, str]] = dict(FALLBACK_VALUES)
    variables = dashboard.get("templating", {}).get("list", []) or []

    # current display values are labels, not usable values
    for var in variables:
        current = (var.get("current") or {}).get("value")
        if isinstance(current, str) and current.strip() and "\n" not in current and "${" not in current:
            if var.get("name") not in values:
                values[var.get("name")] = (current.strip(), "text")

    if db is None:
        return values

    # resolve query variables against the database, twice, so that variables
    # depending on other variables also resolve
    for _ in range(2):
        for var_name, sql in variable_queries(dashboard):
            rendered, unresolved = render(sql, values)
            ok, out = db.prepare([f"PREPARE v_{abs(hash(var_name)) % 10**6} AS {rendered}"])
            if not ok:
                report.warning(name, f"variable '{var_name}' does not prepare", _first_line(out))
                continue
            ok, out = db.query(rendered)
            if not ok:
                continue
            rows = [line for line in out.splitlines() if line.strip()]
            if not rows:
                continue
            first = rows[0].split("|")[0].strip()
            if not first:
                continue
            literal = re.search(r'id="(\d+)"', first)
            if literal:
                first = literal.group(1)
            values[var_name] = (first, "text")
    return values


def _first_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("LINE") and not line.startswith("^"):
            return line[:300]
    return text.strip()[:300]


def _is_teslamate_schema(db: "Database") -> bool:
    ok, out = db.query("SELECT to_regclass('public.drives') IS NOT NULL;")
    return ok and out.strip().lower().startswith("t")


def sql_checks(loaded, db: Database, report: Report) -> int:
    checked = 0
    for name, dashboard in loaded:
        values = resolve_values(dashboard, db, report, name)
        statements = []
        for where, sql in all_sql(dashboard):
            rendered, unresolved = render(sql, values)
            for variable in sorted(set(unresolved)):
                report.warning(name, f"{where}: could not resolve $'{variable}'", "used NULL as a placeholder")
            statements.append((where, rendered))

        # prepare everything first: it checks types and identifiers without running
        for index, (where, rendered) in enumerate(statements):
            checked += 1
            ok, out = db.prepare([f"PREPARE dash_{index} AS {rendered}"])
            if not ok:
                report.error(name, f"{where}: SQL does not prepare", _first_line(out))
                continue
            ok, out = db.explain(rendered)
            if not ok:
                report.error(name, f"{where}: SQL does not plan", _first_line(out))
    return checked


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        help="repository root (default: the parent of this script)")
    parser.add_argument("--dsn", default=DEFAULT_DSN, help="PostgreSQL connection string of a TeslaMate database")
    parser.add_argument("--docker", default=DEFAULT_DOCKER, help="name of the PostgreSQL container to use via docker exec")
    parser.add_argument("--docker-user", default="teslamate", help="database user inside --docker (default: teslamate)")
    parser.add_argument("--docker-db", default="teslamate", help="database name inside --docker (default: teslamate)")
    parser.add_argument("--no-sql", action="store_true", help="run only the static checks (no database needed)")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = parser.parse_args(argv)

    report = Report()
    loaded = static_checks(args.root, report)

    checked = 0
    if loaded and not args.no_sql and (args.dsn or args.docker):
        db = Database(dsn=args.dsn if not args.docker else None, container=args.docker,
                      user=args.docker_user, database=args.docker_db)
        ok, out = db.alive()
        if not ok:
            report.error("database", f"cannot connect to {db.label}", _first_line(out))
        elif not _is_teslamate_schema(db):
            report.error(
                "database",
                f"{db.label} does not look like a TeslaMate database",
                "the 'drives' table is missing; the SQL checks need a migrated TeslaMate schema",
            )
        else:
            print(f"SQL checks against {db.label}")
            checked = sql_checks(loaded, db, report)
    elif loaded and not args.no_sql:
        print("SQL checks skipped: pass --dsn or --docker (or --no-sql to always skip)")

    for level, where, message, detail in report.findings:
        marker = "ERROR  " if level == ERROR else "WARNING"
        print(f"{marker} {where}: {message}")
        if detail:
            print(f"        {detail}")

    print()
    print(f"dashboards: {len(loaded)}   sql statements checked: {checked}")
    print(f"errors: {len(report.errors)}   warnings: {len(report.warnings)}")

    if report.errors or (args.strict and report.warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
