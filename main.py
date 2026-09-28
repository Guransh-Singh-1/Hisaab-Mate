import os
import sys
import sqlite3
from datetime import date

if getattr(sys, "frozen", False):
    APP_DATA = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "TransactionTracker")
else:
    APP_DATA = os.path.dirname(os.path.abspath(__file__))

os.makedirs(APP_DATA, exist_ok=True)
DB_FILE = os.path.join(APP_DATA, "transactions.db")

current_user_id = None
current_username = ""

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

def get_user(username):
    with get_db() as conn:
        return conn.execute("SELECT id, username FROM users WHERE LOWER(username) = LOWER(?)", (username,)).fetchone()

def create_user(username):
    try:
        with get_db() as conn:
            cursor = conn.execute("INSERT INTO users (username) VALUES (?)", (username,))
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

def get_transactions():
    if current_user_id is None:
        return []

    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, name, category, type, amount, date
            FROM transactions
            WHERE user_id = ?
            ORDER BY id
        """, (current_user_id,)).fetchall()
        return [dict(row) for row in rows]

def add_transaction_to_db(name, category, trans_type, amount, trans_date):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO transactions (user_id, name, category, type, amount, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (current_user_id, name, category, trans_type, amount, trans_date))

def update_transaction_in_db(transaction_id, name, category, trans_type, amount, trans_date):
    with get_db() as conn:
        conn.execute("""
            UPDATE transactions
            SET name = ?, category = ?, type = ?, amount = ?, date = ?
            WHERE id = ? AND user_id = ?
        """, (name, category, trans_type, amount, trans_date, transaction_id, current_user_id))

def delete_transaction_from_db(transaction_id):
    with get_db() as conn:
        conn.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (transaction_id, current_user_id))

def add_transaction(kind):
    print(f"\n--- ADD {kind.upper()} ---")
    name = input(f"Enter {kind} name: ").strip()
    category = input("Enter category: ").strip()

    if not name or not category:
        print("\033[31mName and category cannot be empty.\033[0m")
        return

    try:
        amount = float(input("Enter amount: "))
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("\033[31mPlease enter a valid amount greater than 0.\033[0m")
        return

    trans_date = input("Enter date [yyyy-mm-dd] (press Enter for today): ").strip()
    if not trans_date:
        trans_date = str(date.today())
    else:
        try:
            date.fromisoformat(trans_date)
        except ValueError:
            print("\033[31mInvalid date format. Using today's date.\033[0m")
            trans_date = str(date.today())

    add_transaction_to_db(name, category, kind, amount, trans_date)
    print(f"\033[32m{kind.capitalize()} added successfully to database.\033[0m")

def view_transactions(items=None, title="ALL TRANSACTIONS"):
    transactions = get_transactions() if items is None else items
    if not transactions:
        print("\nNo transactions found.")
        return

    print(f"\n--- {title} ---")
    for index, t in enumerate(transactions, start=1):
        print(f"{index}. {t['name']} | {t['category']} | {t['type']} | Rs. {t['amount']:.2f} | {t['date']}")

def view_by_type():
    transactions = get_transactions()
    if not transactions:
        print("\nNo transactions found.")
        return

    while True:
        trans_type = input("Enter transaction type to check (income or expense): ").strip().lower()
        if trans_type in ("income", "expense"):
            break
        print("\033[31mInvalid type. Please enter either 'income' or 'expense'.\033[0m")

    filtered = [t for t in transactions if t["type"] == trans_type]
    view_transactions(filtered, f"{trans_type.upper()} TRANSACTIONS")

def view_monthly():
    transactions = get_transactions()
    if not transactions:
        print("\nNo transactions found.")
        return

    print("========== MONTHLY FILTER ==========")
    while True:
        year = input("\nEnter year (YYYY): ").strip()
        if year.isdigit() and len(year) == 4:
            break
        print("\033[31mInvalid year. Please enter a 4-digit year.\033[0m")

    while True:
        month = input("Enter month (1-12): ").strip()
        if month.isdigit() and 1 <= int(month) <= 12:
            month_str = f"{int(month):02d}"
            break
        print("\033[31mInvalid month. Please enter a month from 1 to 12.\033[0m")

    key = f"{year}-{month_str}"
    filtered = [t for t in transactions if t["date"].startswith(key)]
    view_transactions(filtered, f"TRANSACTIONS - {key}")

def dashboard():
    transactions = get_transactions()
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expense = sum(t["amount"] for t in transactions if t["type"] == "expense")

    print("========== DASHBOARD ==========")
    print(f"\nTotal Income        : Rs. {total_income:.2f}")
    print(f"Total Expense       : Rs. {total_expense:.2f}")
    print(f"Current Balance     : Rs. {total_income - total_expense:.2f}")

def edit_transaction():
    transactions = get_transactions()
    if not transactions:
        print("\nNo transactions found to edit.")
        return

    view_transactions(transactions, "ALL TRANSACTIONS")
    try:
        choice = int(input("\nEnter number of transaction which u want to edit: "))
        if not 1 <= choice <= len(transactions):
            raise ValueError
    except ValueError:
        print("\033[31mPlease enter a valid transaction number.\033[0m")
        return

    old = transactions[choice - 1]
    print(f"\nEditing: {old['name']} ({old['type']})")

    name = input(f"Enter transaction name [{old['name']}]: ").strip() or old["name"]
    category = input(f"Enter category [{old['category']}]: ").strip() or old["category"]
    
    while True:
        trans_type = input(f"Enter transaction type (income or expense) [{old['type']}]: ").strip().lower() or old["type"]
        if trans_type in ("income", "expense"):
            break
        print("\033[31mType must be income or expense.\033[0m")

    try:
        amount_str = input(f"Enter amount [{old['amount']}]: ").strip()
        amount = float(amount_str) if amount_str else old["amount"]
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("\033[31mPlease enter a valid amount greater than 0.\033[0m")
        return

    trans_date = input(f"Enter date [yyyy-mm-dd] [{old['date']}]: ").strip() or old["date"]

    update_transaction_in_db(old["id"], name, category, trans_type, amount, trans_date)
    print("\n\033[32mTransaction edited successfully in database.\033[0m")

def delete_transaction():
    transactions = get_transactions()
    if not transactions:
        print("\nNo transactions found to delete.")
        return

    view_transactions(transactions, "ALL TRANSACTIONS")
    try:
        choice = int(input("\nEnter number of transaction which u want to delete: "))
        if not 1 <= choice <= len(transactions):
            raise ValueError
    except ValueError:
        print("\033[31mPlease enter a valid transaction number.\033[0m")
        return

    target = transactions[choice - 1]
    confirm = input(f"Are you sure you want to delete '{target['name']}'? (y/n): ").strip().lower()
    if confirm == 'y':
        delete_transaction_from_db(target["id"])
        print("\n\033[32mTransaction deleted successfully from database.\033[0m")
    else:
        print("Deletion cancelled.")

def main_menu():
    while True:
        print(f"\n\033[35m========== TRANSACTION TRACKER - {current_username.upper()} ==========")
        print("      MADE BY - GURANSH SINGH")
        print("1. Add expense")
        print("2. Add income")
        print("3. Full Dashboard")
        print("4. View all transactions")
        print("5. View by transaction type")
        print("6. View Monthly Filter")
        print("7. Edit transaction")
        print("8. Delete transaction")
        print("9. Logout / Previous Menu\033[0m")

        choice = input("Enter your choice (1-9): ").strip()

        match choice:
            case "1":
                add_transaction("expense")
            case "2":
                add_transaction("income")
            case "3":
                dashboard()
            case "4":
                view_transactions()
            case "5":
                view_by_type()
            case "6":
                view_monthly()
            case "7":
                edit_transaction()
            case "8":
                delete_transaction()
            case "9":
                print("\033[33mReturning to previous menu...\033[0m")
                return
            case _:
                print("\033[31mInvalid choice. Please enter a number from 1 to 9.\033[0m")

def authenticate(is_register):
    global current_user_id, current_username
    username = input("\033[36mEnter your name: \033[0m").strip()

    if not username:
        print("\033[31mName cannot be empty.\033[0m")
        return

    existing = get_user(username)

    if is_register:
        if existing:
            print("\n\033[31mYou are an old user \nPlease Login...\033[0m")
            return
        user_id = create_user(username)
        if user_id is None:
            print("\n\033[31mCould not create user.\033[0m")
            return
        current_user_id = user_id
        current_username = username
        main_menu()
    else:
        if not existing:
            print("\n\033[31mYou are not an old user \nPlease register yourself...\033[0m")
            return
        current_user_id = existing["id"]
        current_username = existing["username"]
        main_menu()

def main():
    initialize_database()
    while True:
        print("\n\033[32m========== Hisaab Mate ==========")
        print("        An Expense Tracker            ")
        print("      MADE BY - GURANSH SINGH\n")
        print("1. Register")
        print("2. Login")
        print("3. Exit\033[0m")

        choice = input("Enter your choice (1-3): ").strip()

        match choice:
            case "1":
                authenticate(is_register=True)
            case "2":
                authenticate(is_register=False)
            case "3":
                print("\033[36mThank you for using Transaction Tracker.\033[0m")
                break
            case _:
                print("\033[31mInvalid choice. Please enter a number from 1 to 3.\033[0m")

if __name__ == "__main__":
    main()