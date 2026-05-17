# DEF-002 — Daily limit check occurs after balance check, masking correct error code

**Status:** Fixed  
**Severity:** Medium  
**Priority:** High  
**Reported by:** QA Automation  
**Found by:** Test suite `02_error_scenarios` — `Transfer Exceeding Daily Limit`  
**Fixed in:** commit `fix/validation-order-daily-limit`

---

## Summary

When a transfer amount exceeded both the account balance *and* the daily limit, the API returned `INSUFFICIENT_FUNDS` instead of `EXCEEDS_DAILY_LIMIT`. This is incorrect — the daily limit check should take precedence because it is a system-level policy, whereas insufficient funds is an account-level condition. A user seeing `INSUFFICIENT_FUNDS` would incorrectly believe they simply need more money in their account, rather than understanding they have hit a transfer ceiling.

---

## Steps to reproduce

```bash
curl -X POST http://localhost:8001/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "sender_iban": "FI1234567890123456",
    "receiver_iban": "DE89370400440532013000",
    "amount": 10000.00,
    "currency": "EUR"
  }'
```

Account `FI1234567890123456` has balance 175.00 EUR. Amount 10,000.00 exceeds both the balance and the 9,999.99 daily limit.

---

## Expected result

```json
HTTP 422
{ "detail": { "error": "EXCEEDS_DAILY_LIMIT", ... } }
```

## Actual result (before fix)

```json
HTTP 422
{ "detail": { "error": "INSUFFICIENT_FUNDS", ... } }
```

---

## Root cause

Validation checks in `payment_api.py` were ordered: balance check first, daily limit second. When both conditions were violated, balance check fired first and short-circuited the daily limit check.

**Buggy order:**
```python
if req.amount > balance:
    raise ... INSUFFICIENT_FUNDS

if req.amount > DAILY_LIMIT:
    raise ... EXCEEDS_DAILY_LIMIT
```

**Fixed order:**
```python
if req.amount > DAILY_LIMIT:       # system policy checked first
    raise ... EXCEEDS_DAILY_LIMIT

if req.amount > balance:           # account state checked second
    raise ... INSUFFICIENT_FUNDS
```

---

## Test that caught this

**Suite:** `02_error_scenarios.robot`  
**Test:** `Transfer Exceeding Daily Limit`

Robot Framework output showed:
```
Transfer Exceeding Daily Limit    | FAIL |
INSUFFICIENT_FUNDS != EXCEEDS_DAILY_LIMIT
```

---

## Impact assessment

| Area | Impact |
|---|---|
| UX | User shown wrong error message, takes wrong corrective action |
| Support | Increased support tickets from confused users |
| Compliance | Incorrect error codes may violate PSD2 error reporting requirements |
| Severity | **Medium** — wrong behaviour but transfer still correctly rejected |

---

## Verification

Fixed and confirmed passing in CI. Boundary test `Transfer At Exact Daily Limit Is Accepted` also verified the fix didn't break the happy path at exactly 9,999.99.
