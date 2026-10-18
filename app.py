import csv
import io
import json
import sqlite3
import math
import os
from pathlib import Path
from datetime import date
from io import BytesIO
from flask_wtf.csrf import CSRFProtect


from flask import Flask, render_template, request, redirect, url_for, flash, make_response, send_file
from openpyxl import Workbook

app = Flask(__name__)
app.secret_key = "expense-tracker-local-key"
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY",
    "dev-only-change-this-key"
)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")

csrf = CSRFProtect(app)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "transactions.json"
BUDGET_FILE = BASE_DIR / "budgets.json"
DB_FILE = BASE_DIR / "expense_tracker.db"

INCOME_CATEGORIES = [
    "Salary", "Scholarship", "Pocket Money", "Freelancing",
    "Business Income", "Investment Returns", "Gifts Received", "Other Income"
]
EXPENSE_CATEGORIES = [
    "Food", "Travel", "Education Fees", "Shopping",
    "Rent / Accommodation", "Bills / Utilities", "Healthcare",
    "Entertainment", "Other Expenses"
]
CATEGORY_MAP = {"income": INCOME_CATEGORIES, "expense": EXPENSE_CATEGORIES}


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and import existing JSON data once, without deleting the backups."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                month TEXT PRIMARY KEY,
                amount REAL NOT NULL
            )
        """)

        # Import transactions only when the database table is empty.
        count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        if count == 0 and DATA_FILE.exists():
            try:
                with DATA_FILE.open("r", encoding="utf-8") as file:
                    data = json.load(file)
                if isinstance(data, list):
                    for item in data:
                        if not isinstance(item, dict):
                            continue
                        t_type = str(item.get("type", "")).lower()
                        title = str(item.get("title", item.get("description", ""))).strip()
                        try:
                            amount = round(float(item.get("amount", 0)), 2)
                        except (TypeError, ValueError):
                            continue
                        category = str(item.get("category", ""))
                        trans_date = str(item.get("date", date.today().isoformat()))
                        if t_type in CATEGORY_MAP and title and amount > 0 and category in CATEGORY_MAP[t_type]:
                            conn.execute(
                                "INSERT INTO transactions (type, title, amount, category, date) VALUES (?, ?, ?, ?, ?)",
                                (t_type, title, amount, category, trans_date)
                            )
            except (json.JSONDecodeError, OSError):
                app.logger.exception("Could not import transactions.json")

        # Import budgets only when the database budget table is empty.
        budget_count = conn.execute("SELECT COUNT(*) FROM budgets").fetchone()[0]
        if budget_count == 0 and BUDGET_FILE.exists():
            try:
                with BUDGET_FILE.open("r", encoding="utf-8") as file:
                    budgets = json.load(file)
                if isinstance(budgets, dict):
                    for month, amount in budgets.items():
                        try:
                            amount = float(amount)
                        except (TypeError, ValueError):
                            continue
                        if len(str(month)) == 7 and amount > 0:
                            conn.execute(
                                "INSERT OR REPLACE INTO budgets (month, amount) VALUES (?, ?)",
                                (str(month), amount)
                            )
            except (json.JSONDecodeError, OSError):
                app.logger.exception("Could not import budgets.json")


def load_transactions():
    """Return transactions in the same list order used by the original template."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, type, title, amount, category, date FROM transactions ORDER BY id"
        ).fetchall()
    # Keep a database ID privately for routes, while exposing the original fields to the template.
    return [dict(row) for row in rows]


def load_budgets():
    with get_connection() as conn:
        rows = conn.execute("SELECT month, amount FROM budgets").fetchall()
    return {row["month"]: row["amount"] for row in rows}


def save_budget(month, amount):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO budgets (month, amount) VALUES (?, ?) "
            "ON CONFLICT(month) DO UPDATE SET amount=excluded.amount",
            (month, amount)
        )


def find_transaction_by_position(position):
    transactions = load_transactions()
    if 0 <= position < len(transactions):
        return transactions[position]
    return None


