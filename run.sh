#!/bin/bash

# Script để quản lý backend FastAPI cho funding rate
# Chạy trên server 192.168.110.164, port 8010 
# Sử dụng: ./run.sh [start|stop|restart]

PID_FILE="server.pid"
LOG_FILE="main.log"

# Hàm start server
start_server() {
    echo "Starting FastAPI server on 192.168.110.164:8010..."

    # Kiểm tra xem virtual environment có tồn tại không
    if [ -d ".venv" ]; then
        echo "Activating virtual environment..."
        source .venv/bin/activate
    fi

    # Kiểm tra xem server đã chạy chưa
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Server is already running with PID: $PID"
            return 1
        else
            rm "$PID_FILE"
        fi
    fi

    # Chạy uvicorn với nohup
    nohup .venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8010 >> "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"

    echo "Server started in background. PID: $PID"
    echo "Logs: $LOG_FILE"
    echo "API docs: http://0.0.0.0/docs"
}

# Hàm stop server
stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Stopping server with PID: $PID"
            kill "$PID"
            sleep 2
            if kill -0 "$PID" 2>/dev/null; then
                echo "Force killing server..."
                kill -9 "$PID"
            fi
            rm "$PID_FILE"
            echo "Server stopped."
        else
            echo "Server is not running."
            rm "$PID_FILE"
        fi
    else
        echo "No PID file found. Server may not be running."
    fi
}

# Hàm restart server
restart_server() {
    echo "Restarting server..."
    stop_server
    sleep 2
    start_server
}

# Main logic
case "${1:-start}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    *)
        echo "Usage: $0 [start|stop|restart]"
        echo "Default: start"
        exit 1
        ;;
esac