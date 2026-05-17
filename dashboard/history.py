#!/usr/bin/env python3
"""
history.py — Manages a rolling run history file (run_history.json).
Called by run_tests.py and the CI pipeline after each test run.
Also generates the trend section of the dashboard.

Usage:
    python dashboard/history.py results/output.xml          # append current run
    python dashboard/history.py --show                      # print history table
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

HISTORY_FILE = Path("results/run_history.json")
MAX_RUNS = 20


# --------------------------------------------------------------------------- #
# Parse a single output.xml into a run record
# --------------------------------------------------------------------------- #
def parse_run(xml_path: str) -> dict:
    root = ET.parse(xml_path).getroot()
    stats = root.find(".//total/stat")
    passed = int(stats.attrib.get("pass", 0))
    failed = int(stats.attrib.get("fail", 0))
    total = passed + failed

    suite_results = []
    for suite in root.iter("suite"):
        tests = suite.findall("test")
        if not tests:
            continue
        p = sum(1 for t in tests if t.find("status").attrib.get("status") == "PASS")
        suite_results.append({
            "name": suite.attrib.get("name", ""),
            "passed": p,
            "failed": len(tests) - p,
        })

    start_el = root.find(".//status")
    run_time = start_el.attrib.get("starttime", "") if start_el is not None else ""

    return {
        "run_number": None,          # filled in below
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rf_timestamp": run_time,
        "passed": passed,
        "failed": failed,
        "total": total,
        "pass_rate": round(passed / total * 100) if total else 0,
        "result": "PASS" if failed == 0 else "FAIL",
        "suites": suite_results,
    }


# --------------------------------------------------------------------------- #
# Load / save history
# --------------------------------------------------------------------------- #
def load_history() -> list:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return []


def save_history(runs: list):
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(runs, indent=2))


def append_run(xml_path: str) -> dict:
    history = load_history()
    run = parse_run(xml_path)
    run["run_number"] = len(history) + 1
    history.append(run)
    # Keep only last MAX_RUNS
    if len(history) > MAX_RUNS:
        history = history[-MAX_RUNS:]
    save_history(history)
    print(f"Run #{run['run_number']} recorded: {run['passed']} passed, {run['failed']} failed ({run['pass_rate']}%)")
    return run


# --------------------------------------------------------------------------- #
# Build trend HTML snippet
# --------------------------------------------------------------------------- #
def build_trend_html(history: list) -> str:
    if not history:
        return "<p>No run history yet.</p>"

    rows = []
    for r in reversed(history[-10:]):
        icon = "✅" if r["result"] == "PASS" else "❌"
        rate_color = "#1D9E75" if r["pass_rate"] >= 90 else "#D85A30"
        rows.append(f"""
        <tr>
          <td>#{r['run_number']}</td>
          <td>{icon} {r['result']}</td>
          <td style="color:{rate_color};font-weight:600">{r['pass_rate']}%</td>
          <td>{r['passed']}/{r['total']}</td>
          <td style="color:#6b6a65;font-size:12px">{r['timestamp'][:19].replace('T',' ')}</td>
        </tr>""")

    bar_max = max((r["total"] for r in history), default=1)
    bars = ""
    for r in history[-10:]:
        ph = round(r["passed"] / bar_max * 60)
        fh = round(r["failed"] / bar_max * 60)
        color = "#1D9E75" if r["failed"] == 0 else "#D85A30"
        bars += f"""
        <div style="display:flex;flex-direction:column;align-items:center;gap:2px">
          <span style="font-size:10px;color:#6b6a65">#{r['run_number']}</span>
          <div style="width:28px;background:#f1efe8;border-radius:4px;overflow:hidden;height:64px;display:flex;flex-direction:column;justify-content:flex-end">
            <div style="width:100%;height:{ph+fh}px;background:{color};border-radius:4px"></div>
          </div>
          <span style="font-size:9px;color:#6b6a65">{r['pass_rate']}%</span>
        </div>"""

    return f"""
    <div class="suite" style="margin-bottom:20px">
      <div class="suite-header">Run history <span class="counts">last {min(len(history),10)} runs</span></div>
      <div style="padding:16px 20px;display:flex;gap:6px;align-items:flex-end;border-bottom:1px solid var(--border)">
        {bars}
      </div>
      <table>
        <thead><tr><th>Run</th><th>Result</th><th>Pass rate</th><th>Tests</th><th>Timestamp</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>"""


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("xml", nargs="?", help="Path to output.xml to append")
    parser.add_argument("--show", action="store_true", help="Print history table")
    parser.add_argument("--trend-html", action="store_true", help="Print trend HTML snippet")
    args = parser.parse_args()

    if args.show:
        history = load_history()
        if not history:
            print("No history yet.")
            return
        print(f"{'Run':>4}  {'Result':<6}  {'Rate':>5}  {'Pass/Total':<12}  Timestamp")
        print("-" * 55)
        for r in history:
            print(f"#{r['run_number']:>3}  {r['result']:<6}  {r['pass_rate']:>4}%  {r['passed']}/{r['total']:<10}  {r['timestamp'][:19]}")
        return

    if args.trend_html:
        print(build_trend_html(load_history()))
        return

    if args.xml:
        append_run(args.xml)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
