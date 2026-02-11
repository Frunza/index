#!/bin/sh

# Exit immediately if a simple command exits with a nonzero exit value
set -e

docker build -t pythonunittests .

if command -v docker-compose >/dev/null 2>&1; then
  docker-compose run --rm main
else
  docker compose run --rm main
fi
