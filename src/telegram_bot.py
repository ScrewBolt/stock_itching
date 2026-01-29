"""Telegram Bot 處理器模組"""
import asyncio
import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TimedOut, NetworkError
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .alert_manager import AlertManager
from .stock_fetcher import StockFetcher
from .utils import format_price


class TelegramBotHandler:
    """Telegram Bot 處理類別"""

    def __init__(
        self,
        token: str,
        alert_manager: AlertManager,
        stock_fetcher: StockFetcher
    ):
        """
        初始化 Telegram Bot

        Args:
            token: Telegram Bot Token
            alert_manager: 監控管理器
            stock_fetcher: 股票查詢器
        """
        self.token = token
        self.alert_manager = alert_manager
        self.stock_fetcher = stock_fetcher
        self.logger = logging.getLogger(__name__)
        self.application: Optional[Application] = None

    async def safe_reply(self, update: Update, text: str, max_retries: int = 3, **kwargs):
        """
        安全地發送訊息，帶重試機制

        Args:
            update: Telegram Update 對象
            text: 訊息內容
            max_retries: 最大重試次數
            **kwargs: 其他 reply_text 參數
        """
        for attempt in range(max_retries):
            try:
                await update.message.reply_text(text, **kwargs)
                return True
            except (TimedOut, NetworkError) as e:
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"發送訊息超時 (嘗試 {attempt + 1}/{max_retries})，重試中..."
                    )
                    await asyncio.sleep(1)
                else:
                    self.logger.error(f"發送訊息失敗，已重試 {max_retries} 次: {e}")
                    raise
            except Exception as e:
                self.logger.error(f"發送訊息時發生非預期錯誤: {e}", exc_info=True)
                raise
        return False

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /start 命令"""
        welcome_message = """
🎉 歡迎使用 Stock Itching 股票監控 Bot！

我可以幫你監控股票價格，當價格達到你設定的條件時會自動通知你。

📋 可用命令：
/help - 顯示幫助訊息
/price <代碼> - 查詢股票當前價格
/add <代碼> <above/below> <價格> - 新增監控
/list - 列出我的監控清單
/remove <ID> - 移除指定監控
/clear - 清空所有監控
/clearstock <代碼> - 清空指定股票的所有監控

💡 股票代碼格式：
• 台股：2330.TW 或 2330（會自動加 .TW）
• 美股：AAPL、GOOGL 等

範例：
/price 2330.TW
/add AAPL above 150
/clearstock 2330.TW
        """
        await update.message.reply_text(welcome_message)
        self.logger.info(f"用戶 {update.effective_user.id} 開始使用")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /help 命令"""
        help_message = """
📖 Stock Itching 使用說明

🔍 查詢股票價格：
/price <股票代碼>
範例：/price 2330.TW 或 /price AAPL

➕ 新增價格監控：
/add <股票代碼> <above/below> <目標價格>
• above：當價格高於目標時通知
• below：當價格低於目標時通知
範例：
/add 2330.TW above 600
/add AAPL below 140

📋 查看監控清單：
/list

❌ 移除監控：
/remove <監控ID>
（先用 /list 查看 ID）
範例：/remove abc-123-def

🗑️ 清空監控：
/clear - 清空所有監控
/clearstock <股票代碼> - 清空指定股票的監控
範例：
/clearstock 2330.TW

💡 提示：
• 系統每 5 分鐘自動檢查一次價格
• 觸發通知後不會重複提醒（除非價格回到安全範圍）
• 台股代碼可以只輸入數字，系統會自動加 .TW
        """
        await update.message.reply_text(help_message)

    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /price 命令"""
        try:
            if not context.args or len(context.args) != 1:
                await update.message.reply_text(
                    "❌ 用法錯誤！\n正確格式：/price <股票代碼>\n範例：/price 2330.TW"
                )
                return

            symbol = context.args[0]
            user_id = update.effective_user.id
            self.logger.info(f"用戶 {user_id} 請求查詢: {symbol}")

            await update.message.reply_text(f"🔍 查詢中：{symbol}...")

            # 查詢價格（在 thread 中執行，避免阻塞事件循環）
            self.logger.info(f"開始查詢股票價格: {symbol}")
            result = await asyncio.to_thread(self.stock_fetcher.get_price, symbol)
            self.logger.info(f"查詢完成: {symbol}, 成功={result['success']}")

            if result["success"]:
                price_str = format_price(result["price"], result["currency"])
                source = result.get("source", "unknown")
                message = f"""
