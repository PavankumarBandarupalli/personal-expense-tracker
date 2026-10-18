from datetime import date, datetime
import json
import os
from datetime import date

FILE_NAME = "transactions.json"


INCOME_CATEGORIES = [
    "Salary",
    "Scholarship",
    "Pocket Money",
    "Freelancing",
    "Business Income",
    "Investment Returns",
    "Gifts Received",
    "Other Income"
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
    "Other Expenses"
]


def load_transactions():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r") as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                print("Invalid transaction data.")
                return []
        except (json.JSONDecodeError, OSError):
            print("Could not read the data file.")
            return []

    return []


def save_transactions():
    with open(FILE_NAME, "w") as file:
        json.dump(transactions, file, indent=4)


transactions = load_transactions()



def choose_category(transaction_type):
    if transaction_type == "income":
        categories = INCOME_CATEGORIES
    else:
        categories = EXPENSE_CATEGORIES

    print("\nChoose category:")

    for i, category in enumerate(categories, start=1):
        print(f"{i}. {category}")

    try:
        choice = int(input("Enter category number: "))
    except ValueError:
        print("Enter a valid number.")
        return None

    if 1 <= choice <= len(categories):
        return categories[choice - 1]

    print("Invalid category!")
    return None


def add_transaction():
    print("\n1. Income")
    print("2. Expense")

    choice = input("Select transaction type: ")

    if choice == "1":
        transaction_type = "income"
    elif choice == "2":
        transaction_type = "expense"
    else:
        print("Invalid transaction type!")
        return

    title = input("Enter description: ").strip()

    if not title:
        print("Description cannot be empty.")
        return

    try:
        amount = float(input("Enter amount: "))
    except ValueError:
        print("Please enter a valid number.")
        return

    if amount <= 0:
        print("Amount must be greater than zero.")
        return

    category = choose_category(transaction_type)

    if category is None:
        return

    transaction = {
        "type": transaction_type,
        "title": title,
        "amount": round(amount, 2),
        "category": category,
        "date": date.today().isoformat()
    }

    transactions.append(transaction)
    save_transactions()

    print("Transaction saved successfully!")


def view_transactions():
    if not transactions:
        print("No transactions yet.")
        return

    print("\n--- TRANSACTION HISTORY ---")

    for i, transaction in enumerate(transactions, start=1):
        print(
            f"{i}. {transaction.get('date', 'Date unavailable')} | "
            f"{transaction['type'].title()} | "
            f"{transaction['title']} | "
            f"Rs. {transaction['amount']:.2f} | "
            f"{transaction['category']}"
        )


def show_summary():
    total_income = sum(
        t["amount"] for t in transactions
        if t["type"] == "income"
    )

    total_expenses = sum(
        t["amount"] for t in transactions
        if t["type"] == "expense"
    )

    print("\n--- FINANCIAL SUMMARY ---")
    print(f"Total income: Rs. {total_income:.2f}")
    print(f"Total expenses: Rs. {total_expenses:.2f}")
    print(f"Balance: Rs. {total_income - total_expenses:.2f}")


def delete_transaction():
    view_transactions()

    if not transactions:
        return

    try:
        number = int(input("Enter transaction number to delete: "))
    except ValueError:
        print("Enter a valid number.")
        return

    if 1 <= number <= len(transactions):
        removed = transactions.pop(number - 1)
        save_transactions()
        print(f"Deleted: {removed['title']}")
    else:
        print("Invalid transaction number!")


def edit_transaction():
    view_transactions()

    if not transactions:
        return

    try:
        number = int(input("Enter transaction number to edit: "))
    except ValueError:
        print("Enter a valid number.")
        return

    if not 1 <= number <= len(transactions):
        print("Invalid transaction number!")
        return

    transaction = transactions[number - 1]

    print("Press Enter to keep the existing value.")

    new_title = input(
        f"Description [{transaction['title']}]: "
    ).strip()

    if new_title:
        transaction["title"] = new_title

    new_amount = input(
        f"Amount [{transaction['amount']}]: "
    ).strip()

    if new_amount:
        try:
            amount = float(new_amount)

            if amount <= 0:
                print("Amount must be greater than zero.")
                return

            transaction["amount"] = round(amount, 2)

        except ValueError:
            print("Invalid amount!")
            return

    change = input("Change category? (y/n): ").lower()

    if change == "y":
        category = choose_category()

        if category is None:
            return

        transaction["category"] = category

    save_transactions()
    print("Transaction updated successfully!")


def filter_by_date():
    selected_date = input(
        "Enter date (YYYY-MM-DD): "
    ).strip()

    try:
        datetime.strptime(selected_date, "%Y-%m-%d")
    except ValueError:
        print("Invalid date! Use YYYY-MM-DD.")
        return

    found = False

    print(f"\n--- TRANSACTIONS ON {selected_date} ---")

    for transaction in transactions:
        if transaction.get("date") == selected_date:
            print(
                transaction["type"].title(),
                "|", transaction["title"],
                "| Rs.", transaction["amount"],
                "|", transaction["category"]
            )
            found = True

    if not found:
        print("No transactions found for this date.")





while True:
    print("\n--- PERSONAL EXPENSE TRACKER ---")
    print("1. Add income or expense")
    print("2. View transactions")
    print("3. Show summary")
    print("4. Delete transaction")
    print("5. Edit transaction")
    print("6. Filter by date")
    print("7. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":
        add_transaction()
    elif choice == "2":
        view_transactions()
    elif choice == "3":
        show_summary()
    elif choice == "4":
        delete_transaction()
    elif choice == "5":
        edit_transaction()
    elif choice == "6":
        filter_by_date()
    elif choice == "7":
        print("Thank you!")
        break
    else:
        print("Invalid choice!")

#Edit a transaction's description successfully.
# [ ] Edit an amount and verify the updated total.
# [ ] Change a category successfully.
# [ ] Filter transactions using a date (YYYY-MM-DD).
# [ ] Restart the program and confirm edits remain saved in transactions.json.