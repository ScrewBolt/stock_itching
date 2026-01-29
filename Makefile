.PHONY: help install test run clean logs

help:
	@echo "Stock Itching - 股票監控系統"
	@echo ""
	@echo "可用命令："
	@echo "  make install    - 安裝依賴套件"
	@echo "  make test       - 執行基本測試"
	@echo "  make run        - 啟動系統"
	@echo "  make logs       - 查看日誌"
	@echo "  make clean      - 清理測試檔案"
	@echo ""

install:
	@echo "正在安裝依賴套件..."
	pip install -r requirements.txt
	@echo "安裝完成！"
	@echo "請記得設定 .env 檔案中的 TELEGRAM_BOT_TOKEN"

test:
	@echo "執行語法檢查..."
	python3 -m py_compile main.py src/*.py
	@echo "✓ 語法檢查通過"
	@echo ""
	@echo "測試股票查詢模組..."
	python3 test_stock_fetcher.py
	@echo ""
	@echo "測試監控管理模組..."
	python3 test_alert_manager.py
	@echo ""
	@echo "所有測試完成！"

run:
	@echo "啟動 Stock Itching..."
	python3 main.py

logs:
	@echo "=== 最近的應用程式日誌 ==="
	@tail -n 20 logs/app.log 2>/dev/null || echo "尚無日誌檔案"
	@echo ""
	@echo "=== 最近的錯誤日誌 ==="
	@tail -n 20 logs/error.log 2>/dev/null || echo "尚無錯誤日誌"

clean:
	@echo "清理測試檔案..."
	rm -f config/test_watchlist.json
	rm -rf src/__pycache__
	rm -rf __pycache__
	@echo "清理完成！"
