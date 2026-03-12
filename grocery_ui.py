import streamlit as st
from storage import load_history, save_history, CURRENCY
from inventory_client import (
    is_api_available,
    search_products,
    get_all_products,
    check_stock,
    deduct_stock
)
from models import GroceryItem
from datetime import datetime

# -------------------------
# PAGE CONFIG
# -------------------------

st.set_page_config(page_title="Grocery App", page_icon="🛒", layout="centered")

# -------------------------
# SESSION STATE
# -------------------------

if "cart" not in st.session_state:
    st.session_state.cart = []

# -------------------------
# SIDEBAR NAVIGATION
# -------------------------

st.sidebar.title("🛒 Grocery App")
page = st.sidebar.radio("Navigate", ["Browse & Add", "My Cart", "Purchase History"])

# API status in sidebar
if is_api_available():
    st.sidebar.success("✅ Inventory API connected")
else:
    st.sidebar.error("❌ Inventory API not available")

cart_count = len([i for i in st.session_state.cart if not i.is_bought()])
st.sidebar.markdown(f"**Items in cart: {cart_count}**")

# -------------------------
# PAGE 1 — BROWSE & ADD
# -------------------------

if page == "Browse & Add":
    st.title("Browse Products")

    if not is_api_available():
        st.error("Inventory API is not available. Cannot browse products.")
    else:
        # Browse options
        browse_mode = st.radio("Browse by", ["Search by name", "Browse by price", "Browse all"], horizontal=True)

        if browse_mode == "Search by name":
            keyword = st.text_input("Search product")
            if keyword:
                results = search_products(keyword.lower())
            else:
                results = []

        elif browse_mode == "Browse by price":
            results = sorted(get_all_products(), key=lambda p: p["price_per_unit"])

        else:
            results = get_all_products()

        if not results and browse_mode == "Search by name":
            if keyword:
                st.warning("No products found.")

        for product in results:
            col1, col2, col3 = st.columns([3, 2, 2])

            with col1:
                st.markdown(f"**{product['name'].title()}**")
                st.caption(f"{CURRENCY}{product['price_per_unit']} each")

            with col2:
                if product["stock"] > 0:
                    st.success(f"In stock ({product['stock']})")
                else:
                    st.error("Out of stock")

            with col3:
                if product["stock"] > 0:
                    qty = st.number_input(
                        "Qty",
                        min_value=1,
                        max_value=product["stock"],
                        value=1,
                        key=f"qty_{product['sku']}"
                    )
                    if st.button("Add to cart", key=f"add_{product['sku']}"):
                        # Check if already in cart as pending
                        existing = next(
                            (item for item in st.session_state.cart
                             if item.name == product["name"] and not item.is_bought()),
                            None
                        )
                        if existing:
                            if check_stock(product["sku"], existing.quantity + qty):
                                existing.increase_quantity(qty)
                                st.success(f"Updated {product['name'].title()} quantity to {existing.quantity}")
                            else:
                                st.error(f"Not enough stock.")
                        else:
                            if check_stock(product["sku"], qty):
                                item = GroceryItem(
                                    name=product["name"],
                                    quantity=qty,
                                    price=product["price_per_unit"],
                                    sku=product["sku"]
                                )
                                st.session_state.cart.append(item)
                                st.success(f"✅ {product['name'].title()} added to cart!")
                            else:
                                st.error("Not enough stock.")

            st.divider()

# -------------------------
# PAGE 2 — CART & CHECKOUT
# -------------------------

elif page == "My Cart":
    st.title("My Cart")

    pending = [item for item in st.session_state.cart if not item.is_bought()]

    if not pending:
        st.info("Your cart is empty. Go browse some products!")
    else:
        total = 0

        for i, item in enumerate(pending):
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.markdown(f"**{item.name.title()}**")
                st.caption(f"{CURRENCY}{item.price} each x {item.quantity}")

            with col2:
                item_total = item.get_total_value()
                total += item_total
                st.markdown(f"**{CURRENCY}{item_total:.2f}**")

            with col3:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.cart.remove(item)
                    st.rerun()

            st.divider()

        st.markdown(f"### Total: {CURRENCY}{total:.2f}")

        st.markdown("---")

        if st.button("✅ Checkout", type="primary", use_container_width=True):
            if not is_api_available():
                st.error("Inventory API is not available. Cannot checkout.")
            else:
                # Check stock for all items
                out_of_stock = []
                for item in pending:
                    if item.sku and not check_stock(item.sku, item.quantity):
                        out_of_stock.append(item.name)

                if out_of_stock:
                    st.error(f"Not enough stock for: {', '.join(out_of_stock)}")
                else:
                    # Deduct stock
                    failed = []
                    for item in pending:
                        if item.sku:
                            result = deduct_stock(item.sku, item.quantity)
                            if "error" in result:
                                failed.append(item.name)
                                continue
                        item.mark_as_bought()

                    # Save to history
                    history = load_history()
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

                    # Clear cart
                    st.session_state.cart = [item for item in st.session_state.cart if not item.is_bought()]

                    if failed:
                        st.warning(f"Could not process: {', '.join(failed)}")

                    st.success(f"✅ Purchase confirmed! Total: {CURRENCY}{total:.2f}")
                    st.balloons()

# -------------------------
# PAGE 3 — PURCHASE HISTORY
# -------------------------

elif page == "Purchase History":
    st.title("Purchase History")

    history = load_history()

    if not history:
        st.info("No purchase history yet.")
    else:
        for i, order in enumerate(reversed(history), start=1):
            with st.expander(f"Order {len(history) - i + 1} — {order['date'][:10]} | {CURRENCY}{order['total']:.2f}"):
                for item in order["items"]:
                    st.markdown(f"- **{item['name'].title()}** x{item['quantity']} — {CURRENCY}{item['total']:.2f}")
                st.markdown(f"**Order Total: {CURRENCY}{order['total']:.2f}**")