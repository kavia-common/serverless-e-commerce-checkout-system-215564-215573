"""
Seed script to populate the database with initial demo products and inventory.

Usage:
    python -m app.seed
"""
from .db import session_scope, init_db
from .models.product import Product, Inventory


def _seed_products():
    demo_products = [
        {
            "sku": "TSHIRT-BLUE-001",
            "name": "Blue T-Shirt",
            "description": "Comfortable cotton t-shirt in ocean blue.",
            "price_cents": 1999,
            "currency": "usd",
            "image_url": "https://picsum.photos/seed/blue-shirt/600/400",
        },
        {
            "sku": "MUG-AMBER-001",
            "name": "Amber Coffee Mug",
            "description": "Ceramic mug with amber accent handle.",
            "price_cents": 1299,
            "currency": "usd",
            "image_url": "https://picsum.photos/seed/amber-mug/600/400",
        },
        {
            "sku": "HOODIE-NAVY-001",
            "name": "Navy Hoodie",
            "description": "Cozy hoodie with minimalist design.",
            "price_cents": 4599,
            "currency": "usd",
            "image_url": "https://picsum.photos/seed/navy-hoodie/600/400",
        },
    ]

    with session_scope() as s:
        for p in demo_products:
            existing = s.query(Product).filter(Product.sku == p["sku"]).one_or_none()
            if existing:
                continue
            product = Product(**p)
            s.add(product)
            s.flush()
            s.add(Inventory(product_id=product.id, quantity=50, low_stock_threshold=5))


def main():
    init_db(create_all=True)
    _seed_products()
    print("Database seeded successfully.")


if __name__ == "__main__":
    main()
