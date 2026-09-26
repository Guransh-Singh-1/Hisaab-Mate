import os
from datetime import date
    
def add_expense(file_name):
    print("\n--- ADD EXPENSE ---")
    expense_name = input("Enter expense name: ").replace(",", "")  # Remove commas to protect file structure
    category = input("Enter category (food, travel, shopping etc.): ").replace(",", "")

    try:
        amount = float(input("Enter amount: "))
    except ValueError:
        print("\033[31mPlease enter a valid number.\033[0m")
        return

    if amount <= 0:
        print("\033[31mAmount must be greater than 0.\033[0m")
        return

    expense_date = input("Enter date [yyyy-mm-dd] (press Enter for today): ")
    if expense_date.strip() == "":
        expense_date = str(date.today())

    with open(file_name, "a") as file:
        file.write(f"{expense_name},{category},{amount},{expense_date}\n")

    print("\033[32mExpense added successfully.\033[0m")


def get_expenses(file_name):
    expenses = []

    if not os.path.exists(file_name):
        return expenses

    with open(file_name, "r") as file:
        for line in file:
            data = line.strip().split(",")
            if len(data) >= 4:
                try:
                    expense = {
                        "name": data[0],
                        "category": data[1],
                        "amount": float(data[2]),
                        "date": data[3]
                    }
                    expenses.append(expense)
                except ValueError:
                    continue  # Skip corrupted lines safely

    return expenses


def delete_expenses(file_name):
    expenses = get_expenses(file_name)

    if not expenses:
        print("\n\033[33mNo expenses found to delete.\033[0m")
        return

    print("\n--- ALL EXPENSES ---")
    for index, expense in enumerate(expenses, start=1):
        print(f"{index}. {expense['name']} | {expense['category']} | Rs. {expense['amount']:.2f} | {expense['date']}")

    try:
        del_expense = int(input("\nEnter number of expense which you want to delete: "))
    except ValueError:
        print("\033[31mPlease enter a valid number.\033[0m")
        return
    
    if del_expense < 1 or del_expense > len(expenses):
        print("\n\033[31mInvalid input. Please enter a valid serial number.\033[0m")
        return
    
    expenses.pop(del_expense - 1)

    with open(file_name, "w") as file:
        for expense in expenses:
            file.write(f"{expense['name']},{expense['category']},{expense['amount']},{expense['date']}\n")

    print("\033[32mExpense deleted successfully.\033[0m")


def edit_expense(file_name):
    expenses = get_expenses(file_name)

    if not expenses:
        print("\n\033[33mNo expenses found to edit.\033[0m")
        return

    print("\n--- ALL EXPENSES ---")
    for index, expense in enumerate(expenses, start=1):
        print(f"{index}. {expense['name']} | {expense['category']} | Rs. {expense['amount']:.2f} | {expense['date']}")

    try:
        edit_index = int(input("\nEnter number of expense which you want to edit: "))
    except ValueError:
        print("\033[31mPlease enter a valid number.\033[0m")
        return
    
    if edit_index < 1 or edit_index > len(expenses):
        print("\n\033[31mInvalid input. Please enter a valid serial number.\033[0m")
        return
    
    current = expenses[edit_index - 1]
    print(f"\nEditing: {current['name']} | {current['category']} | Rs. {current['amount']} | {current['date']}")
    print("Press Enter to keep the existing value.")

    new_name = input(f"Enter new name [{current['name']}]: ").strip()
    if new_name == "":
        new_name = current['name']
    else:
        new_name = new_name.replace(",", "")

    new_category = input(f"Enter new category [{current['category']}]: ").strip()
    if new_category == "":
        new_category = current['category']
    else:
        new_category = new_category.replace(",", "")

    amount_input = input(f"Enter new amount [{current['amount']}]: ").strip()
    if amount_input == "":
        new_amount = current['amount']
    else:
        try:
            new_amount = float(amount_input)
            if new_amount <= 0:
                print("\033[31mAmount must be greater than 0. Keeping previous amount.\033[0m")
                new_amount = current['amount']
        except ValueError:
            print("\033[31mInvalid amount entered. Keeping previous amount.\033[0m")
            new_amount = current['amount']

    new_date = input(f"Enter new date [yyyy-mm-dd] [{current['date']}]: ").strip()
    if new_date == "":
        new_date = current['date']

    expenses[edit_index - 1] = {
        "name": new_name,
        "category": new_category,
        "amount": new_amount,
        "date": new_date
    }

    with open(file_name, "w") as file:
        for expense in expenses:
            file.write(f"{expense['name']},{expense['category']},{expense['amount']},{expense['date']}\n")

    print("\033[32mExpense updated successfully.\033[0m")


