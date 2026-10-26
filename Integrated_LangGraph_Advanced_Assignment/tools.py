import csv

from langchain_core.tools import tool

PURCHASE_ORDERS_FILE = "data/purchase_orders.csv"
PAYMENT_LEDGER_FILE = "data/payment_ledger.csv"


@tool
def lookup_purchase_order(po_number: str) -> dict:
    """Return the purchase-order row for po_number, or {} if it does not exist."""
    with open(PURCHASE_ORDERS_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["po_number"] == po_number.strip():
                row["approved_amount"] = float(row["approved_amount"])
                return row
    return {}


@tool
def invoice_already_paid(invoice_number: str) -> bool:
    """Return True if invoice_number is already in the payment ledger."""
    with open(PAYMENT_LEDGER_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["invoice_number"] == invoice_number.strip():
                return True
    return False


@tool
def schedule_payment(invoice_number: str, amount: float) -> str:
    """Schedule payment for an approved invoice and return the payment reference."""
    return f"PAY-{invoice_number}-{round(amount)}"
