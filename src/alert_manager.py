"""監控警報管理模組"""
import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from .utils import generate_alert_id, load_json, save_json

# 定義緩衝區比例常數
BUFFER_PERCENTAGE = 0.02  # 2% 緩衝區
MIN_BUFFER_VALUE = 0.5  # 最小緩衝值


class AlertManager:
    """監控清單管理類別"""

    def __init__(self, watchlist_file: str):
        """
        初始化監控管理器

        Args:
            watchlist_file: 監控清單 JSON 檔案路徑
        """
        self.watchlist_file = watchlist_file
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()  # 可重入鎖，避免死鎖
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """載入監控清單資料"""
        default_data = {
            "alerts": [],
            "last_check": None
        }
        data = load_json(self.watchlist_file, default_data)
        self.logger.info(f"載入監控清單: {len(data.get('alerts', []))} 個監控")
        return data

    def save(self) -> bool:
        """儲存監控清單到檔案（線程安全）"""
        with self._lock:
            self.data["last_check"] = datetime.now().isoformat()
            success = save_json(self.watchlist_file, self.data)
            if success:
                self.logger.debug("監控清單已儲存")
            return success

    def add_alert(
        self,
        user_id: int,
        symbol: str,
        target_price: float,
        condition: str
    ) -> Dict[str, Any]:
        """
        新增監控

        Args:
            user_id: Telegram 用戶 ID
            symbol: 股票代碼
            target_price: 目標價格
            condition: 條件 ('above' 或 'below')

        Returns:
            新增的監控資訊
        """
        if condition not in ["above", "below"]:
            raise ValueError(f"無效的條件: {condition}，必須是 'above' 或 'below'")

        with self._lock:
            alert = {
                "id": generate_alert_id(),
                "user_id": user_id,
                "symbol": symbol.upper(),
                "target_price": float(target_price),
                "condition": condition,
                "created_at": datetime.now().isoformat(),
                "notified": False,
                "last_notified_at": None,
                "enabled": True
            }

            self.data["alerts"].append(alert)
            self.save()

            self.logger.info(
                f"新增監控: 用戶 {user_id} | {symbol} | "
                f"{condition} {target_price} | ID: {alert['id']}"
            )

            return alert

    def remove_alert(self, user_id: int, alert_id: str) -> bool:
        """
        移除監控

        Args:
            user_id: Telegram 用戶 ID
            alert_id: 監控 ID

        Returns:
            是否移除成功
        """
        with self._lock:
            original_count = len(self.data["alerts"])

            # 只能移除自己的監控
            self.data["alerts"] = [
                alert for alert in self.data["alerts"]
                if not (alert["id"] == alert_id and alert["user_id"] == user_id)
            ]

            removed = len(self.data["alerts"]) < original_count

            if removed:
                self.save()
                self.logger.info(f"移除監控: 用戶 {user_id} | ID: {alert_id}")
            else:
                self.logger.warning(f"找不到監控或無權限: 用戶 {user_id} | ID: {alert_id}")

            return removed

    def list_alerts(self, user_id: int) -> List[Dict]:
        """
        列出用戶的所有監控

        Args:
            user_id: Telegram 用戶 ID

        Returns:
            監控列表
        """
        user_alerts = [
            alert for alert in self.data["alerts"]
            if alert["user_id"] == user_id and alert["enabled"]
        ]

        self.logger.debug(f"用戶 {user_id} 有 {len(user_alerts)} 個監控")
        return user_alerts

    def get_all_symbols(self) -> List[str]:
        """
        取得所有啟用的監控股票代碼（去重）

        Returns:
            股票代碼列表
        """
        symbols = set()
        for alert in self.data["alerts"]:
            if alert["enabled"]:
                symbols.add(alert["symbol"])

        return list(symbols)

    def check_alerts(self, current_prices: Dict[str, Dict]) -> List[Dict]:
        """
        檢查所有監控，返回需要通知的清單

        Args:
            current_prices: 當前價格字典，格式 {symbol: price_info}

        Returns:
            需要通知的監控列表，每個元素包含 alert 和 current_price
        """
        triggered_alerts = []

        for alert in self.data["alerts"]:
            if not alert["enabled"]:
                continue

            symbol = alert["symbol"]
            price_info = current_prices.get(symbol)

            # 如果查詢失敗，跳過
            if not price_info or not price_info.get("success"):
                self.logger.warning(f"跳過檢查 {symbol}：無價格資訊")
                continue

            current_price = price_info["price"]
            target_price = alert["target_price"]
            condition = alert["condition"]

            # 檢查是否觸發條件
            triggered = False
            if condition == "above" and current_price >= target_price:
                triggered = True
            elif condition == "below" and current_price <= target_price:
                triggered = True

            # 如果觸發且尚未通知
            if triggered and not alert["notified"]:
                self.logger.info(
                    f"觸發監控: {symbol} | {condition} {target_price} | "
                    f"當前: {current_price}"
                )

                triggered_alerts.append({
                    "alert": alert,
                    "current_price": current_price,
                    "currency": price_info.get("currency", "USD")
                })

                # 標記為已通知
                alert["notified"] = True
                alert["last_notified_at"] = datetime.now().isoformat()

            # 檢查是否應重置通知標記（價格回到安全範圍）
            elif alert["notified"]:
                # 計算緩衝區，使用常數並設置最小值
                buffer = max(target_price * BUFFER_PERCENTAGE, MIN_BUFFER_VALUE)

                reset = False
                if condition == "above" and current_price < (target_price - buffer):
                    reset = True
                elif condition == "below" and current_price > (target_price + buffer):
                    reset = True

                if reset:
                    self.logger.info(
                        f"重置監控通知標記: {symbol} | 當前: {current_price}"
                    )
                    alert["notified"] = False

        # 儲存更新
        if triggered_alerts:
            self.save()

        return triggered_alerts

    def get_alert_by_id(self, alert_id: str) -> Optional[Dict]:
        """
        根據 ID 取得監控

        Args:
            alert_id: 監控 ID

        Returns:
            監控資訊，找不到則返回 None
        """
        for alert in self.data["alerts"]:
            if alert["id"] == alert_id:
                return alert
        return None

    def clear_all_alerts(self, user_id: int) -> int:
        """
        清空用戶的所有監控

        Args:
            user_id: Telegram 用戶 ID

        Returns:
            清除的監控數量
        """
        with self._lock:
            original_count = len([
                alert for alert in self.data["alerts"]
                if alert["user_id"] == user_id
            ])

            # 移除該用戶的所有監控
            self.data["alerts"] = [
                alert for alert in self.data["alerts"]
                if alert["user_id"] != user_id
            ]

            if original_count > 0:
                self.save()
                self.logger.info(f"清空用戶 {user_id} 的 {original_count} 個監控")

            return original_count

    def clear_alerts_by_symbol(self, user_id: int, symbol: str) -> int:
        """
        清空用戶指定股票的所有監控

        Args:
            user_id: Telegram 用戶 ID
            symbol: 股票代碼

        Returns:
            清除的監控數量
        """
        with self._lock:
            symbol = symbol.upper()

            original_count = len([
                alert for alert in self.data["alerts"]
                if alert["user_id"] == user_id and alert["symbol"] == symbol
            ])

            # 移除該用戶指定股票的所有監控
            self.data["alerts"] = [
                alert for alert in self.data["alerts"]
                if not (alert["user_id"] == user_id and alert["symbol"] == symbol)
            ]

            if original_count > 0:
                self.save()
                self.logger.info(
                    f"清空用戶 {user_id} 的 {symbol} 監控，共 {original_count} 個"
                )

            return original_count
