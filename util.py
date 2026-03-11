from storage import CURRENCY


def print_menu():
    print("\n---- Grocery App ----")
    print(" 1. Add item")
    print(" 2. Remove item")
    print(" 3. View cart")
    print(" 4. Checkout")
    print(" 5. Decrease quantity")
    print(" 6. Show purchased items")
    print(" 7. Show pending items")
    print(" 8. Show category summary")
    print(" 9. Search items")
    print("10. Sort items")
    print("11. Export to CSV")
    print("12. Edit item")
    print("13. Exit")


def print_item(index, item, item_total):
    status = "Bought" if item.is_bought() else "Pending"
    print(f"{index}. {item.name} ({item.quantity}) - {item.category}")
    print(f"   Price: {CURRENCY}{item.price} each | Total: {CURRENCY}{item_total:.2f} | Status: {status}")


def print_delete_list(grocery_list):
    print("\n--- Cart ---")
    for i, item in enumerate(grocery_list, start=1):
        print(f"{i}. {item.name}")


def print_toggle_list(grocery_list):
    print("\n--- Cart ---")
    for i, item in enumerate(grocery_list, start=1):
        status = "Bought" if item.is_bought() else "Pending"
        print(f"{i}. {item.name} [{status}]")


def get_valid_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a valid number.")


def get_valid_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Please enter a valid price.")


def print_search_menu():
    print("\nSearch by:")
    print("1. Name")
    print("2. Category")


def print_sort_menu():
    print("\nSort by:")
    print("1. Name (A-Z)")
    print("2. Price (Low to High)")
    print("3. Quantity")
    print("4. Category")
    print("5. Status (Bought first)")


def print_export_menu():
    print("\nExport Options:")
    print("1. Export All Items")
    print("2. Export Bought Items")
    print("3. Export Pending Items")