import os
import sys
import sqlite3
import csv
from datetime import date
import tkinter as tk
from tkinter import filedialog
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

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
        conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE)")
        conn.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, category TEXT NOT NULL, type TEXT NOT NULL CHECK(type IN ('income', 'expense')), amount REAL NOT NULL, date TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)")

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
        rows = conn.execute("SELECT id, name, category, type, amount, date FROM transactions WHERE user_id = ? ORDER BY id", (current_user_id,)).fetchall()
        return [dict(row) for row in rows]

def add_transaction_to_db(name, category, trans_type, amount, trans_date):
    with get_db() as conn:
        conn.execute("INSERT INTO transactions (user_id, name, category, type, amount, date) VALUES (?, ?, ?, ?, ?, ?)", (current_user_id, name, category, trans_type, amount, trans_date))

def update_transaction_in_db(transaction_id, name, category, trans_type, amount, trans_date):
    with get_db() as conn:
        conn.execute("UPDATE transactions SET name = ?, category = ?, type = ?, amount = ?, date = ? WHERE id = ? AND user_id = ?", (name, category, trans_type, amount, trans_date, transaction_id, current_user_id))

def delete_transaction_from_db(transaction_id):
    with get_db() as conn:
        conn.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (transaction_id, current_user_id))

def input_box(hint, value=""):
    return TextInput(hint_text=hint, text=value, multiline=False, size_hint_y=None, height=48)

def show_text(title, text):
    box = BoxLayout(orientation="vertical", padding=10, spacing=8)
    scroll = ScrollView()

    label = Label(text=text, font_size=18, halign="left", valign="top", size_hint_y=None)
    label.bind(width=lambda instance, value: setattr(instance, "text_size", (value, None)))
    label.bind(texture_size=lambda instance, value: setattr(instance, "height", max(value[1], scroll.height)))

    scroll.add_widget(label)
    box.add_widget(scroll)

    close = Button(text="Close", size_hint_y=None, height=48)
    box.add_widget(close)

    popup = Popup(title=title, content=box, size_hint=(0.94, 0.88))
    close.bind(on_release=popup.dismiss)
    popup.open()

def format_lines(items):
    return "\n".join(f"{i}. {t['name']} | {t['category']} | {t['type']} | Rs. {t['amount']:.2f} | {t['date']}" for i, t in enumerate(items, 1))

def dashboard():
    transactions = get_transactions()
    total_income = sum(x["amount"] for x in transactions if x["type"] == "income")
    total_expense = sum(x["amount"] for x in transactions if x["type"] == "expense")
    show_text("Full Dashboard", f"========== DASHBOARD ==========\n\nTotal Income        : Rs. {total_income:.2f}\nTotal Expense       : Rs. {total_expense:.2f}\nCurrent Balance     : Rs. {total_income - total_expense:.2f}")

def view_transactions(items=None, title="ALL TRANSACTIONS"):
    transactions = get_transactions() if items is None else items
    show_text(title, format_lines(transactions) if transactions else "No transactions found.")

def add_transaction(kind):
    box = BoxLayout(orientation="vertical", padding=10, spacing=7)
    fields = [input_box(f"Enter {kind} name"), input_box("Enter category"), input_box("Enter amount"), input_box("Enter date [yyyy-mm-dd] (optional)")]
    for field in fields:
        box.add_widget(field)
    save = Button(text=f"Save {kind.capitalize()}", size_hint_y=None, height=48)
    box.add_widget(save)
    popup = Popup(title=f"Add {kind.capitalize()}", content=box, size_hint=(0.9, 0.82))
    
    def do_save(_):
        name, category, amount, trans_date = [field.text.strip() for field in fields]
        if not name or not category:
            show_text("Error", "Name and category cannot be empty.")
            return
        try:
            value = float(amount)
            if value <= 0:
                raise ValueError
        except ValueError:
            show_text("Error", "Please enter a valid amount greater than 0.")
            return
        if trans_date:
            try:
                date.fromisoformat(trans_date)
            except ValueError:
                show_text("Error", "Invalid date format. Use YYYY-MM-DD.")
                return
        else:
            trans_date = str(date.today())
        add_transaction_to_db(name, category, kind, value, trans_date)
        popup.dismiss()
        show_text("Success", f"{kind.capitalize()} added successfully to database.")
    save.bind(on_release=do_save)
    popup.open()

def view_by_type():
    box = BoxLayout(orientation="vertical", padding=10, spacing=8)
    popup = Popup(title="View By Transaction Type", content=box, size_hint=(0.8, 0.4))
    for kind in ("income", "expense"):
        button = Button(text=kind.capitalize(), size_hint_y=None, height=48)
        box.add_widget(button)

        def make_handler(selected_type):
            return lambda _: (popup.dismiss(), view_transactions([x for x in get_transactions() if x["type"] == selected_type], f"{selected_type.upper()} TRANSACTIONS"))
        button.bind(on_release=make_handler(kind))
    popup.open()

