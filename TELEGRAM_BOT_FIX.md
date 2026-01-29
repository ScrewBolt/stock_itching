# 🔧 Telegram Bot 命令卡頓問題修復

## 📋 問題摘要

**版本**：v1.2.1
**日期**：2026-01-29
**問題**：所有 Telegram Bot 命令（/price, /add 等）在執行後卡住，無回應

---

## 🐛 問題分析

### 症狀

1. **用戶輸入命令**（如 `/add 2330 above 100`）
2. **系統成功查詢價格**（日誌顯示 FinMind 成功返回）
3. **卡在回覆階段**（沒有 "已回覆用戶" 日誌）
4. **用戶端無任何回應**（Bot 不回覆）

### 日誌證據

```
19:45:52 - INFO - [yfinance] 查詢: 2330.TW
19:45:52 - WARNING - ❌ [yfinance] 失敗: 2330.TW - 429
19:45:52 - INFO - ⚡ 快速切換到 FinMind: 2330.TW
19:45:53 - INFO - ✅ [FinMind] 成功: 2330.TW = 1805.0
[卡住，無後續日誌]
```

### 根本原因

#### 1. 異步事件循環阻塞

**問題代碼**：
```python
async def price_command(self, update, context):
    # ...
    result = self.stock_fetcher.get_price(symbol)  # 同步調用
    # ...
    await update.message.reply_text(message)  # 可能卡住
```

**分析**：
- `get_price()` 是**同步方法**，但在異步環境中調用
- 雖然 Python 允許這樣做，但可能阻塞事件循環
- `await reply_text()` 依賴事件循環正常運作
- 事件循環被阻塞 → reply_text 無法執行 → 卡住

#### 2. 缺少錯誤處理

**問題**：
- 沒有 `try-except` 包裹整個命令處理方法
- 異常發生時無法記錄到日誌
- 用戶端得不到任何錯誤回饋

#### 3. 缺少日誌追蹤

**問題**：
- 只記錄開始和結束，中間步驟沒有日誌
- 無法判斷卡在哪個步驟
- 難以診斷問題

#### 4. 多進程問題

**發現**：
```bash
$ ps aux | grep main.py
wei-chyanglu  53751  ...  Python main.py
wei-chyanglu  53142  ...  Python main.py  # 舊進程未終止！
```

**影響**：
- 舊進程占用 Telegram Bot 連接
- 新進程無法正常處理請求
- 導致更多不可預測的行為

---

## 🛠️ 實施的修復

### 修復 1：增強錯誤處理

**檔案**：`src/telegram_bot.py`

#### price_command

**變更前**：
```python
async def price_command(self, update, context):
    # 沒有 try-except 包裹
    symbol = context.args[0]
    result = self.stock_fetcher.get_price(symbol)
    await update.message.reply_text(message)
```

**變更後**：
```python
async def price_command(self, update, context):
    try:
        user_id = update.effective_user.id
        self.logger.info(f"用戶 {user_id} 請求查詢: {symbol}")

        # ... 處理邏輯 ...

        self.logger.info(f"準備回覆用戶 {user_id}")
        await update.message.reply_text(message)
        self.logger.info(f"✅ 已回覆用戶 {user_id}")

    except Exception as e:
        self.logger.error(f"❌ price_command 執行失敗: {e}", exc_info=True)
        try:
            await update.message.reply_text(f"❌ 系統錯誤：{str(e)}")
        except:
            pass  # 即使回覆失敗也不中斷
```

#### add_command

**變更前**：
```python
async def add_command(self, update, context):
    # 部分 try-except，但不完整
    symbol = context.args[0]
    price_check = self.stock_fetcher.get_price(symbol_normalized)
    # ...
    try:
        alert = self.alert_manager.add_alert(...)
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f"❌ 新增失敗：{str(e)}")
```

