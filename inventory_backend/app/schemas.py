from marshmallow import Schema, fields, validates, ValidationError


# PUBLIC_INTERFACE
class ProductSchema(Schema):
    """Schema for Product serialization."""
    id = fields.Int(dump_only=True, description="Product ID")
    sku = fields.Str(required=True, description="Stock keeping unit (unique)")
    name = fields.Str(required=True, description="Product name")
    description = fields.Str(allow_none=True, description="Product description")
    price_cents = fields.Int(required=True, description="Price in cents")
    currency = fields.Str(required=True, description="Currency code, e.g., usd")
    image_url = fields.Str(allow_none=True, description="Image URL")
    active = fields.Bool(missing=True, description="Whether product is active")


# PUBLIC_INTERFACE
class InventorySchema(Schema):
    """Schema for Inventory serialization."""
    id = fields.Int(dump_only=True)
    product_id = fields.Int(required=True, description="Product ID")
    quantity = fields.Int(required=True, description="Available quantity")
    low_stock_threshold = fields.Int(required=True, description="Low stock threshold")


# PUBLIC_INTERFACE
class OrderItemInputSchema(Schema):
    """Input schema for a single line item when creating checkout session."""
    id = fields.Int(required=True, description="Product ID")
    name = fields.Str(required=False, allow_none=True, description="Product name (optional; will be resolved)")
    price = fields.Int(required=False, allow_none=True, description="Unit price in cents (optional; will be resolved)")
    quantity = fields.Int(required=True, description="Quantity requested")

    @validates("quantity")
    def _validate_quantity(self, value: int):
        if value <= 0:
            raise ValidationError("quantity must be greater than 0")


# PUBLIC_INTERFACE
class CheckoutSessionRequestSchema(Schema):
    """Schema for incoming request to create a checkout session."""
    items = fields.List(fields.Nested(OrderItemInputSchema), required=True, description="List of items to purchase")
    email = fields.Email(required=False, allow_none=True, description="Customer email")


# PUBLIC_INTERFACE
class CheckoutSessionResponseSchema(Schema):
    """Schema for response with Stripe Checkout session info."""
    checkout_session_id = fields.Str(required=True, description="Stripe Checkout Session ID")
    checkout_url = fields.Str(required=True, description="URL for redirect to Stripe hosted checkout")


# PUBLIC_INTERFACE
class InventoryUpdateSchema(Schema):
    """Schema for updating inventory quantities."""
    quantity = fields.Int(required=True, description="New quantity for inventory")
    low_stock_threshold = fields.Int(required=False, allow_none=True, description="New low stock threshold")
