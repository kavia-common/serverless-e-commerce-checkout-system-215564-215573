"""
Models package initializer to ensure convenient imports.
"""
# Re-export commonly used models for convenience
from .product import Product, Inventory  # noqa: F401
from .order import Order, OrderItem, StripeEvent  # noqa: F401
