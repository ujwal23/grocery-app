import requests

BASE_URL = "http://127.0.0.1:8000"


def get_all_products():
    """Fetch all products from Inventory API."""
    try:
        response = requests.get(f"{BASE_URL}/products")
        return response.json()
    except requests.exceptions.ConnectionError:
        print("Warning: Inventory API is not available.")
        return []


def search_products(keyword):
    """Search products by name keyword."""
    products = get_all_products()
    return [p for p in products if keyword.lower() in p["name"].lower()]


def get_product_by_sku(sku):
    """Fetch a single product by SKU."""
    try:
        response = requests.get(f"{BASE_URL}/products/{sku}")
        data = response.json()
        if "error" in data:
            return None
        return data
    except requests.exceptions.ConnectionError:
        print("Warning: Inventory API is not available.")
        return None


def check_stock(sku, quantity_needed):
    """
    Check if a product has enough stock.
    Returns True if stock is sufficient, False otherwise.
    """
    product = get_product_by_sku(sku)
    if not product:
        return False
    return product["stock"] >= quantity_needed


def deduct_stock(sku, amount):
    """
    Deduct stock from Inventory API after checkout.
    Called once per item when customer confirms purchase.
    """
    try:
        response = requests.patch(
            f"{BASE_URL}/products/{sku}/stock",
            json={"amount": amount, "operation": "decrease"}
        )
        return response.json()
    except requests.exceptions.ConnectionError:
        print("Warning: Inventory API is not available.")
        return {"error": "API unavailable"}


def is_api_available():
    """Check if Inventory API is running."""
    try:
        requests.get(f"{BASE_URL}/")
        return True
    except requests.exceptions.ConnectionError:
        return False