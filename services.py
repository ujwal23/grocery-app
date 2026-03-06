import csv


def find_item_by_name(grocery_list, name):
    for item in grocery_list:
        if item.name.lower() == name.lower():
            return item
    return None


def calculate_item_total(item):
    return item.get_total_value()


def calculate_cart_total(grocery_list):
    total = 0
    for item in grocery_list:
        if item.is_bought():
            total += item.get_total_value()
    return total


def decrease_item_quantity(grocery_list, index, qty):
    if not (0 <= index < len(grocery_list)):
        return "invalid_index"

    item = grocery_list[index]

    if qty <= 0:
        return "invalid"

    if qty >= item.quantity:
        return "delete"

    item.decrease_quantity(qty)
    return "updated"


def filter_items(grocery_list, status):
    """
    status = "bought" or "pending"
    """
    if status == "bought":
        return [item for item in grocery_list if item.is_bought()]
    elif status == "pending":
        return [item for item in grocery_list if not item.is_bought()]
    return []


def category_summary(grocery_list):
    summary = {}
    for item in grocery_list:
        category = item.category
        total = item.get_total_value()
        if category in summary:
            summary[category] += total
        else:
            summary[category] = total
    return summary


def search_items(grocery_list, keyword, field="name"):
    """
    field: "name" or "category"
    keyword: partial match (case-insensitive)
    """
    keyword = keyword.lower().strip()

    if field == "name":
        return [item for item in grocery_list
                if keyword in item.name.lower()]

    elif field == "category":
        return [item for item in grocery_list
                if keyword in item.category.lower()]

    return []


def sort_items(grocery_list, sort_key):
    """
    sort_key: "name", "price", "quantity", "category", "status"
    """
    if sort_key == "name":
        return sorted(grocery_list, key=lambda item: item.name.lower())

    elif sort_key == "price":
        return sorted(grocery_list, key=lambda item: item.price)

    elif sort_key == "quantity":
        return sorted(grocery_list, key=lambda item: item.quantity)

    elif sort_key == "category":
        return sorted(grocery_list, key=lambda item: item.category.lower())

    elif sort_key == "status":
        return sorted(grocery_list, key=lambda item: item.is_bought(), reverse=True)

    return grocery_list


def export_to_csv(grocery_list, filename, filter_type="all"):
    """
    filter_type: "all", "bought", "pending"
    """
    if filter_type == "bought":
        data = [item for item in grocery_list if item.is_bought()]
    elif filter_type == "pending":
        data = [item for item in grocery_list if not item.is_bought()]
    else:
        data = grocery_list

    if not data:
        raise ValueError("No data available for export.")

    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "Name", "Category", "Quantity", "Price", "Total", "Status"
        ])

        for item in data:
            writer.writerow([
                item.name,
                item.category,
                item.quantity,
                item.price,
                item.get_total_value(),
                "Bought" if item.is_bought() else "Pending"
            ])