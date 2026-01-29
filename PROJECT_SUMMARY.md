# Stock Itching - 專案總覽

## 實作完成狀態 ✅

所有計劃的功能和檔案都已完整實作。

## 檔案清單

### 核心程式檔案

| 檔案 | 行數 | 說明 | 狀態 |
|------|------|------|------|
| `main.py` | ~150 | 主程式入口，協調所有模組 | ✅ 完成 |
| `src/utils.py` | ~120 | 工具函數（日誌、JSON、格式化） | ✅ 完成 |
| `src/stock_fetcher.py` | ~150 | 股票價格查詢，支援重試 | ✅ 完成 |
| `src/alert_manager.py` | ~200 | 監控清單管理，防重複通知 | ✅ 完成 |
| `src/telegram_bot.py` | ~350 | Telegram Bot 處理器 | ✅ 完成 |
| `src/scheduler.py` | ~130 | 背景任務排程器 | ✅ 完成 |

### 配置檔案

| 檔案 | 說明 | 狀態 |
|------|------|------|
| `.env.example` | 環境變數範例 | ✅ 完成 |
| `.env` | 環境變數（需用戶填入 Token） | ✅ 已建立 |
| `.gitignore` | Git 忽略清單 | ✅ 完成 |
| `requirements.txt` | Python 依賴套件 | ✅ 完成 |

### 文件檔案

| 檔案 | 說明 | 狀態 |
|------|------|------|
| `README.md` | 完整使用說明 | ✅ 完成 |
| `QUICKSTART.md` | 5 分鐘快速啟動 | ✅ 完成 |
| `TESTING_GUIDE.md` | 詳細測試指南 | ✅ 完成 |
| `PROJECT_SUMMARY.md` | 專案總覽（本文件） | ✅ 完成 |

### 測試檔案

| 檔案 | 說明 | 狀態 |
|------|------|------|
| `test_stock_fetcher.py` | 股票查詢測試腳本 | ✅ 完成 |
| `test_alert_manager.py` | 監控管理測試腳本 | ✅ 完成 |

### 輔助檔案

| 檔案 | 說明 | 狀態 |
|------|------|------|
| `Makefile` | 常用命令快捷方式 | ✅ 完成 |

## 功能實作狀態

### 核心功能

- ✅ **股票價格查詢**
  - 支援台股（自動補 .TW）
  - 支援美股
  - 重試機制（3 次，間隔 5 秒）
  - 錯誤處理

- ✅ **監控管理**
  - 新增監控（above/below 條件）
  - 列出監控
  - 移除監控
  - JSON 持久化儲存
  - 多用戶隔離

- ✅ **智能通知**
  - 價格觸發時自動通知
  - 防重複通知機制
  - 價格回到安全範圍自動重置（±2% 緩衝）

- ✅ **背景排程**
  - 每 5 分鐘自動檢查
  - 批次查詢所有股票
  - 優雅關閉

- ✅ **Telegram Bot**
  - `/start` - 歡迎訊息
  - `/help` - 幫助說明
  - `/price` - 即時查價
  - `/add` - 新增監控
  - `/list` - 列出監控
  - `/remove` - 移除監控
  - 完整錯誤處理

### 非功能性需求

- ✅ **日誌系統**
  - 分級日誌（INFO/ERROR）
  - 自動輪轉（10MB，5 個備份）
  - 控制台和檔案同步輸出

- ✅ **錯誤處理**
  - API 失敗重試
  - JSON 損壞恢復
  - Telegram 發送失敗記錄
  - 全局異常捕獲

- ✅ **程式碼品質**
  - 模組化設計
  - 依賴注入
  - 類型提示
  - 詳細註解
  - 符合 PEP 8

## 技術架構

```
用戶 (Telegram)
    ↓
TelegramBotHandler
    ↓
StockFetcher + AlertManager
    ↓
yfinance API + JSON Storage
    ↑
StockMonitorScheduler (每 5 分鐘)
```

## 資料流程

### 1. 新增監控流程

```
用戶: /add 2330.TW above 600
  → TelegramBotHandler.add_command()
  → StockFetcher.get_price() (驗證代碼)
  → AlertManager.add_alert()
  → 儲存到 watchlist.json
  → 回覆成功訊息
```

### 2. 背景檢查流程

