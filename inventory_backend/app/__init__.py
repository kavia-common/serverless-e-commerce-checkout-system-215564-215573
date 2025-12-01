from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

from .routes.health import blp as health_blp
from .routes.catalog import blp as catalog_blp
from .routes.checkout import blp as checkout_blp
from .db import init_db

app = Flask(__name__)
app.url_map.strict_slashes = False
# CORS configuration: allow all origins for demo; in production restrict to frontend domain
CORS(app, resources={r"/*": {"origins": "*"}})

# OpenAPI / API Docs metadata
app.config["API_TITLE"] = "Inventory & Checkout API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

# Initialize API and register blueprints
api = Api(app)

# Initialize Database and create tables on startup
init_db(create_all=True)

# Register routes
api.register_blueprint(health_blp)
api.register_blueprint(catalog_blp)
api.register_blueprint(checkout_blp)
