#!/usr/bin/env python3
"""測試股票查詢功能"""
from src.stock_fetcher import StockFetcher
from src.utils import setup_logging

setup_logging()
fetcher = StockFetcher()

# 測試台股
print("=== 測試台股（台積電）===")
result = fetcher.get_price("2330.TW")
print(f"成功: {result['success']}")
if result['success']:
    print(f"股票: {result['symbol']}")
    print(f"價格: {result['price']}")
    print(f"貨幣: {result['currency']}")
else:
    print(f"錯誤: {result.get('error')}")

print()

# 測試美股
print("=== 測試美股（蘋果）===")
result = fetcher.get_price("AAPL")
print(f"成功: {result['success']}")
if result['success']:
    print(f"股票: {result['symbol']}")
    print(f"價格: {result['price']}")
    print(f"貨幣: {result['currency']}")
else:
    print(f"錯誤: {result.get('error')}")

print()

# 測試自動補 .TW
print("=== 測試自動補 .TW（輸入 2330）===")
result = fetcher.get_price("2330")
print(f"成功: {result['success']}")
if result['success']:
    print(f"股票: {result['symbol']}")
    print(f"價格: {result['price']}")
    print(f"貨幣: {result['currency']}")
else:
    print(f"錯誤: {result.get('error')}")

print()

# 測試無效代碼
print("=== 測試無效代碼 ===")
result = fetcher.get_price("INVALID123")
print(f"成功: {result['success']}")
if not result['success']:
    print(f"錯誤: {result.get('error', 'N/A')}")
