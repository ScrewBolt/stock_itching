# Stock Itching - 股票價格監控系統 📈

> 一個基於 Python 和 Telegram Bot 的智能股票價格監控系統，支援台股和美股即時監控與價格查詢。

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

## ✨ 功能特色

- 🎯 **價格監控**：設定目標價格，達標時自動通知
- 📊 **即時查價**：隨時查詢任何股票的當前價格
- 🔔 **智能通知**：觸發後防重複通知，價格回到安全範圍時自動重置
- 🌏 **多市場支援**：支援台股（.TW）和美股
- ⏰ **背景運行**：每 5 分鐘自動檢查所有監控
- 💾 **持久化儲存**：監控清單自動儲存到 JSON 檔案
- 🛡️ **穩定可靠**：完整的錯誤處理和重試機制

## 🚀 快速開始（5 分鐘）

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 設定環境變數（填入你的 Telegram Bot Token）
cp .env.example .env
# 編輯 .env 填入 TELEGRAM_BOT_TOKEN

# 3. 啟動系統
python main.py
```

然後在 Telegram 找到你的 Bot，發送 `/start` 開始使用！

📖 詳細步驟請參考 [快速啟動指南](QUICKSTART.md)

## 📋 目錄

- [功能特色](#-功能特色)
- [快速開始](#-快速開始5-分鐘)
- [系統需求](#-系統需求)
- [安裝步驟](#-安裝步驟)
- [使用說明](#-使用說明)
- [命令範例](#-bot-命令範例)
- [進階功能](#-防重複通知機制)
- [文件](#-相關文件)
- [常見問題](#-常見問題)

## 💻 系統需求

- Python 3.8 或以上版本
- 穩定的網路連線
- Telegram 帳號

## 📦 技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| Python | 3.8+ | 主要語言 |
| yfinance | 0.2.37 | 股票價格 API |
| python-telegram-bot | 20.8 | Telegram Bot 框架 |
| APScheduler | 3.10.4 | 背景任務排程 |

## 🔧 安裝步驟

### 🪟 Windows 用戶專用指引

<details>
<summary>點擊展開 Windows 安裝步驟</summary>

#### 1. 安裝 Python

1. 前往 [Python 官網](https://www.python.org/downloads/) 下載 Python 3.8 或以上版本
2. 執行安裝程式時，**務必勾選「Add Python to PATH」**
3. 安裝完成後，開啟「命令提示字元」（cmd）或「PowerShell」
4. 驗證安裝：
   ```cmd
   python --version
   ```
   應該顯示 Python 3.8 或以上版本

#### 2. 下載專案

```cmd
cd C:\Users\你的使用者名稱\Documents
git clone <專案網址>
cd stock_itching
```

或直接下載 ZIP 檔案並解壓縮。

#### 3. 安裝依賴套件

```cmd
pip install -r requirements.txt
```

如果遇到權限問題，試試：
```cmd
pip install --user -r requirements.txt
```

#### 4. 設定環境變數

```cmd
copy .env.example .env
notepad .env
```

在記事本中編輯 `.env` 檔案，填入你的 Telegram Bot Token：
```
TELEGRAM_BOT_TOKEN=你的_Bot_Token_在這裡
```

儲存後關閉記事本。

#### 5. 啟動系統

```cmd
python main.py
```

#### 6. 停止系統

按 `Ctrl+C` 停止程式。

#### ⚠️ Windows 常見問題

**Q: 顯示「python 不是內部或外部命令」**
- A: Python 沒有加入 PATH，重新安裝 Python 並勾選「Add Python to PATH」

**Q: 安裝套件時出現錯誤**
- A: 嘗試使用 `python -m pip install -r requirements.txt`

**Q: 中文顯示亂碼**
- A: 在 cmd 執行 `chcp 65001` 切換為 UTF-8 編碼

**Q: 如何在背景執行？**
- A: 可以使用 Windows 工作排程器，或安裝 `pythonw` 執行：
  ```cmd
  pythonw main.py
  ```

</details>

---

### 步驟 1：安裝 Python 依賴

**Mac/Linux:**
```bash
pip install -r requirements.txt
```

**Windows:**
```cmd
pip install -r requirements.txt
```

### 步驟 2：建立 Telegram Bot

1. 在 Telegram 搜尋 `@BotFather`
2. 發送 `/newbot` 命令
3. 依照指示設定 Bot 名稱和用戶名
4. 取得 Bot Token（格式：`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 步驟 3：設定環境變數

複製環境變數範例檔案：

```bash
cp .env.example .env
```

編輯 `.env` 檔案，填入你的 Bot Token：

