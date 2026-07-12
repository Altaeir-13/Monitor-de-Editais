#!/bin/sh
set -eu

if [ "$#" -gt 0 ]; then
    exec "$@"
fi

workers="${UVICORN_WORKERS:-1}"
case "$workers" in
    ''|*[!0-9]*)
        echo "UVICORN_WORKERS must be a positive integer." >&2
        exit 64
        ;;
esac
if [ "$workers" -lt 1 ]; then
    echo "UVICORN_WORKERS must be a positive integer." >&2
    exit 64
fi

case "${CRAWLER_SCHEDULER_ENABLED:-false}" in
    true|TRUE|True|1|yes|YES|on|ON)
        if [ "$workers" -ne 1 ]; then
            echo "The crawler scheduler requires exactly one Uvicorn worker." >&2
            exit 64
        fi
        ;;
esac

exec uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "$workers" \
    --proxy-headers \
    --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}" \
    --log-level "${LOG_LEVEL:-info}"
