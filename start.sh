#!/bin/bash
# Start BTBG server
cd "$(dirname "$0")"

# Check if already running
if pgrep -f "python3 -m robot.server" > /dev/null; then
    echo "BTBG already running (PID: $(pgrep -f 'python3 -m robot.server'))"
    echo "Stop first: ./stop.sh"
    exit 0
fi

mkdir -p ~/btbg_logs

echo "Starting BTBG server..."
python3 -m robot.server --port 9090 2>&1 | tee ~/btbg_logs/btbg.log
