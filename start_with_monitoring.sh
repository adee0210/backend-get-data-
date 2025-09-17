#!/bin/bash

# Script để chạy ứng dụng với monitoring
# Sử dụng: ./start_with_monitoring.sh

echo "🚀 Khởi động Crypto Data API với Monitoring System"
echo "================================================="

# Kiểm tra file .env
if [ ! -f ".env" ]; then
    echo "⚠️  File .env không tồn tại. Tạo từ .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Đã tạo file .env từ .env.example"
        echo "🔧 Vui lòng cấu hình Telegram Bot trong file .env"
    else
        echo "❌ File .env.example không tồn tại"
        exit 1
    fi
fi

# Kiểm tra và cài đặt dependencies
echo "📦 Kiểm tra dependencies..."
if [ ! -d ".venv" ]; then
    echo "🔧 Tạo virtual environment..."
    python3 -m venv .venv
fi

echo "🔧 Kích hoạt virtual environment..."
source .venv/bin/activate

echo "📥 Cài đặt/cập nhật dependencies..."
pip install -r requirements.txt

# Kiểm tra cấu hình Telegram
echo "🔍 Kiểm tra cấu hình Telegram..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if bot_token and chat_id and bot_token != 'your_bot_token_here':
    print('✅ Telegram đã được cấu hình')
else:
    print('⚠️  Telegram chưa được cấu hình đầy đủ')
    print('🔧 Vui lòng cập nhật TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID trong file .env')
"

echo ""
echo "🎯 Chọn chế độ chạy:"
echo "1. Chạy API Server (mặc định)"
echo "2. Test Monitoring System"
echo "3. Chạy API Server với port tùy chỉnh"

read -p "Nhập lựa chọn (1-3) [1]: " choice
choice=${choice:-1}

case $choice in
    1)
        echo "🚀 Khởi động API Server trên port 8000..."
        echo "📊 Monitoring system sẽ tự động khởi động"
        echo "📖 API Docs: http://localhost:8000/docs"
        echo "📈 Monitoring: http://localhost:8000/monitoring/funding_rate/status"
        echo ""
        uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
        ;;
    2)
        echo "🧪 Chạy test Monitoring System..."
        python test_monitoring.py
        ;;
    3)
        read -p "Nhập port (ví dụ: 8010): " port
        port=${port:-8010}
        echo "🚀 Khởi động API Server trên port $port..."
        echo "📖 API Docs: http://localhost:$port/docs"
        echo "📈 Monitoring: http://localhost:$port/monitoring/funding_rate/status"
        echo ""
        uvicorn src.main:app --reload --host 0.0.0.0 --port $port
        ;;
    *)
        echo "❌ Lựa chọn không hợp lệ"
        exit 1
        ;;
esac