def view_monthly():
    box = BoxLayout(orientation="vertical", padding=10, spacing=8)
    year_input = input_box("Enter year (YYYY)")
    month_input = input_box("Enter month (1-12)")
    box.add_widget(year_input)
    box.add_widget(month_input)
    button = Button(text="Show Monthly Filter", size_hint_y=None, height=48)
    box.add_widget(button)
    popup = Popup(title="Monthly Filter", content=box, size_hint=(0.8, 0.55))

    def show(_):
        year = year_input.text.strip()
        month = month_input.text.strip()
        if not (year.isdigit() and len(year) == 4 and month.isdigit() and 1 <= int(month) <= 12):
            show_text("Error", "Please enter a valid 4-digit year and month (1-12).")
            return
        key = f"{year}-{int(month):02d}"
        items = [x for x in get_transactions() if x["date"].startswith(key)]
        popup.dismiss()
        view_transactions(items, f"TRANSACTIONS - {key}")
    button.bind(on_release=show)
    popup.open()

def choose_transaction(title, action):
    items = get_transactions()
    if not items:
        show_text(title, "No transactions found.")
        return
    box = BoxLayout(orientation="vertical", padding=10, spacing=8)
    scroll = ScrollView()
    label = Label(text=format_lines(items), font_size=18, halign="left", valign="top", size_hint_x=1, size_hint_y=None)
    label.bind(texture_size=lambda w, s: setattr(w, "height", max(s[1], scroll.height)))
    scroll.add_widget(label)
    box.add_widget(scroll)
    number = input_box("Enter transaction number")
    box.add_widget(number)
    button = Button(text=title, size_hint_y=None, height=48)
    box.add_widget(button)
    popup = Popup(title=f"Select Transaction - {title}", content=box, size_hint=(0.95, 0.9))

    def choose(_):
        try:
            index = int(number.text) - 1
            if not 0 <= index < len(items):
                raise ValueError
        except ValueError:
            show_text("Error", "Please enter a valid transaction number.")
            return
        popup.dismiss()
        action(items, index)
    button.bind(on_release=choose)
    popup.open()

def edit_action(items, i):
    old = items[i]
    box = BoxLayout(orientation="vertical", padding=10, spacing=6)
    fields = [input_box(f"Enter name [{old['name']}]", old["name"]), input_box(f"Enter category [{old['category']}]", old["category"]), input_box(f"Enter type (income/expense) [{old['type']}]", old["type"]), input_box(f"Enter amount [{old['amount']}]", str(old["amount"])), input_box(f"Enter date [yyyy-mm-dd] [{old['date']}]", old["date"])]
    for field in fields:
        box.add_widget(field)
    button = Button(text="Save Changes", size_hint_y=None, height=48)
    box.add_widget(button)
    popup = Popup(title=f"Editing: {old['name']}", content=box, size_hint=(0.9, 0.86))

    def save(_):
        name, category, trans_type, amount, trans_date = [field.text.strip() for field in fields]
        trans_type = trans_type.lower()
        if trans_type not in ("income", "expense"):
            show_text("Error", "Type must be income or expense.")
            return
        if not name or not category:
            show_text("Error", "Name and category cannot be empty.")
            return
        try:
            value = float(amount)
            if value <= 0:
                raise ValueError
        except ValueError:
            show_text("Error", "Please enter a valid amount greater than 0.")
            return
        if trans_date:
            try:
                date.fromisoformat(trans_date)
            except ValueError:
                show_text("Error", "Invalid date format. Use YYYY-MM-DD.")
                return
        else:
            trans_date = old["date"]
        update_transaction_in_db(old["id"], name, category, trans_type, value, trans_date)
        popup.dismiss()
        show_text("Success", "Transaction edited successfully in database.")
    button.bind(on_release=save)
    popup.open()

def edit_transaction():
    choose_transaction("Edit Transaction", edit_action)

def delete_action(items, i):
    box = BoxLayout(orientation="vertical", padding=10, spacing=8)
    box.add_widget(Label(text=f"Are you sure you want to delete '{items[i]['name']}'?", font_size=18))
    yes = Button(text="Yes (Delete)", size_hint_y=None, height=48)
    no = Button(text="No (Cancel)", size_hint_y=None, height=48)
    box.add_widget(yes)
    box.add_widget(no)
    popup = Popup(title="Confirm Deletion", content=box, size_hint=(0.85, 0.45))
    no.bind(on_release=popup.dismiss)

    def remove(_):
        delete_transaction_from_db(items[i]["id"])
        popup.dismiss()
        show_text("Success", "Transaction deleted successfully from database.")
    yes.bind(on_release=remove)
    popup.open()

