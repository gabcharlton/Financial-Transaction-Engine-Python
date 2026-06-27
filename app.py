"""
Financial Transaction Engine
A lightweight Flask app for small businesses to categorize transactions
and generate income statements and balance sheets.

Run with:
    python app.py

Then open http://localhost:5000 in your browser.
"""

import csv
import io
import json
import os
import re
import webbrowser
from datetime import datetime
from threading import Timer

from flask import Flask, jsonify, render_template, request, Response

app = Flask(__name__)

# ─── Category definitions ────────────────────────────────────────────────────

CATEGORIES = {
    "income": [
        "Revenue / Sales",
        "Service income",
        "Consulting income",
        "Rental income",
        "Interest income",
        "Other income",
    ],
    "expense": [
        "Cost of goods sold",
        "Salaries & wages",
        "Rent & utilities",
        "Office supplies",
        "Marketing & advertising",
        "Professional fees",
        "Bank fees",
        "Insurance",
        "Travel & meals",
        "Depreciation",
        "Interest expense",
        "Tax expense",
        "Other expense",
    ],
    "asset": [
        "Cash & equivalents",
        "Accounts receivable",
        "Inventory",
        "Prepaid expenses",
        "Fixed assets",
        "Other assets",
    ],
    "liability": [
        "Accounts payable",
        "Credit card payable",
        "Line of credit",
        "Loans payable",
        "Accrued liabilities",
        "Other liabilities",
    ],
    "equity": [
        "Owner's equity",
        "Retained earnings",
        "Capital contributions",
        "Distributions / withdrawals",
    ],
    "transfer": ["Transfer / inter-account"],
}

# Flat list for lookups
ALL_CATEGORIES = [c for cats in CATEGORIES.values() for c in cats]

# Map category → group
CAT_TO_GROUP = {c: g for g, cats in CATEGORIES.items() for c in cats}

# ─── AI suggestion rules (keyword-based) ─────────────────────────────────────
# To upgrade to a real AI model, replace `ai_suggest()` with an API call.
# See the README for details.

AI_RULES = [
    (r"payroll|salary|wage|gusto|adp",                          "Salaries & wages",          "expense"),
    (r"rent|lease|hydro|electricity|water|utility|telus|rogers|bell", "Rent & utilities",    "expense"),
    (r"office|staples|amazon|supplies",                         "Office supplies",            "expense"),
    (r"ads|google ads|facebook|meta|marketing|advertising",     "Marketing & advertising",    "expense"),
    (r"lawyer|legal|accountant|cpa|bookkeep|audit|professional","Professional fees",          "expense"),
    (r"bank fee|service charge|nsf|monthly fee",                "Bank fees",                  "expense"),
    (r"insurance|insur",                                        "Insurance",                  "expense"),
    (r"travel|flight|hotel|airbnb|uber|taxi|meal|restaurant|food", "Travel & meals",          "expense"),
    (r"interest charge|interest payment",                       "Interest expense",           "expense"),
    (r"transfer|e-transfer|etransfer",                          "Transfer / inter-account",   "transfer"),
    (r"invoice|payment received|client|revenue|sale",           "Revenue / Sales",            "income"),
    (r"consulting",                                             "Consulting income",          "income"),
    (r"interest earned|interest credit",                        "Interest income",            "income"),
]


def ai_suggest(description: str, amount: float, acct_type: str) -> dict:
    """
    Keyword-based category suggestion.

    Returns:
        { "category": str, "tx_type": str, "confident": bool }

    To swap in a real AI model, replace the body of this function with
    an API call, e.g.:
        response = requests.post("https://api.anthropic.com/v1/messages", ...)
        return parse_ai_response(response.json())
    """
    desc_lower = description.lower()
    for pattern, category, tx_type in AI_RULES:
        if re.search(pattern, desc_lower):
            return {"category": category, "tx_type": tx_type, "confident": True}

    # Fallback: use account type + sign
    if acct_type == "asset":
        if amount >= 0:
            return {"category": "Revenue / Sales", "tx_type": "income", "confident": False}
        else:
            return {"category": "Other expense", "tx_type": "expense", "confident": False}
    else:
        if amount >= 0:
            return {"category": "Accounts payable", "tx_type": "liability", "confident": False}
        else:
            return {"category": "Other expense", "tx_type": "expense", "confident": False}


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES)


@app.route("/api/categories")
def get_categories():
    return jsonify(CATEGORIES)


@app.route("/api/parse-csv", methods=["POST"])
def parse_csv():
    """
    Parse posted CSV text and return transactions with AI suggestions.

    Expected JSON body:
        {
            "csv_text":   "date,description,amount\\n...",
            "acct_name":  "TD Business Chequing",
            "acct_type":  "asset"   # or "liability"
        }
    """
    data = request.get_json()
    csv_text = data.get("csv_text", "").strip()
    acct_name = data.get("acct_name", "Account")
    acct_type = data.get("acct_type", "asset")

    if not csv_text:
        return jsonify({"error": "No CSV data provided"}), 400

    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    if not rows:
        return jsonify({"error": "Empty CSV"}), 400

    # Skip header row if present
    if rows and re.search(r"date|description|amount", rows[0][0], re.IGNORECASE):
        rows = rows[1:]

    transactions = []
    for i, row in enumerate(rows):
        if len(row) < 3:
            continue
        date = row[0].strip()
        description = row[1].strip()
        try:
            amount = float(row[2].strip())
        except ValueError:
            continue

        suggestion = ai_suggest(description, amount, acct_type)
        transactions.append({
            "id": i,
            "date": date,
            "description": description,
            "amount": amount,
            "acct_type": acct_type,
            "account_name": acct_name,
            "category": suggestion["category"],
            "tx_type": suggestion["tx_type"],
            "ai_suggested": suggestion["confident"],
            "user_overridden": False,
        })

    return jsonify({"transactions": transactions, "count": len(transactions)})


