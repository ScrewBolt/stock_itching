"""股票價格查詢模組"""
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

import yfinance as yf


class StockFetcher:
    """股票價格查詢類別"""

    def __init__(self, retry_attempts: int = 3, retry_delay: int = 5):
        """
        初始化股票查詢器

        Args:
            retry_attempts: 最大重試次數
            retry_delay: 重試間隔秒數
        """
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)

    def normalize_symbol(self, symbol: str) -> str:
        """
        標準化股票代碼

        Args:
            symbol: 原始股票代碼

        Returns:
            標準化後的代碼（台股自動加 .TW）
        """
        symbol = symbol.strip().upper()

        # 如果是純數字且長度為 4，視為台股代碼
        if symbol.isdigit() and len(symbol) == 4:
            symbol = f"{symbol}.TW"
            self.logger.debug(f"台股代碼標準化: {symbol}")

        return symbol

    def validate_symbol(self, symbol: str) -> bool:
        """
        驗證股票代碼格式是否有效（輕量級驗證）

        Args:
            symbol: 股票代碼

        Returns:
            是否有效
        """
        # 輕量級格式驗證，避免頻繁 API 呼叫
        if not symbol or len(symbol) < 1:
            return False

        # 基本格式檢查：只允許 ASCII 字母、數字、點號
        if not all((c.isascii() and c.isalnum()) or c == '.' for c in symbol):
            self.logger.warning(f"無效的股票代碼格式: {symbol}")
            return False

        return True

    def get_price(self, symbol: str) -> Dict[str, Any]:
        """
        查詢股票當前價格（帶重試機制）

        Args:
            symbol: 股票代碼

        Returns:
            包含價格資訊的字典：
            {
                'symbol': str,
                'price': float,
                'currency': str,
                'timestamp': str,
                'success': bool,
                'error': str (如果失敗)
            }
        """
        # 標準化代碼
        symbol = self.normalize_symbol(symbol)

        # 重試邏輯
        for attempt in range(1, self.retry_attempts + 1):
            try:
                self.logger.info(f"查詢股票價格: {symbol} (嘗試 {attempt}/{self.retry_attempts})")

                # 使用 yfinance 查詢
                ticker = yf.Ticker(symbol)
                info = ticker.info

                # 嘗試多種價格欄位（不同市場欄位名稱可能不同）
                price = None
                price_fields = [
                    "regularMarketPrice",
                    "currentPrice",
                    "previousClose",
                    "open"
                ]

                for field in price_fields:
                    if field in info and info[field] is not None:
                        price = float(info[field])
                        break

                if price is None:
                    raise ValueError(f"無法取得 {symbol} 的價格資訊")

                # 取得貨幣
                currency = info.get("currency", "USD")

                result = {
                    "symbol": symbol,
                    "price": price,
                    "currency": currency,
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }

                self.logger.info(f"成功查詢: {symbol} = {price} {currency}")
                return result

            except Exception as e:
                self.logger.error(f"查詢失敗 ({symbol}, 嘗試 {attempt}/{self.retry_attempts}): {e}")

                # 如果還有重試機會，等待後重試
                if attempt < self.retry_attempts:
                    self.logger.info(f"等待 {self.retry_delay} 秒後重試...")
                    time.sleep(self.retry_delay)

        # 所有重試都失敗（迴圈結束）
        return {
            "symbol": symbol,
            "price": None,
            "currency": None,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": "所有重試都失敗"
        }

    def get_multiple_prices(self, symbols: list) -> Dict[str, Dict]:
        """
        批次查詢多個股票價格（帶簡單的 rate limiting）

        Args:
            symbols: 股票代碼列表

        Returns:
            字典，key 為股票代碼，value 為價格資訊
        """
        results = {}

        for i, symbol in enumerate(symbols):
            result = self.get_price(symbol)
            results[symbol] = result

            # 簡單的 rate limiting：每次查詢後暫停 0.5 秒
            if i < len(symbols) - 1:  # 最後一個不需要等待
                time.sleep(0.5)

        return results
