#!/usr/bin/env python3
"""測試 alert_manager.py 模組"""
import os
import tempfile
import threading
import time
import unittest

from src.alert_manager import AlertManager


class TestAlertManager(unittest.TestCase):
    """測試監控管理功能"""

    def setUp(self):
        """測試前準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_watchlist.json")
        self.manager = AlertManager(self.test_file)

    def tearDown(self):
        """測試後清理"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_add_alert(self):
        """測試新增監控"""
        alert = self.manager.add_alert(
            user_id=123,
            symbol="AAPL",
            target_price=150.0,
            condition="above"
        )

        self.assertIsNotNone(alert)
        self.assertEqual(alert["user_id"], 123)
        self.assertEqual(alert["symbol"], "AAPL")
        self.assertEqual(alert["target_price"], 150.0)
        self.assertEqual(alert["condition"], "above")
        self.assertFalse(alert["notified"])
        self.assertTrue(alert["enabled"])

    def test_add_alert_invalid_condition(self):
        """測試無效的條件"""
        with self.assertRaises(ValueError):
            self.manager.add_alert(
                user_id=123,
                symbol="AAPL",
                target_price=150.0,
                condition="invalid"
            )

    def test_list_alerts(self):
        """測試列出監控"""
        # 新增兩個監控
        self.manager.add_alert(123, "AAPL", 150.0, "above")
        self.manager.add_alert(123, "GOOGL", 140.0, "below")

        # 列出監控
        alerts = self.manager.list_alerts(123)
        self.assertEqual(len(alerts), 2)

    def test_list_alerts_user_isolation(self):
        """測試用戶隔離"""
        # 用戶 123 新增監控
        self.manager.add_alert(123, "AAPL", 150.0, "above")

        # 用戶 456 新增監控
        self.manager.add_alert(456, "GOOGL", 140.0, "below")

        # 用戶 123 只能看到自己的
        alerts_123 = self.manager.list_alerts(123)
        self.assertEqual(len(alerts_123), 1)
        self.assertEqual(alerts_123[0]["symbol"], "AAPL")

        # 用戶 456 只能看到自己的
        alerts_456 = self.manager.list_alerts(456)
        self.assertEqual(len(alerts_456), 1)
        self.assertEqual(alerts_456[0]["symbol"], "GOOGL")

    def test_remove_alert(self):
        """測試移除監控"""
        # 新增監控
        alert = self.manager.add_alert(123, "AAPL", 150.0, "above")
        alert_id = alert["id"]

        # 移除監控
        result = self.manager.remove_alert(123, alert_id)
        self.assertTrue(result)

        # 確認已移除
        alerts = self.manager.list_alerts(123)
        self.assertEqual(len(alerts), 0)

    def test_remove_alert_wrong_user(self):
        """測試無法移除其他用戶的監控"""
        # 用戶 123 新增監控
        alert = self.manager.add_alert(123, "AAPL", 150.0, "above")
        alert_id = alert["id"]

        # 用戶 456 嘗試移除
        result = self.manager.remove_alert(456, alert_id)
        self.assertFalse(result)

        # 確認監控仍存在
        alerts = self.manager.list_alerts(123)
        self.assertEqual(len(alerts), 1)

    def test_clear_all_alerts(self):
        """測試清空所有監控"""
        # 新增多個監控
        self.manager.add_alert(123, "AAPL", 150.0, "above")
        self.manager.add_alert(123, "GOOGL", 140.0, "below")
        self.manager.add_alert(123, "MSFT", 300.0, "above")

        # 清空
        count = self.manager.clear_all_alerts(123)
        self.assertEqual(count, 3)

        # 確認已清空
        alerts = self.manager.list_alerts(123)
        self.assertEqual(len(alerts), 0)

    def test_clear_alerts_by_symbol(self):
        """測試清空指定股票監控"""
        # 新增多個監控，包括同一股票的多個條件
        self.manager.add_alert(123, "AAPL", 150.0, "above")
        self.manager.add_alert(123, "AAPL", 140.0, "below")
        self.manager.add_alert(123, "GOOGL", 140.0, "below")

        # 清空 AAPL
        count = self.manager.clear_alerts_by_symbol(123, "AAPL")
        self.assertEqual(count, 2)

        # 確認只剩 GOOGL
        alerts = self.manager.list_alerts(123)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["symbol"], "GOOGL")

    def test_get_all_symbols(self):
        """測試取得所有股票代碼"""
        # 新增多個監控
        self.manager.add_alert(123, "AAPL", 150.0, "above")
        self.manager.add_alert(456, "AAPL", 140.0, "below")  # 重複的
        self.manager.add_alert(123, "GOOGL", 140.0, "below")

        symbols = self.manager.get_all_symbols()

        # 應該去重
        self.assertEqual(len(symbols), 2)
        self.assertIn("AAPL", symbols)
        self.assertIn("GOOGL", symbols)

    def test_check_alerts_trigger_above(self):
        """測試觸發條件：above"""
        # 新增監控：AAPL 高於 150
        self.manager.add_alert(123, "AAPL", 150.0, "above")

        # 模擬價格資料
        current_prices = {
            "AAPL": {
                "symbol": "AAPL",
                "price": 155.0,  # 高於 150
                "currency": "USD",
                "success": True
            }
        }

        # 檢查觸發
        triggered = self.manager.check_alerts(current_prices)

        self.assertEqual(len(triggered), 1)
        self.assertEqual(triggered[0]["alert"]["symbol"], "AAPL")
        self.assertEqual(triggered[0]["current_price"], 155.0)

    def test_check_alerts_trigger_below(self):
        """測試觸發條件：below"""
        # 新增監控：AAPL 低於 150
        self.manager.add_alert(123, "AAPL", 150.0, "below")

        # 模擬價格資料
        current_prices = {
            "AAPL": {
                "symbol": "AAPL",
                "price": 145.0,  # 低於 150
                "currency": "USD",
                "success": True
            }
        }

        # 檢查觸發
        triggered = self.manager.check_alerts(current_prices)

        self.assertEqual(len(triggered), 1)

    def test_check_alerts_no_trigger(self):
        """測試未觸發"""
        # 新增監控：AAPL 高於 150
        self.manager.add_alert(123, "AAPL", 150.0, "above")

        # 模擬價格資料：未達標
        current_prices = {
            "AAPL": {
                "symbol": "AAPL",
                "price": 145.0,  # 低於 150
                "currency": "USD",
                "success": True
            }
        }

        # 檢查觸發
        triggered = self.manager.check_alerts(current_prices)

        self.assertEqual(len(triggered), 0)

    def test_check_alerts_no_duplicate_notification(self):
        """測試防重複通知"""
        # 新增監控
        self.manager.add_alert(123, "AAPL", 150.0, "above")

        # 第一次觸發
        current_prices = {
            "AAPL": {
                "symbol": "AAPL",
                "price": 155.0,
                "currency": "USD",
                "success": True
            }
        }
        triggered = self.manager.check_alerts(current_prices)
        self.assertEqual(len(triggered), 1)

        # 第二次觸發（應該不會重複通知）
        triggered = self.manager.check_alerts(current_prices)
        self.assertEqual(len(triggered), 0)

    def test_check_alerts_reset_notification(self):
        """測試重置通知標記"""
        # 新增監控：AAPL 高於 150
        self.manager.add_alert(123, "AAPL", 150.0, "above")

        # 第一次觸發
        current_prices = {
            "AAPL": {
                "symbol": "AAPL",
                "price": 155.0,
                "currency": "USD",
                "success": True
            }
        }
        self.manager.check_alerts(current_prices)

        # 價格回到安全範圍（150 - 2% = 147）
        current_prices["AAPL"]["price"] = 146.0
        self.manager.check_alerts(current_prices)

        # 再次觸發（應該可以通知）
        current_prices["AAPL"]["price"] = 155.0
        triggered = self.manager.check_alerts(current_prices)
        self.assertEqual(len(triggered), 1)

    def test_persistence(self):
        """測試資料持久化"""
        # 新增監控
        alert = self.manager.add_alert(123, "AAPL", 150.0, "above")
        alert_id = alert["id"]

        # 建立新的 manager（重新載入）
        new_manager = AlertManager(self.test_file)

        # 確認資料被載入
        alerts = new_manager.list_alerts(123)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["id"], alert_id)


