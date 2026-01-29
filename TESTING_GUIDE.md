# Stock Itching 測試指南

本指南將引導你完成系統的安裝、設定和測試流程。

## 前置準備

### 1. 安裝 Python 依賴套件

```bash
pip install -r requirements.txt
```

預期輸出：應該成功安裝所有套件
- yfinance==0.2.37
- python-telegram-bot==20.8
- APScheduler==3.10.4
- python-dotenv==1.0.1
- pytz==2024.1

### 2. 建立 Telegram Bot

1. 在 Telegram 搜尋 `@BotFather`
2. 發送命令：`/newbot`
3. 依照指示設定：
   - Bot 名稱（例如：Stock Itching Test）
   - Bot 用戶名（例如：stock_itching_test_bot，必須以 bot 結尾）
4. 複製取得的 Token（格式：`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 3. 設定環境變數

編輯 `.env` 檔案，填入你的 Bot Token：

```bash
TELEGRAM_BOT_TOKEN=你的_實際_Token
WATCHLIST_FILE=config/watchlist.json
LOG_LEVEL=INFO
LOG_DIR=logs
CHECK_INTERVAL_MINUTES=5
RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=5
TIMEZONE=Asia/Taipei
```

## 階段一：語法與模組測試

### 測試 1：檢查 Python 語法

```bash
python3 -m py_compile main.py src/*.py
```

✅ 預期結果：無錯誤輸出

### 測試 2：測試匯入模組

```bash
python3 -c "from src.utils import setup_logging; print('utils OK')"
python3 -c "from src.stock_fetcher import StockFetcher; print('stock_fetcher OK')"
python3 -c "from src.alert_manager import AlertManager; print('alert_manager OK')"
```

✅ 預期結果：每行都輸出 "... OK"

## 階段二：股票查詢功能測試

### 測試 3：測試 stock_fetcher 模組

建立測試腳本 `test_stock_fetcher.py`：

```python
from src.stock_fetcher import StockFetcher
from src.utils import setup_logging

setup_logging()
fetcher = StockFetcher()

# 測試台股
print("=== 測試台股 ===")
result = fetcher.get_price("2330.TW")
print(f"成功: {result['success']}")
if result['success']:
    print(f"股票: {result['symbol']}")
    print(f"價格: {result['price']}")
    print(f"貨幣: {result['currency']}")

# 測試美股
print("\n=== 測試美股 ===")
result = fetcher.get_price("AAPL")
print(f"成功: {result['success']}")
if result['success']:
    print(f"股票: {result['symbol']}")
    print(f"價格: {result['price']}")
    print(f"貨幣: {result['currency']}")

# 測試無效代碼
print("\n=== 測試無效代碼 ===")
result = fetcher.get_price("INVALID123")
print(f"成功: {result['success']}")
print(f"錯誤: {result.get('error', 'N/A')}")
```

執行：
```bash
python3 test_stock_fetcher.py
```

✅ 預期結果：
- 台股和美股都能成功查詢到價格
- 無效代碼返回失敗

## 階段三：監控管理測試

### 測試 4：測試 alert_manager 模組

建立測試腳本 `test_alert_manager.py`：

```python
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
print(f"新增成功: {alert1['id']}")

alert2 = manager.add_alert(
    user_id=123456,
    symbol="AAPL",
    target_price=150.0,
    condition="below"
)
print(f"新增成功: {alert2['id']}")

# 測試列出監控
print("\n=== 測試列出監控 ===")
alerts = manager.list_alerts(123456)
print(f"用戶有 {len(alerts)} 個監控")
for alert in alerts:
    print(f"  - {alert['symbol']} {alert['condition']} {alert['target_price']}")

# 測試取得所有股票代碼
print("\n=== 測試取得股票代碼 ===")
symbols = manager.get_all_symbols()
print(f"需要監控的股票: {symbols}")

# 測試移除監控
print("\n=== 測試移除監控 ===")
removed = manager.remove_alert(123456, alert1['id'])
print(f"移除成功: {removed}")

alerts = manager.list_alerts(123456)
print(f"剩餘 {len(alerts)} 個監控")
```

執行：
```bash
python3 test_alert_manager.py
```

✅ 預期結果：
- 能夠新增監控
- 能夠列出監控
- 能夠移除監控
- 會在 config/ 建立 test_watchlist.json

## 階段四：完整系統測試

### 測試 5：啟動系統（需要 Telegram Bot Token）

確認 `.env` 檔案已設定正確的 Token，然後啟動：

```bash
python3 main.py
```

✅ 預期輸出：
```
[時間戳] - __main__ - INFO - ============================================================
[時間戳] - __main__ - INFO - Stock Itching 股票監控系統啟動
[時間戳] - __main__ - INFO - ============================================================
[時間戳] - __main__ - INFO - 初始化模組...
[時間戳] - src.alert_manager - INFO - 載入監控清單: 0 個監控
[時間戳] - __main__ - INFO - 模組初始化完成
[時間戳] - scheduler - INFO - 啟動排程器 - 每 5 分鐘檢查一次
[時間戳] - scheduler - INFO - 執行初始檢查...
[時間戳] - scheduler - INFO - ==================================================
[時間戳] - scheduler - INFO - 開始檢查所有監控股票
[時間戳] - scheduler - INFO - 目前沒有任何監控，跳過檢查
[時間戳] - telegram_bot - INFO - 正在啟動 Telegram Bot...
[時間戳] - telegram_bot - INFO - Telegram Bot 已啟動
```

### 測試 6：Telegram Bot 命令測試

在 Telegram 中找到你的 Bot，依序測試：

#### 6.1 基本命令測試

1. **測試 /start**
   ```
   /start
   ```
   ✅ 應該收到歡迎訊息

2. **測試 /help**
   ```
   /help
   ```
   ✅ 應該收到幫助訊息

#### 6.2 價格查詢測試

3. **測試查詢台股**
   ```
   /price 2330.TW
   ```
   ✅ 應該顯示台積電當前價格

4. **測試查詢美股**
   ```
   /price AAPL
   ```
   ✅ 應該顯示蘋果股價

5. **測試自動補 .TW**
   ```
   /price 2330
   ```
   ✅ 應該自動查詢 2330.TW

6. **測試無效代碼**
   ```
   /price INVALID123
   ```
   ✅ 應該顯示查詢失敗

#### 6.3 監控管理測試

7. **測試新增監控**
   ```
   /add 2330.TW above 600
   ```
   ✅ 應該顯示新增成功訊息，包含當前價格

8. **測試新增另一個監控**
   ```
   /add AAPL below 150
   ```
   ✅ 應該顯示新增成功

9. **測試列出監控**
   ```
   /list
   ```
   ✅ 應該顯示剛才新增的兩個監控

10. **測試移除監控**
    ```
    /remove <ID前幾個字元>
    ```
    （從 /list 取得 ID）
    ✅ 應該顯示移除成功

11. **再次列出確認**
    ```
    /list
    ```
    ✅ 應該只剩一個監控

#### 6.4 錯誤處理測試

12. **測試錯誤的命令格式**
    ```
    /add 2330.TW
    /price
    /remove
    ```
    ✅ 應該顯示用法錯誤訊息

## 階段五：通知功能測試

### 測試 7：價格觸發通知（實際測試）

**方法 1：設定容易觸發的條件**

查詢當前價格：
```
/price AAPL
```

假設顯示 $145.50，設定一個稍低的監控：
```
/add AAPL above 145
```

✅ 等待最多 5 分鐘，應該會收到觸發通知

**方法 2：手動測試（開發測試）**

建立測試腳本 `test_notification.py`：

```python
import asyncio
from src.alert_manager import AlertManager
from src.stock_fetcher import StockFetcher
from src.telegram_bot import TelegramBotHandler
from src.utils import setup_logging
from dotenv import load_dotenv
import os

load_dotenv()
setup_logging()

# 初始化模組
manager = AlertManager("config/watchlist.json")
fetcher = StockFetcher()
bot = TelegramBotHandler(
    token=os.getenv("TELEGRAM_BOT_TOKEN"),
    alert_manager=manager,
    stock_fetcher=fetcher
)

# 新增測試監控（使用你的 Telegram User ID）
YOUR_USER_ID = 123456789  # 修改為你的 ID
alert = manager.add_alert(
    user_id=YOUR_USER_ID,
    symbol="AAPL",
    target_price=1.0,  # 設定很低的價格，必定觸發
    condition="above"
)

# 查詢價格
prices = fetcher.get_multiple_prices(["AAPL"])

# 檢查觸發
triggered = manager.check_alerts(prices)
print(f"觸發的監控數量: {len(triggered)}")

# 發送通知
if triggered:
    for alert_info in triggered:
        asyncio.run(bot.send_alert(YOUR_USER_ID, alert_info))
        print("通知已發送")
```

執行：
```bash
python3 test_notification.py
```

✅ 應該在 Telegram 收到通知

### 測試 8：防重複通知測試

1. 設定一個容易觸發的監控
2. 等待觸發通知
3. 觀察日誌，確認不會重複通知
4. 修改 watchlist.json，將價格條件設回未觸發狀態
5. 再次觸發，確認會重新通知

## 階段六：長時間運行測試

### 測試 9：穩定性測試

讓系統持續運行至少 1 小時：

```bash
python3 main.py
```

觀察重點：
- ✅ 每 5 分鐘執行一次檢查
- ✅ 日誌正常記錄
- ✅ 記憶體使用穩定
- ✅ 沒有異常錯誤

查看日誌：
```bash
tail -f logs/app.log
```

### 測試 10：優雅關閉測試

按 `Ctrl+C` 停止程式

✅ 預期輸出：
```
收到信號 2，正在優雅關閉...
正在停止排程器...
排程器已停止
正在停止 Telegram Bot...
應用程式已安全關閉
```

## 測試清單總結

- [ ] 階段一：語法檢查通過
- [ ] 階段二：股票查詢功能正常
- [ ] 階段三：監控管理功能正常
- [ ] 階段四：系統啟動成功
- [ ] 階段五：Telegram Bot 命令全部正常
- [ ] 階段六：價格通知功能正常
- [ ] 階段七：防重複通知機制正常
- [ ] 階段八：長時間運行穩定
- [ ] 階段九：優雅關閉正常

## 常見問題排除

### 問題 1：ModuleNotFoundError

```
解決方案：安裝依賴套件
pip install -r requirements.txt
```

### 問題 2：Telegram Bot Token 錯誤

```
解決方案：確認 .env 檔案中的 Token 正確
檢查 @BotFather 提供的 Token 是否完整複製
```

### 問題 3：股票查詢失敗

```
解決方案：
1. 確認網路連線正常
2. 確認股票代碼正確
3. 非交易時間可能查到舊價格
```

### 問題 4：沒有收到通知

```
解決方案：
1. 確認有先與 Bot 對話過（/start）
2. 確認監控條件設定正確
3. 等待下一個 5 分鐘檢查週期
4. 查看日誌確認是否有錯誤
```

## 開發建議

1. **開發階段**：將 `CHECK_INTERVAL_MINUTES` 設為 1，加快測試
2. **日誌層級**：測試時可以設為 `DEBUG` 看更詳細的資訊
3. **測試用監控**：設定容易觸發的條件（如當前價格附近）
4. **清理測試資料**：測試完記得移除 `config/test_watchlist.json`

## 進階測試

### 多用戶測試

1. 使用不同的 Telegram 帳號
2. 新增各自的監控
3. 確認監控清單互不干擾
4. 確認通知發送到正確的用戶

### 壓力測試

1. 新增 20+ 個監控
2. 觀察查詢效能
3. 檢查記憶體使用
4. 確認所有通知都能正確發送

### 容錯測試

1. 網路斷線時的行為
2. JSON 檔案損壞時的恢復
3. API 查詢失敗時的重試機制

祝測試順利！ 🚀
