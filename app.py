
import csv
import io
import math
import os
import sqlite3
from pathlib import Path
from datetime import date
from io import BytesIO

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, make_response, send_file
)
from flask_login import (
    LoginManager, UserMixin, current_user, login_required
)
from flask_wtf.csrf import CSRFProtect
from openpyxl import Workbook


# --------------------------------------------------
# APP CONFIGURATION
# --------------------------------------------------

app = Flask(__name__)

secret_key = os.environ.get("FLASK_SECRET_KEY")
if not secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY is missing. Set it before starting the app."
    )

app.config["SECRET_KEY"] = secret_key

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "expense_tracker.db"

# auth.py uses this setting to connect to the same database.
app.config["DB_FILE"] = str(DB_FILE)

csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"


# --------------------------------------------------
# CATEGORIES
# --------------------------------------------------

INCOME_CATEGORIES = [
    "Salary",
    "Scholarship",
    "Pocket Money",
    "Freelancing",
    "Business Income",
    "Investment Returns",
    "Gifts Received",
    "Other Income",
]

EXPENSE_CATEGORIES = [
    "Food",
    "Travel",
    "Education Fees",
    "Shopping",
    "Rent / Accommodation",
    "Bills / Utilities",
    "Healthcare",
    "Entertainment",
    "Other Expenses",
]

CATEGORY_MAP = {
    "income": INCOME_CATEGORIES,
    "expense": EXPENSE_CATEGORIES,
}


# --------------------------------------------------
# USER MODEL
# --------------------------------------------------

class User(UserMixin):
    def __init__(self, user_id, username, email):
        self.id = str(user_id)
        self.username = username
        self.email = email


@login_manager.user_loader
def load_user(user_id):
    """Load the logged-in user from the database."""
    try:
        with get_connection() as conn:
            user = conn.execute(
                """
                SELECT id, username, email
                FROM users
                WHERE id = ?
                """,
                (int(user_id),),
            ).fetchone()
    except (ValueError, TypeError):
        return None

    if user is None:
        return None

    return User(user["id"], user["username"], user["email"])


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the tables needed by the application."""
    with get_connection() as conn:

        # Create users first because other tables reference users.id.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS budgets (
                user_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                amount REAL NOT NULL,
                PRIMARY KEY (user_id, month),
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )


# --------------------------------------------------
# TRANSACTION AND BUDGET HELPERS
# --------------------------------------------------

def load_transactions(user_id):
    """Load only the transactions belonging to this user."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, type, title, amount, category, date
            FROM transactions
            WHERE user_id = ?
            ORDER BY id
            """,
            (user_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def load_budgets(user_id):
    """Load only this user's monthly budgets."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT month, amount
            FROM budgets
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchall()

    return {
        row["month"]: row["amount"]
        for row in rows
    }


def save_budget(user_id, month, amount):
    """Create or update one monthly budget for this user."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO budgets (user_id, month, amount)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, month)
            DO UPDATE SET amount = excluded.amount
            """,
            (user_id, month, amount),
        )


