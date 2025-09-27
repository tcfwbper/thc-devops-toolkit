#!/bin/bash
set -e
cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"/../

# Python
python -m isort src/thc_devops_toolkit
python -m black -q src/thc_devops_toolkit
python -m docformatter -i -r src/thc_devops_toolkit
python -m ruff check --fix src/thc_devops_toolkit
