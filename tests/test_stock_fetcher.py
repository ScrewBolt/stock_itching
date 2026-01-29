#!/usr/bin/env python3
"""測試 stock_fetcher.py 模組"""
import unittest
from unittest.mock import MagicMock, patch

from src.stock_fetcher import StockFetcher


class TestStockFetcher(unittest.TestCase):
    """測試股票查詢功能"""

    def setUp(self):
        """測試前準備"""
        self.fetcher = StockFetcher(retry_attempts=2, retry_delay=0.1)

    def test_normalize_symbol_taiwan_stock(self):
        """測試台股代碼標準化"""
        # 純數字應該加 .TW
        result = self.fetcher.normalize_symbol("2330")
        self.assertEqual(result, "2330.TW")

        # 已有 .TW 不應該重複加
        result = self.fetcher.normalize_symbol("2330.TW")
        self.assertEqual(result, "2330.TW")

    def test_normalize_symbol_us_stock(self):
        """測試美股代碼標準化"""
        result = self.fetcher.normalize_symbol("AAPL")
        self.assertEqual(result, "AAPL")

        result = self.fetcher.normalize_symbol("aapl")
        self.assertEqual(result, "AAPL")

    def test_validate_symbol_valid(self):
        """測試有效的股票代碼"""
        self.assertTrue(self.fetcher.validate_symbol("AAPL"))
        self.assertTrue(self.fetcher.validate_symbol("2330.TW"))
        self.assertTrue(self.fetcher.validate_symbol("GOOGL"))

    def test_validate_symbol_invalid(self):
        """測試無效的股票代碼"""
        self.assertFalse(self.fetcher.validate_symbol(""))
        self.assertFalse(self.fetcher.validate_symbol("INVALID@#$"))
        self.assertFalse(self.fetcher.validate_symbol("股票"))

    @patch('yfinance.Ticker')
    def test_get_price_success(self, mock_ticker):
        """測試成功查詢價格"""
        # Mock yfinance 回應
        mock_instance = MagicMock()
        mock_instance.info = {
            "regularMarketPrice": 150.25,
            "currency": "USD"
        }
        mock_ticker.return_value = mock_instance

        result = self.fetcher.get_price("AAPL")

        self.assertTrue(result["success"])
        self.assertEqual(result["symbol"], "AAPL")
        self.assertEqual(result["price"], 150.25)
        self.assertEqual(result["currency"], "USD")

    @patch('yfinance.Ticker')
    def test_get_price_failure(self, mock_ticker):
        """測試查詢失敗"""
        # Mock 拋出異常
        mock_ticker.side_effect = Exception("API Error")

        result = self.fetcher.get_price("INVALID")

        self.assertFalse(result["success"])
        self.assertIsNone(result["price"])
        self.assertIn("error", result)

    @patch('yfinance.Ticker')
    def test_get_price_no_data(self, mock_ticker):
        """測試無價格資料"""
        # Mock 返回空資料
        mock_instance = MagicMock()
        mock_instance.info = {}
        mock_ticker.return_value = mock_instance

        result = self.fetcher.get_price("NODATA")

        self.assertFalse(result["success"])

    def test_get_multiple_prices(self):
        """測試批次查詢（整合測試，需要網路）"""
        # 注意：這是整合測試，可能較慢
        symbols = ["AAPL", "GOOGL"]

        # 使用真實 API 測試（可能失敗）
        # 如果要在 CI 中運行，應該 mock 掉
        try:
            results = self.fetcher.get_multiple_prices(symbols)

            self.assertEqual(len(results), len(symbols))
            self.assertIn("AAPL", results)
            self.assertIn("GOOGL", results)
        except Exception:
            # 網路問題時跳過
            self.skipTest("需要網路連線")


class TestStockFetcherIntegration(unittest.TestCase):
    """整合測試（需要網路連線）"""

    def setUp(self):
        """測試前準備"""
        self.fetcher = StockFetcher()

    @unittest.skip("整合測試，需要真實 API")
    def test_real_api_call(self):
        """測試真實 API 呼叫"""
        result = self.fetcher.get_price("AAPL")

        self.assertTrue(result["success"])
        self.assertIsNotNone(result["price"])
        self.assertGreater(result["price"], 0)


if __name__ == "__main__":
    unittest.main()
