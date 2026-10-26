import json

from agents import (assign_action_owner_priority, draft_vendor_note,
                    extract_follow_up_actions, extract_invoice_data)
from state import ProcurementState
from tools import invoice_already_paid, lookup_purchase_order, schedule_payment

AMOUNT_TOLERANCE = 0.02
MEETINGS_FILE = "data/procurement_meetings.json"


def load_invoice(state: ProcurementState) -> dict:
    with open(state["invoice_path"], encoding="utf-8") as f:
        return {"invoice_text": f.read()}


def extract_invoice(state: ProcurementState) -> dict:
    return {"invoice": extract_invoice_data(state["invoice_text"])}


def decide(invoice: dict, po: dict) -> tuple[str, str]:
    """Apply the business rules in order. The first failing rule decides."""
    # Rule 1: PO must exist and be open
    if not po:
        return "rejected", f"Purchase order {invoice['po_number']} was not found in the register."
    if po["status"].strip().lower() != "open":
        return "rejected", f"Purchase order {po['po_number']} is not open (status: {po['status']})."

    # Rule 2: invoice must not be paid already
    if invoice_already_paid.invoke({"invoice_number": invoice["invoice_number"]}):
        return "rejected", (f"Invoice {invoice['invoice_number']} is already in the payment ledger; "
                            "paying it again would be a duplicate payment.")

    # Rule 3: vendor names must match (ignoring case and surrounding spaces)
    if invoice["vendor_name"].strip().lower() != po["vendor_name"].strip().lower():
        return "review", (f"Vendor name '{invoice['vendor_name']}' does not match "
                          f"the PO vendor '{po['vendor_name']}'.")

    # Rule 4: amount must be within 2% of the approved amount
    if abs(invoice["amount"] - po["approved_amount"]) > AMOUNT_TOLERANCE * po["approved_amount"]:
        return "review", (f"Invoice total {invoice['amount']:.2f} is outside the permitted 2% tolerance "
                          f"of the approved amount {po['approved_amount']:.2f}.")

    # Rule 5: everything passed
    return "approved", "All payment eligibility checks passed."


def match_purchase_order(state: ProcurementState) -> dict:
    invoice = state["invoice"]
    po = lookup_purchase_order.invoke({"po_number": invoice["po_number"]})
    decision, reason = decide(invoice, po)
    return {"purchase_order": po, "decision": decision, "reason": reason}


def approve_payment(state: ProcurementState) -> dict:
    invoice = state["invoice"]
    reference = schedule_payment.invoke(
        {"invoice_number": invoice["invoice_number"], "amount": invoice["amount"]})
    return {"payment_reference": reference}


def load_review_meeting(state: ProcurementState) -> dict:
    with open(MEETINGS_FILE, encoding="utf-8") as f:
        meetings = json.load(f)["meetings"]
    for meeting in meetings:
        if meeting["po_number"] == state["invoice"]["po_number"]:
            return {"meeting_id": meeting["meeting_id"], "meeting_title": meeting["title"],
                    "attendees": meeting["attendees"], "notes": meeting["notes"]}
    return {"meeting_id": "", "meeting_title": "", "attendees": [], "notes": ""}


def extract_actions(state: ProcurementState) -> dict:
    if not state["notes"]:
        return {"action_items": []}
    tasks = extract_follow_up_actions(state["notes"])
    return {"action_items": [{"task": task, "owner": "", "priority": ""} for task in tasks]}


def assign_owners(state: ProcurementState) -> dict:
    items = []
    for item in state["action_items"]:
        owner, priority = assign_action_owner_priority(item["task"], state["attendees"])
        items.append({"task": item["task"], "owner": owner, "priority": priority})
    return {"action_items": items}


def notify_vendor(state: ProcurementState) -> dict:
    return {"vendor_note": draft_vendor_note(state["invoice"], state["decision"], state["reason"])}


def format_report(state: ProcurementState) -> dict:
    invoice = state["invoice"]
    lines = [
        "PROCUREFLOW AI — INVOICE REVIEW",
        f"Invoice Number : {invoice['invoice_number']}",
        f"Vendor         : {invoice['vendor_name']}",
        f"Purchase Order : {invoice['po_number']}",
        f"Decision       : {state['decision']}",
        f"Reason         : {state['reason']}",
    ]

    if state["decision"] == "approved":
        lines.append(f"Payment Ref.   : {state['payment_reference']}")
        return {"report": "\n".join(lines)}

    note = state["vendor_note"]
    lines += ["", "VENDOR NOTE",
              f"Subject : {note['subject']}",
              f"Message : {note['message']}",
              "", "PROCUREMENT FOLLOW-UP"]

    if not state["meeting_id"]:
        lines.append("No linked procurement meeting was found; no actions were identified.")
        return {"report": "\n".join(lines)}

    lines += [f"Meeting ID : {state['meeting_id']}",
              f"Meeting    : {state['meeting_title']}",
              f"Actions ({len(state['action_items'])}):"]
    for number, item in enumerate(state["action_items"], start=1):
        lines.append(f"  {number}. [{item['priority']}] {item['task']}")
        lines.append(f"     Owner: {item['owner']}")
    return {"report": "\n".join(lines)}
