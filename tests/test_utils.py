#!/usr/bin/env python3
"""測試 utils.py 模組"""
import os
import tempfile
import unittest
from pathlib import Path

from src.utils import (
    format_price,
    generate_alert_id,
    load_json,
    save_json,
    setup_logging,
)


class TestUtils(unittest.TestCase):
    """測試工具函數"""

    def setUp(self):
        """測試前準備"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """測試後清理"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_format_price_usd(self):
        """測試美元價格格式化"""
        result = format_price(150.25, "USD")
        self.assertEqual(result, "$ 150.25")

    def test_format_price_twd(self):
        """測試台幣價格格式化"""
        result = format_price(605.50, "TWD")
        self.assertEqual(result, "NT$ 605.50")

    def test_format_price_with_thousands(self):
        """測試千位分隔符"""
        result = format_price(1234.56, "USD")
        self.assertEqual(result, "$ 1,234.56")

    def test_format_price_none(self):
        """測試 None 價格"""
        result = format_price(None, "USD")
        self.assertEqual(result, "N/A")

    def test_format_price_invalid_type(self):
        """測試無效類型"""
        result = format_price("invalid", "USD")
        self.assertEqual(result, "N/A")

    def test_generate_alert_id(self):
        """測試生成唯一 ID"""
        id1 = generate_alert_id()
        id2 = generate_alert_id()

        # 確認是字串
        self.assertIsInstance(id1, str)
        self.assertIsInstance(id2, str)

        # 確認唯一性
        self.assertNotEqual(id1, id2)

        # 確認長度合理（UUID4 格式）
        self.assertGreater(len(id1), 30)

    def test_save_and_load_json(self):
        """測試 JSON 儲存和載入"""
        test_file = os.path.join(self.temp_dir, "test.json")
        test_data = {
            "name": "測試",
            "value": 123,
            "items": ["a", "b", "c"]
        }

        # 測試儲存
        result = save_json(test_file, test_data)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(test_file))

        # 測試載入
        loaded_data = load_json(test_file)
        self.assertEqual(loaded_data, test_data)

    def test_load_json_nonexistent_file(self):
        """測試載入不存在的檔案"""
        test_file = os.path.join(self.temp_dir, "nonexistent.json")
        default_data = {"default": True}

        result = load_json(test_file, default_data)
        self.assertEqual(result, default_data)

    def test_load_json_invalid_json(self):
        """測試載入無效的 JSON"""
        test_file = os.path.join(self.temp_dir, "invalid.json")

        # 寫入無效的 JSON
        with open(test_file, "w") as f:
            f.write("{invalid json content")

        default_data = {"default": True}
        result = load_json(test_file, default_data)
        self.assertEqual(result, default_data)

    def test_setup_logging(self):
        """測試日誌系統設定"""
        log_dir = os.path.join(self.temp_dir, "logs")

        # 測試設定日誌
        setup_logging(log_dir, "INFO")

        # 確認日誌目錄被建立
        self.assertTrue(os.path.exists(log_dir))

    def test_setup_logging_invalid_level(self):
        """測試無效的日誌級別"""
        log_dir = os.path.join(self.temp_dir, "logs")

        # 不應該拋出異常，應該使用預設值
        try:
            setup_logging(log_dir, "INVALID_LEVEL")
        except Exception as e:
            self.fail(f"setup_logging 不應該拋出異常: {e}")


if __name__ == "__main__":
    unittest.main()
