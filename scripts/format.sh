#!/bin/sh
set -e
echo "formatting..."
python -m ruff format pytest_gather_fixtures tests
echo "sorting import with ruff..."
python -m ruff check pytest_gather_fixtures tests --select I,F401 --fix --show-fixes
# run lint as a convenience
sh scripts/lint.sh