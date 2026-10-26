# ProcureFlow AI

Processes one vendor invoice per run. Gemini extracts the invoice fields; Python rules decide
`approved` / `review` / `rejected`. Approved invoices get a payment reference. Other invoices get
follow-up actions from the linked procurement meeting (each with an owner and priority) and a vendor note.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then set GEMINI_API_KEY and GEMINI_MODEL
```

## Run

```bash
python3 main.py
# Enter the invoice number: INV-25041
```

## Test

```bash
python3 -m pytest tests.py -vv
```

The tests replace Gemini with a fake client, so they need no API key or network.

## Sample invoices

| Invoice | Expected decision | Why |
|---|---|---|
| INV-25041 | approved | all checks pass (48,500.40 vs 48,500) |
| INV-25042 | approved | exactly 2% over, vendor in capitals, PO status `open` |
| INV-25043 | review | amount more than 2% over |
| INV-25044 | review | vendor name differs |
| INV-25045 | rejected | already in the payment ledger |
| INV-25046 | rejected | PO closed (amount is also wrong, but rule 1 wins) |
| INV-25047 | rejected | PO not in the register, no linked meeting |
| INV-25048 | rejected | PO on hold |
