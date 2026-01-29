#!/usr/bin/env python3
"""
Stock Itching - 股票價格監控系統
主程式入口
"""
import os
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv

# 將 src 目錄加入 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.alert_manager import AlertManager
from src.scheduler import StockMonitorScheduler
from src.stock_fetcher import StockFetcher
from src.telegram_bot import TelegramBotHandler
from src.utils import setup_logging


class StockItchingApp:
    """股票監控應用程式"""

    def __init__(self):
        """初始化應用程式"""
        # 載入環境變數
        load_dotenv()

        # 取得環境變數
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.watchlist_file = os.getenv("WATCHLIST_FILE", "config/watchlist.json")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_dir = os.getenv("LOG_DIR", "logs")

        # 安全地轉換環境變數為整數
        try:
            self.check_interval = int(os.getenv("CHECK_INTERVAL_MINUTES", "5"))
        except ValueError:
            self.check_interval = 5
            print("⚠️ CHECK_INTERVAL_MINUTES 無效，使用預設值 5")

        try:
            self.retry_attempts = int(os.getenv("RETRY_ATTEMPTS", "3"))
        except ValueError:
            self.retry_attempts = 3
            print("⚠️ RETRY_ATTEMPTS 無效，使用預設值 3")

        try:
            self.retry_delay = int(os.getenv("RETRY_DELAY_SECONDS", "5"))
        except ValueError:
            self.retry_delay = 5
            print("⚠️ RETRY_DELAY_SECONDS 無效，使用預設值 5")

        # 驗證必要參數
        if not self.telegram_token or self.telegram_token == "your_bot_token_here":
            print("❌ 錯誤：未設定 TELEGRAM_BOT_TOKEN")
            print("請複製 .env.example 為 .env 並填入你的 Telegram Bot Token")
            sys.exit(1)

        # 設定日誌系統
        setup_logging(self.log_dir, self.log_level)

        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 60)
        self.logger.info("Stock Itching 股票監控系統啟動")
        self.logger.info("=" * 60)

        # 初始化模組
        self.alert_manager = None
        self.stock_fetcher = None
        self.telegram_handler = None
        self.scheduler = None

    def initialize_modules(self):
        """初始化各個模組"""
        self.logger.info("初始化模組...")

        # 初始化監控管理器
        self.alert_manager = AlertManager(self.watchlist_file)

        # 初始化股票查詢器
        self.stock_fetcher = StockFetcher(
            retry_attempts=self.retry_attempts,
            retry_delay=self.retry_delay
        )

        # 初始化 Telegram Bot
        self.telegram_handler = TelegramBotHandler(
            token=self.telegram_token,
            alert_manager=self.alert_manager,
            stock_fetcher=self.stock_fetcher
        )

        # 初始化排程器
        self.scheduler = StockMonitorScheduler(
            alert_manager=self.alert_manager,
            stock_fetcher=self.stock_fetcher,
            telegram_handler=self.telegram_handler,
            check_interval_minutes=self.check_interval
        )

        self.logger.info("模組初始化完成")

    def setup_signal_handlers(self):
        """設定信號處理器用於優雅關閉"""
        def signal_handler(sig, frame):
            self.logger.info(f"收到信號 {sig}，正在優雅關閉...")
            self.shutdown()
            # 移除 sys.exit(0)，讓 shutdown 自然完成

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        self.logger.info("信號處理器已設定")

    def start(self):
        """啟動應用程式"""
        try:
            # 初始化模組
            self.initialize_modules()

            # 設定信號處理器
            self.setup_signal_handlers()

            # 啟動排程器
            self.scheduler.start()

            # 顯示啟動資訊
            next_check = self.scheduler.get_next_run_time()
            self.logger.info("系統啟動成功！")
            self.logger.info(f"監控清單檔案: {self.watchlist_file}")
            self.logger.info(f"檢查間隔: {self.check_interval} 分鐘")
            if next_check:
                self.logger.info(f"下次檢查時間: {next_check}")
            self.logger.info("按 Ctrl+C 可安全停止程式")
            self.logger.info("-" * 60)

            # 啟動 Telegram Bot（阻塞運行）
            self.telegram_handler.run()

        except Exception as e:
            self.logger.error(f"啟動失敗: {e}", exc_info=True)
            self.shutdown()
            sys.exit(1)

    def shutdown(self):
        """優雅關閉"""
        self.logger.info("正在關閉應用程式...")

        try:
            # 停止排程器
            if self.scheduler:
                self.scheduler.stop()

            # 停止 Telegram Bot
            if self.telegram_handler:
                self.telegram_handler.stop()

            # 儲存監控清單
            if self.alert_manager:
                self.alert_manager.save()

            self.logger.info("應用程式已安全關閉")

        except Exception as e:
            self.logger.error(f"關閉過程發生錯誤: {e}", exc_info=True)


def main():
    """主函數"""
    app = StockItchingApp()
    app.start()


if __name__ == "__main__":
    main()