class TestAlertManagerConcurrency(unittest.TestCase):
    """測試並發安全性"""

    def setUp(self):
        """測試前準備"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_watchlist.json")
        self.manager = AlertManager(self.test_file)

    def tearDown(self):
        """測試後清理"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_concurrent_add_alerts(self):
        """測試並發新增監控"""
        def add_alerts(user_id, count):
            for i in range(count):
                self.manager.add_alert(
                    user_id=user_id,
                    symbol=f"STOCK{i}",
                    target_price=100.0,
                    condition="above"
                )

        # 啟動多個線程
        threads = []
        for user_id in range(1, 4):  # 3 個用戶
            t = threading.Thread(target=add_alerts, args=(user_id, 5))
            threads.append(t)
            t.start()

        # 等待所有線程完成
        for t in threads:
            t.join()

        # 驗證結果：每個用戶應該有 5 個監控
        for user_id in range(1, 4):
            alerts = self.manager.list_alerts(user_id)
            self.assertEqual(len(alerts), 5)

    def test_concurrent_remove_alerts(self):
        """測試並發移除監控"""
        # 先新增一些監控
        alert_ids = []
        for i in range(10):
            alert = self.manager.add_alert(123, f"STOCK{i}", 100.0, "above")
            alert_ids.append(alert["id"])

        # 並發移除
        def remove_alerts(ids):
            for alert_id in ids:
                self.manager.remove_alert(123, alert_id)

        # 將 IDs 分成兩組
        mid = len(alert_ids) // 2
        t1 = threading.Thread(target=remove_alerts, args=(alert_ids[:mid],))
        t2 = threading.Thread(target=remove_alerts, args=(alert_ids[mid:],))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # 驗證所有監控都被移除
        alerts = self.manager.list_alerts(123)
        self.assertEqual(len(alerts), 0)


if __name__ == "__main__":
    unittest.main()