def find_transaction_by_position(user_id, position):
    """
    Find a transaction using its position in this user's list.

    This supports templates that use loop.index0 in their
    edit/delete URLs.
    """
    transactions = load_transactions(user_id)

    if 0 <= position < len(transactions):
        return transactions[position]

    return None


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/")
@login_required
def index():
    user_id = int(current_user.get_id())
    transactions = load_transactions(user_id)

    total_income = sum(
        float(t["amount"])
        for t in transactions
        if t["type"] == "income"
    )

    total_expenses = sum(
        float(t["amount"])
        for t in transactions
        if t["type"] == "expense"
    )

    balance = total_income - total_expenses

    # Current month's budget
    today = date.today()
    current_month = today.strftime("%Y-%m")

    budgets = load_budgets(user_id)
    monthly_budget = float(budgets.get(current_month, 0) or 0)

    current_month_expenses = sum(
        float(t["amount"])
        for t in transactions
        if t["type"] == "expense"
        and str(t["date"]).startswith(current_month)
    )

    budget_remaining = monthly_budget - current_month_expenses

    budget_percentage = (
        round(
            (current_month_expenses / monthly_budget) * 100,
            1,
        )
        if monthly_budget > 0
        else 0
    )

    budget_exceeded = (
        monthly_budget > 0
        and current_month_expenses > monthly_budget
    )

    # Expense chart: totals grouped by category
    expense_by_category = {}

    for transaction in transactions:
        if transaction["type"] == "expense":
            category = transaction["category"]
            amount = float(transaction["amount"])

            expense_by_category[category] = (
                expense_by_category.get(category, 0) + amount
            )

    expense_chart_labels = list(expense_by_category.keys())
    expense_chart_values = list(expense_by_category.values())

    # Monthly income and expense report
    monthly_data = {}

    for transaction in transactions:
        transaction_date = str(transaction.get("date", ""))

        try:
            if (
                len(transaction_date) < 10
                or transaction_date[4] != "-"
                or transaction_date[7] != "-"
            ):
                continue

            year = int(transaction_date[0:4])
            month_number = int(transaction_date[5:7])

            if not 1 <= month_number <= 12:
                continue

            month = f"{year:04d}-{month_number:02d}"

        except (ValueError, TypeError, IndexError):
            continue

        amount = float(transaction["amount"])
        transaction_type = transaction["type"]

        if month not in monthly_data:
            monthly_data[month] = {
                "income": 0,
                "expenses": 0,
            }

        if transaction_type == "income":
            monthly_data[month]["income"] += amount

        elif transaction_type == "expense":
            monthly_data[month]["expenses"] += amount

    # Show the current month and previous five months.
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
            monthly_data[month] = {
                "income": 0,
                "expenses": 0,
            }

    monthly_expense_values = [
        round(monthly_data[month]["expenses"], 2)
        for month in monthly_labels
    ]

    return render_template(
        "index.html",
        transactions=transactions,
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        income_categories=INCOME_CATEGORIES,
        expense_categories=EXPENSE_CATEGORIES,
        expense_chart_labels=expense_chart_labels,
        expense_chart_values=expense_chart_values,
        monthly_data=monthly_data,
        monthly_labels=monthly_labels,
        monthly_expense_values=monthly_expense_values,
        current_month=current_month,
        monthly_budget=monthly_budget,
        current_month_expenses=current_month_expenses,
        budget_remaining=budget_remaining,
        budget_percentage=budget_percentage,
        budget_exceeded=budget_exceeded,
    )


# --------------------------------------------------
# SET MONTHLY BUDGET
# --------------------------------------------------

@app.route("/set-budget", methods=["POST"])
@login_required
def set_budget():
    user_id = int(current_user.get_id())
    current_month = date.today().strftime("%Y-%m")

    raw_budget = request.form.get("monthly_budget", "").strip()

    try:
        amount = round(float(raw_budget), 2)
    except (ValueError, TypeError):
        flash("Please enter a valid monthly budget amount.")
        return redirect(url_for("index"))

    if not math.isfinite(amount) or amount <= 0:
        flash("Budget must be a valid amount greater than zero.")
        return redirect(url_for("index"))

    save_budget(user_id, current_month, amount)

    flash(
        f"Monthly budget set to ₹{amount:,.2f} "
        f"for {current_month}."
    )

    return redirect(url_for("index"))


# --------------------------------------------------
# ADD TRANSACTION
# --------------------------------------------------

@app.route("/add", methods=["POST"])
@login_required
def add_transaction():
    user_id = int(current_user.get_id())

    transaction_type = (
        request.form.get("type", "").strip().lower()
    )
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()

    try:
        amount = round(
            float(request.form.get("amount", "")),
            2,
        )
    except (ValueError, TypeError):
        flash("Please enter a valid amount.")
        return redirect(url_for("index"))

    if transaction_type not in CATEGORY_MAP:
        flash("Please select a valid transaction type.")

    elif not title:
        flash("Description cannot be empty.")

    elif not math.isfinite(amount) or amount <= 0:
        flash("Amount must be a valid number greater than zero.")

    elif category not in CATEGORY_MAP[transaction_type]:
        flash("Please select a valid category for this transaction.")

    else:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO transactions
                    (user_id, type, title, amount, category, date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    transaction_type,
                    title,
                    amount,
                    category,
                    date.today().isoformat(),
                ),
            )

        flash("Transaction added successfully!")

    return redirect(url_for("index"))


