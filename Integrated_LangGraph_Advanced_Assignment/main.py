import os

from graph import build_graph


def process_invoice(invoice_number: str) -> dict:
    invoice_number = invoice_number.strip()
    path = f"data/invoices/{invoice_number}.txt"
    if not os.path.exists(path):
        return {}
    graph = build_graph()
    return graph.invoke({"invoice_path": path})


if __name__ == "__main__":
    number = input("Enter the invoice number: ").strip()
    result = process_invoice(number)
    if not result:
        print(f"Invoice {number} was not found")
    else:
        print(result["report"])
