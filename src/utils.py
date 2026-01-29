"""工具函數模組 - 日誌、JSON 操作和格式化"""
import json
import logging
import logging.handlers
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional


def setup_logging(log_dir: str = "logs", log_level: str = "INFO") -> None:
    """
    配置日誌系統

    Args:
        log_dir: 日誌目錄路徑
        log_level: 日誌層級（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    """
    # 建立日誌目錄
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # 設定日誌格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 設定根日誌記錄器
    logger = logging.getLogger()
    try:
        level = getattr(logging, log_level.upper())
    except AttributeError:
        level = logging.INFO
        logging.warning(f"無效的日誌級別 '{log_level}'，使用預設值 INFO")
    logger.setLevel(level)

    # 清除現有的處理器
    logger.handlers.clear()

    # 控制台處理器（INFO 及以上）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(console_handler)

    # 一般日誌檔案處理器
    app_log_path = os.path.join(log_dir, "app.log")
    file_handler = logging.handlers.RotatingFileHandler(
        app_log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(file_handler)

    # 錯誤日誌檔案處理器
    error_log_path = os.path.join(log_dir, "error.log")
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(error_handler)

    logging.info(f"日誌系統已初始化 - 層級: {log_level}")


def load_json(file_path: str, default: Optional[Dict] = None) -> Dict[str, Any]:
    """
    安全地載入 JSON 檔案

    Args:
        file_path: JSON 檔案路徑
        default: 載入失敗時返回的預設值

    Returns:
        JSON 內容字典
    """
    if default is None:
        default = {}

    try:
        if not os.path.exists(file_path):
            logging.info(f"JSON 檔案不存在，使用預設值: {file_path}")
            return default

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logging.debug(f"成功載入 JSON: {file_path}")
            return data
    except json.JSONDecodeError as e:
        logging.error(f"JSON 解析錯誤 ({file_path}): {e}")
        return default
    except Exception as e:
        logging.error(f"載入 JSON 失敗 ({file_path}): {e}")
        return default


def save_json(file_path: str, data: Dict[str, Any]) -> bool:
    """
    安全地儲存 JSON 檔案

    Args:
        file_path: JSON 檔案路徑
        data: 要儲存的字典資料

    Returns:
        是否儲存成功
    """
    try:
        # 確保目錄存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # 寫入檔案
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logging.debug(f"成功儲存 JSON: {file_path}")
        return True
    except Exception as e:
        logging.error(f"儲存 JSON 失敗 ({file_path}): {e}")
        return False


def format_price(price: float, currency: str = "USD") -> str:
    """
    格式化價格顯示

    Args:
        price: 價格數值
        currency: 貨幣代碼（USD, TWD 等）

    Returns:
        格式化後的價格字串
    """
    # 驗證價格是否為有效數字
    if price is None:
        return "N/A"

    try:
        price = float(price)
    except (TypeError, ValueError):
        return "N/A"

    if currency == "TWD":
        return f"NT$ {price:,.2f}"
    elif currency == "USD":
        return f"$ {price:,.2f}"
    else:
        return f"{price:,.2f} {currency}"


def generate_alert_id() -> str:
    """
    生成唯一的監控 ID

    Returns:
        UUID 字串
    """
    return str(uuid.uuid4())
