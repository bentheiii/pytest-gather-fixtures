#!/bin/sh
set -e
echo "running ruff..."
python -m ruff format pytest_gather_fixtures tests --check
python -m ruff check pytest_gather_fixtures tests
echo "running mypy..."
python3 -m mypy --show-error-codes pytest_gather_fixtures
