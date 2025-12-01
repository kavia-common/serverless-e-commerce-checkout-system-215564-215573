# serverless-e-commerce-checkout-system-215564-215573

Inventory backend (Flask) - Quick Start

1) Install dependencies
   cd inventory_backend
   pip install --no-input --upgrade pip
   pip install --no-input -r requirements.txt

Note: requirements.txt already includes flask-cors (correct casing: flask-cors). If you encounter an ImportError for flask_cors, ensure you installed requirements in the active virtual environment.

2) Start the server (preferred)
   python run.py

- This binds to 0.0.0.0:3001 and disables the reloader to suit preview/CI.
- Avoid using "flask run" unless FLASK_APP is exported. If you must use flask run, set:
   export FLASK_APP=app
   export FLASK_RUN_HOST=0.0.0.0
   export FLASK_RUN_PORT=3001
   flask run

3) Health check
   curl -i http://localhost:3001/
   Expected: HTTP/1.1 200 OK with JSON {"message": "Healthy"}

OpenAPI/Docs:
- After starting the server, interactive docs are available under /docs (Swagger UI).
- The OpenAPI JSON is available at /openapi.json.

Environment configuration:
- Do not hardcode configuration. Use environment variables:
  - DATABASE_URL (defaults to sqlite:///./inventory.db if unset)
  - STRIPE_SECRET_KEY (required for checkout endpoints)
  - STRIPE_WEBHOOK_SECRET (optional for signed webhook verification)
  - SITE_URL (used for checkout redirect URLs; defaults to http://localhost:3000)