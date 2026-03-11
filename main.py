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
from inventory_client import (
    is_api_available,
    search_products,
    check_stock,
    deduct_stock
)


# -------------------------
# STARTUP
# -------------------------

def check_api_on_startup():
    if is_api_available():
        print("✅ Inventory API connected.")
    else:
        print("⚠️  Inventory API not available. Running in offline mode.")
        print("   You can still manage your cart, but stock checking is disabled.")


# -------------------------
# CORE OPERATIONS
# -------------------------

def add_item(grocery_list):
    """Search Inventory API and add product to cart."""

    if not is_api_available():
        print("Inventory API is not available. Cannot browse products.")
        return

    keyword = input("Search product: ").strip().lower()
    if not keyword:
        print("Search keyword cannot be empty.")
        return

    results = search_products(keyword)

    if not results:
        print("No products found matching your search.")
        return

    # Show results to customer
    print("\nSearch Results:")
    for i, product in enumerate(results, start=1):
        print(f"{i}. {product['name']} — {CURRENCY}{product['price_per_unit']} (Stock: {product['stock']})")

    index = get_valid_int("Enter number to add to cart (0 to cancel): ") - 1

    if index == -1:
        print("Cancelled.")
        return

    if not (0 <= index < len(results)):
        print("Invalid selection.")
        return

    selected = results[index]

    # Check if already in cart
    existing = find_item_by_name(grocery_list, selected["name"])
    if existing:
        qty = get_valid_int("Already in cart. Enter quantity to add: ")
        try:
            existing.increase_quantity(qty)
            print(f"Updated quantity to {existing.quantity}")
        except ValueError as e:
            print("Error:", e)
        return

    quantity = get_valid_int("Enter quantity: ")
    if quantity <= 0:
        print("Quantity must be positive.")
        return

    # Check stock availability
    if not check_stock(selected["sku"], quantity):
        print(f"Not enough stock. Available: {selected['stock']}")
        return

    try:
        item = GroceryItem(
            name=selected["name"],
            quantity=quantity,
            price=selected["price_per_unit"],
            sku=selected["sku"]
        )
        grocery_list.append(item)
        print(f"{selected['name']} added to cart.")
    except ValueError as e:
        print("Error:", e)


def delete_item(grocery_list):
    if not grocery_list:
        print("Cart is empty.")
        return

    print_delete_list(grocery_list)
    index = get_valid_int("Enter item number to delete: ") - 1

    if 0 <= index < len(grocery_list):
        removed = grocery_list.pop(index)
        print(f"{removed.name} removed from cart.")
    else:
        print("Invalid item number.")


def decrease_quantity(grocery_list):
    if not grocery_list:
        print("Cart is empty.")
        return

    print_toggle_list(grocery_list)
    index = get_valid_int("Enter item number: ") - 1
    qty = get_valid_int("Enter quantity to decrease: ")

    result = decrease_item_quantity(grocery_list, index, qty)

    if result == "updated":
        print("Quantity updated successfully.")
    elif result == "delete":
        confirm = input("Quantity becomes 0. Remove from cart? (y/n): ").lower()
        if confirm == "y":
            grocery_list.pop(index)
            print("Item removed.")
        else:
            print("No changes made.")
    elif result == "invalid":
        print("Quantity must be positive and less than current.")
    else:
        print("Invalid item number.")


def view_items(grocery_list):
    if not grocery_list:
        print("Cart is empty.")
        return

    print("\n--- Your Cart ---")
    for i, item in enumerate(grocery_list, start=1):
        print_item(i, item, item.get_total_value())

    total = calculate_cart_total(grocery_list)
    print(f"\nCart Total: {CURRENCY}{total:.2f}\n")


def checkout(grocery_list):
    """Check stock for all items and deduct on confirmation."""
    pending = [item for item in grocery_list if not item.is_bought()]

    if not pending:
        print("No pending items in cart.")
        return

    if not is_api_available():
        print("Inventory API is not available. Cannot checkout.")
        return

    print("\n--- Checkout ---")
    print("Checking stock availability...\n")

    # Check stock for all items first
    out_of_stock = []
    for item in pending:
        if not item.sku:
            print(f"⚠️  {item.name} — not linked to inventory, skipping stock check.")
            continue
        if not check_stock(item.sku, item.quantity):
            out_of_stock.append(item.name)

    if out_of_stock:
        print("❌ The following items don't have enough stock:")
        for name in out_of_stock:
            print(f"   - {name}")
        print("\nPlease adjust quantities and try again.")
        return

    # Show cart summary
    print("All items in stock ✅\n")
    for item in pending:
        print_item(pending.index(item) + 1, item, item.get_total_value())

    total = sum(item.get_total_value() for item in pending)
    print(f"\nTotal: {CURRENCY}{total:.2f}")

    confirm = input("\nConfirm purchase? (y/n): ").strip().lower()
    if confirm != "y":
        print("Checkout cancelled.")
        return

    # Deduct stock and mark as bought
    for item in pending:
        if item.sku:
            result = deduct_stock(item.sku, item.quantity)
            if "error" in result:
                print(f"⚠️  Could not deduct stock for {item.name}: {result['error']}")
                continue
        item.mark_as_bought()

    print(f"\n✅ Purchase confirmed! Total: {CURRENCY}{total:.2f}")
    print("Thank you for shopping!")


def edit_item(grocery_list):
    if not grocery_list:
        print("Cart is empty.")
        return

    print_delete_list(grocery_list)
    index = get_valid_int("Enter item number to edit: ") - 1

    if not (0 <= index < len(grocery_list)):
        print("Invalid item number.")
        return

    item = grocery_list[index]
    print(f"\nEditing: {item.name}")
    print("Press Enter to keep current value.\n")

    new_category = input(f"Category [{item.category}]: ").strip()
    if new_category:
        item.category = new_category

    new_qty = input(f"Quantity [{item.quantity}]: ").strip()
    if new_qty:
        try:
            new_qty = int(new_qty)
            if new_qty <= 0:
                print("Quantity must be positive. Keeping current value.")
            else:
                item.quantity = new_qty
        except ValueError:
            print("Invalid quantity. Keeping current value.")

    print(f"{item.name} updated successfully.")


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
        print(f"{category}: {CURRENCY}{total:.2f}")


def search_menu(grocery_list):
    if not grocery_list:
        print("Cart is empty.")
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
        print("Cart is empty.")
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
        print("Cart is empty.")
        return

    print_export_menu()
    choice = input("Choose option: ").strip()

    mapping = {"1": "all", "2": "bought", "3": "pending"}

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
        print(f"Exported successfully to {filename}")
    except ValueError as e:
        print("Error:", e)


# -------------------------
# MAIN LOOP
# -------------------------

def main():
    grocery_list = load_data()

    # Check API on startup
    check_api_on_startup()

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
            checkout(grocery_list)
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