def delete_transaction():
    choose_transaction("Delete Transaction", delete_action)

def export_csv():
    all_transactions = get_transactions()
    if not all_transactions:
        show_text("Export", "You have no transactions to export.")
        return
    main_layout = BoxLayout(orientation="vertical", padding=15, spacing=10)
    scroll_view = ScrollView()
    content_box = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
    content_box.bind(minimum_height=content_box.setter("height"))
    error_label = Label(text="", color=(1, 0.3, 0.3, 1), size_hint_y=None, height=25, bold=True)
    content_box.add_widget(Label(text="Export Options & Date Range", font_size=18, bold=True, size_hint_y=None, height=35))
    export_mode = {"full": True}
    mode_box = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=48)
    full_button = Button(text="[ FULL HISTORY ]", bold=True)
    range_button = Button(text="CUSTOM RANGE", bold=False)
    mode_box.add_widget(full_button)
    mode_box.add_widget(range_button)
    from_date_input = input_box("From YYYY-MM-DD")
    to_date_input = input_box("To YYYY-MM-DD")

    def set_full(_):
        export_mode["full"] = True
        full_button.text = "[ FULL HISTORY ]"
        full_button.bold = True
        range_button.text = "CUSTOM RANGE"
        range_button.bold = False

    def set_range(_):
        export_mode["full"] = False
        full_button.text = "FULL HISTORY"
        full_button.bold = False
        range_button.text = "[ CUSTOM RANGE ]"
        range_button.bold = True

    full_button.bind(on_release=set_full)
    range_button.bind(on_release=set_range)
    content_box.add_widget(mode_box)
    content_box.add_widget(Label(text="Date Filters (Optional for Custom Range):", size_hint_y=None, height=20))
    content_box.add_widget(from_date_input)
    content_box.add_widget(to_date_input)
    content_box.add_widget(Label(text="Destination Folder:", size_hint_y=None, height=20))
    folder_path_holder = {"path": os.path.expanduser("~")}
    path_display_btn = Button(text=folder_path_holder["path"], size_hint_y=None, height=48)

    def choose_folder(_):
        root_tk = tk.Tk()
        root_tk.withdraw()
        root_tk.attributes("-topmost", True)
        selected_dir = filedialog.askdirectory(initialdir=folder_path_holder["path"])
        root_tk.destroy()
        if selected_dir:
            folder_path_holder["path"] = selected_dir
            path_display_btn.text = selected_dir

    path_display_btn.bind(on_release=choose_folder)
    content_box.add_widget(path_display_btn)
    filename_input = input_box("CSV File Name", f"{current_username}_transactions.csv")
    content_box.add_widget(Label(text="File Name:", size_hint_y=None, height=20))
    content_box.add_widget(filename_input)
    content_box.add_widget(error_label)
    scroll_view.add_widget(content_box)
    main_layout.add_widget(scroll_view)
    btn_box = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=48)
    save_button = Button(text="Save Export CSV", bold=True)
    cancel_button = Button(text="Cancel")
    btn_box.add_widget(save_button)
    btn_box.add_widget(cancel_button)
    main_layout.add_widget(btn_box)
    export_popup = Popup(title="Export CSV Setup", content=main_layout, size_hint=(0.90, 0.85), auto_dismiss=False)

    def do_export(_):
        error_label.text = ""
        from_d = from_date_input.text.strip()
        to_d = to_date_input.text.strip()
        raw_filename = filename_input.text.strip()
        folder = folder_path_holder["path"]
        filename = os.path.basename(raw_filename)
        if not filename:
            error_label.text = "Enter a valid file name."
            return
        if not filename.lower().endswith(".csv"):
            filename += ".csv"
        export_list = []
        if export_mode["full"]:
            export_list = all_transactions
            range_info = "Full History"
        else:
            from_dt = None
            to_dt = None
            if from_d:
                try:
                    from_dt = date.fromisoformat(from_d)
                except ValueError:
                    error_label.text = "From date must be YYYY-MM-DD."
                    return
            if to_d:
                try:
                    to_dt = date.fromisoformat(to_d)
                except ValueError:
                    error_label.text = "To date must be YYYY-MM-DD."
                    return
            if from_dt and to_dt and from_dt > to_dt:
                error_label.text = "From date cannot be after To date."
                return
            for transaction in all_transactions:
                try:
                    t_dt = date.fromisoformat(transaction["date"])
                    if from_dt and t_dt < from_dt:
                        continue
                    if to_dt and t_dt > to_dt:
                        continue
                    export_list.append(transaction)
                except ValueError:
                    t_date = transaction["date"]
                    if from_d and t_date < from_d:
                        continue
                    if to_d and t_date > to_d:
                        continue
                    export_list.append(transaction)
            range_info = f"Range: {from_d or 'Start'} to {to_d or 'End'}"
        if not export_list:
            error_label.text = "No transactions found within range."
            return
        file_path = os.path.join(folder, filename)
        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(["Transaction Name", "Category", "Type", "Amount", "Date"])
                for transaction in export_list:
                    writer.writerow([transaction["name"], transaction["category"], transaction["type"], transaction["amount"], transaction["date"]])
            export_popup.dismiss()
            Clock.schedule_once(lambda dt: show_text("Export Successful", f"Exported {len(export_list)} transactions ({range_info}) to:\n{file_path}"), 0.1)
        except OSError as error:
            error_label.text = f"Could not save export file:\n{error}"
    save_button.bind(on_release=do_export)
    cancel_button.bind(on_release=export_popup.dismiss)
    export_popup.open()