def index_for_template(transaction):
    """Not used by routes; included for clarity on database IDs."""
    return transaction.get("id")


@app.route("/")
def index():
    transactions = load_transactions()
    total_income = sum(float(t.get("amount", 0)) for t in transactions if t.get("type") == "income")
    total_expenses = sum(float(t.get("amount", 0)) for t in transactions if t.get("type") == "expense")
    balance = total_income - total_expenses

    today = date.today()
    current_month = today.strftime("%Y-%m")
    budgets = load_budgets()
    monthly_budget = float(budgets.get(current_month, 0) or 0)
    current_month_expenses = sum(
        float(t.get("amount", 0)) for t in transactions
        if t.get("type") == "expense" and str(t.get("date", "")).startswith(current_month)
    )
    budget_remaining = monthly_budget - current_month_expenses
    budget_percentage = round((current_month_expenses / monthly_budget) * 100, 1) if monthly_budget > 0 else 0
    budget_exceeded = monthly_budget > 0 and current_month_expenses > monthly_budget

    expense_by_category = {}
    for transaction in transactions:
        if transaction.get("type") == "expense":
            category = transaction.get("category", "Other Expenses")
            expense_by_category[category] = expense_by_category.get(category, 0) + float(transaction.get("amount", 0))
    expense_chart_labels = list(expense_by_category.keys())
    expense_chart_values = list(expense_by_category.values())

    monthly_data = {}
    for transaction in transactions:
        transaction_date = str(transaction.get("date", ""))
        try:
            if len(transaction_date) < 10 or transaction_date[4] != "-" or transaction_date[7] != "-":
                continue
            year = int(transaction_date[0:4])
            month_number = int(transaction_date[5:7])
            if not 1 <= month_number <= 12:
                continue
            month = f"{year:04d}-{month_number:02d}"
        except (ValueError, TypeError, IndexError):
            continue

        amount = float(transaction.get("amount", 0))
        transaction_type = transaction.get("type")
        if month not in monthly_data:
            monthly_data[month] = {"income": 0, "expenses": 0}
        if transaction_type == "income":
            monthly_data[month]["income"] += amount
        elif transaction_type == "expense":
            monthly_data[month]["expenses"] += amount

    monthly_labels = []
    for offset in range(5, -1, -1):
        year = today.year
        month_number = today.month - offset
        while month_number <= 0:
            month_number += 12
            year -= 1
        month = f"{year:04d}-{month_number:02d}"
        monthly_labels.append(month)
        if month not in monthly_data:
            monthly_data[month] = {"income": 0, "expenses": 0}

    monthly_expense_values = [round(monthly_data[month]["expenses"], 2) for month in monthly_labels]

    return render_template(
        "index.html", transactions=transactions, total_income=total_income,
        total_expenses=total_expenses, balance=balance,
        income_categories=INCOME_CATEGORIES, expense_categories=EXPENSE_CATEGORIES,
        expense_chart_labels=expense_chart_labels, expense_chart_values=expense_chart_values,
        monthly_data=monthly_data, monthly_labels=monthly_labels,
        monthly_expense_values=monthly_expense_values, current_month=current_month,
        monthly_budget=monthly_budget, current_month_expenses=current_month_expenses,
        budget_remaining=budget_remaining, budget_percentage=budget_percentage,
        budget_exceeded=budget_exceeded
    )



@app.route("/set-budget", methods=["POST"])

def set_budget():
    current_month = date.today().strftime("%Y-%m")
    raw_budget = request.form.get("monthly_budget", "").strip()

    try:
        amount = round(float(raw_budget), 2)
    except (ValueError, TypeError):
        flash("Please enter a valid monthly budget amount.")
        return redirect(url_for("index"))

    if not math.isfinite(amount):
        flash("Budget must be a valid finite number.")
        return redirect(url_for("index"))

    if amount <= 0:
        flash("Monthly budget must be greater than zero.")
        return redirect(url_for("index"))

    save_budget(current_month, amount)
    flash(f"Monthly budget set to ₹{amount:,.2f} for {current_month}.")
    return redirect(url_for("index"))



