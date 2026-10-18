# 💰 Personal Expense Tracker

**A Flask-based web application to manage income, track expenses, monitor monthly budgets, and understand spending habits through reports and visualizations.**

Organize your finances with a simple dashboard, transaction management, category-based tracking, and monthly summaries.

## 📌 Table of Contents

- [Overview]
- [Features]
- [Screenshots]
- [Technology Stack]
- [Project Structure]
- [Getting Started]
- [How to Use]
- [Database and Data Storage]
- [Security]
- [Future Improvements]
- [What I Learned]


## 🌟 Overview

The Personal Expense Tracker is a web application built with Python and Flask that helps users record income and expenses in one place.

Users can organize transactions into categories, monitor their financial balance, review transaction history, set monthly budgets, and export transaction records.

The project was developed to practice Python programming, backend web development, database integration, form validation, and frontend design.

## ✨ Features

### 📊 Financial Dashboard
- View total income and expenses.
- Track the remaining balance.
- Get an overview of recorded transactions.

### 💵 Income and Expense Management
- Add income and expense transactions.
- Edit existing transactions.
- Delete transactions when needed.
- Organize transactions using separate income and expense categories.

### 🔎 Transaction History
- View recorded transactions.
- Search and filter transactions using the available options.
- Review transaction details.

### 📅 Reports and Visualizations
- View monthly financial reports.
- Visualize financial information using charts.
- Understand income and spending patterns.

### 🎯 Monthly Budget Management
- Set monthly budgets.
- Review budget information.
- Monitor spending against your planned budget.

### 📥 Data Export
- Export transaction records to CSV.
- Export transaction records to Excel.

### 🗄️ Database
- Store transactions and budgets using SQLite.
- Preserve data locally between application restarts.

### 🔐 Form Security
- CSRF protection using Flask-WTF.
- Input validation for transaction and budget forms.

##  Screenshots

Screenshots help visitors understand the application before installing it.



### Dashboard
![alt text](DASHBOARD.png)

### Add Income and Expense
![alt text](<income transaction.png>)
![alt text](<Expense transaction.png>)

### Transaction History
![alt text](<Transaction history.png>)

### Monthly Reports
![alt text](<Monthly report.png>)
### Monthly Budget Management
![alt text](<monthly budget management.png>)

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic and backend programming |
| Flask | Web application framework |
| SQLite | Local database |
| Flask-WTF | CSRF protection |
| HTML5 | Web page structure |
| CSS3 | Styling and responsive layout |
| JavaScript | Interactive frontend behavior |
| OpenPyXL | Excel export, if used by the application |

## 📁 Project Structure

```text
personal-expense-tracker/
├── app.py
├── main.py                 
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   └── index.html
├── static/
│   └── style.css
|──Screenshots\
    |-Dashboard.png
    |-Expense transaction.png
    |-Income transaction.png
    |-Monthly budget transaction.png
    |-Monthly report.png
    |-Transaction history.png    
The SQLite database and local transaction data are created or maintained separately and should not be committed to the public repository.

## 🚀 Getting Started

Follow these steps to run the project on your computer.

### Prerequisites

- Python installed on your computer.
- Git installed if you want to clone the repository.
- A terminal such as PowerShell or the VS Code terminal.

### 1. Clone the repository

```bash
git clone https://github.com/pavankumarBandarupalli/personal-expense-tracker.git
cd personal-expense-tracker
```

###  Install dependencies

```powershell
py -m pip install -r requirements.txt
```

###  Configure the secret key

In Windows PowerShell, generate a secret key for the current session:

```powershell
$env:FLASK_SECRET_KEY = py -c "import secrets; print(secrets.token_hex(32))"
```

Keep secret keys out of source code and never commit them to GitHub.

###  Run the application

```powershell
py app.py
```

###  Open the application

Visit the following address in your browser:

http://127.0.0.1:5000/

The application should now be available on your local computer.

## 📖 How to Use

1. Start the Flask application.
2. Open the dashboard in your browser.
3. Add an income or expense transaction.
4. Select the appropriate category and enter the amount.
5. View your updated financial summary.
6. Search or filter transaction history using the available controls.
7. Edit or delete transactions when required.
8. Set a monthly budget and review monthly reports.
9. Export your transaction records when needed.

## 🗄️ Database and Data Storage

This application uses SQLite for local data storage.

- Transaction records are stored in the database.
- Budget information is stored using the application's database implementation.
- Data is intended to persist between local application restarts.

The database file is local application data and is not required in the public source repository. Each user should initialize their own local database.

## 🔐 Security and Privacy

- CSRF protection is implemented using Flask-WTF.
- Input validation is used for transaction and budget operations.
- Secret keys should be configured through environment variables.
- Local databases and personal transaction files should be excluded from Git tracking.

**Privacy notice:** Do not enter sensitive real-world financial information into an untrusted or publicly deployed instance.

## 🚧 Future Improvements

Potential improvements for future versions include:

- User registration and authentication.
- Separate financial data for each user.
- Persistent cloud database storage.
- Deploying the application online.
- Improved mobile-friendly dashboard design.
- Additional charts and financial insights.
- Automated tests for important application features.

These are planned improvements, not necessarily features available in the current version.

## 🎓 What I Learned

Building this project helped me practice:

- Python functions and application logic.
- Flask routes and HTTP methods.
- HTML, CSS, and JavaScript integration.
- CRUD operations: Create, Read, Update, and Delete.
- SQLite database integration.
- Form validation and CSRF protection.
- File exports and data handling.
- Git and GitHub version control.

---

If you find this project useful, feel free to explore the code, try it locally, or suggest improvements.

**Built as a learning project using Python, Flask, and SQLite.**