```env
TELEGRAM_BOT_TOKEN=你的_Bot_Token
WATCHLIST_FILE=config/watchlist.json
LOG_LEVEL=INFO
LOG_DIR=logs
CHECK_INTERVAL_MINUTES=5
RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=5
TIMEZONE=Asia/Taipei
```

### 步驟 4：啟動系統

```bash
python main.py
```

✅ 啟動成功後你會看到：
```
[INFO] Stock Itching 股票監控系統啟動
[INFO] 模組初始化完成
[INFO] Telegram Bot 已啟動
[INFO] 系統啟動成功！
```

系統會自動：
- ✅ 初始化所有模組
- ✅ 立即執行一次價格檢查
- ✅ 每 5 分鐘自動檢查所有監控
- ✅ 在背景持續運行

### 停止系統

按 `Ctrl+C` 即可優雅關閉（會等待當前任務完成）

## 📱 使用說明

### Bot 命令總覽

在 Telegram 中找到你的 Bot，可使用以下命令：

| 命令 | 功能 | 範例 |
|------|------|------|
| `/start` | 開始使用 | `/start` |
| `/help` | 幫助說明 | `/help` |
| `/price <代碼>` | 查詢價格 | `/price AAPL` |
| `/add <代碼> <條件> <價格>` | 新增監控 | `/add 2330.TW above 600` |
| `/list` | 監控清單 | `/list` |
| `/remove <ID>` | 移除監控 | `/remove abc123` |
| `/clear` | 清空所有監控 | `/clear` |
| `/clearstock <代碼>` | 清空指定股票監控 | `/clearstock 2330.TW` |

## 💡 Bot 命令範例

### 基本命令

**🎬 `/start` - 開始使用**
```
你: /start
Bot: 🎉 歡迎使用 Stock Itching！...
```

**❓ `/help` - 幫助說明**
```
你: /help
Bot: 📖 使用說明...
```

### 價格查詢

**📊 `/price <股票代碼>`**

查詢台股（台積電）：
```
你: /price 2330.TW
Bot: 📊 2330.TW
     💰 當前價格：NT$ 605.00
     🕐 查詢時間：2026-01-29 14:30:00
```

查詢美股（蘋果）：
```
你: /price AAPL
Bot: 📊 AAPL
     💰 當前價格：$ 150.25
     🕐 查詢時間：2026-01-29 14:30:00
```

自動補 .TW（輸入純數字）：
```
你: /price 2330
Bot: 📊 2330.TW
     💰 當前價格：NT$ 605.00
```

### 監控管理

**➕ `/add <代碼> <above|below> <價格>`**

新增台股監控：
```
你: /add 2330.TW above 600
Bot: ✅ 監控已新增！
     📊 股票：2330.TW
     🎯 條件：價格高於 NT$ 600.00
     💰 當前價格：NT$ 605.00
```

新增美股監控：
```
你: /add AAPL below 140
Bot: ✅ 監控已新增！
     📊 股票：AAPL
     🎯 條件：價格低於 $ 140.00
```

**📋 `/list` - 查看監控清單**
```
你: /list
Bot: 📋 你的監控清單：

     1. 2330.TW
        條件：高於 600.0
        狀態：⏳ 監控中
        ID：abc123...

     2. AAPL
        條件：低於 140.0
        狀態：🔔 已通知
        ID：def456...
```

**❌ `/remove <ID>` - 移除監控**
```
你: /remove abc123
Bot: ✅ 已移除監控：2330.TW
```

**🗑️ `/clear` - 清空所有監控**
```
你: /clear
Bot: ✅ 已清空 5 個監控！
     使用 /add 可以重新新增監控。
```

**🗑️ `/clearstock <股票代碼>` - 清空指定股票監控**
```
你: /clearstock 2330.TW
Bot: ✅ 已清空 2330.TW 的 3 個監控！
```

### 自動通知

當價格觸發條件時，你會收到：
```
Bot: 🔔 價格警報觸發！

     📊 股票：2330.TW
     💰 當前價格：NT$ 610.00
     🎯 目標價格：高於 NT$ 600.00

     條件已達成，請注意！
```

## 股票代碼格式

### 台股
- 完整格式：`2330.TW`（台積電）
- 簡短格式：`2330`（系統會自動加 .TW）

### 美股
- 直接使用股票代號：`AAPL`（蘋果）、`GOOGL`（Google）、`MSFT`（微軟）

## 防重複通知機制

系統採用智能通知機制：

1. **首次觸發**：價格達到設定條件時發送通知
2. **防重複**：觸發後標記為「已通知」，不會重複提醒
3. **自動重置**：當價格回到安全範圍（目標價 ±2%）時，自動重置通知狀態

