#!/bin/sh
set -e
coverage run --branch --include="pytest_gather_fixtures/*" -m pytest tests/unittests
coverage html
coverage report -m
coverage xml