import math

@app.route("/add", methods=["POST"])
def add_transaction():
    transaction_type = request.form.get("type", "").strip().lower()
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()

    try:
        amount = round(float(request.form.get("amount", "")), 2)
    except (ValueError, TypeError):
        flash("Please enter a valid amount.")
        return redirect(url_for("index"))

    if transaction_type not in CATEGORY_MAP:
        flash("Please select a valid transaction type.")
    elif not title:
        flash("Description cannot be empty.")
    elif not math.isfinite(amount):
        flash("Amount must be a valid finite number.")
    elif amount <= 0:
        flash("Amount must be greater than zero.")
    elif category not in CATEGORY_MAP[transaction_type]:
        flash("Please select a valid category for this transaction.")
    else:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO transactions
                   (type, title, amount, category, date)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    transaction_type,
                    title,
                    amount,
                    category,
                    date.today().isoformat()
                )
            )
        flash("Transaction added successfully!")

    return redirect(url_for("index"))



@app.route("/delete/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):
    # Original template uses zero-based list positions, so map that position to the database row.
    transaction = find_transaction_by_position(transaction_id)
    if transaction:
        with get_connection() as conn:
            conn.execute("DELETE FROM transactions WHERE id = ?", (transaction["id"],))
        flash(f"Deleted '{transaction.get('title', 'Transaction')}' successfully!")
    else:
        flash("Transaction not found.")
    return redirect(url_for("index"))



@app.route("/edit/<int:transaction_id>", methods=["POST"])
def edit_transaction(transaction_id):
    transaction = find_transaction_by_position(transaction_id)

    if not transaction:
        flash("Transaction not found.")
        return redirect(url_for("index"))

    transaction_type = request.form.get("type", "").strip().lower()
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()

    try:
        amount = round(float(request.form.get("amount", "")), 2)
    except (ValueError, TypeError):
        flash("Invalid amount.")
        return redirect(url_for("index"))

    if transaction_type not in CATEGORY_MAP:
        flash("Invalid transaction type.")
    elif not title:
        flash("Description cannot be empty.")
    elif not math.isfinite(amount):
        flash("Amount must be a valid finite number.")
    elif amount <= 0:
        flash("Amount must be greater than zero.")
    elif category not in CATEGORY_MAP[transaction_type]:
        flash("Invalid category.")
    else:
        with get_connection() as conn:
            conn.execute(
                """UPDATE transactions
                   SET type=?, title=?, amount=?, category=?
                   WHERE id=?""",
                (
                    transaction_type,
                    title,
                    amount,
                    category,
                    transaction["id"]
                )
            )

        flash("Transaction updated successfully!")

    return redirect(url_for("index"))

@app.route("/export/csv")
def export_csv():
    transactions = load_transactions()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Description", "Category", "Type", "Amount"])
    for transaction in transactions:
        writer.writerow([
            transaction.get("date", ""), transaction.get("title", ""),
            transaction.get("category", ""), transaction.get("type", ""),
            transaction.get("amount", 0)
        ])
    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=transactions.csv"
    return response


@app.route("/export/excel")
def export_excel():
    transactions = load_transactions()
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Transactions"
    sheet.append(["ID", "Date", "Type", "Description", "Category", "Amount"])
    for transaction in transactions:
        sheet.append([
            transaction.get("id", ""), transaction.get("date", ""),
            transaction.get("type", ""), transaction.get("title", transaction.get("description", "")),
            transaction.get("category", ""), transaction.get("amount", 0)
        ])
    for column in sheet.columns:
        max_length = max(len(str(cell.value or "")) for cell in column)
        sheet.column_dimensions[column[0].column_letter].width = min(max_length + 2, 30)
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return send_file(
        output, as_attachment=True, download_name="transactions.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# Create tables and import JSON data before Flask starts accepting requests.
init_db()

if __name__ == "__main__":
    app.run(debug=True)