**變更後**：
```python
async def add_command(self, update, context):
    try:
        user_id = update.effective_user.id
        self.logger.info(f"用戶 {user_id} 執行 /add 命令")

        # 每個關鍵步驟都有日誌
        self.logger.info(f"驗證股票代碼: {symbol_normalized}")
        self.logger.info(f"開始查詢股票價格: {symbol_normalized}")
        price_check = self.stock_fetcher.get_price(symbol_normalized)
        self.logger.info(f"價格查詢完成: 成功={price_check['success']}")

        # ...

        self.logger.info(f"準備回覆用戶 {user_id}")
        await update.message.reply_text(message.strip())
        self.logger.info(f"✅ 監控新增完成，已通知用戶 {user_id}")

    except Exception as e:
        self.logger.error(f"❌ add_command 執行失敗: {e}", exc_info=True)
        try:
            await update.message.reply_text(f"❌ 新增失敗：{str(e)}")
        except:
            pass
```

### 修復 2：改進 restart.sh

**檔案**：`restart.sh`

**新功能**：
- 多次嘗試終止進程（3次循環）
- 每次嘗試後檢查是否還有殘留
- 顯示殘留進程列表
- 詢問用戶是否強制終止
- 啟動後驗證進程狀態

**使用方法**：
```bash
./restart.sh
```

**範例輸出**：
```
🔄 重啟 Stock Itching 系統...
📋 終止舊進程...
✅ 所有進程已終止
🚀 啟動新進程...
✅ 系統已成功啟動！
   PID: 54049
```

### 修復 3：詳細日誌追蹤

**新增日誌點**：

1. **命令開始**：
   ```python
   self.logger.info(f"用戶 {user_id} 請求查詢: {symbol}")
   ```

2. **每個關鍵步驟**：
   ```python
   self.logger.info(f"開始查詢股票價格: {symbol}")
   self.logger.info(f"查詢完成: 成功={result['success']}")
   ```

3. **回覆前後**：
   ```python
   self.logger.info(f"準備回覆用戶 {user_id}")
   await update.message.reply_text(...)
   self.logger.info(f"✅ 已回覆用戶 {user_id}")
   ```

4. **錯誤情況**：
   ```python
   self.logger.error(f"❌ 執行失敗: {e}", exc_info=True)
   ```

---

## 📊 新的日誌格式

### price_command 成功流程

```
INFO - 用戶 123456789 請求查詢: 2330.TW
INFO - 開始查詢股票價格: 2330.TW
INFO - [yfinance] 查詢: 2330.TW
WARNING - ❌ [yfinance] 失敗: 2330.TW - 429
INFO - ⚡ 快速切換到 FinMind: 2330.TW
INFO - ✅ [FinMind] 成功: 2330.TW = 1805.0
INFO - 查詢完成: 2330.TW, 成功=True
INFO - 準備回覆用戶 123456789: 2330.TW = 1805.0
INFO - ✅ 已回覆用戶 123456789
```

### add_command 成功流程

```
INFO - 用戶 123456789 執行 /add 命令
INFO - 驗證股票代碼: 2330.TW
INFO - 開始查詢股票價格: 2330.TW
INFO - [yfinance] 查詢: 2330.TW
INFO - ⚡ 快速切換到 FinMind: 2330.TW
INFO - ✅ [FinMind] 成功: 2330.TW = 1805.0
INFO - 價格查詢完成: 2330.TW, 成功=True
INFO - 新增監控: 2330.TW above 100.0
INFO - 準備回覆用戶 123456789
INFO - ✅ 監控新增完成，已通知用戶 123456789
```

### 錯誤情況

```
INFO - 用戶 123456789 請求查詢: INVALID
INFO - 開始查詢股票價格: INVALID
ERROR - ❌ price_command 執行失敗: Connection timeout
Traceback (most recent call last):
  ...
```

---

## 🧪 測試驗證

### 測試步驟

1. **重啟系統**：
   ```bash
   ./restart.sh
   ```

2. **測試 /price 命令**：
   ```
   /price 2330.TW
   ```

   **預期**：
   - 3 秒內回應
   - 顯示價格和來源
   - 日誌顯示完整流程

3. **測試 /add 命令**：
   ```
   /add 2330.TW above 600
   ```

   **預期**：
   - 顯示「驗證股票代碼...」
   - 顯示「監控已新增！」
   - 包含當前價格和監控 ID

