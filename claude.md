# Stock Itching - Claude AI 助手專案說明

> 這是給 AI 助手（如 Claude Code）閱讀的專案技術文件，幫助快速理解專案架構和開發指南。

## 專案概述

**專案名稱**：Stock Itching - 股票價格監控系統
**語言**：Python 3.8+
**類型**：Telegram Bot 應用程式
**用途**：監控股票價格並在達到目標價時自動通知用戶

## 核心功能

1. 透過 Telegram Bot 設定股票價格監控（台股/美股）
2. 背景定時查詢（每 5 分鐘）
3. 價格觸發時自動通知（防重複通知機制）
4. 即時查詢任何股票的當前價格

## 技術棧

| 技術 | 用途 | 版本 |
|------|------|------|
| Python | 主要語言 | 3.8+ |
| yfinance | 股票價格 API | 0.2.37 |
| python-telegram-bot | Bot 框架 | 20.8 |
| APScheduler | 背景排程 | 3.10.4 |
| python-dotenv | 環境變數 | 1.0.1 |

## 專案結構

```
stock_itching/
├── main.py                    # 主程式入口（150 行）
├── .env                       # 環境變數（包含 Bot Token）
├── .env.example               # 環境變數範例
├── requirements.txt           # Python 依賴
├── Makefile                   # 常用命令
│
├── src/                       # 核心模組
│   ├── __init__.py
│   ├── utils.py               # 工具函數（日誌、JSON、格式化）
│   ├── stock_fetcher.py       # 股票價格查詢（含重試機制）
│   ├── alert_manager.py       # 監控管理（核心邏輯）
│   ├── telegram_bot.py        # Bot 命令處理器
│   └── scheduler.py           # 背景排程器
│
├── config/
│   └── watchlist.json         # 監控清單（自動生成）
│
├── logs/
│   ├── app.log                # 一般日誌（自動生成）
│   └── error.log              # 錯誤日誌（自動生成）
│
├── test_stock_fetcher.py      # 股票查詢測試
├── test_alert_manager.py      # 監控管理測試
│
└── docs/                      # 文件
    ├── README.md              # 使用說明
    ├── QUICKSTART.md          # 快速啟動
    ├── TESTING_GUIDE.md       # 測試指南
    ├── PROJECT_SUMMARY.md     # 專案總覽
    └── IMPLEMENTATION_REPORT.md  # 實作報告
```

## 核心模組詳解

### 1. main.py - 主程式

**職責**：應用程式入口、模組初始化、信號處理

**關鍵類別**：
- `StockItchingApp` - 主應用類別

**關鍵流程**：
```python
1. 載入環境變數 (.env)
2. 設定日誌系統
3. 初始化模組（依賴注入）：
   - AlertManager
   - StockFetcher
   - TelegramBotHandler
   - StockMonitorScheduler
4. 註冊信號處理器（SIGINT/SIGTERM）
5. 啟動 scheduler
6. 啟動 telegram bot（阻塞運行）
```

### 2. src/utils.py - 工具函數

**職責**：基礎功能（日誌、JSON、格式化）

**關鍵函數**：
- `setup_logging(log_dir, log_level)` - 配置日誌系統
- `load_json(file_path, default)` - 安全載入 JSON
- `save_json(file_path, data)` - 安全儲存 JSON
- `format_price(price, currency)` - 價格格式化
- `generate_alert_id()` - 生成 UUID

### 3. src/stock_fetcher.py - 股票查詢

**職責**：查詢股票價格（yfinance API）

**關鍵類別**：
- `StockFetcher`

**關鍵方法**：
- `normalize_symbol(symbol)` - 標準化代碼（台股自動加 .TW）
- `validate_symbol(symbol)` - 驗證代碼有效性
- `get_price(symbol)` - 查詢價格（含重試機制）
- `get_multiple_prices(symbols)` - 批次查詢

**重試機制**：
- 最多重試 3 次
- 間隔 5 秒
- 失敗返回 `success: false`

### 4. src/alert_manager.py - 監控管理（核心）

**職責**：管理監控清單、檢查觸發條件、防重複通知

**關鍵類別**：
- `AlertManager`

**關鍵方法**：
- `add_alert(user_id, symbol, target_price, condition)` - 新增監控
- `remove_alert(user_id, alert_id)` - 移除指定監控
- `list_alerts(user_id)` - 列出用戶監控
- `get_all_symbols()` - 取得所有監控股票（去重）
- `check_alerts(current_prices)` - 檢查觸發（核心邏輯）
- `clear_all_alerts(user_id)` - 清空用戶的所有監控
- `clear_alerts_by_symbol(user_id, symbol)` - 清空用戶指定股票的所有監控

**防重複通知機制**：
```python
1. 觸發條件時：設定 notified = True
2. 已通知後：跳過重複通知
3. 價格回到安全範圍（目標價 ±2%）：重置 notified = False
4. 重置後可再次通知
```

**資料結構（watchlist.json）**：
```json
{
  "alerts": [
    {
      "id": "uuid",
      "user_id": 123456789,
      "symbol": "2330.TW",
      "target_price": 600.0,
      "condition": "above",  // or "below"
      "created_at": "ISO8601",
      "notified": false,
      "last_notified_at": null,
      "enabled": true
    }
  ],
  "last_check": "ISO8601"
}
```

