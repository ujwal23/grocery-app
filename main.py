from datetime import datetime
from models import GroceryItem
from storage import load_data, save_data, load_history, save_history, CURRENCY
from services import (
    export_to_csv
)
from util import (
    print_menu,
    print_item,
    get_valid_int,
    print_browse_menu,
    print_export_menu
)
from inventory_client import (
    is_api_available,
    search_products,
    get_all_products,
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
        print("   Browsing and checkout are disabled until API is back.")


# -------------------------
# BROWSE & ADD TO CART
# -------------------------

def browse_and_add(grocery_list):
    if not is_api_available():
        print("Inventory API is not available. Cannot browse products.")
        return

    while True:
        print_browse_menu()
        choice = input("Choose option: ").strip()

        if choice == "1":
            keyword = input("Search by name: ").strip().lower()
            if not keyword:
                print("Keyword cannot be empty.")
                continue
            results = search_products(keyword)

        elif choice == "2":
            keyword = input("Enter category: ").strip().lower()
            all_products = get_all_products()
            results = [p for p in all_products if keyword in p.get("category_id", "").lower()]
            if not results:
                results = [p for p in all_products if keyword in p["name"].lower()]

        elif choice == "3":
            results = get_all_products()
            results = sorted(results, key=lambda p: p["price_per_unit"])

        elif choice == "4":
            results = get_all_products()

        elif choice == "5":
            break

        else:
            print("Invalid choice.")
            continue

        if not results:
            print("No products found.")
            continue

        print("\nAvailable Products:")
        for i, product in enumerate(results, start=1):
            stock_status = "✅ In stock" if product["stock"] > 0 else "❌ Out of stock"
            print(f"{i}. {product['name']} — {CURRENCY}{product['price_per_unit']} | {stock_status} ({product['stock']} left)")

        index = get_valid_int("\nEnter number to add to cart (0 to go back): ") - 1

        if index == -1:
            continue

        if not (0 <= index < len(results)):
            print("Invalid selection.")
            continue

        selected = results[index]

        if selected["stock"] <= 0:
            print("Sorry, this product is out of stock.")
            continue

        # Only match pending items — ignore already bought ones
        existing = next(
            (item for item in grocery_list if item.name == selected["name"] and not item.is_bought()),
            None
        )

        if existing:
            qty = get_valid_int(f"{selected['name']} is already in cart (qty: {existing.quantity}). Add more: ")
            if qty <= 0:
                print("Quantity must be positive.")
                continue
            if not check_stock(selected["sku"], existing.quantity + qty):
                print(f"Not enough stock. Available: {selected['stock']}")
                continue
            try:
                existing.increase_quantity(qty)
                save_data(grocery_list)
                print(f"Updated quantity to {existing.quantity}")
            except ValueError as e:
                print("Error:", e)
            continue

        qty = get_valid_int("Enter quantity: ")
        if qty <= 0:
            print("Quantity must be positive.")
            continue

        if not check_stock(selected["sku"], qty):
            print(f"Not enough stock. Available: {selected['stock']}")
            continue

        try:
            item = GroceryItem(
                name=selected["name"],
                quantity=qty,
                price=selected["price_per_unit"],
                sku=selected["sku"]
            )
            grocery_list.append(item)
            save_data(grocery_list)
            print(f"✅ {selected['name']} added to cart.")
        except ValueError as e:
            print("Error:", e)


# -------------------------
# VIEW CART
# -------------------------

def view_cart(grocery_list):
    pending = [item for item in grocery_list if not item.is_bought()]

    if not pending:
        print("Your cart is empty.")
        return

    print(f"\n--- Your Cart ({len(pending)} items) ---")
    for i, item in enumerate(pending, start=1):
        print_item(i, item, item.get_total_value())

    total = sum(item.get_total_value() for item in pending)
    print(f"\nTotal: {CURRENCY}{total:.2f}")


# -------------------------
# REMOVE ITEM
# -------------------------

def remove_item(grocery_list):
    pending = [item for item in grocery_list if not item.is_bought()]

    if not pending:
        print("Your cart is empty.")
        return

    print("\n--- Cart ---")
    for i, item in enumerate(pending, start=1):
        print(f"{i}. {item.name} x{item.quantity}")

    index = get_valid_int("Enter item number to remove (0 to cancel): ") - 1

    if index == -1:
        return

    if 0 <= index < len(pending):
        item_to_remove = pending[index]
        grocery_list.remove(item_to_remove)
        save_data(grocery_list)
        print(f"{item_to_remove.name} removed from cart.")
    else:
        print("Invalid item number.")


# -------------------------
# CHECKOUT
# -------------------------

def checkout(grocery_list, history):
    pending = [item for item in grocery_list if not item.is_bought()]

    if not pending:
        print("Your cart is empty.")
        return

    if not is_api_available():
        print("Inventory API is not available. Cannot checkout.")
        return

    print("\n--- Checkout ---")
    print("Checking stock availability...\n")

    out_of_stock = []
    for item in pending:
        if not item.sku:
            continue
        if not check_stock(item.sku, item.quantity):
            out_of_stock.append(item.name)

    if out_of_stock:
        print("❌ The following items don't have enough stock:")
        for name in out_of_stock:
            print(f"   - {name}")
        print("\nPlease adjust quantities and try again.")
        return

    print("All items in stock ✅\n")
    for i, item in enumerate(pending, start=1):
        print_item(i, item, item.get_total_value())

    total = sum(item.get_total_value() for item in pending)
    print(f"\nTotal: {CURRENCY}{total:.2f}")

    confirm = input("\nConfirm purchase? (y/n): ").strip().lower()
    if confirm != "y":
        print("Checkout cancelled.")
        return

    failed = []
    for item in pending:
        if item.sku:
            result = deduct_stock(item.sku, item.quantity)
            if "error" in result:
                failed.append(item.name)
                continue
        item.mark_as_bought()

    # Remove bought items from cart — cart is clean after checkout
    grocery_list[:] = [item for item in grocery_list if not item.is_bought()]

    # Save to purchase history
    history_entry = {
        "date": datetime.now().isoformat(),
        "items": [
            {
                "name": item.name,
                "quantity": item.quantity,
                "price": item.price,
                "total": item.get_total_value()
            }
            for item in pending if item.name not in failed
        ],
        "total": total
    }
    history.append(history_entry)
    save_history(history)
    save_data(grocery_list)

    if failed:
        print(f"\n⚠️  Could not process: {', '.join(failed)}")

    print(f"\n✅ Purchase confirmed! Total: {CURRENCY}{total:.2f}")
    print("Thank you for shopping!")


# -------------------------
# PURCHASE HISTORY
# -------------------------

def view_history(history):
    if not history:
        print("No purchase history yet.")
        return

    print(f"\n--- Purchase History ({len(history)} orders) ---")
    for i, order in enumerate(history, start=1):
        print(f"\nOrder {i} — {order['date'][:10]}")
        for item in order["items"]:
            print(f"  {item['name']} x{item['quantity']} — {CURRENCY}{item['total']:.2f}")
        print(f"  Order Total: {CURRENCY}{order['total']:.2f}")


# -------------------------
# EXPORT RECEIPT
# -------------------------

def export_receipt(grocery_list, history):
    print("\nExport Options:")
    print("1. Export current cart")
    print("2. Export last purchase receipt")

    choice = input("Choose option: ").strip()

    if choice == "1":
        pending = [item for item in grocery_list if not item.is_bought()]
        if not pending:
            print("Cart is empty.")
            return
        filename = input("Enter filename (without extension): ").strip() + ".csv"
        try:
            export_to_csv(pending, filename, "all")
            print(f"Cart exported to {filename}")
        except ValueError as e:
            print("Error:", e)

    elif choice == "2":
        if not history:
            print("No purchase history yet.")
            return
        last_order = history[-1]
        filename = input("Enter filename (without extension): ").strip() + ".csv"
        with open(filename, "w", newline="") as file:
            import csv
            writer = csv.writer(file)
            writer.writerow(["Name", "Quantity", "Price", "Total"])
            for item in last_order["items"]:
                writer.writerow([item["name"], item["quantity"], item["price"], item["total"]])
            writer.writerow([])
            writer.writerow(["Order Total", "", "", last_order["total"]])
        print(f"Receipt exported to {filename}")

    else:
        print("Invalid choice.")


# -------------------------
# MAIN LOOP
# -------------------------

def main():
    grocery_list = load_data()
    history = load_history()

    check_api_on_startup()

    while True:
        print_menu()
        choice = input("Choose option: ").strip()

        if choice == "1":
            browse_and_add(grocery_list)

        elif choice == "2":
            view_cart(grocery_list)

        elif choice == "3":
            remove_item(grocery_list)

        elif choice == "4":
            checkout(grocery_list, history)

        elif choice == "5":
            view_history(history)

        elif choice == "6":
            export_receipt(grocery_list, history)

        elif choice == "7":
            save_data(grocery_list)
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()