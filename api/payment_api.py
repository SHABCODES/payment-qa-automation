import random
import time
import re
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

app = FastAPI(title="Payment API Simulator", version="1.0.0")

# --------------------------------------------------------------------------- #
# In-memory transaction store
# --------------------------------------------------------------------------- #
transactions: dict = {}

# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
class TransferRequest(BaseModel):
    sender_iban: str
    receiver_iban: str
    amount: float
    currency: str = "EUR"
    reference: str = ""

    @field_validator("sender_iban", "receiver_iban")
    @classmethod
    def validate_iban(cls, v: str) -> str:
        v = v.replace(" ", "").upper()
        if not re.match(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{4,}$", v):
            raise ValueError("Invalid IBAN format")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        allowed = {"EUR", "USD", "GBP", "SEK"}
        if v.upper() not in allowed:
            raise ValueError(f"Unsupported currency. Allowed: {allowed}")
        return v.upper()


class ValidateRequest(BaseModel):
    iban: str
    currency: str = "EUR"


# --------------------------------------------------------------------------- #
# Simulated account balances (keyed by IBAN)
# --------------------------------------------------------------------------- #
INITIAL_BALANCES: dict[str, float] = {
    "FI2112345600000785": 50000.00,
    "FI1234567890123456": 175.00,
    "DE89370400440532013000": 10000.00,
    "GB29NWBK60161331926819": 750.00,
}

ACCOUNTS: dict[str, float] = dict(INITIAL_BALANCES)

DAILY_LIMIT = 9999.99
TIMEOUT_IBAN = "FI0000000000000000"   # special IBAN that simulates a timeout


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@app.post("/testing/reset")
def reset_state():
    """Test-only: resets account balances and transaction store to initial state."""
    global transactions
    transactions = {}
    ACCOUNTS.clear()
    ACCOUNTS.update(INITIAL_BALANCES)
    return {"reset": True}


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/transfer")
def transfer(req: TransferRequest):
    # Simulate network timeout
    if req.receiver_iban == TIMEOUT_IBAN or req.sender_iban == TIMEOUT_IBAN:
        time.sleep(0.5)
        raise HTTPException(status_code=504, detail={
            "error": "TIMEOUT",
            "message": "Payment processor did not respond in time",
        })

    # Sender must exist in our system
    if req.sender_iban not in ACCOUNTS:
        raise HTTPException(status_code=404, detail={
            "error": "ACCOUNT_NOT_FOUND",
            "message": f"Sender account {req.sender_iban} not found",
        })

    balance = ACCOUNTS[req.sender_iban]

    # Daily transfer limit (check before balance)
    if req.amount > DAILY_LIMIT:
        raise HTTPException(status_code=422, detail={
            "error": "EXCEEDS_DAILY_LIMIT",
            "message": f"Transfer amount exceeds daily limit of {DAILY_LIMIT:.2f}",
        })

    # Insufficient funds
    if req.amount > balance:
        raise HTTPException(status_code=422, detail={
            "error": "INSUFFICIENT_FUNDS",
            "message": f"Available balance {balance:.2f} {req.currency}, requested {req.amount:.2f}",
        })

    # Commit the transaction
    ACCOUNTS[req.sender_iban] -= req.amount
    tx_id = str(uuid4())
    transactions[tx_id] = {
        "transaction_id": tx_id,
        "sender_iban": req.sender_iban,
        "receiver_iban": req.receiver_iban,
        "amount": req.amount,
        "currency": req.currency,
        "reference": req.reference,
        "status": "COMPLETED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return transactions[tx_id]


@app.post("/validate")
def validate(req: ValidateRequest):
    iban = req.iban.replace(" ", "").upper()
    if not re.match(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{4,}$", iban):
        return {"valid": False, "reason": "INVALID_FORMAT"}

    country = iban[:2]
    supported_countries = {"FI", "DE", "GB", "SE", "NL", "FR"}
    if country not in supported_countries:
        return {"valid": False, "reason": "UNSUPPORTED_COUNTRY"}

    return {
        "valid": True,
        "iban": iban,
        "country": country,
        "currency": req.currency,
    }


@app.get("/transaction/{transaction_id}")
def get_transaction(transaction_id: str):
    tx = transactions.get(transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail={
            "error": "TRANSACTION_NOT_FOUND",
            "message": f"No transaction found with ID {transaction_id}",
        })
    return tx


@app.get("/account/{iban}/balance")
def get_balance(iban: str):
    iban = iban.replace(" ", "").upper()
    if iban not in ACCOUNTS:
        raise HTTPException(status_code=404, detail={
            "error": "ACCOUNT_NOT_FOUND",
            "message": f"Account {iban} not found",
        })
    return {"iban": iban, "balance": ACCOUNTS[iban], "currency": "EUR"}
