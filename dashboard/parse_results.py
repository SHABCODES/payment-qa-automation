#!/usr/bin/env python3
"""
parse_results.py — Generates an HTML QA dashboard from Robot Framework output.xml
Usage: python parse_results.py [output.xml] [--out dashboard.html]
"""

import sys
import argparse
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    sys.path.insert(0, str(Path(__file__).parent))
    from history import load_history, build_trend_html, append_run
    HAS_HISTORY = True
except ImportError:
    HAS_HISTORY = False


def parse_output(xml_path: str) -> dict:
    root = ET.parse(xml_path).getroot()
    suites = []
    total_pass = total_fail = 0

    for suite in root.iter("suite"):
        tests = []
        for test in suite.findall("test"):
            status_el = test.find("status")
            status = status_el.attrib.get("status", "UNKNOWN")
            elapsed = _elapsed(status_el)
            msg_el = test.find(".//msg[@level='FAIL']")
            tests.append({
                "name": test.attrib.get("name"),
                "status": status,
                "elapsed_ms": elapsed,
                "tags": [t.text for t in test.findall("tag")],
                "message": msg_el.text if msg_el is not None else "",
            })
            if status == "PASS":
                total_pass += 1
            else:
                total_fail += 1
        if tests:
            suites.append({"name": suite.attrib.get("name"), "tests": tests})

    generated = root.find(".//status")
    run_time = generated.attrib.get("starttime", "") if generated is not None else ""
    return {
        "run_time": run_time,
        "total_pass": total_pass,
        "total_fail": total_fail,
        "total": total_pass + total_fail,
        "suites": suites,
    }


def _elapsed(el) -> int:
    if el is None:
        return 0
    try:
        return int(el.attrib.get("elapsed", 0))
    except (ValueError, TypeError):
        return 0


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Payment QA Dashboard</title>
<style>
  :root {{
    --pass: #1D9E75; --fail: #D85A30; --bg: #f8f7f4;
    --card: #ffffff; --border: #e2e0d9; --text: #2c2c2a;
    --muted: #6b6a65; --radius: 10px;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 32px 24px; max-width: 960px; margin: 0 auto; }}
  h1 {{ font-size: 22px; font-weight: 600; margin-bottom: 4px; }}
  .run-time {{ color: var(--muted); font-size: 13px; margin-bottom: 28px; }}
  .summary {{ display: flex; gap: 16px; margin-bottom: 28px; flex-wrap: wrap; }}
  .stat-card {{ background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px 28px; flex: 1; min-width: 140px; }}
  .stat-card .label {{ font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }}
  .stat-card .value {{ font-size: 32px; font-weight: 700; margin-top: 4px; }}
  .stat-card.pass .value {{ color: var(--pass); }}
  .stat-card.fail .value {{ color: var(--fail); }}
  .progress-bar {{ height: 8px; background: var(--border); border-radius: 4px; margin-bottom: 28px; overflow: hidden; }}
  .progress-bar .fill {{ height: 100%; background: var(--pass); border-radius: 4px; }}
  .suite {{ background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 20px; overflow: hidden; }}
  .suite-header {{ padding: 14px 20px; font-weight: 600; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }}
  .suite-header .counts {{ font-size: 13px; font-weight: 400; color: var(--muted); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; padding: 10px 20px; font-size: 11px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); border-bottom: 1px solid var(--border); }}
  td {{ padding: 10px 20px; border-bottom: 1px solid var(--border); vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
  .badge.PASS {{ background: #e1f5ee; color: #0f6e56; }}
  .badge.FAIL {{ background: #faece7; color: #993c1d; }}
  .tag {{ display: inline-block; background: #f1efe8; color: var(--muted); border-radius: 3px; padding: 1px 6px; font-size: 11px; margin-right: 3px; }}
  .fail-msg {{ color: var(--fail); font-size: 12px; margin-top: 4px; font-family: monospace; white-space: pre-wrap; }}
  footer {{ margin-top: 32px; text-align: center; font-size: 12px; color: var(--muted); }}
  h2 {{ font-size: 16px; font-weight: 600; margin: 28px 0 14px; }}
</style>
</head>
<body>
<h1>Payment QA Dashboard</h1>
<p class="run-time">Run: {run_time} &nbsp;|&nbsp; {total} tests</p>

<div class="summary">
  <div class="stat-card pass">
    <div class="label">Passed</div>
    <div class="value">{total_pass}</div>
  </div>
  <div class="stat-card fail">
    <div class="label">Failed</div>
    <div class="value">{total_fail}</div>
  </div>
  <div class="stat-card">
    <div class="label">Pass rate</div>
    <div class="value">{pass_rate}%</div>
  </div>
</div>

<div class="progress-bar">
  <div class="fill" style="width:{pass_rate}%"></div>
</div>

{trend_html}

<h2>Test results</h2>
{suites_html}

<footer>Generated by parse_results.py &mdash; Payment QA Demo</footer>
</body>
</html>
"""


def build_suites_html(suites: list) -> str:
    html = []
    for suite in suites:
        pass_count = sum(1 for t in suite["tests"] if t["status"] == "PASS")
        fail_count = len(suite["tests"]) - pass_count
        rows = []
        for t in suite["tests"]:
            tags = "".join(f'<span class="tag">{tag}</span>' for tag in t["tags"])
            fail_msg = f'<div class="fail-msg">{t["message"][:300]}</div>' if t["message"] else ""
            rows.append(f"""
              <tr>
                <td>{t['name']}{fail_msg}</td>
                <td><span class="badge {t['status']}">{t['status']}</span></td>
                <td>{t['elapsed_ms']} ms</td>
                <td>{tags}</td>
              </tr>""")
        html.append(f"""
<div class="suite">
  <div class="suite-header">
    {suite['name']}
    <span class="counts">{pass_count} passed &nbsp; {fail_count} failed</span>
  </div>
  <table>
    <thead><tr><th>Test</th><th>Status</th><th>Duration</th><th>Tags</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</div>""")
    return "\n".join(html)


def main():
    parser = argparse.ArgumentParser(description="Generate QA dashboard from RF output.xml")
    parser.add_argument("xml", nargs="?", default="output.xml")
    parser.add_argument("--out", default="dashboard.html")
    parser.add_argument("--no-history", action="store_true")
    args = parser.parse_args()

    xml_path = Path(args.xml)
    if not xml_path.exists():
        print(f"Error: {xml_path} not found.")
        sys.exit(1)

    # Append to history
    trend_html = ""
    if HAS_HISTORY and not args.no_history:
        append_run(str(xml_path))
        trend_html = "<h2>Run history</h2>" + build_trend_html(load_history())

    data = parse_output(str(xml_path))
    pass_rate = round(data["total_pass"] / data["total"] * 100) if data["total"] else 0

    html = HTML_TEMPLATE.format(
        run_time=data["run_time"],
        total=data["total"],
        total_pass=data["total_pass"],
        total_fail=data["total_fail"],
        pass_rate=pass_rate,
        trend_html=trend_html,
        suites_html=build_suites_html(data["suites"]),
    )

    Path(args.out).write_text(html, encoding="utf-8")
    print(f"Dashboard written to {args.out}")
    print(f"Results: {data['total_pass']} passed, {data['total_fail']} failed ({pass_rate}% pass rate)")


if __name__ == "__main__":
    main()
