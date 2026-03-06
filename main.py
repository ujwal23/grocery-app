from models import GroceryItem
from storage import load_data, save_data, CURRENCY
from services import (
    find_item_by_name,
    calculate_cart_total,
    calculate_item_total,
    decrease_item_quantity,
    filter_items,
    category_summary,
    search_items,
    sort_items,
    export_to_csv
)
from util import (
    print_menu,
    print_item,
    print_delete_list,
    print_toggle_list,
    get_valid_int,
    get_valid_float,
    print_search_menu,
    print_sort_menu,
    print_export_menu
)


# -------------------------
# CORE OPERATIONS
# -------------------------

def add_item(grocery_list):
    name = input("Enter item name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return

    # Check for duplicate
    existing_item = find_item_by_name(grocery_list, name)
    if existing_item:
        print(f"{name} already exists.")
        qty = get_valid_int("Enter quantity to add: ")
        try:
            existing_item.increase_quantity(qty)     # model handles validation
            print(f"Updated quantity to {existing_item.quantity}")
        except ValueError as e:
            print("Error:", e)
        return

    # New item — collect details
    quantity = get_valid_int("Enter quantity: ")
    price = get_valid_float("Enter price per unit: ")
    category = input("Enter category: ").strip() or "General"

    # Let the model validate — catch any errors it raises
    try:
        item = GroceryItem(name, quantity, price, category)
        grocery_list.append(item)
        print(f"{name} added successfully.")
    except ValueError as e:
        print("Error:", e)


def delete_item(grocery_list):
    if not grocery_list:
        print("Grocery list is empty.")
        return

    print_delete_list(grocery_list)
    index = get_valid_int("Enter item number to delete: ") - 1

    if 0 <= index < len(grocery_list):
        removed = grocery_list.pop(index)
        print(f"{removed.name} deleted successfully.")     # dot notation
    else:
        print("Invalid item number.")


def toggle_item(grocery_list):
    if not grocery_list:
        print("Grocery list is empty.")
        return

    print_toggle_list(grocery_list)
    index = get_valid_int("Enter item number to toggle: ") - 1

    if 0 <= index < len(grocery_list):
        grocery_list[index].toggle_bought()               # model method
        print("Status updated successfully.")
    else:
        print("Invalid item number.")


def decrease_quantity(grocery_list):
    if not grocery_list:
        print("Grocery list is empty.")
        return

    print_toggle_list(grocery_list)
    index = get_valid_int("Enter item number: ") - 1
    qty = get_valid_int("Enter quantity to decrease: ")

    result = decrease_item_quantity(grocery_list, index, qty)

    if result == "updated":
        print("Quantity updated successfully.")

    elif result == "delete":
        confirm = input("Quantity becomes 0. Delete item? (y/n): ").lower()
        if confirm == "y":
            grocery_list.pop(index)
            print("Item deleted.")
        else:
            print("No changes made.")

    elif result == "invalid":
        print("Quantity must be positive and less than current.")

    else:
        print("Invalid item number.")


def edit_item(grocery_list):
    if not grocery_list:
        print("Grocery list is empty.")
        return

    print_delete_list(grocery_list)
    index = get_valid_int("Enter item number to edit: ") - 1

    if not (0 <= index < len(grocery_list)):
        print("Invalid item number.")
        return

    item = grocery_list[index]
    print(f"\nEditing: {item.name}")
    print("Press Enter to keep current value.\n")

    # Each field is optional — only update if user enters something
    new_name = input(f"Name [{item.name}]: ").strip()
    if new_name:
        item.name = new_name

    new_category = input(f"Category [{item.category}]: ").strip()
    if new_category:
        item.category = new_category

    new_price = input(f"Price [{item.price}]: ").strip()
    if new_price:
        try:
            new_price = float(new_price)
            if new_price < 0:
                print("Price cannot be negative. Keeping current value.")
            else:
                item.price = new_price
        except ValueError:
            print("Invalid price. Keeping current value.")

    print(f"{item.name} updated successfully.")


def view_items(grocery_list):
    if not grocery_list:
        print("Grocery list is empty.")
        return

    print("\n--- Grocery List ---")
    for i, item in enumerate(grocery_list, start=1):
        print_item(i, item, item.get_total_value())       # model method

    total = calculate_cart_total(grocery_list)
    print(f"\nTotal (bought items only): {CURRENCY}{total:.2f}\n")   # CURRENCY constant


def show_filtered(grocery_list, status):
    filtered = filter_items(grocery_list, status)

    if not filtered:
        print("No items found.")
        return

    for i, item in enumerate(filtered, start=1):
        print_item(i, item, item.get_total_value())


def show_category_summary(grocery_list):
    summary = category_summary(grocery_list)

    if not summary:
        print("No items available.")
        return

    print("\nCategory-wise Spending:")
    for category, total in summary.items():
        print(f"{category}: {CURRENCY}{total:.2f}")       # CURRENCY constant


def search_menu(grocery_list):
    if not grocery_list:
        print("Grocery list is empty.")
        return

    print_search_menu()
    choice = input("Choose option: ").strip()

    if choice == "1":
        keyword = input("Enter name keyword: ")
        results = search_items(grocery_list, keyword, "name")
    elif choice == "2":
        keyword = input("Enter category keyword: ")
        results = search_items(grocery_list, keyword, "category")
    else:
        print("Invalid choice.")
        return

    if not results:
        print("No matching items found.")
        return

    print("\nSearch Results:")
    for i, item in enumerate(results, start=1):
        print_item(i, item, item.get_total_value())


def sort_menu(grocery_list):
    if not grocery_list:
        print("Grocery list is empty.")
        return

    print_sort_menu()
    choice = input("Choose option: ").strip()

    sort_mapping = {
        "1": "name",
        "2": "price",
        "3": "quantity",
        "4": "category",
        "5": "status"
    }

    if choice not in sort_mapping:
        print("Invalid choice.")
        return

    sorted_list = sort_items(grocery_list, sort_mapping[choice])

    print("\nSorted Results:")
    for i, item in enumerate(sorted_list, start=1):
        print_item(i, item, item.get_total_value())


def export_menu(grocery_list):
    if not grocery_list:
        print("Grocery list is empty.")
        return

    print_export_menu()
    choice = input("Choose option: ").strip()

    mapping = {
        "1": "all",
        "2": "bought",
        "3": "pending"
    }

    if choice not in mapping:
        print("Invalid choice.")
        return

    filename = input("Enter filename (without extension): ").strip()
    if not filename:
        print("Filename cannot be empty.")
        return

    filename = filename + ".csv"

    try:
        export_to_csv(grocery_list, filename, mapping[choice])
        print(f"Data exported successfully to {filename}")
    except ValueError as e:
        print("Error:", e)


# -------------------------
# MAIN LOOP
# -------------------------

def main():
    grocery_list = load_data()

    while True:
        print_menu()
        choice = input("Choose option: ").strip()

        if choice == "1":
            add_item(grocery_list)
            save_data(grocery_list)

        elif choice == "2":
            delete_item(grocery_list)
            save_data(grocery_list)

        elif choice == "3":
            view_items(grocery_list)

        elif choice == "4":
            toggle_item(grocery_list)
            save_data(grocery_list)

        elif choice == "5":
            decrease_quantity(grocery_list)
            save_data(grocery_list)

        elif choice == "6":
            show_filtered(grocery_list, "bought")

        elif choice == "7":
            show_filtered(grocery_list, "pending")

        elif choice == "8":
            show_category_summary(grocery_list)

        elif choice == "9":
            search_menu(grocery_list)

        elif choice == "10":
            sort_menu(grocery_list)

        elif choice == "11":
            export_menu(grocery_list)

        elif choice == "12":
            edit_item(grocery_list)
            save_data(grocery_list)

        elif choice == "13":
            save_data(grocery_list)
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()