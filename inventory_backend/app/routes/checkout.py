import json
import os
from typing import List, Dict

from flask import request
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from sqlalchemy import select

from ..db import session_scope
from ..models.order import Order, OrderItem, StripeEvent
from ..models.product import Product, Inventory
from ..schemas import CheckoutSessionRequestSchema, CheckoutSessionResponseSchema

# Lazy import stripe to avoid import errors if not installed at import-time
try:
    import stripe  # type: ignore
except Exception:  # pragma: no cover
    stripe = None

blp = Blueprint(
    "Checkout & Stripe",
    "checkout",
    url_prefix="",
    description="Checkout session creation and Stripe webhook handling",
)


def _get_stripe_client():
    """Create and return the Stripe client configured from env."""
    if stripe is None:
        abort(500, message="Stripe SDK not installed. Please install 'stripe' package.")
    secret_key = os.getenv("STRIPE_SECRET_KEY")
    if not secret_key:
        abort(500, message="STRIPE_SECRET_KEY is not configured.")
    stripe.api_key = secret_key
    return stripe


def _get_site_url() -> str:
    """Resolve site URL for redirect success/cancel."""
    # The orchestrator will set SITE_URL in env; fallback to localhost for dev.
    return os.getenv("SITE_URL", "http://localhost:3000")


def _build_line_items(items: List[Dict]) -> List[Dict]:
    """Build Stripe line_items verifying product, price, and inventory."""
    line_items = []
    with session_scope() as s:
        for it in items:
            product_id = it["id"]
            quantity = int(it["quantity"])
            product = s.get(Product, product_id)
            if not product or not product.active:
                abort(400, message=f"Invalid product {product_id}")
            inv = s.execute(select(Inventory).where(Inventory.product_id == product_id)).scalars().first()
            if not inv or inv.quantity < quantity:
                abort(400, message=f"Insufficient inventory for product {product.sku}")
            line_items.append({
                "quantity": quantity,
                "price_data": {
                    "currency": product.currency,
                    "unit_amount": product.price_cents,
                    "product_data": {
                        "name": product.name,
                        "metadata": {"product_id": str(product.id), "sku": product.sku},
                        "images": [product.image_url] if product.image_url else [],
                    },
                },
            })
    return line_items


@blp.route("/checkout/session")
class CheckoutSession(MethodView):
    """
    PUBLIC_INTERFACE
    post:
        Create a Stripe Checkout Session for provided items.
    """
    @blp.arguments(CheckoutSessionRequestSchema)
    @blp.response(201, CheckoutSessionResponseSchema)
    def post(self, payload):
        """Create checkout session and provisional order record."""
        items = payload["items"]
        email = payload.get("email")

        if not items:
            abort(400, message="No items provided")

        # Build stripe line items and validate inventory
        line_items = _build_line_items(items)

        # Prepare success/cancel redirect URLs
        site_url = _get_site_url()
        success_url = f"{site_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{site_url}/checkout/cancel"

        client = _get_stripe_client()
        try:
            session = client.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=line_items,
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=email if email else None,
                automatic_tax={"enabled": False},
            )
        except Exception as e:
            abort(502, message=f"Stripe error: {str(e)}")

        # Create provisional order for tracking
        subtotal = 0
        with session_scope() as s:
            order = Order(
                status="pending",
                customer_email=email,
                stripe_checkout_session_id=session.id,
                subtotal_cents=0,
                total_cents=0,
                tax_cents=0,
                shipping_cents=0,
                currency="usd",
            )
            s.add(order)
            s.flush()
            for it in items:
                product = s.get(Product, it["id"])
                if not product:
                    continue
                oi = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    sku=product.sku,
                    name=product.name,
                    unit_price_cents=product.price_cents,
                    quantity=int(it["quantity"]),
                    currency=product.currency,
                )
                subtotal += product.price_cents * int(it["quantity"])
                s.add(oi)
            order.subtotal_cents = subtotal
            order.total_cents = subtotal  # no taxes/shipping in demo
            s.add(order)
        return {"checkout_session_id": session.id, "checkout_url": session.url}, 201


@blp.route("/webhooks/stripe", methods=["POST"])
class StripeWebhook(MethodView):
    """
    PUBLIC_INTERFACE
    post:
        Handle Stripe webhook events to confirm payment and adjust inventory.
    """
    def post(self):
        """Validate event using Stripe signature and update orders/inventory."""
        client = _get_stripe_client()
        endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        payload = request.get_data()
        sig_header = request.headers.get("Stripe-Signature")

        if endpoint_secret:
            try:
                event = client.Webhook.construct_event(
                    payload=payload, sig_header=sig_header, secret=endpoint_secret
                )
            except Exception as e:
                abort(400, message=f"Webhook signature verification failed: {str(e)}")
        else:
            # Unsigned (dev) - parse payload as JSON
            try:
                event = json.loads(payload.decode("utf-8"))
            except Exception:
                abort(400, message="Invalid JSON payload")
            if isinstance(event, dict) and "type" not in event:
                abort(400, message="Invalid event format")

        event_id = event.get("id")
        event_type = event.get("type")

        # Idempotency: store event if not seen
        with session_scope() as s:
            seen = s.execute(select(StripeEvent).where(StripeEvent.event_id == event_id)).scalars().first()
            if not seen:
                s.add(StripeEvent(event_id=event_id, type=event_type, payload=json.dumps(event)[:10000]))

        # Handle completed checkout session
        if event_type == "checkout.session.completed":
            data_obj = event.get("data", {}).get("object", {})
            session_id = data_obj.get("id")
            payment_intent = data_obj.get("payment_intent")

            # Update order status and decrement inventory
            with session_scope() as s:
                order = s.execute(
                    select(Order).where(Order.stripe_checkout_session_id == session_id)
                ).scalars().first()
                if order:
                    order.status = "paid"
                    order.stripe_payment_intent_id = payment_intent
                    s.add(order)
                    # decrement inventory
                    for item in order.items:
                        inv = s.execute(
                            select(Inventory).where(
                                Inventory.product_id == item.product_id
                            )
                        ).scalars().first()
                        if inv:
                            inv.quantity = max(0, inv.quantity - item.quantity)
                            s.add(inv)
        elif event_type in {"checkout.session.expired", "payment_intent.payment_failed"}:
            # Mark orders as canceled/failed
            data_obj = event.get("data", {}).get("object", {})
            session_id = data_obj.get("id") or data_obj.get("checkout_session")
            with session_scope() as s:
                order = s.execute(
                    select(Order).where(
                        Order.stripe_checkout_session_id == session_id
                    )
                ).scalars().first()
                if order:
                    order.status = "canceled"
                    s.add(order)

        return {"received": True}
