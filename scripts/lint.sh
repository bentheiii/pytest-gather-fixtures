#!/bin/sh
# run various linters
set -e
# linting is disabled until we introduce ruff to this project
#echo "running isort..."
#python -m isort . -c
#echo "running flake8..."
#poetry run flake8 --max-line-length 120 pytest_gather_fixtures tests
echo "running mypy..."
python3 -m mypy --show-error-codes pytest_gather_fixtures
