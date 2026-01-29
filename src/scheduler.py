"""背景任務排程器模組"""
import logging
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .alert_manager import AlertManager
from .stock_fetcher import StockFetcher
from .telegram_bot import TelegramBotHandler


class StockMonitorScheduler:
    """股票監控排程器"""

    def __init__(
        self,
        alert_manager: AlertManager,
        stock_fetcher: StockFetcher,
        telegram_handler: TelegramBotHandler,
        check_interval_minutes: int = 5
    ):
        """
        初始化排程器

        Args:
            alert_manager: 監控管理器
            stock_fetcher: 股票查詢器
            telegram_handler: Telegram Bot 處理器
            check_interval_minutes: 檢查間隔（分鐘）
        """
        self.alert_manager = alert_manager
        self.stock_fetcher = stock_fetcher
        self.telegram_handler = telegram_handler
        self.check_interval_minutes = check_interval_minutes
        self.logger = logging.getLogger(__name__)
        self.scheduler = BackgroundScheduler()

    def check_all_stocks(self):
        """
        主要檢查邏輯：查詢所有監控股票並發送通知
        """
        try:
            self.logger.info("=" * 50)
            self.logger.info("開始檢查所有監控股票")

            # 1. 取得所有需要監控的股票代碼
            symbols = self.alert_manager.get_all_symbols()

            if not symbols:
                self.logger.info("目前沒有任何監控，跳過檢查")
                return

            self.logger.info(f"需要檢查 {len(symbols)} 個股票: {', '.join(symbols)}")

            # 2. 批次查詢所有股票價格
            current_prices = self.stock_fetcher.get_multiple_prices(symbols)

            # 記錄查詢結果
            success_count = sum(
                1 for info in current_prices.values() if info.get("success")
            )
            self.logger.info(f"成功查詢 {success_count}/{len(symbols)} 個股票")

            # 3. 檢查是否有監控被觸發
            triggered_alerts = self.alert_manager.check_alerts(current_prices)

            if not triggered_alerts:
                self.logger.info("沒有監控被觸發")
            else:
                self.logger.info(f"有 {len(triggered_alerts)} 個監控被觸發")

                # 4. 發送通知（使用 asyncio 因為 telegram 是異步的）
                for alert_info in triggered_alerts:
                    user_id = alert_info["alert"]["user_id"]

                    # 安全地運行異步函數
                    try:
                        # 嘗試獲取現有事件循環
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # 如果循環正在運行，創建任務
                                asyncio.create_task(
                                    self.telegram_handler.send_alert(user_id, alert_info)
                                )
                            else:
                                # 如果循環未運行，直接運行
                                loop.run_until_complete(
                                    self.telegram_handler.send_alert(user_id, alert_info)
                                )
                        except RuntimeError:
                            # 沒有事件循環，創建新的
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(
                                self.telegram_handler.send_alert(user_id, alert_info)
                            )
                    except Exception as e:
                        self.logger.error(
                            f"發送通知失敗 (用戶 {user_id}): {e}"
                        )

            self.logger.info("檢查完成")
            self.logger.info("=" * 50)

        except Exception as e:
            self.logger.error(f"檢查過程發生錯誤: {e}", exc_info=True)

    def start(self):
        """啟動排程器"""
        self.logger.info(
            f"啟動排程器 - 每 {self.check_interval_minutes} 分鐘檢查一次"
        )

        # 立即執行一次檢查
        self.logger.info("執行初始檢查...")
        self.check_all_stocks()

        # 設定定時任務
        self.scheduler.add_job(
            func=self.check_all_stocks,
            trigger=IntervalTrigger(minutes=self.check_interval_minutes),
            id="stock_check",
            name="檢查股票價格",
            replace_existing=True
        )

        # 啟動排程器
        self.scheduler.start()
        self.logger.info("排程器已啟動")

    def stop(self):
        """停止排程器"""
        self.logger.info("正在停止排程器...")

        if self.scheduler.running:
            # 等待當前任務完成
            self.scheduler.shutdown(wait=True)
            self.logger.info("排程器已停止")

    def get_next_run_time(self):
        """取得下次執行時間"""
        job = self.scheduler.get_job("stock_check")
        if job:
            return job.next_run_time
        return None
