#!/usr/bin/env python3
"""測試監控管理功能"""
from src.alert_manager import AlertManager
from src.utils import setup_logging

setup_logging()
manager = AlertManager("config/test_watchlist.json")

# 測試新增監控
print("=== 測試新增監控 ===")
alert1 = manager.add_alert(
    user_id=123456,
    symbol="2330.TW",
    target_price=600.0,
    condition="above"
)
print(f"新增成功 - ID: {alert1['id']}")
print(f"  股票: {alert1['symbol']}")
print(f"  條件: {alert1['condition']} {alert1['target_price']}")

alert2 = manager.add_alert(
    user_id=123456,
    symbol="AAPL",
    target_price=150.0,
    condition="below"
)
print(f"新增成功 - ID: {alert2['id']}")
print(f"  股票: {alert2['symbol']}")
print(f"  條件: {alert2['condition']} {alert2['target_price']}")

print()

# 測試列出監控
print("=== 測試列出監控 ===")
alerts = manager.list_alerts(123456)
print(f"用戶有 {len(alerts)} 個監控:")
for i, alert in enumerate(alerts, 1):
    print(f"  {i}. {alert['symbol']} {alert['condition']} {alert['target_price']}")
    print(f"     ID: {alert['id'][:8]}...")
    print(f"     已通知: {alert['notified']}")

print()

# 測試取得所有股票代碼
print("=== 測試取得股票代碼 ===")
symbols = manager.get_all_symbols()
print(f"需要監控的股票: {symbols}")

print()

# 測試移除監控
print("=== 測試移除監控 ===")
removed = manager.remove_alert(123456, alert1['id'])
print(f"移除 {alert1['symbol']} 成功: {removed}")

alerts = manager.list_alerts(123456)
print(f"剩餘 {len(alerts)} 個監控")

print()

# 測試檢查觸發（模擬）
print("=== 測試檢查觸發（模擬價格）===")
mock_prices = {
    "AAPL": {
        "symbol": "AAPL",
        "price": 140.0,  # 低於 150，應該觸發
        "currency": "USD",
        "success": True
    }
}

triggered = manager.check_alerts(mock_prices)
print(f"觸發的監控數量: {len(triggered)}")
for alert_info in triggered:
    alert = alert_info['alert']
    print(f"  - {alert['symbol']}: {alert_info['current_price']} {alert_info['currency']}")
    print(f"    條件: {alert['condition']} {alert['target_price']}")

print()
print("測試完成！")
print(f"測試資料儲存於: config/test_watchlist.json")
