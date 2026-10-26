from typing import TypedDict


class ProcurementState(TypedDict, total=False):
    invoice_path: str
    invoice_text: str
    invoice: dict
    purchase_order: dict
    decision: str
    reason: str
    payment_reference: str
    meeting_id: str
    meeting_title: str
    attendees: list[str]
    notes: str
    action_items: list[dict]
    vendor_note: dict
    report: str
