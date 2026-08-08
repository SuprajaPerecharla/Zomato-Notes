#!/usr/bin/env bash
# install.sh — sets up the backend virtualenv correctly on any Python version
set -e

PYTHON=${PYTHON:-python3}
PY_VER=$($PYTHON -c "import sys; print(sys.version_info[:2])")

echo "Using $PYTHON (version $PY_VER)"
$PYTHON -m venv .venv
source .venv/bin/activate

pip install --upgrade pip --quiet

# pydantic-core doesn't yet have a stable wheel for Python 3.14+;
# install the latest pre-release in that case.
if $PYTHON -c "import sys; sys.exit(0 if sys.version_info >= (3,14) else 1)" 2>/dev/null; then
  echo "Python 3.14+ detected — installing pydantic pre-release …"
  pip install --pre pydantic pydantic-settings --quiet
fi

pip install -r requirements.txt --quiet
echo "Backend dependencies installed."
echo "Run:  uvicorn app.main:app --reload --port 8000"