def view_expenses(file_name):
    expenses = get_expenses(file_name)

    if not expenses:
        print("\n\033[33mNo expenses found.\033[0m")
        return

    print("\n--- ALL EXPENSES ---")
    for index, expense in enumerate(expenses, start=1):
        print(f"{index}. {expense['name']} | {expense['category']} | Rs. {expense['amount']:.2f} | {expense['date']}")


def show_total(file_name):
    expenses = get_expenses(file_name)
    total = sum(expense["amount"] for expense in expenses)
    print(f"\nYour total expense is: Rs. {total:.2f}")


def show_category_total(file_name):
    expenses = get_expenses(file_name)

    if not expenses:
        print("\n\033[33mNo expenses found.\033[0m")
        return

    category_name = input("Enter category to check: ").strip().lower()
    total = sum(expense["amount"] for expense in expenses if expense["category"].lower() == category_name)

    print(f"\nTotal spent on '{category_name}' is: Rs. {total:.2f}")


def main(file_name):
    while True:
        print("\n\033[35m========== EXPENSE TRACKER ==========")
        print("      MADE BY - GURANSH SINGH")
        print("1. Add expense")
        print("2. View all expenses")
        print("3. View total expense")
        print("4. View total by category")
        print("5. Delete expense")
        print("6. Edit expense")
        print("7. Previous Menu")

        choice = input("Enter your choice (1-7): \033[0m")

        if choice == "1":
            add_expense(file_name)
        elif choice == "2":
            view_expenses(file_name)
        elif choice == "3":
            show_total(file_name)
        elif choice == "4":
            show_category_total(file_name)
        elif choice == "5":
            delete_expenses(file_name)
        elif choice == "6":
            edit_expense(file_name)
        elif choice == "7":
            print("\033[33mReturning to previous menu...\033[0m")
            return
        else:
            print("\033[31mInvalid choice. Please enter a number from 1 to 7.\033[0m")


def register():
    name = input("\033[36mEnter your name: \033[0m").strip()
    if not name:
        print("\033[31mName cannot be empty.\033[0m")
        return
    
    file_name = name + ".txt"
    if os.path.exists(file_name):
        print("\n\033[31mYou are an old user. Please login instead.\033[0m")
        return
    main(file_name)


def login():
    name = input("\033[36mEnter your name: \033[0m").strip()
    if not name:
        print("\033[31mName cannot be empty.\033[0m")
        return

    file_name = name + ".txt"
    if not os.path.exists(file_name):
        print("\n\033[31mUser not found. Please register yourself first.\033[0m")
        return
    main(file_name)


def main_1():
    while True:
        print("\n\033[32m========== Hisaab Mate ==========")
        print("        A Expense Tracker            ")
        print("      MADE BY - GURANSH SINGH\n")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter your choice (1-3): \033[0m")

        if choice == "1":
            register()
        elif choice == "2":
            login()
        elif choice == "3":
            print("\033[36mThank you for using Expense Tracker. Goodbye!\033[0m")
            return
        else:
            print("\033[31mInvalid choice. Please enter a number from 1 to 3.\033[0m")

if __name__ == "__main__":
    main_1()