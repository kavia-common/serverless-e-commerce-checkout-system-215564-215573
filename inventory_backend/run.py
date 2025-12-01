from app import app

if __name__ == "__main__":
    # Bind to 0.0.0.0 so the container is accessible externally and use port 3001 per project spec
    # Disable debug and reloader in preview/CI environments to avoid forking processes
    app.run(host="0.0.0.0", port=3001, debug=False, use_reloader=False)
