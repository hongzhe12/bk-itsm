#!/usr/bin/env bash

set -e
cd "$(dirname "$0")"
source .venv/bin/activate
export PATH="${NVM_DIR:-$HOME/.nvm}/versions/node/v16.20.2/bin:$PATH"

pids=()
python manage.py runserver 0.0.0.0:8000 & pids+=($!)
python manage.py celery worker -l info -B & pids+=($!)
(cd frontend/pc && npm run dev) & pids+=($!)

trap 'kill "${pids[@]}" 2>/dev/null' EXIT INT TERM
wait
