#!/bin/bash
set -e
cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"/../

echo "=== test.sh ==="

echo "- Start Python checks"

echo "- isort: start"
python -m isort --check-only src/thc_devops_toolkit
echo "- isort: done"

echo "- black: start"
python -m black --check src/thc_devops_toolkit
echo "- black: done"

echo "- docformatter: start"
python -m docformatter -c -r src/thc_devops_toolkit
echo "- docformatter:  done"

echo "- ruff: start"
python -m ruff check src/thc_devops_toolkit
echo "- ruff: done"

echo "- mypy: start"
python -m mypy src/thc_devops_toolkit
echo "- mypy: done"

echo "- pylint: start"
python -m pylint src/thc_devops_toolkit
echo "- pylint: done"

echo "- flake8: start"
python -m flake8 src/thc_devops_toolkit
echo "- flake8: done"

echo "- pytest: start"
python -m pytest --cov=src/thc_devops_toolkit --disable-warnings
echo "- pytest: done"

echo "- All Python checks passed"
