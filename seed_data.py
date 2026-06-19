"""
seed_data.py
------------
Generates a realistic sample dataset for the Inventory Management System:
- 8 suppliers
- ~40 products across 6 categories (a Zepto/quick-commerce style catalog)
- 90 days of randomized sales history, with some products selling fast
  (to feed "top sellers"), some slow (to feed "stale products"), and a
  handful deliberately pushed below their reorder level (to feed
  "low stock alerts" and "reorder recommendations").

Run this file directly (`python seed_data.py`) or call seed_all() from
the app's sidebar "Reset Sample Data" button.
"""

import random
from datetime import datetime, timedelta

from database import init_db, reset_database, get_connection
import inventory
import sales as sales_module


SUPPLIERS = [
    ("FreshFarm Distributors", "+91-9810012345", "contact@freshfarm.in"),
    ("Daily Needs Wholesale", "+91-9820023456", "sales@dailyneeds.in"),
    ("Metro Grocery Supplies", "+91-9830034567", "info@metrogrocery.in"),
    ("QuickStock Logistics", "+91-9840045678", "orders@quickstock.in"),
    ("Urban Pantry Co.", "+91-9850056789", "hello@urbanpantry.in"),
    ("GreenLeaf Produce", "+91-9860067890", "support@greenleaf.in"),
    ("HomeEssentials Ltd.", "+91-9870078901", "care@homeessentials.in"),
    ("SnackWorld Traders", "+91-9880089012", "biz@snackworld.in"),
]

# (ProductName, Category, Price, ReorderLevel, supplier_index, base_demand)
# base_demand drives how fast each item sells in the simulated history --
# this is what creates believable "fast movers" vs "slow movers".
PRODUCTS = [
    ("Amul Toned Milk 500ml", "Dairy", 28, 40, 0, 9.0),
    ("Amul Butter 100g", "Dairy", 58, 30, 0, 6.0),
    ("Mother Dairy Curd 400g", "Dairy", 45, 25, 0, 5.0),
    ("Britannia Cheese Slices", "Dairy", 120, 20, 0, 3.0),
    ("Paneer 200g", "Dairy", 90, 20, 5, 4.0),

    ("Tomato 1kg", "Vegetables", 30, 50, 5, 8.5),
    ("Onion 1kg", "Vegetables", 35, 50, 5, 8.0),
    ("Potato 1kg", "Vegetables", 25, 50, 5, 7.5),
    ("Spinach Bunch", "Vegetables", 20, 25, 5, 3.5),
    ("Carrot 500g", "Vegetables", 22, 25, 5, 3.0),
    ("Capsicum 500g", "Vegetables", 28, 20, 5, 2.5),

    ("Banana Dozen", "Fruits", 50, 30, 5, 6.0),
    ("Apple 1kg (Shimla)", "Fruits", 140, 25, 5, 4.0),
    ("Mango 1kg (Alphonso)", "Fruits", 220, 15, 5, 2.0),
    ("Papaya 1pc", "Fruits", 35, 15, 5, 2.0),
    ("Pomegranate 500g", "Fruits", 80, 15, 5, 1.5),

    ("Tata Salt 1kg", "Staples", 25, 40, 1, 4.0),
    ("Fortune Sunflower Oil 1L", "Staples", 145, 30, 1, 5.0),
    ("India Gate Basmati Rice 1kg", "Staples", 95, 30, 1, 4.5),
    ("Aashirvaad Atta 5kg", "Staples", 245, 20, 1, 3.5),
    ("Toor Dal 1kg", "Staples", 130, 20, 1, 3.0),
    ("Sugar 1kg", "Staples", 45, 35, 1, 4.0),

    ("Lay's Classic Salted 52g", "Snacks", 20, 60, 7, 10.0),
    ("Kurkure Masala Munch 90g", "Snacks", 20, 50, 7, 7.0),
    ("Oreo Biscuits 120g", "Snacks", 35, 40, 7, 5.5),
    ("Parle-G Biscuits 200g", "Snacks", 25, 50, 7, 6.0),
    ("Maggi Noodles 70g (pack of 4)", "Snacks", 56, 45, 7, 8.0),
    ("Bingo Mad Angles 72g", "Snacks", 20, 30, 7, 3.0),

    ("Coca-Cola 750ml", "Beverages", 40, 35, 3, 6.0),
    ("Real Mixed Fruit Juice 1L", "Beverages", 110, 20, 3, 2.5),
    ("Tata Tea Premium 250g", "Beverages", 130, 25, 3, 3.5),
    ("Nescafe Classic Coffee 50g", "Beverages", 180, 20, 3, 2.0),
    ("Bisleri Water 1L (pack of 6)", "Beverages", 90, 30, 3, 5.0),

    ("Surf Excel Detergent 1kg", "Household", 135, 20, 6, 2.5),
    ("Vim Dishwash Liquid 500ml", "Household", 95, 20, 6, 2.0),
    ("Harpic Toilet Cleaner 500ml", "Household", 99, 15, 6, 1.5),
    ("Colgate Toothpaste 150g", "Household", 89, 25, 6, 3.0),
    ("Dettol Soap (pack of 4)", "Household", 150, 20, 6, 2.0),
    ("Good Knight Mosquito Repellent", "Household", 75, 15, 6, 1.0),
]


