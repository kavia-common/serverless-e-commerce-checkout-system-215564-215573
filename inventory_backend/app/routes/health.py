from flask_smorest import Blueprint
from flask.views import MethodView

blp = Blueprint("Health", "health", url_prefix="/", description="Health check route")

@blp.route("/")
class HealthCheck(MethodView):
    """PUBLIC_INTERFACE: Simple health probe endpoint returning 200 OK with a JSON payload."""
    def get(self):
        """Return a simple health status."""
        return {"message": "Healthy"}, 200
