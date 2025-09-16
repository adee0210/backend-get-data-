#!/bin/bash

# Script để quản lý backend FastAPI cho funding rate
# Chạy trên server 192.168.110.164, port 8010 
# Sử dụng: ./run.sh [start|stop|restart]

PID_FILE="server.pid"
LOG_FILE="main.log"

# Hàm start server
start_server() {
    echo "Khởi động FastAPI server trên 192.168.110.164:8010..."

    # Kiểm tra xem virtual environment có tồn tại không
    if [ -d ".venv" ]; then
        echo "Kích hoạt virtual environment..."
        source .venv/bin/activate
    fi

    # Kiểm tra xem server đã chạy chưa
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Server đã đang chạy với PID: $PID"
            return 1
        else
            rm "$PID_FILE"
        fi
    fi

    # Chạy uvicorn với nohup
    nohup .venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8010 >> "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"

    echo "Server đã khởi động trong background. PID: $PID"
    echo "Logs: $LOG_FILE"
    echo "API docs: http://0.0.0.0:8010/docs"
}

# Hàm stop server
stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Dừng server với PID: $PID"
            kill "$PID"
            sleep 2
            if kill -0 "$PID" 2>/dev/null; then
                echo "Buộc dừng server..."
                kill -9 "$PID"
            fi
            rm "$PID_FILE"
            echo "Server đã dừng."
        else
            echo "Server không đang chạy."
            rm "$PID_FILE"
        fi
    else
        echo "Không tìm thấy file PID. Server có thể không đang chạy."
    fi
}

# Hàm restart server
restart_server() {
    echo "Khởi động lại server..."
    stop_server
    sleep 2
    start_server
}

# Logic chính
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
        echo "Cách sử dụng: $0 [start|stop|restart]"
        echo "Mặc định: start"
        exit 1
        ;;
esac