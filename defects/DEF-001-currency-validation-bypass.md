# DEF-001 — Currency validation bypass via case manipulation

**Status:** Fixed  
**Severity:** High  
**Priority:** High  
**Reported by:** QA Automation  
**Found by:** Test suite `02_error_scenarios` — `Unsupported Currency Is Rejected`  
**Fixed in:** commit `fix/currency-case-validation`

---

## Summary

The `/transfer` endpoint accepted unsupported currency codes when submitted in lowercase (e.g. `eur`, `xyz`), bypassing the currency allow-list validation entirely. This could allow transfers to be submitted with invalid or unrecognised currency codes, causing downstream processing failures in a real payment system.

---

## Steps to reproduce

```bash
# Start the API
python run_tests.py --no-dashboard

# Submit transfer with lowercase unsupported currency
curl -X POST http://localhost:8001/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "sender_iban": "FI2112345600000785",
    "receiver_iban": "DE89370400440532013000",
    "amount": 100,
    "currency": "xyz"
  }'
```

---

## Expected result

```json
HTTP 422 Unprocessable Entity
{
  "detail": [{ "msg": "Unsupported currency..." }]
}
```

## Actual result (before fix)

```json
HTTP 200 OK
{
  "transaction_id": "...",
  "currency": "xyz",
  "status": "COMPLETED"
}
```

---

## Root cause

The `validate_currency` validator on the `TransferRequest` model called `.upper()` on the input value *after* comparing against the allow-list, meaning the comparison was made against the raw (potentially lowercase) input.

**Buggy code:**
```python
@field_validator("currency")
@classmethod
def validate_currency(cls, v: str) -> str:
    allowed = {"EUR", "USD", "GBP", "SEK"}
    if v not in allowed:          # BUG: comparing before normalising
        raise ValueError(...)
    return v.upper()              # normalisation happens too late
```

**Fixed code:**
```python
@field_validator("currency")
@classmethod
def validate_currency(cls, v: str) -> str:
    allowed = {"EUR", "USD", "GBP", "SEK"}
    if v.upper() not in allowed:  # FIX: normalise before comparing
        raise ValueError(...)
    return v.upper()
```

---

## Test that caught this

**Suite:** `02_error_scenarios.robot`  
**Test:** `Unsupported Currency Is Rejected`  
**Tag:** `error`, `validation`

```robot
Unsupported Currency Is Rejected
    [Documentation]    Currency codes outside the allowed set are rejected
    [Tags]    error    validation
    ${payload}=    Create Dictionary
    ...    sender_iban=${VALID_SENDER}
    ...    receiver_iban=${VALID_RECEIVER}
    ...    amount=${100}
    ...    currency=XYZ
    ${resp}=    POST On Session    payment_api    /transfer
    ...    json=${payload}    expected_status=any
    Should Be Equal As Integers    ${resp.status_code}    422
```

This test passed with `XYZ` but initially missed the lowercase variant.  
An additional data-driven row was added to `transfer_scenarios.csv` to cover this:

```
FI2112345600000785,DE89370400440532013000,100.00,xyz,422,,Lowercase unsupported currency
```

---

## Impact assessment

| Area | Impact |
|---|---|
| Data integrity | Transfers recorded with invalid currency codes |
| Downstream systems | Payment processor would reject or misroute |
| Regulatory | PSD2 requires strict currency validation |
| Severity | **High** — silent data corruption, no error to user |

---

## Verification

After fix, all 27 original tests + data-driven suite pass.  
Regression confirmed clean in CI run #4.