def seed_suppliers():
    ids = []
    for name, phone, email in SUPPLIERS:
        sid = inventory.add_supplier(name, phone, email)
        ids.append(sid)
    return ids


def seed_products(supplier_ids):
    """Adds all products, with starting stock set deliberately to create a
    realistic mix: some healthy, some right at/under reorder level."""
    product_map = []  # (ProductID, base_demand, price)
    for name, category, price, reorder_level, supplier_idx, base_demand in PRODUCTS:
        # ~20% of products start already low on stock, for immediate demo value
        if random.random() < 0.2:
            starting_stock = max(0, reorder_level - random.randint(0, 5))
        else:
            starting_stock = reorder_level + random.randint(10, 60)

        supplier_id = supplier_ids[supplier_idx]
        pid = inventory.add_product(
            product_name=name,
            category=category,
            price=price,
            current_stock=starting_stock,
            reorder_level=reorder_level,
            supplier_id=supplier_id,
        )
        product_map.append((pid, base_demand, price))
    return product_map


def seed_sales_history(product_map, days=90, stale_product_count=4):
    """
    Simulates `days` days of sales (ending TODAY, so recency-based analytics
    like "low stock in last 30 days" behave correctly) using a randomized
    walk around each product's base_demand, with weekend seasonality.

    This models a real store that gets restocked regularly -- sales history
    is demand data, independent of the CurrentStock snapshot set in
    seed_products(). That snapshot already encodes today's stock picture
    (including the deliberately-low-stock items), so this function does not
    touch CurrentStock at all.

    To make the "products with no sales in 30 days" business question
    demonstrable, a handful of products (stale_product_count) are chosen to
    have their sales history artificially cut off more than 30 days ago.
    """
    today = datetime.now().date()
    start_date = today - timedelta(days=days)

    # Pick a few low-demand products to act as deliberately "stale" (no
    # recent sales) for a reliable demo of that business question.
    sorted_by_demand = sorted(product_map, key=lambda x: x[1])
    stale_ids = {pid for pid, _, _ in sorted_by_demand[:stale_product_count]}

    all_sales_rows = []

    for pid, base_demand, price in product_map:
        is_stale = pid in stale_ids
        # Stale products stop selling 35-50 days ago; everyone else sells
        # all the way up through yesterday.
        last_sale_offset = random.randint(35, 50) if is_stale else 0
        sale_end_day = days - last_sale_offset

        for day_offset in range(sale_end_day):
            sale_date = start_date + timedelta(days=day_offset)
            weekday = sale_date.weekday()  # 0=Mon ... 6=Sun
            weekend_multiplier = 1.4 if weekday >= 5 else 1.0

            daily_qty = max(0, round(random.gauss(base_demand * weekend_multiplier, base_demand * 0.4)))
            if daily_qty <= 0:
                continue

            all_sales_rows.append({
                "ProductID": pid,
                "QuantitySold": int(daily_qty),
                "SaleDate": sale_date.strftime("%Y-%m-%d"),
                "UnitPriceAtSale": price,
            })

    sales_module.bulk_record_sales(all_sales_rows)
    return len(all_sales_rows)


def seed_all(verbose: bool = True):
    """Resets the database and populates it with fresh sample data."""
    reset_database()
    supplier_ids = seed_suppliers()
    product_map = seed_products(supplier_ids)
    n_sales = seed_sales_history(product_map, days=90)

    if verbose:
        print(f"Seeded {len(supplier_ids)} suppliers, {len(product_map)} products, "
              f"{n_sales} sales records.")


if __name__ == "__main__":
    init_db()
    seed_all()
