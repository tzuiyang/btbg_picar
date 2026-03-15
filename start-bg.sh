#!/bin/bash
# Start BTBG server in background
cd "$(dirname "$0")"

if pgrep -f "python3 -m robot.server" > /dev/null; then
    echo "BTBG already running (PID: $(pgrep -f 'python3 -m robot.server'))"
    exit 0
fi

mkdir -p ~/btbg_logs
echo "Starting BTBG server in background..."
nohup python3 -m robot.server --port 9090 > ~/btbg_logs/btbg.log 2>&1 &
echo "PID: $!"
echo "Logs: tail -f ~/btbg_logs/btbg.log"

# Wait for port
for i in $(seq 1 10); do
    sleep 1
    if ss -tlnp 2>/dev/null | grep -q 9090; then
        IP=$(hostname -I | awk '{print $1}')
        echo ""
        echo "BTBG running on ws://$IP:9090"
        exit 0
    fi
done
echo "WARNING: Server may not have started. Check logs."
