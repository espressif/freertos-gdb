#!/bin/bash
set -eo pipefail

PUBLISHED_VERSION=$(curl https://pypi.org/pypi/freertos-gdb/json 2>/dev/null | jq -r '.info.version')
CURRENT_VERSION=$(python setup.py --version 2>/dev/null)

if [ "$PUBLISHED_VERSION" == "$CURRENT_VERSION" ]; then
  echo "Version ${PUBLISHED_VERSION} already published, skipping..."
else
  echo "Packaging and publishing new version: ${CURRENT_VERSION}"
  rm -rf dist
  python setup.py sdist bdist_wheel
  twine upload dist/*
fi