### 5. src/telegram_bot.py - Bot 處理器

**職責**：處理 Telegram 命令、發送通知

**關鍵類別**：
- `TelegramBotHandler`

**命令處理器**：
| 命令 | 處理器 | 功能 |
|------|--------|------|
| `/start` | `start_command()` | 歡迎訊息 |
| `/help` | `help_command()` | 幫助說明 |
| `/price <code>` | `price_command()` | 即時查價 |
| `/add <code> <above\|below> <price>` | `add_command()` | 新增監控 |
| `/list` | `list_command()` | 列出監控 |
| `/remove <id>` | `remove_command()` | 移除指定監控 |
| `/clear` | `clear_command()` | 清空所有監控 |
| `/clearstock <code>` | `clearstock_command()` | 清空指定股票的所有監控 |

**關鍵方法**：
- `send_alert(user_id, alert_info)` - 發送價格觸發通知（異步）
- `error_handler()` - 全局錯誤處理
- `run()` - 啟動 Bot（阻塞）
- `stop()` - 停止 Bot

### 6. src/scheduler.py - 背景排程

**職責**：定時檢查所有監控、發送通知

**關鍵類別**：
- `StockMonitorScheduler`

**關鍵方法**：
- `check_all_stocks()` - 主檢查邏輯（每 5 分鐘執行）
- `start()` - 啟動排程器
- `stop()` - 停止排程器（優雅關閉）

**檢查流程**：
```python
1. 取得所有需監控的股票代碼（AlertManager.get_all_symbols()）
2. 批次查詢所有股票價格（StockFetcher.get_multiple_prices()）
3. 檢查觸發條件（AlertManager.check_alerts()）
4. 發送通知（TelegramBotHandler.send_alert()）
5. 更新 notified 狀態並儲存
```

## 資料流程圖

### 新增監控流程

```
用戶
  ↓ /add 2330.TW above 600
TelegramBotHandler.add_command()
  ↓ 驗證代碼
StockFetcher.get_price("2330.TW")
  ↓ 查詢成功
AlertManager.add_alert()
  ↓ 儲存
watchlist.json
  ↓ 回應
用戶收到成功訊息
```

### 背景檢查流程

```
Scheduler（每 5 分鐘）
  ↓
check_all_stocks()
  ↓
AlertManager.get_all_symbols()
  → ["2330.TW", "AAPL", ...]
  ↓
StockFetcher.get_multiple_prices()
  → {"2330.TW": {price: 605, ...}, ...}
  ↓
AlertManager.check_alerts()
  → [triggered_alert_1, ...]
  ↓
TelegramBotHandler.send_alert()
  → 發送 Telegram 通知
  ↓
更新 watchlist.json（notified=true）
```

## 環境變數（.env）

```bash
# 必填
TELEGRAM_BOT_TOKEN=<從 @BotFather 取得>

# 可選（有預設值）
WATCHLIST_FILE=config/watchlist.json
LOG_LEVEL=INFO
LOG_DIR=logs
CHECK_INTERVAL_MINUTES=5
RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=5
TIMEZONE=Asia/Taipei
```

## 開發指南

### 安裝依賴

```bash
pip install -r requirements.txt
```

### 執行測試

```bash
# 語法檢查
python3 -m py_compile main.py src/*.py

# 股票查詢測試
python3 test_stock_fetcher.py

# 監控管理測試
python3 test_alert_manager.py

# 或使用 Makefile
make test
```

### 啟動系統

```bash
# 確保已設定 .env 中的 TELEGRAM_BOT_TOKEN
python3 main.py

# 或使用 Makefile
make run
```

### 查看日誌

```bash
# 即時查看
tail -f logs/app.log

# 查看錯誤
tail -f logs/error.log

# 或使用 Makefile
make logs
```

## 常見開發任務

### 清空監控功能

系統提供三種清空監控的方式：

1. **移除單一監控**：`/remove <ID>` - 移除指定 ID 的監控
2. **清空所有監控**：`/clear` - 清空用戶的所有監控
3. **清空指定股票**：`/clearstock <代碼>` - 清空指定股票的所有監控

實作位置：
- `alert_manager.py`：
  - `remove_alert()` - 移除單一監控
  - `clear_all_alerts()` - 清空所有監控
  - `clear_alerts_by_symbol()` - 清空指定股票監控
- `telegram_bot.py`：
  - `remove_command()` - 處理 /remove
  - `clear_command()` - 處理 /clear
  - `clearstock_command()` - 處理 /clearstock

### 新增 Telegram 命令

1. 在 `src/telegram_bot.py` 新增命令處理函數：
```python
async def new_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 處理邏輯
    pass
```

2. 在 `run()` 方法中註冊：
```python
self.application.add_handler(CommandHandler("new", self.new_command))
```

### 修改檢查頻率

編輯 `.env`：
```bash
CHECK_INTERVAL_MINUTES=1  # 改為 1 分鐘（測試用）
```

### 新增監控條件類型

