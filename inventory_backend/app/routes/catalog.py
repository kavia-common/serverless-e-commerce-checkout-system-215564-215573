from flask_smorest import Blueprint, abort
from flask.views import MethodView
from sqlalchemy import select
from ..db import session_scope
from ..models.product import Product, Inventory
from ..schemas import ProductSchema, InventorySchema, InventoryUpdateSchema

blp = Blueprint(
    "Catalog & Inventory",
    "catalog",
    url_prefix="",
    description="Product catalog and inventory management",
)

@blp.route("/products")
class ProductsList(MethodView):
    """
    PUBLIC_INTERFACE
    get:
        Get list of active products.
    """
    @blp.response(200, ProductSchema(many=True))
    def get(self):
        """Return all active products."""
        with session_scope() as s:
            products = s.execute(select(Product).where(Product.active == True)).scalars().all()  # noqa: E712
            return products

@blp.route("/products/<int:product_id>")
class ProductDetail(MethodView):
    """
    PUBLIC_INTERFACE
    get:
        Get a single product by ID.
    """
    @blp.response(200, ProductSchema)
    def get(self, product_id: int):
        """Return single product details."""
        with session_scope() as s:
            product = s.get(Product, product_id)
            if not product or not product.active:
                abort(404, message="Product not found")
            return product

@blp.route("/inventory/<int:product_id>")
class InventoryDetail(MethodView):
    """
    PUBLIC_INTERFACE
    get:
        Get inventory for a product.
    patch:
        Update inventory for a product.
    """
    @blp.response(200, InventorySchema)
    def get(self, product_id: int):
        """Return inventory for a product ID."""
        with session_scope() as s:
            inv = s.execute(select(Inventory).where(Inventory.product_id == product_id)).scalars().first()
            if not inv:
                abort(404, message="Inventory not found for product")
            return inv

    @blp.arguments(InventoryUpdateSchema)
    @blp.response(200, InventorySchema)
    def patch(self, payload, product_id: int):
        """Update inventory quantities."""
        with session_scope() as s:
            inv = s.execute(select(Inventory).where(Inventory.product_id == product_id)).scalars().first()
            if not inv:
                abort(404, message="Inventory not found for product")
            inv.quantity = payload.get("quantity", inv.quantity)
            if payload.get("low_stock_threshold") is not None:
                inv.low_stock_threshold = payload["low_stock_threshold"]
            s.add(inv)
            s.flush()
            return inv
