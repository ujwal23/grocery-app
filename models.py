from datetime import datetime


class GroceryItem:
    def __init__(self, name, quantity, price, category="General", bought=False):

        # --- Validation ---
        if not name.strip():
            raise ValueError("Item name cannot be empty.")
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if price < 0:
            raise ValueError("Price cannot be negative.")

        # --- Store on object ---
        self.name = name.strip()
        self.quantity = quantity
        self.price = price
        self.category = category.strip() or "General"
        self.bought = bought
        self.created_at = datetime.now().isoformat()

    # -------- Instance Methods --------

    def get_total_value(self):
        """Returns total cost: quantity × price."""
        return self.quantity * self.price

    def increase_quantity(self, amount):
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        self.quantity += amount

    def decrease_quantity(self, amount):
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        if amount >= self.quantity:
            raise ValueError("Cannot decrease by more than current quantity.")
        self.quantity -= amount

    def toggle_bought(self):
        """Flips bought status between True and False."""
        self.bought = not self.bought

    def is_bought(self):
        return self.bought

    # -------- Serialization --------

    def to_dict(self):
        """Converts item to a plain dict for JSON storage."""
        return {
            "name": self.name,
            "quantity": self.quantity,
            "price": self.price,
            "category": self.category,
            "bought": self.bought,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a GroceryItem from a dict (used when loading from JSON)."""
        item = cls(
            name=data["name"],
            quantity=data["quantity"],
            price=data["price"],
            category=data.get("category", "General"),
            bought=data.get("bought", False)
        )
        item.created_at = data.get("created_at", datetime.now().isoformat())
        return item