from storage import CURRENCY


def print_menu():
    print("\n---- Grocery App ----")
    print("1. Browse & Add to cart")
    print("2. View cart")
    print("3. Remove item")
    print("4. Checkout")
    print("5. Purchase history")
    print("6. Export receipt")
    print("7. Exit")


def print_item(index, item, item_total):
    status = "✅ Bought" if item.is_bought() else "⏳ Pending"
    print(f"{index}. {item.name} x{item.quantity} — {CURRENCY}{item.price} each | Total: {CURRENCY}{item_total:.2f} | {status}")


def print_delete_list(grocery_list):
    print("\n--- Cart ---")
    for i, item in enumerate(grocery_list, start=1):
        print(f"{i}. {item.name} x{item.quantity}")


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


def print_browse_menu():
    print("\n---- Browse Products ----")
    print("1. Search by name")
    print("2. Browse by category")
    print("3. Browse by price (low to high)")
    print("4. Browse all")
    print("5. Back")


def print_export_menu():
    print("\nExport Options:")
    print("1. Export full cart")
    print("2. Export purchased items only")