範例：
- 設定「2330.TW 高於 600」
- 價格達到 610 → 發送通知並標記
- 價格持續在 600 以上 → 不再通知
- 價格降到 588 以下 → 重置標記
- 價格再次超過 600 → 再次通知

## 📁 專案結構

```
stock_itching/
├── 📄 main.py                    # 主程式入口
├── 📄 requirements.txt           # Python 依賴套件
├── 📄 .env.example               # 環境變數範例
├── 📄 .env                       # 環境變數（需建立）
├── 📄 Makefile                   # 常用命令
│
├── 📂 src/                       # 核心模組
│   ├── utils.py                 # 工具函數
│   ├── stock_fetcher.py         # 股票價格查詢
│   ├── alert_manager.py         # 監控管理（核心）
│   ├── telegram_bot.py          # Bot 處理器
│   └── scheduler.py             # 背景排程
│
├── 📂 config/
│   └── watchlist.json           # 監控清單（自動生成）
│
├── 📂 logs/
│   ├── app.log                  # 一般日誌（自動生成）
│   └── error.log                # 錯誤日誌（自動生成）
│
└── 📂 docs/                      # 文件
    ├── README.md
    ├── QUICKSTART.md
    ├── TESTING_GUIDE.md
    └── ...
```

## 日誌系統

系統會自動記錄運行日誌：

- **logs/app.log**：一般運行日誌（INFO 層級）
- **logs/error.log**：錯誤和異常日誌（ERROR 層級）
- 自動輪轉：每個檔案最大 10MB，保留 5 個備份

## 📚 相關文件

- **[快速啟動指南](QUICKSTART.md)** - 5 分鐘快速體驗
- **[測試指南](TESTING_GUIDE.md)** - 完整的測試流程
- **[專案總覽](PROJECT_SUMMARY.md)** - 專案架構和統計
- **[實作報告](IMPLEMENTATION_REPORT.md)** - 詳細實作說明
- **[Claude AI 文件](claude.md)** - 給 AI 助手的技術文件

## ❓ 常見問題

### Q: 查詢失敗怎麼辦？
A: 系統會自動重試 3 次（間隔 5 秒）。如果仍然失敗：
- 確認股票代碼是否正確
- 檢查網路連線
- 確認是否在交易時間（非交易時間可能查不到最新價格）

### Q: 非交易時間會查到什麼價格？
A: 會查到該市場的最後收盤價或前一個交易日的價格。

### Q: 可以同時監控多少個股票？
A: 理論上無限制，但建議不要超過 50 個（API 查詢可能較慢）。

### Q: 監控資料會遺失嗎？
A: 不會。所有監控都儲存在 `config/watchlist.json`，重啟後會自動載入。

### Q: 如何修改檢查頻率？
A: 編輯 `.env` 檔案中的 `CHECK_INTERVAL_MINUTES` 參數。

### Q: 可以多人使用同一個 Bot 嗎？
A: 可以。每個用戶的監控清單是獨立的，互不干擾。

## 錯誤處理

系統具備完善的錯誤處理機制：

- **API 請求失敗**：自動重試，失敗則記錄並跳過
- **JSON 檔案損壞**：使用預設空白結構
- **Telegram 發送失敗**：記錄錯誤但不中斷運行
- **優雅關閉**：Ctrl+C 時等待當前任務完成

## 🔧 進階使用

### 使用 Makefile（Mac/Linux）

```bash
make install    # 安裝依賴
make test       # 執行測試
make run        # 啟動系統
make logs       # 查看日誌
make clean      # 清理檔案
```

### 修改檢查頻率

編輯 `.env` 檔案：
```bash
CHECK_INTERVAL_MINUTES=1  # 改為 1 分鐘（測試用）
```

### 查看日誌

```bash
# 即時查看一般日誌
tail -f logs/app.log

# 即時查看錯誤日誌
tail -f logs/error.log
```

## 🛡️ 技術架構

- **Python 3.8+**：主要程式語言
- **yfinance**：免費股票 API（支援台股和美股）
- **python-telegram-bot**：Telegram Bot 框架
- **APScheduler**：背景任務排程
- **python-dotenv**：環境變數管理

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

MIT License

## 👥 作者

Stock Itching Team

## 📝 更新日誌

### v1.0.0 (2026-01-29)
- ✅ 初始版本
- ✅ 支援台股和美股監控
- ✅ 實作價格查詢和自動通知功能
- ✅ 防重複通知機制
- ✅ 完整的錯誤處理和日誌系統

---

⭐ 如果這個專案對你有幫助，請給我們一個星星！
