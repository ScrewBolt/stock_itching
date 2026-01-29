# Stock Itching 快速啟動指南

這是一個 5 分鐘快速設定指南，讓你快速開始使用股票監控系統。

## 步驟 1：安裝依賴（30 秒）

```bash
pip install -r requirements.txt
```

## 步驟 2：建立 Telegram Bot（2 分鐘）

1. 在 Telegram 搜尋 `@BotFather`
2. 發送：`/newbot`
3. 設定 Bot 名稱：`My Stock Monitor`
4. 設定用戶名：`my_stock_monitor_bot`（必須以 bot 結尾）
5. 複製取得的 Token

## 步驟 3：設定環境變數（30 秒）

編輯 `.env` 檔案（已存在），將第一行改為：

```env
TELEGRAM_BOT_TOKEN=你的_Token_貼在這裡
```

其他設定保持不變。

## 步驟 4：啟動系統（10 秒）

```bash
python3 main.py
```

## 步驟 5：開始使用（1 分鐘）

在 Telegram 找到你的 Bot，發送：

```
/start
```

然後試試看：

```
/price AAPL
/add AAPL above 150
/list
```

就這麼簡單！🎉

## 常用命令速查

- `/price <代碼>` - 查詢價格
- `/add <代碼> <above/below> <價格>` - 新增監控
- `/list` - 查看我的監控
- `/remove <ID>` - 移除監控
- `/help` - 完整說明

## 停止系統

按 `Ctrl+C` 即可安全停止。

## 完整文件

- 詳細說明：[README.md](README.md)
- 測試指南：[TESTING_GUIDE.md](TESTING_GUIDE.md)

## 需要幫助？

如果遇到問題：
1. 確認 `.env` 的 Token 設定正確
2. 確認已安裝所有依賴套件
3. 查看 `logs/error.log` 找出錯誤原因
4. 閱讀完整的 README.md
