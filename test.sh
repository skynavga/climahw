#!/bin/bash

echo "python -m black --check climahw"
python -m black --check climahw
echo "python -m pylint climahw"
python -m pylint climahw
echo "python -m mypy climahw"
python -m mypy climahw
echo "python -m unittest discover -v climahw"
python -m unittest discover -v climahw
