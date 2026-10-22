#!/bin/bash
# Dev server for the browser suites. Usage: tests/browser/start_server.sh [port]
# Writes the PID to /tmp/ceo.pid; stop it with: kill "$(cat /tmp/ceo.pid)"
# (never put this command line into a pkill pattern - it would match the caller).
cd "$(dirname "$0")/../.."
PORT="${1:-5001}"
if [ -f /tmp/ceo.pid ] && kill -0 "$(cat /tmp/ceo.pid)" 2>/dev/null; then kill "$(cat /tmp/ceo.pid)"; sleep 1; fi
nohup .venv/bin/python -c "from gw2ceo.app import app; app.run(port=$PORT)" > /tmp/ceo.log 2>&1 &
echo $! > /tmp/ceo.pid
for _ in $(seq 1 40); do
  curl -s -o /dev/null "http://127.0.0.1:$PORT/" && echo "server up on $PORT (pid $(cat /tmp/ceo.pid))" && exit 0
  sleep 0.5
done
echo "server did not start"; tail -5 /tmp/ceo.log; exit 1