📊 {result['symbol']}
💰 當前價格：{price_str}
🔹 資料來源：{source}
🕐 查詢時間：{result['timestamp'][:19]}
                """
                self.logger.info(f"準備回覆用戶 {user_id}: {symbol} = {result['price']}")
                await update.message.reply_text(message.strip())
                self.logger.info(f"✅ 已回覆用戶 {user_id}")
            else:
                error_msg = result.get('error', '未知錯誤')
                self.logger.warning(f"查詢失敗: {symbol}, 錯誤: {error_msg}")
                await update.message.reply_text(
                    f"❌ 查詢失敗：{symbol}\n錯誤：{error_msg}\n"
                    f"請確認股票代碼是否正確。"
                )

        except Exception as e:
            self.logger.error(f"❌ price_command 執行失敗: {e}", exc_info=True)
            try:
                await update.message.reply_text(f"❌ 系統錯誤：{str(e)}")
            except:
                pass

    async def add_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /add 命令"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"用戶 {user_id} 執行 /add 命令")

            if not context.args or len(context.args) != 3:
                await update.message.reply_text(
                    "❌ 用法錯誤！\n"
                    "正確格式：/add <股票代碼> <above/below> <目標價格>\n"
                    "範例：/add 2330.TW above 600"
                )
                return

            symbol = context.args[0]
            condition = context.args[1].lower()

            try:
                target_price = float(context.args[2])
            except ValueError:
                await update.message.reply_text("❌ 目標價格必須是數字！")
                return

            if condition not in ["above", "below"]:
                await update.message.reply_text("❌ 條件必須是 'above' 或 'below'！")
                return

            # 先驗證股票代碼
            symbol_normalized = self.stock_fetcher.normalize_symbol(symbol)
            self.logger.info(f"驗證股票代碼: {symbol_normalized}")

            await self.safe_reply(update, f"⏳ 驗證股票代碼：{symbol_normalized}...")

            self.logger.info(f"開始查詢股票價格: {symbol_normalized}")
            price_check = await asyncio.to_thread(self.stock_fetcher.get_price, symbol_normalized)
            self.logger.info(f"價格查詢完成: {symbol_normalized}, 成功={price_check['success']}")

            if not price_check["success"]:
                await update.message.reply_text(
                    f"❌ 無法查詢到此股票：{symbol_normalized}\n"
                    f"請確認代碼是否正確。"
                )
                return

            # 新增監控
            self.logger.info(f"新增監控: {symbol_normalized} {condition} {target_price}")
            alert = self.alert_manager.add_alert(
                user_id=user_id,
                symbol=symbol_normalized,
                target_price=target_price,
                condition=condition
            )

            # 檢查是否重複（add_alert 返回 None 表示忽略重複警報）
            if alert is None:
                condition_text = "高於" if condition == "above" else "低於"
                price_str = format_price(target_price, price_check["currency"])
                current_price_str = format_price(price_check['price'], price_check['currency'])

                message = f"""
ℹ️ 此監控已存在，未重複新增

📊 股票：{symbol_normalized}
🎯 條件：價格 {condition_text} {price_str}
💰 當前價格：{current_price_str}

使用 /list 查看所有監控。
                """
                self.logger.info(f"通知用戶 {user_id} 重複警報已忽略")
                await self.safe_reply(update, message.strip())
                return

            condition_text = "高於" if condition == "above" else "低於"
            price_str = format_price(target_price, price_check["currency"])
            current_price_str = format_price(price_check['price'], price_check['currency'])

            message = f"""
✅ 監控已新增！

📊 股票：{alert['symbol']}
🎯 條件：價格 {condition_text} {price_str}
🆔 監控ID：{alert['id'][:8]}...
💰 當前價格：{current_price_str}

