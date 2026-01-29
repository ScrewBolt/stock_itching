#!/bin/bash
# Stock Itching 自動重啟腳本

echo "🔄 重啟 Stock Itching 系統..."

# 1. 終止所有 main.py 進程（多次嘗試確保完全終止）
echo "📋 終止舊進程..."
for i in {1..3}; do
    pkill -9 -f "python.*main.py" 2>/dev/null
    sleep 1
    REMAINING=$(ps aux | grep "python.*main.py" | grep -v grep | wc -l | tr -d ' ')
    if [ "$REMAINING" -eq 0 ]; then
        echo "✅ 所有進程已終止"
        break
    fi
    echo "⚠️  嘗試 $i/3: 仍有 $REMAINING 個進程..."
done

# 2. 最後檢查
REMAINING=$(ps aux | grep "python.*main.py" | grep -v grep | wc -l | tr -d ' ')
if [ "$REMAINING" -gt 0 ]; then
    echo "⚠️  警告：仍有 $REMAINING 個進程未終止"
    echo "進程列表："
    ps aux | grep "python.*main.py" | grep -v grep
    echo ""
    read -p "是否強制終止所有進程？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null
        sleep 2
    else
        echo "❌ 已取消重啟"
        exit 1
    fi
fi

# 3. 啟動新進程
echo "🚀 啟動新進程..."
cd "$(dirname "$0")"
nohup python3 main.py > /dev/null 2>&1 &
NEW_PID=$!

sleep 3

# 4. 驗證新進程
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✅ 系統已成功啟動！"
    echo "   PID: $NEW_PID"
    echo ""
    echo "📊 查看即時日誌："
    echo "   tail -f logs/app.log"
    echo ""
    echo "🔍 檢查進程狀態："
    echo "   ps aux | grep main.py | grep -v grep"
    echo ""
    echo "🧪 測試 Bot 命令："
    echo "   /price 2330.TW"
    echo "   /add 2330.TW above 600"
else
    echo "❌ 啟動失敗！請檢查日誌："
    echo "   tail -50 logs/error.log"
    exit 1
fi
