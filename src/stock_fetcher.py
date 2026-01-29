"""股票價格查詢模組"""
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import yfinance as yf
import requests


class StockFetcher:
    """股票價格查詢類別"""

    def __init__(self, retry_attempts: int = 1, retry_delay: int = 2):
        """
        初始化股票查詢器

        Args:
            retry_attempts: 每個 API 的最大嘗試次數（預設 1，快速故障轉移）
            retry_delay: 重試間隔秒數
        """
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
        self._last_request_time = None
        self._min_request_interval = 1.0  # 最小請求間隔 1 秒（減少等待）
        self._rate_limit_wait = 60  # 遇到 429 錯誤時等待 60 秒
        self._use_finmind_backup = True  # 啟用 FinMind 備援
        self._alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")  # Alpha Vantage API Key

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
        從 FinMind API 查詢股票價格（支援台股和美股）

        Args:
            symbol: 股票代碼（台股如 2330.TW，美股如 AAPL）

        Returns:
            價格資訊字典
        """
        try:
            # 判斷是台股還是美股
            is_taiwan_stock = ".TW" in symbol.upper() or (
                symbol.replace(".TW", "").replace(".tw", "").isdigit() and
                len(symbol.replace(".TW", "").replace(".tw", "")) == 4
            )

            if is_taiwan_stock:
                # 台股：移除 .TW 後綴
                stock_id = symbol.replace(".TW", "").replace(".tw", "")
                dataset = "TaiwanStockPrice"
                currency = "TWD"
                self.logger.info(f"使用 FinMind 查詢台股: {stock_id}")
            else:
                # 美股：直接使用代碼
                stock_id = symbol.upper()
                dataset = "USStockPrice"
                currency = "USD"
                self.logger.info(f"使用 FinMind 查詢美股: {stock_id}")

            # 呼叫 FinMind API
            url = "https://api.finmindtrade.com/api/v4/data"

            # 查詢最近 3 天的資料（確保有資料）
            end_date = datetime.now()
            start_date = end_date - timedelta(days=3)

            params = {
                "dataset": dataset,
                "data_id": stock_id,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 檢查是否有資料
            if data.get("status") == 200 and data.get("data") and len(data["data"]) > 0:
                # 取得最新一筆資料
                latest = data["data"][-1]

                # FinMind 回傳的欄位名稱（大寫 C）
                price = float(latest.get("Close", latest.get("close", 0)))

                if price > 0:
                    # 保持原始 symbol 格式
                    return_symbol = f"{stock_id}.TW" if is_taiwan_stock else stock_id
                    return {
                        "symbol": return_symbol,
                        "price": price,
                        "currency": currency,
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

    def _get_price_from_alphavantage(self, symbol: str) -> Dict[str, Any]:
        """
        從 Alpha Vantage API 查詢股票價格（第三層備援）

        Args:
            symbol: 股票代碼（支援美股和台股）

        Returns:
            價格資訊字典
        """
        try:
            # Alpha Vantage 不支援 .TW 後綴，台股需要特殊處理
            av_symbol = symbol
            is_taiwan = False

            if ".TW" in symbol.upper():
                # 台股：移除 .TW 並加上 .TPE（台北交易所代碼）
                stock_id = symbol.replace(".TW", "").replace(".tw", "")
                av_symbol = f"{stock_id}.TPE"
                is_taiwan = True
                self.logger.info(f"使用 Alpha Vantage 查詢台股: {av_symbol}")
            else:
                self.logger.info(f"使用 Alpha Vantage 查詢: {av_symbol}")

            # 呼叫 Alpha Vantage API
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": av_symbol,
                "apikey": self._alpha_vantage_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 檢查是否有 "Global Quote" 資料
            if "Global Quote" in data and data["Global Quote"]:
                quote = data["Global Quote"]
                price_str = quote.get("05. price")

                if price_str:
                    price = float(price_str)
                    currency = "TWD" if is_taiwan else "USD"

                    return {
                        "symbol": symbol,
                        "price": price,
                        "currency": currency,
                        "timestamp": datetime.now().isoformat(),
                        "success": True,
                        "source": "alphavantage"
                    }

            # 檢查是否有 API 限制訊息
            if "Note" in data:
                self.logger.warning(f"Alpha Vantage API 限制: {data['Note']}")
                return {
                    "symbol": symbol,
                    "price": None,
                    "currency": None,
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": "Alpha Vantage API 達到請求限制",
                    "source": "alphavantage"
                }

            return {
                "symbol": symbol,
                "price": None,
                "currency": None,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": "Alpha Vantage API 無資料",
                "source": "alphavantage"
            }

        except Exception as e:
            self.logger.error(f"Alpha Vantage 查詢失敗 ({symbol}): {e}")
            return {
                "symbol": symbol,
                "price": None,
                "currency": None,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": f"Alpha Vantage API 錯誤: {str(e)}",
                "source": "alphavantage"
            }

    def get_price(self, symbol: str) -> Dict[str, Any]:
        """
        查詢股票當前價格（快速故障轉移機制）

        策略：
        1. 嘗試 yfinance（1次）
        2. 如果失敗 → FinMind（支援台股和美股）
        3. 如果仍失敗 → Alpha Vantage（需有效 API Key）

        Args:
            symbol: 股票代碼

        Returns:
            包含價格資訊的字典
        """
        # 標準化代碼
        symbol = self.normalize_symbol(symbol)
        is_taiwan_stock = ".TW" in symbol.upper()

        # 1. 嘗試 yfinance（主要 API）
        try:
            self._wait_for_rate_limit()
            self.logger.info(f"[yfinance] 查詢: {symbol}")

            ticker = yf.Ticker(symbol)
            info = ticker.info

            # 嘗試多種價格欄位
            price = None
            for field in ["regularMarketPrice", "currentPrice", "previousClose", "open"]:
                if field in info and info[field] is not None:
                    price = float(info[field])
                    break

            if price is not None:
                currency = info.get("currency", "USD")
                self.logger.info(f"✅ [yfinance] 成功: {symbol} = {price} {currency}")
                return {
                    "symbol": symbol,
                    "price": price,
                    "currency": currency,
                    "timestamp": datetime.now().isoformat(),
                    "success": True,
                    "source": "yfinance"
                }

        except Exception as e:
            self.logger.warning(f"❌ [yfinance] 失敗: {symbol} - {e}")

        # 2. yfinance 失敗，快速切換到 FinMind（支援台股和美股）
        if self._use_finmind_backup:
            self.logger.info(f"⚡ 快速切換到 FinMind: {symbol}")
            finmind_result = self._get_price_from_finmind(symbol)

            if finmind_result.get("success"):
                self.logger.info(f"✅ [FinMind] 成功: {symbol} = {finmind_result['price']}")
                return finmind_result
            else:
                self.logger.warning(f"❌ [FinMind] 失敗: {symbol}")

        # 3. 嘗試 Alpha Vantage（台股和美股都支援）
        if self._alpha_vantage_key and self._alpha_vantage_key != "demo":
            self.logger.info(f"⚡ 嘗試 Alpha Vantage: {symbol}")
            av_result = self._get_price_from_alphavantage(symbol)

            if av_result.get("success"):
                self.logger.info(f"✅ [Alpha Vantage] 成功: {symbol} = {av_result['price']}")
                return av_result
            else:
                self.logger.warning(f"❌ [Alpha Vantage] 失敗: {symbol}")

        # 所有 API 都失敗
        apis_tried = ["yfinance"]
        if self._use_finmind_backup:
            apis_tried.append("FinMind")
        if self._alpha_vantage_key and self._alpha_vantage_key != "demo":
            apis_tried.append("Alpha Vantage")

        error_msg = f"所有 API 都失敗: {', '.join(apis_tried)}"
        self.logger.error(f"❌ {error_msg} ({symbol})")

        return {
            "symbol": symbol,
            "price": None,
            "currency": None,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": error_msg
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
