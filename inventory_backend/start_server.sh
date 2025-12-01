#!/usr/bin/env bash
set -euo pipefail

# Ensure we're in the inventory_backend directory
cd "$(dirname "$0")"

# Create venv if not exists
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# Activate venv
# shellcheck disable=SC1091
. ./.venv/bin/activate

# Upgrade pip and install requirements
python -V
pip install --no-input --upgrade pip
pip install --no-input -r requirements.txt

# Preferred: start via python run.py (binds 0.0.0.0:3001)
if [ -f "run.py" ]; then
  echo "Starting Flask app via python run.py on 0.0.0.0:3001"
  exec python run.py
fi

# Fallback: flask run if run.py is not found or preview strictly uses flask run
export FLASK_APP=app
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=3001
echo "Starting Flask app via flask run on 0.0.0.0:3001"
exec flask run
