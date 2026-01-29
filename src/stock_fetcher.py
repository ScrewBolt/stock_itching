"""股票價格查詢模組"""
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import yfinance as yf
import requests


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
        self._last_request_time = None
        self._min_request_interval = 2.0  # 最小請求間隔 2 秒
        self._rate_limit_wait = 60  # 遇到 429 錯誤時等待 60 秒
        self._use_finmind_backup = True  # 啟用 FinMind 備援

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

    def _wait_for_rate_limit(self):
        """確保請求之間有足夠的間隔，避免 Rate Limiting"""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_request_interval:
                wait_time = self._min_request_interval - elapsed
                self.logger.debug(f"Rate limiting: 等待 {wait_time:.2f} 秒")
                time.sleep(wait_time)
        self._last_request_time = time.time()

    def _get_price_from_finmind(self, symbol: str) -> Dict[str, Any]:
        """
        從 FinMind API 查詢台股價格（備援方案）

        Args:
            symbol: 股票代碼（必須是台股，例如 2330）

        Returns:
            價格資訊字典
        """
        try:
            # FinMind 只支援台股，移除 .TW 後綴
            stock_id = symbol.replace(".TW", "").replace(".tw", "")

            # 檢查是否為台股代碼（4 位數字）
            if not (stock_id.isdigit() and len(stock_id) == 4):
                return {
                    "symbol": symbol,
                    "price": None,
                    "currency": None,
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": "FinMind 只支援台股代碼",
                    "source": "finmind"
                }

            self.logger.info(f"使用 FinMind 備援查詢: {stock_id}")

            # 呼叫 FinMind API（使用台灣即時股價 API）
            url = "https://api.finmindtrade.com/api/v4/data"
            params = {
                "dataset": "TaiwanStockPrice",
                "data_id": stock_id,
                "start_date": datetime.now().strftime("%Y-%m-%d")
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 檢查是否有資料
            if data.get("status") == 200 and data.get("data") and len(data["data"]) > 0:
                # 取得最新一筆資料
                latest = data["data"][-1]
                price = float(latest.get("close", 0))

                if price > 0:
                    return {
                        "symbol": f"{stock_id}.TW",
                        "price": price,
                        "currency": "TWD",
                        "timestamp": datetime.now().isoformat(),
                        "success": True,
                        "source": "finmind"
                    }

            return {
                "symbol": symbol,
                "price": None,
                "currency": None,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": "FinMind API 無資料",
                "source": "finmind"
            }

        except Exception as e:
            self.logger.error(f"FinMind 查詢失敗 ({symbol}): {e}")
            return {
                "symbol": symbol,
                "price": None,
                "currency": None,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": f"FinMind API 錯誤: {str(e)}",
                "source": "finmind"
            }

    def get_price(self, symbol: str) -> Dict[str, Any]:
        """
        查詢股票當前價格（帶重試機制和 Rate Limiting）

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
                # Rate Limiting：確保請求間隔
                self._wait_for_rate_limit()

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
                    "success": True,
                    "source": "yfinance"
                }

                self.logger.info(f"成功查詢 (yfinance): {symbol} = {price} {currency}")
                return result

            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"查詢失敗 ({symbol}, 嘗試 {attempt}/{self.retry_attempts}): {e}")

                # 檢查是否是 429 錯誤（Rate Limit）
                if "429" in error_msg or "Too Many Requests" in error_msg:
                    wait_time = self._rate_limit_wait if attempt == 1 else self._rate_limit_wait * attempt
                    self.logger.warning(
                        f"遇到 API Rate Limit (429)，等待 {wait_time} 秒後重試..."
                    )
                    time.sleep(wait_time)
                # 如果還有重試機會，等待後重試
                elif attempt < self.retry_attempts:
                    self.logger.info(f"等待 {self.retry_delay} 秒後重試...")
                    time.sleep(self.retry_delay)

        # 所有重試都失敗，嘗試使用 FinMind 備援（僅限台股）
        if self._use_finmind_backup and (".TW" in symbol.upper() or symbol.isdigit()):
            self.logger.warning(f"yfinance 查詢失敗，嘗試使用 FinMind 備援查詢 {symbol}")
            finmind_result = self._get_price_from_finmind(symbol)

            if finmind_result.get("success"):
                self.logger.info(f"FinMind 備援查詢成功: {symbol} = {finmind_result['price']}")
                return finmind_result

        # 所有方法都失敗
        return {
            "symbol": symbol,
            "price": None,
            "currency": None,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": "所有 API 都失敗（yfinance + FinMind）"
        }

    def get_multiple_prices(self, symbols: list) -> Dict[str, Dict]:
        """
        批次查詢多個股票價格（帶智能 Rate Limiting）

        Args:
            symbols: 股票代碼列表

        Returns:
            字典，key 為股票代碼，value 為價格資訊
        """
        results = {}

        self.logger.info(f"開始批次查詢 {len(symbols)} 個股票")

        for i, symbol in enumerate(symbols):
            result = self.get_price(symbol)
            results[symbol] = result

            # 如果遇到 Rate Limit 錯誤，增加後續請求的間隔
            if not result.get("success") and result.get("error") and "429" in result.get("error", ""):
                self.logger.warning("檢測到 Rate Limit，增加請求間隔到 5 秒")
                self._min_request_interval = 5.0

        return results