```
Scheduler (每 5 分鐘)
  → AlertManager.get_all_symbols()
  → StockFetcher.get_multiple_prices()
  → AlertManager.check_alerts()
  → TelegramBotHandler.send_alert() (如果觸發)
  → 更新 notified 狀態
  → 儲存到 watchlist.json
```

### 3. 即時查價流程

```
用戶: /price AAPL
  → TelegramBotHandler.price_command()
  → StockFetcher.get_price()
  → 格式化價格
  → 回覆用戶
```

## 設定說明

### 環境變數 (.env)

```env
TELEGRAM_BOT_TOKEN=         # 必填：從 @BotFather 取得
WATCHLIST_FILE=             # 監控清單檔案路徑
LOG_LEVEL=                  # 日誌層級
LOG_DIR=                    # 日誌目錄
CHECK_INTERVAL_MINUTES=     # 檢查間隔（分鐘）
RETRY_ATTEMPTS=             # API 重試次數
RETRY_DELAY_SECONDS=        # 重試間隔（秒）
TIMEZONE=                   # 時區設定
```

### 監控清單結構 (watchlist.json)

```json
{
  "alerts": [
    {
      "id": "uuid-string",
      "user_id": 123456789,
      "symbol": "2330.TW",
      "target_price": 600.0,
      "condition": "above",
      "created_at": "2026-01-29T10:30:00",
      "notified": false,
      "last_notified_at": null,
      "enabled": true
    }
  ],
  "last_check": "2026-01-29T15:40:00"
}
```

## 下一步：開始使用

### 快速啟動（5 分鐘）

閱讀 [QUICKSTART.md](QUICKSTART.md)

### 詳細測試（30 分鐘）

閱讀 [TESTING_GUIDE.md](TESTING_GUIDE.md)

### 完整說明

閱讀 [README.md](README.md)

## 快速命令

```bash
# 安裝依賴
make install

# 執行測試
make test

# 啟動系統
make run

# 查看日誌
make logs

# 清理測試資料
make clean
```

## 系統需求

- Python 3.8+
- 網路連線
- Telegram 帳號
- 約 50MB 磁碟空間

## 依賴套件

```
yfinance==0.2.37          # 股票 API
python-telegram-bot==20.8  # Telegram Bot
APScheduler==3.10.4        # 背景排程
python-dotenv==1.0.1       # 環境變數
pytz==2024.1               # 時區處理
```

## 專案統計

- **總行數**：約 1,100 行 Python 程式碼
- **模組數**：6 個核心模組
- **命令數**：6 個 Telegram 命令
- **測試腳本**：2 個
- **文件頁數**：約 400 行文件

## 開發時程

按照計劃完整實作：
- ✅ 階段 1：專案初始化
- ✅ 階段 2：核心模組實作
- ✅ 階段 3：Telegram Bot 整合
- ✅ 階段 4：背景任務排程
- ✅ 階段 5：主程式整合
- ✅ 階段 6：文件和配置

## 注意事項

1. **首次使用前**：必須設定 `.env` 中的 `TELEGRAM_BOT_TOKEN`
2. **測試建議**：先執行 `make test` 確認環境正常
3. **日誌位置**：`logs/app.log` 和 `logs/error.log`
4. **監控清單**：`config/watchlist.json`（自動建立）
5. **安全性**：`.env` 和 `watchlist.json` 已加入 `.gitignore`

## 已知限制

1. **API 限制**：yfinance 為非官方 API，可能有查詢限制
2. **非交易時間**：查詢到的是最後收盤價
3. **延遲**：價格資料可能有數分鐘延遲
4. **檢查頻率**：預設 5 分鐘，不建議設太短（避免 API 限制）

## 擴充建議

未來可以加入的功能：
- 價格走勢圖表
- 技術指標監控（RSI、MA 等）
- 成交量監控
- 新聞通知整合
- 多個價格條件組合
- Web 儀表板
- 資料庫儲存（取代 JSON）
- 單元測試覆蓋

## 貢獻指南

如果要貢獻程式碼：
1. Fork 專案
2. 建立 feature 分支
3. 遵循現有的程式碼風格
4. 新增測試
5. 提交 Pull Request

## 授權

MIT License

## 作者

Stock Itching Team

---

**專案狀態**：✅ 已完成，可以開始使用

**最後更新**：2026-01-29