@app.route("/api/statements", methods=["POST"])
def build_statements():
    """
    Generate income statement and balance sheet from categorized transactions.

    Expected JSON body:
        {
            "transactions": [...],
            "biz_name":     "Acme Corp.",
            "structure":    "sole",
            "period_start": "2024-01-01",
            "period_end":   "2024-12-31"
        }
    """
    data = request.get_json()
    transactions = data.get("transactions", [])
    biz_name = data.get("biz_name", "Your Business")
    structure = data.get("structure", "sole")
    period_start = data.get("period_start", "")
    period_end = data.get("period_end", "")

    # Sum amounts by category
    grouped = {}
    for tx in transactions:
        cat = tx.get("category", "Other expense")
        grouped[cat] = grouped.get(cat, 0) + tx.get("amount", 0)

    def sum_cats(cats):
        return sum(grouped.get(c, 0) for c in cats)

    # ── Income statement ──────────────────────────────────────
    total_revenue = sum_cats(CATEGORIES["income"])
    cogs = abs(grouped.get("Cost of goods sold", 0))
    gross_profit = total_revenue - cogs

    op_exp_cats = [c for c in CATEGORIES["expense"]
                   if c not in ("Cost of goods sold", "Tax expense")]
    op_expenses = sum(abs(grouped.get(c, 0)) for c in op_exp_cats)
    ebit = gross_profit - op_expenses
    tax_expense = abs(grouped.get("Tax expense", 0))
    net_income = ebit - tax_expense

    income_statement = {
        "revenue": {c: grouped[c] for c in CATEGORIES["income"] if c in grouped},
        "total_revenue": total_revenue,
        "cogs": cogs,
        "gross_profit": gross_profit,
        "operating_expenses": {c: abs(grouped[c]) for c in op_exp_cats if c in grouped},
        "total_op_expenses": op_expenses,
        "ebit": ebit,
        "tax_expense": tax_expense,
        "net_income": net_income,
    }

    # ── Balance sheet ─────────────────────────────────────────
    equity_labels = {
        "sole":        "Owner's equity",
        "partnership": "Partners' equity",
        "corp":        "Shareholders' equity",
        "llc":         "Members' equity",
    }
    equity_label = equity_labels.get(structure, "Equity")

    asset_tx_sum = sum(tx["amount"] for tx in transactions if tx.get("acct_type") == "asset")
    liab_tx_sum = abs(sum(tx["amount"] for tx in transactions if tx.get("acct_type") == "liability"))
    capital_contrib = grouped.get("Capital contributions", 0)
    distributions = abs(grouped.get("Distributions / withdrawals", 0))
    total_equity = capital_contrib + net_income - distributions

    balance_sheet = {
        "assets": {c: abs(grouped[c]) for c in CATEGORIES["asset"] if c in grouped},
        "asset_account_sum": asset_tx_sum,
        "total_assets": asset_tx_sum,
        "liabilities": {c: abs(grouped[c]) for c in CATEGORIES["liability"] if c in grouped},
        "liab_account_sum": liab_tx_sum,
        "total_liabilities": liab_tx_sum,
        "equity_label": equity_label,
        "capital_contributions": capital_contrib,
        "retained_earnings": net_income,
        "distributions": distributions,
        "total_equity": total_equity,
        "total_liab_equity": liab_tx_sum + total_equity,
    }

    return jsonify({
        "biz_name": biz_name,
        "period_start": period_start,
        "period_end": period_end,
        "income_statement": income_statement,
        "balance_sheet": balance_sheet,
    })


@app.route("/api/export-csv", methods=["POST"])
def export_csv():
    """Return categorized transactions as a downloadable CSV file."""
    data = request.get_json()
    transactions = data.get("transactions", [])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "description", "account", "account_type",
                     "amount", "category", "tx_type"])
    for tx in transactions:
        writer.writerow([
            tx.get("date", ""),
            tx.get("description", ""),
            tx.get("account_name", ""),
            tx.get("acct_type", ""),
            tx.get("amount", ""),
            tx.get("category", ""),
            tx.get("tx_type", ""),
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions_categorized.csv"},
    )


# ─── Launch ───────────────────────────────────────────────────────────────────

def open_browser():
    webbrowser.open("http://localhost:5000")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  Financial Transaction Engine")
    print("  Running at http://localhost:5000")
    print("  Press Ctrl+C to quit")
    print("=" * 50 + "\n")
    # Open browser automatically after a short delay
    Timer(1.2, open_browser).start()
    app.run(debug=False, port=5000)
