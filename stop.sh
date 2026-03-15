#!/bin/bash
# Stop BTBG server and motors
cd "$(dirname "$0")"

echo "Stopping motors..."
python3 -c "
try:
    from picarx import Picarx
    px = Picarx()
    px.stop()
    print('  Motors stopped')
except Exception as e:
    print(f'  Skipped: {e}')
" 2>/dev/null

echo "Stopping server..."
pkill -f "python3 -m robot.server" 2>/dev/null
pkill -f "python3.*server.main" 2>/dev/null
sleep 1

if pgrep -f "server.main" > /dev/null 2>&1; then
    echo "Force killing..."
    pkill -9 -f "server.main"
fi

echo "BTBG stopped."
