#!/bin/sh

# Exit immediately if a simple command exits with a nonzero exit value
set -e

docker build -t pythonunittests .
docker-compose run --rm main
