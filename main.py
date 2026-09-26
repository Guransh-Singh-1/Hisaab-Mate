import os
from datetime import date
    
def add_expense(file_name):
    print("\n--- ADD EXPENSE ---")
    expense_name = input("Enter expense name: ")
    category = input("Enter category (food, travel, shopping etc.): ")

    try:
        amount = float(input("Enter amount: "))
    except ValueError:
        print("Please enter a valid number.")
        return

    if amount <= 0:
        print("Amount must be greater than 0.")
        return

    expense_date = input("Enter date [yyyy-mm-dd]-(press Enter for today): ")
    if expense_date == "":
        expense_date = str(date.today())

    with open(file_name, "a") as file:
        file.write(expense_name + "," + category + "," + str(amount) + "," + expense_date + "\n")

    print("Expense added successfully.")


def get_expenses(file_name):
    expenses = []

    if not os.path.exists(file_name):
        return expenses

    with open(file_name, "r") as file:
        for line in file:
            data = line.strip().split(",")
            if len(data) == 4:
                expense = {
                    "name": data[0],
                    "category": data[1],
                    "amount": float(data[2]),
                    "date": data[3]
                }
                expenses.append(expense)

    return expenses


def view_expenses(file_name):
    expenses = get_expenses(file_name)

    if len(expenses) == 0:
        print("\nNo expenses found.")
        return

    print("\n--- ALL EXPENSES ---")
    for index, expense in enumerate(expenses, start=1):
        print(index, ".", expense["name"], "|", expense["category"], "| Rs.", expense["amount"], "|", expense["date"])


def show_total(file_name):
    expenses = get_expenses(file_name)
    total = sum(expense["amount"] for expense in expenses)

    print(f"\nYour total expense is: Rs. {total:.2f}")


def show_category_total(file_name):
    expenses = get_expenses(file_name)

    if len(expenses) == 0:
        print("\nNo expenses found.")
        return

    category_name = input("Enter category to check: ").lower()
    total = 0

    for expense in expenses:
        if expense["category"].lower() == category_name:
            total += expense["amount"]

    print("\nTotal spent on", category_name, "is: Rs.", total)


def main():
    file_name = "expenses.txt"
    
    while True:
        print("\n========== HISAAB MATE ==========")
        print("\n        A Expense Tracker        ")
        print("      MADE BY - GURANSH SINGH")
        print("1. Add expense")
        print("2. View all expenses")
        print("3. View total expense")
        print("4. View total by category")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ")

        if choice == "1":
            add_expense(file_name)
        elif choice == "2":
            view_expenses(file_name)
        elif choice == "3":
            show_total(file_name)
        elif choice == "4":
            show_category_total(file_name)
        elif choice == "5":
            print("Thank you for using Expense Tracker.")
            return
        else:
            print("Invalid choice. Please enter a number from 1 to 5.")

if __name__ == "__main__":
    main()
