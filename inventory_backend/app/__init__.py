from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

from .routes.health import blp
from .db import init_db

app = Flask(__name__)
app.url_map.strict_slashes = False
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
api.register_blueprint(blp)