系統會每 5 分鐘檢查一次，達標時會通知你。
使用 /list 查看所有監控。
            """

            self.logger.info(f"準備回覆用戶 {user_id}")
            await self.safe_reply(update, message.strip())
            self.logger.info(f"✅ 監控新增完成，已通知用戶 {user_id}")

        except Exception as e:
            self.logger.error(f"❌ add_command 執行失敗: {e}", exc_info=True)
            try:
                await update.message.reply_text(f"❌ 新增失敗：{str(e)}")
            except:
                pass

    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /list 命令"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"用戶 {user_id} 執行 /list 命令")
            alerts = self.alert_manager.list_alerts(user_id)

            if not alerts:
                await self.safe_reply(
                    update,
                    "📋 你目前沒有任何監控。\n使用 /add 命令來新增監控。"
                )
                return

            message_parts = ["📋 你的監控清單：\n"]

            for i, alert in enumerate(alerts, 1):
                condition_text = "高於" if alert["condition"] == "above" else "低於"
                status = "🔔 已通知" if alert["notified"] else "⏳ 監控中"

                message_parts.append(
                    f"{i}. {alert['symbol']}\n"
                    f"   條件：{condition_text} {alert['target_price']}\n"
                    f"   狀態：{status}\n"
                    f"   ID：{alert['id'][:8]}...\n"
                )

            message_parts.append(
                f"\n共 {len(alerts)} 個監控\n使用 /remove <ID> 可移除監控"
            )

            await self.safe_reply(update, "\n".join(message_parts))
            self.logger.info(f"✅ 已回覆用戶 {user_id} 監控清單")

        except Exception as e:
            self.logger.error(f"❌ list_command 執行失敗: {e}", exc_info=True)
            try:
                await update.message.reply_text(f"❌ 查詢失敗：{str(e)}")
            except:
                pass

    async def remove_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /remove 命令"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"用戶 {user_id} 執行 /remove 命令")

            if not context.args or len(context.args) != 1:
                await self.safe_reply(
                    update,
                    "❌ 用法錯誤！\n"
                    "正確格式：/remove <監控ID>\n"
                    "先使用 /list 查看監控 ID"
                )
                return

            alert_id_prefix = context.args[0]

            # 尋找匹配的監控 ID
            alerts = self.alert_manager.list_alerts(user_id)
            matched_alert = None

            for alert in alerts:
                if alert["id"].startswith(alert_id_prefix):
                    matched_alert = alert
                    break

            if not matched_alert:
                await self.safe_reply(
                    update,
                    f"❌ 找不到 ID 為 {alert_id_prefix} 的監控。\n"
                    f"使用 /list 查看你的監控清單。"
                )
                return

            # 移除監控
            success = self.alert_manager.remove_alert(user_id, matched_alert["id"])

            if success:
                await self.safe_reply(
                    update,
                    f"✅ 已移除監控：{matched_alert['symbol']}"
                )
                self.logger.info(
                    f"✅ 用戶 {user_id} 移除監控: {matched_alert['id']}"
                )
            else:
                await self.safe_reply(update, "❌ 移除失敗，請稍後再試。")

        except Exception as e:
            self.logger.error(f"❌ remove_command 執行失敗: {e}", exc_info=True)
            try:
                await update.message.reply_text(f"❌ 移除失敗：{str(e)}")
            except:
                pass

    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /clear 命令 - 清空所有監控"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"用戶 {user_id} 執行 /clear 命令")

            # 先檢查是否有監控
            alerts = self.alert_manager.list_alerts(user_id)

            if not alerts:
                await self.safe_reply(update, "📋 你目前沒有任何監控。")
                return

            # 執行清空
            cleared_count = self.alert_manager.clear_all_alerts(user_id)

            if cleared_count > 0:
                await self.safe_reply(
                    update,
                    f"✅ 已清空 {cleared_count} 個監控！\n"
                    f"使用 /add 可以重新新增監控。"
                )
                self.logger.info(f"用戶 {user_id} 清空了 {cleared_count} 個監控")
            else:
                await self.safe_reply(update, "📋 沒有監控需要清空。")

        except Exception as e:
            self.logger.error(f"❌ clear_command 執行失敗: {e}", exc_info=True)
            try:
                await update.message.reply_text(f"❌ 清空失敗：{str(e)}")
            except:
                pass

    async def clearstock_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /clearstock 命令 - 清空指定股票的所有監控"""
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "❌ 用法錯誤！\n"
                "正確格式：/clearstock <股票代碼>\n"
                "範例：/clearstock 2330.TW"
            )
            return

        user_id = update.effective_user.id
        symbol = self.stock_fetcher.normalize_symbol(context.args[0])

        # 執行清空
        cleared_count = self.alert_manager.clear_alerts_by_symbol(user_id, symbol)

        if cleared_count > 0:
            await update.message.reply_text(
                f"✅ 已清空 {symbol} 的 {cleared_count} 個監控！"
            )
            self.logger.info(
                f"用戶 {user_id} 清空了 {symbol} 的 {cleared_count} 個監控"
            )
        else:
            await update.message.reply_text(
                f"📋 沒有 {symbol} 的監控需要清空。"
            )

    async def error_handler(
        self,
        update: Optional[Update],
        context: ContextTypes.DEFAULT_TYPE
    ):
        """全局錯誤處理器"""
        self.logger.error(f"Bot 發生錯誤: {context.error}", exc_info=context.error)

        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ 發生錯誤，請稍後再試或聯絡管理員。"
            )

    async def send_alert(self, user_id: int, alert_info: dict):
        """
        發送價格觸發通知

        Args:
            user_id: Telegram 用戶 ID
            alert_info: 包含 alert、current_price、currency 的字典
        """
        try:
            # 檢查 Bot 是否已初始化
            if not self.application or not self.application.bot:
                self.logger.warning(
                    f"Telegram Bot 尚未初始化，無法發送通知給用戶 {user_id}"
                )
                return

            alert = alert_info["alert"]
            current_price = alert_info["current_price"]
            currency = alert_info["currency"]

            condition_text = "高於" if alert["condition"] == "above" else "低於"
            target_str = format_price(alert["target_price"], currency)
            current_str = format_price(current_price, currency)

            message = f"""
🔔 價格警報觸發！

📊 股票：{alert['symbol']}
💰 當前價格：{current_str}
🎯 目標價格：{condition_text} {target_str}

條件已達成，請注意！
            """

            # 創建移除按鈕
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🗑️ 移除此警報",
                        callback_data=f"remove_alert:{alert['id']}"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            self.logger.info(
                f"正在發送通知給用戶 {user_id}: {alert['symbol']} {current_price}"
            )

            await self.application.bot.send_message(
                chat_id=user_id,
                text=message.strip(),
                reply_markup=reply_markup
            )

            self.logger.info(
                f"✅ 通知發送成功 (用戶 {user_id})"
            )

        except Exception as e:
            self.logger.error(f"❌ 發送通知失敗 (用戶 {user_id}): {e}", exc_info=True)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理按鈕點擊回調"""
        query = update.callback_query
        await query.answer()  # 回應按鈕點擊

        try:
            user_id = query.from_user.id
            callback_data = query.data

            self.logger.info(f"收到按鈕點擊: {callback_data} (用戶 {user_id})")

            # 解析 callback_data
            if callback_data.startswith("remove_alert:"):
                alert_id = callback_data.split(":", 1)[1]

                # 移除警報
                self.logger.info(f"嘗試移除警報: {alert_id}")
                success = self.alert_manager.remove_alert(user_id, alert_id)

                if success:
                    # 更新訊息，移除按鈕
                    await query.edit_message_text(
                        text=f"{query.message.text}\n\n✅ 警報已移除",
                        reply_markup=None
                    )
                    self.logger.info(f"✅ 警報已移除: {alert_id} (用戶 {user_id})")
                else:
                    await query.edit_message_text(
                        text=f"{query.message.text}\n\n❌ 移除失敗（警報不存在或無權限）",
                        reply_markup=None
                    )
                    self.logger.warning(f"移除警報失敗: {alert_id} (用戶 {user_id})")

        except Exception as e:
            self.logger.error(f"❌ 按鈕回調處理失敗: {e}", exc_info=True)
            try:
                await query.edit_message_text(
                    text=f"{query.message.text}\n\n❌ 操作失敗：{str(e)}",
                    reply_markup=None
                )
            except:
                pass

    def run(self):
        """啟動 Bot（阻塞運行）"""
        self.logger.info("正在啟動 Telegram Bot...")

        # 建立應用程式
        self.application = Application.builder().token(self.token).build()

        # 註冊命令處理器
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("price", self.price_command))
        self.application.add_handler(CommandHandler("add", self.add_command))
        self.application.add_handler(CommandHandler("list", self.list_command))
        self.application.add_handler(CommandHandler("remove", self.remove_command))
        self.application.add_handler(CommandHandler("clear", self.clear_command))
        self.application.add_handler(CommandHandler("clearstock", self.clearstock_command))

        # 註冊按鈕回調處理器
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

        # 註冊錯誤處理器
        self.application.add_error_handler(self.error_handler)

        self.logger.info("Telegram Bot 已啟動")

        # 運行 Bot（阻塞）
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    def stop(self):
        """停止 Bot"""
        if self.application:
            self.logger.info("正在停止 Telegram Bot...")
            self.application.stop()