1. 修改 `alert_manager.py` 的 `check_alerts()` 方法
2. 新增條件判斷邏輯
3. 更新 JSON 結構

### Debug 技巧

1. **啟用 DEBUG 日誌**：
   ```bash
   LOG_LEVEL=DEBUG
   ```

2. **檢查 JSON 檔案**：
   ```bash
   cat config/watchlist.json | python3 -m json.tool
   ```

3. **測試單一模組**：
   ```python
   from src.stock_fetcher import StockFetcher
   fetcher = StockFetcher()
   result = fetcher.get_price("AAPL")
   print(result)
   ```

## 錯誤處理策略

| 錯誤類型 | 處理方式 |
|---------|---------|
| API 查詢失敗 | 重試 3 次，間隔 5 秒，失敗則跳過 |
| JSON 損壞 | 使用預設空白結構 |
| Telegram 發送失敗 | 記錄錯誤但不中斷系統 |
| 用戶輸入錯誤 | 回傳友善錯誤訊息 |
| 系統異常 | 記錄到 error.log，優雅關閉 |

## 重要設計模式

### 1. 依賴注入

```python
# main.py
alert_manager = AlertManager(watchlist_file)
stock_fetcher = StockFetcher(retry_attempts, retry_delay)
telegram_handler = TelegramBotHandler(token, alert_manager, stock_fetcher)
scheduler = StockMonitorScheduler(alert_manager, stock_fetcher, telegram_handler)
```

優點：模組解耦、易於測試

### 2. 單一職責

每個模組只負責一個核心功能：
- `stock_fetcher` → 只負責查詢價格
- `alert_manager` → 只負責管理監控
- `telegram_bot` → 只負責用戶互動
- `scheduler` → 只負責定時觸發

### 3. 防禦性程式設計

- 所有外部呼叫都有錯誤處理
- JSON 操作有預設值
- 用戶輸入有驗證
- 優雅關閉機制

## 測試覆蓋

| 模組 | 測試檔案 | 覆蓋項目 |
|------|---------|---------|
| stock_fetcher | test_stock_fetcher.py | 台股、美股、無效代碼 |
| alert_manager | test_alert_manager.py | 新增、列出、移除、觸發 |
| 完整系統 | 手動測試 | 參考 TESTING_GUIDE.md |

## 效能考量

- **批次查詢**：一次查詢所有股票，減少 API 呼叫
- **去重處理**：多個監控同一股票只查詢一次
- **異步通知**：使用 asyncio 發送通知不阻塞
- **日誌輪轉**：避免檔案過大

## 安全性考量

- ✅ Token 不寫入日誌
- ✅ 敏感檔案加入 .gitignore
- ✅ 用戶只能操作自己的監控
- ✅ 輸入驗證和消毒

## 已知限制

1. **API 限制**：yfinance 非官方 API，有頻率限制
2. **價格延遲**：實時數據可能有數分鐘延遲
3. **非交易時間**：查到的是最後收盤價
4. **儲存方式**：JSON 不適合大量數據（建議 < 100 個監控）

## 擴充建議

未來可加入的功能：
- [ ] 資料庫儲存（PostgreSQL/SQLite）
- [ ] 價格走勢圖表
- [ ] 技術指標（RSI、MA、MACD）
- [ ] Web 介面
- [ ] 多個條件組合（AND/OR）
- [ ] 停損停利自動化
- [ ] Webhook 整合

## Git 工作流程

```bash
# 開發新功能
git checkout -b feature/new-feature
# 開發...
git add .
git commit -m "Add new feature"
git push origin feature/new-feature

# 修復 Bug
git checkout -b fix/bug-name
# 修復...
git commit -m "Fix bug"
```

## Makefile 命令

```bash
make help      # 顯示幫助
make install   # 安裝依賴
make test      # 執行測試
make run       # 啟動系統
make logs      # 查看日誌
make clean     # 清理測試檔案
```

## 常見問題（開發）

### Q: 如何測試 Telegram Bot 不啟動背景排程？

A: 直接建立 TelegramBotHandler 並呼叫 `run()`：
```python
from src.telegram_bot import TelegramBotHandler
# ... 初始化
bot.run()  # 只啟動 Bot
```

### Q: 如何手動觸發一次價格檢查？

A: 直接呼叫 scheduler 的檢查方法：
```python
scheduler.check_all_stocks()
```

### Q: 如何清空所有監控？

A: 刪除 `config/watchlist.json` 或手動編輯清空 alerts 陣列。

### Q: 如何修改股票代碼標準化邏輯？

A: 修改 `src/stock_fetcher.py` 的 `normalize_symbol()` 方法。

## 相關資源

- **yfinance 文件**：https://pypi.org/project/yfinance/
- **python-telegram-bot 文件**：https://python-telegram-bot.org/
- **APScheduler 文件**：https://apscheduler.readthedocs.io/

## 聯絡資訊

- **專案倉庫**：（待補充）
- **Issue 追蹤**：（待補充）
- **作者**：Stock Itching Team

---

**最後更新**：2026-01-29
**版本**：v1.0.0
**狀態**：✅ 生產就緒
