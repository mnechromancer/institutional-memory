#!/usr/bin/env bash
# Start the HOLOCRON-9 live viz server.
# Sources .env for ANTHROPIC_API_KEY; the server itself strips the proxy.
set -euo pipefail
cd "$(dirname "$0")"
if [ -f .env ]; then set -a; . ./.env; set +a; fi
exec python3 viz_server.py
