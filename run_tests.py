#!/usr/bin/env python3
"""
run_tests.py — One-command test runner for the Payment QA Demo
Usage:
    python run_tests.py               # run all suites
    python run_tests.py --suite 01    # run a specific suite
    python run_tests.py --tags smoke  # run by tag
"""

import argparse
import multiprocessing
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

API_HOST = "127.0.0.1"
API_PORT = 8001
RESULTS_DIR = Path("results")


# --------------------------------------------------------------------------- #
# API process
# --------------------------------------------------------------------------- #
def start_api():
    import uvicorn
    from api.payment_api import app
    uvicorn.run(app, host=API_HOST, port=API_PORT, log_level="warning")


def wait_for_api(timeout: int = 10) -> bool:
    url = f"http://{API_HOST}:{API_PORT}/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description="Payment QA test runner")
    parser.add_argument("--suite", help="Suite number to run, e.g. 01, 02, 03")
    parser.add_argument("--tags", help="Robot Framework tag filter, e.g. smoke")
    parser.add_argument("--no-dashboard", action="store_true", help="Skip dashboard generation")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(exist_ok=True)

    # Start API
    print("▶  Starting payment API...")
    api_proc = multiprocessing.Process(target=start_api, daemon=True)
    api_proc.start()

    if not wait_for_api():
        print("✗  API failed to start within 10 seconds.")
        api_proc.terminate()
        sys.exit(1)
    print(f"✓  API running at http://{API_HOST}:{API_PORT}")

    # Build robot command
    cmd = [
        sys.executable, "-m", "robot",
        "--outputdir", str(RESULTS_DIR),
        "--loglevel", "INFO",
    ]
    if args.tags:
        cmd += ["--include", args.tags]
    if args.suite:
        cmd += [f"tests/suites/0{args.suite.lstrip('0')}_*.robot"]
        # glob-style won't work directly, build path list instead
        matches = sorted(Path("tests/suites").glob(f"0{args.suite.lstrip('0')}*.robot"))
        if not matches:
            print(f"✗  No suite found matching '0{args.suite}'")
            api_proc.terminate()
            sys.exit(1)
        cmd = [
            sys.executable, "-m", "robot",
            "--outputdir", str(RESULTS_DIR),
            "--loglevel", "INFO",
        ] + ([f"--include", args.tags] if args.tags else []) + [str(m) for m in matches]
    else:
        cmd += ["tests/suites/"]

    # Run tests
    print("\n▶  Running Robot Framework tests...\n")
    result = subprocess.run(cmd)

    # Generate dashboard
    if not args.no_dashboard:
        xml = RESULTS_DIR / "output.xml"
        if xml.exists():
            print("\n▶  Generating QA dashboard...")
            subprocess.run([
                sys.executable, "dashboard/parse_results.py",
                str(xml), "--out", str(RESULTS_DIR / "dashboard.html")
            ])
            print(f"✓  Dashboard: {RESULTS_DIR / 'dashboard.html'}")

    api_proc.terminate()
    print("\n✓  API stopped.")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
