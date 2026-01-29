# 更新日誌

## v1.1.0 (2026-01-29)

### ✨ 新增功能

#### 1. 清空監控功能

新增三種清空監控的方式：

**`/clear` - 清空所有監控**
- 一鍵清空用戶的所有監控
- 顯示清空數量
- 實作：`AlertManager.clear_all_alerts()`

**`/clearstock <股票代碼>` - 清空指定股票監控**
- 清空指定股票的所有監控（例如：`/clearstock 2330.TW`）
- 支援自動標準化股票代碼
- 實作：`AlertManager.clear_alerts_by_symbol()`

**原有 `/remove <ID>`**
- 移除單一指定 ID 的監控
- 支援部分 ID 匹配（只需輸入前幾個字元）

#### 2. Windows 用戶支援

在 README.md 新增完整的 Windows 安裝指引：

- Python 安裝步驟（強調 Add to PATH）
- 專案下載和設定
- 依賴套件安裝
- 環境變數設定（使用 Windows 命令）
- Windows 特有問題解決方案
- 背景執行建議

### 📝 文件更新

#### README.md 重大改版

**視覺優化**：
- 加入專案狀態徽章（Python 版本、授權、狀態）
- 表格化命令總覽
- Emoji 圖示增強可讀性
- 優化排版和結構

**新增區段**：
- 📋 目錄導航
- 🚀 快速開始（5 分鐘）
- 🪟 Windows 用戶專用指引（可摺疊）
- 💻 系統需求
- 📦 技術棧表格
- 💡 Bot 命令範例（實際對話範例）
- 📚 相關文件連結
- 🔧 進階使用

**命令範例增強**：
- 真實對話格式
- Bot 回應範例
- Emoji 圖示
- 清晰的輸入輸出

#### claude.md 更新

- 新增清空監控功能說明
- 更新命令處理器列表
- 加入 `clear_all_alerts()` 和 `clear_alerts_by_symbol()` 方法說明
- 新增常見開發任務：清空監控功能實作

### 🔧 程式碼更新

#### src/alert_manager.py

**新增方法**：
```python
def clear_all_alerts(user_id: int) -> int:
    """清空用戶的所有監控"""

def clear_alerts_by_symbol(user_id: int, symbol: str) -> int:
    """清空用戶指定股票的所有監控"""
```

#### src/telegram_bot.py

**新增命令處理器**：
```python
async def clear_command():
    """處理 /clear 命令 - 清空所有監控"""

async def clearstock_command():
    """處理 /clearstock 命令 - 清空指定股票的所有監控"""
```

**更新說明訊息**：
- `start_command()` - 加入新命令說明
- `help_command()` - 加入新命令詳細說明

**命令註冊**：
- 註冊 `/clear` 命令
- 註冊 `/clearstock` 命令

### 📊 統計

**程式碼變更**：
- 新增程式碼：約 80 行
- 修改檔案：3 個核心檔案
- 新增命令：2 個

**文件變更**：
- README.md：重大改版，新增約 150 行
- claude.md：新增約 30 行
- 新增 UPDATE_LOG.md

### 🧪 測試建議

測試新功能：

```bash
# 1. 測試清空所有監控
/add 2330.TW above 600
/add AAPL below 150
/add GOOGL above 140
/list
/clear
/list  # 應該顯示沒有監控

# 2. 測試清空指定股票
/add 2330.TW above 600
/add 2330.TW below 500
/add AAPL below 150
/list
/clearstock 2330.TW
/list  # 應該只剩 AAPL

# 3. 測試 Windows 安裝
按照 README.md 的 Windows 指引安裝
```

### 🔄 向後兼容性

✅ 完全向後兼容
- 所有原有功能保持不變
- 原有命令功能不受影響
- 原有資料格式不變

### 📋 已知問題

無

### 🚀 下個版本計劃

可能的未來功能：
- [ ] 資料庫儲存（取代 JSON）
- [ ] 批次匯入監控
- [ ] 監控分組功能
- [ ] 價格走勢圖表
- [ ] 技術指標監控

---

**發布日期**：2026-01-29
**影響範圍**：功能增強、文件更新
**升級建議**：直接覆蓋檔案即可
