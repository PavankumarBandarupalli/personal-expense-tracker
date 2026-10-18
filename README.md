# 💰 Personal Expense Tracker

A web-based expense tracker built with Python and Flask to manage income, expenses, and monthly budgets.

## ✨ Features

- 📊 Dashboard showing total income, expenses, and balance
- 💵 Add income and expense transactions
- ✏️ Edit and delete transactions
- 🔍 Search and filter transaction history
- 📅 Monthly reports and charts
- 🎯 Set and manage monthly budgets
- 📥 Export transactions to CSV and Excel
- 🗄️ SQLite database for persistent storage
- 🔐 CSRF protection for forms

## 🛠️ Technologies Used

- Python
- Flask
- Flask-WTF
- SQLite
- HTML
- CSS
- JavaScript
- OpenPyXL (Excel export, if used)

## 🚀 How to Run

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd personal-expense-tracker
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual repository URL.

### 2. Install dependencies

```bash
py -m pip install -r requirements.txt
```

### 3. Configure the secret key

In Windows PowerShell:

```powershell
$env:FLASK_SECRET_KEY = py -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Start the application

```powershell
py app.py
```

Open `http://127.0.0.1:5000/` in your browser.

## 📁 Project Structure
personal-expense-tracker/
├── .gitignore
├── README.md
├── requirements.txt
├── app.py
├── Expense_tracker.db
├── transactions.json
├── budgets.json
├── P-E-T/
│   └── main.py
├── templates/
│   └── index.html
└── static/
    └── style.css

The SQLite database is created locally when the application initializes.


## 🎯 Project Goal

This project demonstrates Python programming, Flask web development, database operations, form validation, and basic data visualization.