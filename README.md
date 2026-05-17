# Payment QA Automation Demo

[![Payment QA Suite](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=github-actions&logoColor=white)](https://github.com/SHABCODES/payment-qa-automation/actions)
[![Tests](https://img.shields.io/badge/tests-29%20passing-1D9E75)](https://github.com/SHABCODES/payment-qa-automation/actions)
[![Robot Framework](https://img.shields.io/badge/Robot_Framework-7.1-black?logo=robot-framework)](https://robotframework.org)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)

A portfolio project demonstrating production-grade test automation skills for the banking and payments domain.

Built with **Python · FastAPI · Robot Framework · Jenkins · GitHub Actions**, this project simulates a SEPA-style payment API and runs 29 automated tests across 5 suites — covering happy paths, error scenarios, boundary conditions, and data-driven validation.

---

## What this demonstrates

| Job requirement | How it's shown |
|---|---|
| Python | FastAPI server, keyword libraries, dashboard generator, history tracker |
| Robot Framework | 5 suites, keyword-driven + data-driven (CSV), tags, fixtures, FOR loops |
| Jenkins | `Jenkinsfile` with full pipeline: build → test → report → archive |
| GitHub Actions | `.github/workflows/test.yml` — runs on push, PR, and nightly schedule |
| Payment domain | SEPA IBANs, multi-currency, transfer limits, PSD2-style error codes |
| ISTQB test design | Boundary analysis, equivalence partitioning, negative testing, regression |
| Test reporting | RF `output.xml` → custom HTML dashboard with run trend history |
| Defect management | 2 documented defects found and fixed (see `/defects`) |
| Test isolation | Reset endpoint, suite-level setup/teardown |

---

## Project structure

```
payment-qa-demo/
│
├── .github/workflows/
│   └── test.yml                      # GitHub Actions CI pipeline
│
├── api/
│   └── payment_api.py                # FastAPI payment simulator
│
├── tests/
│   ├── data/
│   │   ├── iban_validation.csv       # 14 IBAN test cases
│   │   └── transfer_scenarios.csv    # 13 transfer scenarios
│   ├── keywords/
│   │   └── payment_keywords.robot    # Reusable RF keyword library
│   └── suites/
│       ├── 01_happy_path.robot       # 8 tests — valid flows
│       ├── 02_error_scenarios.robot  # 11 tests — error codes
│       ├── 03_boundary_regression.robot  # 8 tests — boundaries
│       ├── 04_data_driven_validation.robot  # CSV-driven IBAN tests
│       └── 05_data_driven_transfers.robot   # CSV-driven transfers
│
├── dashboard/
│   ├── parse_results.py              # output.xml → HTML dashboard
│   └── history.py                   # Multi-run trend tracker
│
├── defects/
│   ├── DEF-001-currency-validation-bypass.md
│   └── DEF-002-validation-order-daily-limit.md
│
├── results/                          # Generated after running tests
│   ├── output.xml
│   ├── log.html
│   ├── report.html
│   ├── run_history.json
│   └── dashboard.html               # Custom QA dashboard with trends
│
├── Jenkinsfile                       # Jenkins CI pipeline
├── run_tests.py                      # One-command local runner
├── requirements.txt
└── README.md
```

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run everything (API + all 5 suites + dashboard)
python run_tests.py

# 3. Open the dashboard
open results/dashboard.html
```

### Filtering runs

```bash
python run_tests.py --suite 01          # happy path only
python run_tests.py --suite 02          # error scenarios only
python run_tests.py --tags smoke        # smoke tests only
python run_tests.py --tags data-driven  # data-driven suites only
```

---

## CI/CD

### GitHub Actions
Runs automatically on every push to `main` or `develop`, on pull requests, and nightly (Mon–Fri 06:00 UTC).

Results are uploaded as build artifacts (retained 30 days) and a summary is written to the GitHub Actions job summary page.

### Jenkins
The `Jenkinsfile` defines a pipeline:
```
Setup Python env → Start API → Run RF tests → Generate dashboard → Archive results
```

---

## API reference

Base URL: `http://localhost:8001`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/transfer` | Submit a payment |
| POST | `/validate` | Validate an IBAN |
| GET | `/transaction/{id}` | Fetch a transaction |
| GET | `/account/{iban}/balance` | Get account balance |
| POST | `/testing/reset` | Reset state (test isolation) |

### Error codes

| Code | HTTP | Trigger |
|------|------|---------|
| `INSUFFICIENT_FUNDS` | 422 | Balance too low |
| `EXCEEDS_DAILY_LIMIT` | 422 | Amount > 9,999.99 |
| `ACCOUNT_NOT_FOUND` | 404 | Unknown sender IBAN |
| `TRANSACTION_NOT_FOUND` | 404 | Unknown transaction ID |
| `TIMEOUT` | 504 | Receiver = `FI0000000000000000` |
| `INVALID_FORMAT` | 422 | Malformed IBAN |
| `UNSUPPORTED_COUNTRY` | 422 | IBAN country not supported |

---

## Test design approach

Tests follow ISTQB principles throughout:

- **Equivalence partitioning** — valid/invalid IBANs, supported/unsupported currencies
- **Boundary value analysis** — 9,999.99 (pass) vs 10,000.00 (fail), 0.01 minimum, balance edge
- **Error guessing** — timeout IBAN, negative amounts, missing accounts, lowercase currency
- **Data-driven testing** — CSV tables with 14 IBAN cases and 13 transfer scenarios
- **Regression testing** — balance consistency, API contract fields, timestamp format
- **Test isolation** — suite-level reset, `/testing/reset` endpoint

---

## Defects found

Real bugs discovered during development, documented as formal defect reports:

| ID | Title | Severity | Status |
|----|-------|----------|--------|
| [DEF-001](defects/DEF-001-currency-validation-bypass.md) | Currency validation bypass via lowercase input | High | Fixed |
| [DEF-002](defects/DEF-002-validation-order-daily-limit.md) | Daily limit check fires after balance check, wrong error code returned | Medium | Fixed |

---

## Test results

**29 tests · 5 suites · 100% pass rate**

| Suite | Tests | Coverage |
|-------|-------|----------|
| 01 Happy Path | 8 | Valid EUR/GBP transfers, IBAN validation, balance, transaction lookup |
| 02 Error Scenarios | 11 | All 7 error codes, boundary inputs, invalid formats |
| 03 Boundary Regression | 8 | Limit boundaries, min amount, balance consistency, contract fields |
| 04 Data-Driven Validation | 1* | 14 IBAN cases from CSV |
| 05 Data-Driven Transfers | 1* | 13 transfer scenarios from CSV |

*Each data-driven test iterates all rows from its CSV file.
