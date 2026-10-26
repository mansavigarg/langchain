from langgraph.graph import END, START, StateGraph

from nodes import (approve_payment, assign_owners, extract_actions, extract_invoice,
                   format_report, load_invoice, load_review_meeting, match_purchase_order,
                   notify_vendor)
from state import ProcurementState


def route_after_matching(state: ProcurementState) -> str:
    if state["decision"] == "approved":
        return "approve_payment"
    return "load_review_meeting"


def build_graph():
    builder = StateGraph(ProcurementState)

    for node in (load_invoice, extract_invoice, match_purchase_order, approve_payment,
                 load_review_meeting, extract_actions, assign_owners, notify_vendor, format_report):
        builder.add_node(node.__name__, node)

    builder.add_edge(START, "load_invoice")
    builder.add_edge("load_invoice", "extract_invoice")
    builder.add_edge("extract_invoice", "match_purchase_order")
    builder.add_conditional_edges("match_purchase_order", route_after_matching,
                                  ["approve_payment", "load_review_meeting"])

    # approved branch
    builder.add_edge("approve_payment", "format_report")

    # review / rejected branch
    builder.add_edge("load_review_meeting", "extract_actions")
    builder.add_edge("extract_actions", "assign_owners")
    builder.add_edge("assign_owners", "notify_vendor")
    builder.add_edge("notify_vendor", "format_report")

    builder.add_edge("format_report", END)
    return builder.compile()
