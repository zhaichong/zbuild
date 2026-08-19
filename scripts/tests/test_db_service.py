# -*- coding: utf-8 -*-
"""Unit tests for server/db_service.py."""

import unittest
from unittest.mock import MagicMock, patch

from server.db_service import (
    assert_db_host_allowed,
    assert_safe_insert_sql,
    execute_db_sql,
    is_private_or_local_host,
    test_db_connection,
)


class TestDbService(unittest.TestCase):
    def test_is_private_or_local_host(self):
        self.assertTrue(is_private_or_local_host("localhost"))
        self.assertTrue(is_private_or_local_host("127.0.0.1"))
        self.assertTrue(is_private_or_local_host("192.168.1.100"))
        self.assertTrue(is_private_or_local_host("10.0.0.5"))
        self.assertTrue(is_private_or_local_host("172.20.0.1"))
        self.assertTrue(is_private_or_local_host("::1"))

        self.assertFalse(is_private_or_local_host("8.8.8.8"))
        self.assertFalse(is_private_or_local_host("example.com"))

    def test_assert_db_host_allowed(self):
        # Local & private IPs allowed by default
        self.assertEqual(assert_db_host_allowed("192.168.78.63"), "192.168.78.63")
        self.assertEqual(assert_db_host_allowed("127.0.0.1"), "127.0.0.1")

        # Empty host or metadata host
        with self.assertRaises(ValueError):
            assert_db_host_allowed("")
        with self.assertRaises(ValueError):
            assert_db_host_allowed("169.254.169.254")

        # Public host without allowlist fails
        with self.assertRaises(ValueError):
            assert_db_host_allowed("203.0.113.1", env={})

        # Public host with allowlist succeeds
        self.assertEqual(
            assert_db_host_allowed("203.0.113.1", env={"ZBUILD_DB_HOST_ALLOWLIST": "203.0.113.1"}),
            "203.0.113.1",
        )

    def test_assert_safe_insert_sql(self):
        # Valid INSERT statements
        sql1 = "INSERT INTO `bn_patient_in` (`id`, `name`) VALUES ('1', '张三');"
        self.assertEqual(
            assert_safe_insert_sql(sql1),
            "INSERT INTO `bn_patient_in` (`id`, `name`) VALUES ('1', '张三')",
        )

        sql2 = "INSERT IGNORE INTO `YHDB`.`bn_patient_in` (`id`) VALUES ('2');"
        self.assertEqual(
            assert_safe_insert_sql(sql2),
            "INSERT IGNORE INTO `YHDB`.`bn_patient_in` (`id`) VALUES ('2')",
        )

        # Comments and empty lines
        self.assertIsNone(assert_safe_insert_sql("-- This is a comment"))
        self.assertIsNone(assert_safe_insert_sql("   "))

        # Forbidden commands
        with self.assertRaises(ValueError):
            assert_safe_insert_sql("DELETE FROM `bn_patient_in`")
        with self.assertRaises(ValueError):
            assert_safe_insert_sql("DROP TABLE `bn_patient_in`")
        with self.assertRaises(ValueError):
            assert_safe_insert_sql("UPDATE `bn_patient_in` SET name='abc'")

        # Multiple statements injection
        with self.assertRaises(ValueError):
            assert_safe_insert_sql("INSERT INTO `t` VALUES (1); DROP TABLE `t`")

    @patch("server.db_service.pymysql.connect")
    def test_test_db_connection_success(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        res = test_db_connection({
            "host": "192.168.78.63",
            "port": 3306,
            "user": "root",
            "password": "secret",
            "database": "YHDB",
        })
        self.assertTrue(res["success"])
        self.assertIn("数据库连接成功", res["message"])

    def test_test_db_connection_invalid_db(self):
        res = test_db_connection({
            "host": "192.168.78.63",
            "port": 3306,
            "user": "root",
            "password": "secret",
            "database": "mysql",
        })
        self.assertFalse(res["success"])
        self.assertIn("不允许的数据库名", res["error"])

    @patch("server.db_service.pymysql.connect")
    def test_execute_db_sql_success_and_skip(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # First query inserts 1 row, second query inserts 0 rows (duplicate skipped)
        mock_cursor.execute.side_effect = [1, 0]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        statements = [
            "-- comment",
            "INSERT INTO `YHDB`.`bn_patient_in` (`id`) VALUES ('1');",
            "INSERT IGNORE INTO `YHDB`.`bn_patient_in` (`id`) VALUES ('2');",
        ]

        res = execute_db_sql({
            "host": "192.168.78.63",
            "port": 3306,
            "user": "root",
            "password": "secret",
            "database": "YHDB",
            "sqlStatements": statements,
        })

        self.assertTrue(res["success"])
        self.assertEqual(res["successCount"], 1)
        self.assertEqual(res["skippedCount"], 1)
        self.assertEqual(res["errorCount"], 0)
        self.assertIn("成功写入 1 行", res["logs"])
        self.assertIn("已存在(重复)被自动跳过", res["logs"])


if __name__ == "__main__":
    unittest.main()
