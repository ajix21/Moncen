#!/usr/bin/env bash
cd "$(dirname "$0")"

_kill_pid() {
    local pidfile="$1"
    local name="$2"
    if [ -f "$pidfile" ]; then
        local pid
        pid=$(cat "$pidfile")
        kill "$pid" 2>/dev/null && echo "$name dihentikan (PID: $pid)" || echo "$name tidak berjalan"
        rm -f "$pidfile"
    else
        echo "$name: tidak berjalan"
    fi
}

_kill_pid /tmp/semar-cv.pid "CV Engine"
_kill_pid /tmp/semar-dashboard.pid "Dashboard"
_kill_pid /tmp/semar-frontend.pid "Frontend"
echo "Semua service dihentikan."