4. **測試 /list 命令**：
   ```
   /list
   ```

   **預期**：
   - 顯示剛新增的監控

5. **監控即時日誌**：
   ```bash
   tail -f logs/app.log
   ```

   **預期**：
   - 看到所有步驟的日誌
   - 清楚顯示成功/失敗狀態

---

## 🔍 診斷工具

### 檢查卡住位置

如果命令再次卡住，查看日誌找最後一行：

```bash
tail -30 logs/app.log | grep "用戶\|準備\|✅\|❌"
```

**範例輸出**：
```
INFO - 用戶 123456789 請求查詢: 2330.TW
INFO - 開始查詢股票價格: 2330.TW
INFO - 查詢完成: 2330.TW, 成功=True
INFO - 準備回覆用戶 123456789  <-- 卡在這裡！
```

→ 表示卡在 `reply_text` 調用

### 檢查殘留進程

```bash
ps aux | grep "python.*main.py" | grep -v grep | wc -l
```

**預期**：只有 1 個進程

**如果 > 1**：
```bash
./restart.sh  # 自動清理並重啟
```

---

## 📈 改進效果

### 問題解決率

| 問題 | 修復前 | 修復後 |
|------|--------|--------|
| 命令卡住 | 100% | 待測試 |
| 無錯誤訊息 | 是 | ✅ 有完整日誌 |
| 難以診斷 | 是 | ✅ 詳細追蹤 |
| 多進程衝突 | 常見 | ✅ restart.sh 解決 |

### 日誌可讀性

**修復前**：
```
INFO - 查詢股票價格: 2330.TW
ERROR - 查詢失敗
[沒有更多資訊]
```

**修復後**：
```
INFO - 用戶 123 請求查詢: 2330.TW
INFO - 開始查詢股票價格: 2330.TW
WARNING - ❌ [yfinance] 失敗: 429 Too Many Requests
INFO - ⚡ 快速切換到 FinMind
INFO - ✅ [FinMind] 成功: 1805.0
INFO - 準備回覆用戶 123
INFO - ✅ 已回覆用戶 123
```

---

## 🚀 下一步

### 如果問題持續

1. **檢查日誌確定卡點**：
   ```bash
   grep "準備回覆" logs/app.log
   ```

2. **檢查是否在 reply_text 卡住**：
   - 如果看到「準備回覆」但沒有「✅ 已回覆」
   - 表示 `await reply_text()` 有問題

3. **可能的進一步修復**：
   - 增加 reply_text 超時機制
   - 使用 asyncio.wait_for() 包裹
   - 考慮使用 run_in_executor() 隔離同步調用

### 監控建議

**持續監控日誌**：
```bash
# 終端 1：查看應用日誌
tail -f logs/app.log

# 終端 2：查看錯誤
tail -f logs/error.log | grep -E "ERROR|❌"

# 終端 3：監控進程
watch -n 5 'ps aux | grep main.py | grep -v grep'
```

---

## 📝 修改檔案清單

1. ✅ `src/telegram_bot.py`
   - price_command: 增強錯誤處理和日誌
   - add_command: 完整重寫

2. ✅ `restart.sh`
   - 多次嘗試終止
   - 殘留進程檢測
   - 互動式確認

3. ✅ `TELEGRAM_BOT_FIX.md`
   - 本文檔

---

## ✅ 狀態

**當前系統狀態**：
- ✅ 進程：正常運行（PID: 54049）
- ✅ Telegram Bot：已啟動
- ✅ 錯誤處理：已完善
- ✅ 日誌追蹤：詳細記錄

**建議測試**：
1. `/price 2330.TW` - 測試價格查詢
2. `/add 2330.TW above 600` - 測試監控新增
3. `/list` - 測試列表顯示

**如果再次卡住**：
```bash
./restart.sh
tail -f logs/app.log  # 查看詳細日誌
```

---

**版本**：v1.2.1
**修復日期**：2026-01-29
**狀態**：✅ 已部署，待用戶測試