# --------------------------------------------------
# DELETE TRANSACTION
# --------------------------------------------------

@app.route("/delete/<int:transaction_id>", methods=["POST"])
@login_required
def delete_transaction(transaction_id):
    user_id = int(current_user.get_id())

    # The parameter is treated as the list position to keep
    # compatibility with templates that use loop.index0.
    transaction = find_transaction_by_position(
        user_id,
        transaction_id,
    )

    if transaction:
        with get_connection() as conn:
            conn.execute(
                """
                DELETE FROM transactions
                WHERE id = ? AND user_id = ?
                """,
                (transaction["id"], user_id),
            )

        flash(
            f"Deleted '{transaction['title']}' successfully!"
        )
    else:
        flash("Transaction not found.")

    return redirect(url_for("index"))


# --------------------------------------------------
# EDIT TRANSACTION
# --------------------------------------------------

@app.route("/edit/<int:transaction_id>", methods=["POST"])
@login_required
def edit_transaction(transaction_id):
    user_id = int(current_user.get_id())

    transaction = find_transaction_by_position(
        user_id,
        transaction_id,
    )

    if not transaction:
        flash("Transaction not found.")
        return redirect(url_for("index"))

    transaction_type = (
        request.form.get("type", "").strip().lower()
    )
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()

    try:
        amount = round(
            float(request.form.get("amount", "")),
            2,
        )
    except (ValueError, TypeError):
        flash("Please enter a valid amount.")
        return redirect(url_for("index"))

    if transaction_type not in CATEGORY_MAP:
        flash("Invalid transaction type.")

    elif not title:
        flash("Description cannot be empty.")

    elif not math.isfinite(amount) or amount <= 0:
        flash("Amount must be a valid number greater than zero.")

    elif category not in CATEGORY_MAP[transaction_type]:
        flash("Invalid category for the selected transaction type.")

    else:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE transactions
                SET type = ?, title = ?, amount = ?, category = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    transaction_type,
                    title,
                    amount,
                    category,
                    transaction["id"],
                    user_id,
                ),
            )

        flash("Transaction updated successfully!")

    return redirect(url_for("index"))


# --------------------------------------------------
# EXPORT TO CSV
# --------------------------------------------------

@app.route("/export/csv")
@login_required
def export_csv():
    user_id = int(current_user.get_id())
    transactions = load_transactions(user_id)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Date",
        "Description",
        "Category",
        "Type",
        "Amount",
    ])

    for transaction in transactions:
        writer.writerow([
            transaction["date"],
            transaction["title"],
            transaction["category"],
            transaction["type"],
            transaction["amount"],
        ])

    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        "attachment; filename=transactions.csv"
    )

    return response


# --------------------------------------------------
# EXPORT TO EXCEL
# --------------------------------------------------

@app.route("/export/excel")
@login_required
def export_excel():
    user_id = int(current_user.get_id())
    transactions = load_transactions(user_id)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Transactions"

    sheet.append([
        "ID",
        "Date",
        "Type",
        "Description",
        "Category",
        "Amount",
    ])

    for transaction in transactions:
        sheet.append([
            transaction["id"],
            transaction["date"],
            transaction["type"],
            transaction["title"],
            transaction["category"],
            transaction["amount"],
        ])

    # Adjust column widths for readability.
    for column in sheet.columns:
        max_length = max(
            len(str(cell.value or ""))
            for cell in column
        )

        sheet.column_dimensions[
            column[0].column_letter
        ].width = min(max_length + 2, 30)

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="transactions.xlsx",
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )


# --------------------------------------------------
# INITIALIZE DATABASE AND REGISTER AUTHENTICATION
# --------------------------------------------------

init_db()

# auth.py must not contain "from app import ...".
# It should use current_app.config["DB_FILE"] instead.
from auth import auth

app.register_blueprint(auth)


if __name__ == "__main__":
    app.run(debug=True)