def main_menu(root):
    root.clear_widgets()
    header_box = BoxLayout(orientation="vertical", size_hint_y=None, height=70, spacing=2)
    header_box.add_widget(Label(text=f"TRANSACTION TRACKER - {current_username.upper()}", font_size=20, bold=True))
    header_box.add_widget(Label(text="MADE BY - GURANSH SINGH", font_size=14, bold=True, color=(0.8, 0.8, 0.8, 1)))
    root.add_widget(header_box)
    menu_buttons = [("1. Add expense", lambda _: add_transaction("expense")), ("2. Add income", lambda _: add_transaction("income")), ("3. Full Dashboard", lambda _: dashboard()), ("4. View all transactions", lambda _: view_transactions()), ("5. View by transaction type", lambda _: view_by_type()), ("6. View Monthly Filter", lambda _: view_monthly()), ("7. Edit transaction", lambda _: edit_transaction()), ("8. Delete transaction", lambda _: delete_transaction()), ("9. Export CSV Data", lambda _: export_csv()), ("10. Logout / Previous Menu", lambda _: login_screen(root))]
    for text, action in menu_buttons:
        btn = Button(text=text, size_hint_y=None, height=42)
        root.add_widget(btn)
        btn.bind(on_release=action)

def login_screen(root):
    global current_user_id, current_username
    current_user_id = None
    current_username = ""
    root.clear_widgets()
    title = Label(text="========== Hisaab Mate ==========", font_size=26, bold=True, size_hint_y=None, height=45, color=(0.2, 0.8, 0.4, 1))
    subtitle = Label(text="An Expense Tracker", font_size=18, size_hint_y=None, height=30)
    made = Label(text="MADE BY - GURANSH SINGH", font_size=16, bold=True, size_hint_y=None, height=35)
    name_input = input_box("Enter your name")
    reg_btn = Button(text="1. Register", size_hint_y=None, height=48)
    login_btn = Button(text="2. Login", size_hint_y=None, height=48)
    exit_btn = Button(text="3. Exit", size_hint_y=None, height=48)
    root.add_widget(title)
    root.add_widget(subtitle)
    root.add_widget(made)
    root.add_widget(Label(text="", size_hint_y=None, height=10))
    root.add_widget(name_input)
    root.add_widget(reg_btn)
    root.add_widget(login_btn)
    root.add_widget(exit_btn)

    def authenticate(_, is_register):
        global current_user_id, current_username
        username = name_input.text.strip()
        if not username:
            show_text("Error", "Name cannot be empty.")
            return
        existing = get_user(username)
        if is_register:
            if existing:
                show_text("Notice", "You are an old user.\nPlease Login...")
                return
            user_id = create_user(username)
            if user_id is None:
                show_text("Error", "Could not create user.")
                return
            current_user_id = user_id
            current_username = username
            main_menu(root)
        else:
            if not existing:
                show_text("Notice", "You are not an old user.\nPlease register yourself...")
                return
            current_user_id = existing["id"]
            current_username = existing["username"]
            main_menu(root)
    reg_btn.bind(on_release=lambda w: authenticate(w, is_register=True))
    login_btn.bind(on_release=lambda w: authenticate(w, is_register=False))
    exit_btn.bind(on_release=lambda _: App.get_running_app().stop())

def build_app():
    from kivy.core.window import Window

    Window.size = (500, 800)
    Window.minimum_size = (450, 700)
    Window.title = "Hisaab Mate - Transaction Tracker"

    initialize_database()
    root = BoxLayout(orientation="vertical", padding=15, spacing=8)
    login_screen(root)
    return root

if __name__ == "__main__":
    app_instance = App()
    app_instance.build = build_app
    app_instance.run()