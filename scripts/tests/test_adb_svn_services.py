# -*- coding: utf-8 -*-
"""Unit tests for svn_browser and adb_service modules."""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from server.svn_browser import normalize_svn_url, _format_bytes, _build_target_url
from server.adb_service import extract_package_name_from_axml, resolve_adb_path
from uploaders.svn import convert_visualsvn_url


class TestSvnBrowser(unittest.TestCase):
    def test_convert_visualsvn_url(self):
        self.assertEqual(convert_visualsvn_url(""), "")
        # VisualSVN Web UI hash URL
        self.assertEqual(
            convert_visualsvn_url("https://192.168.30.124/!/#智慧病房通用版"),
            "https://192.168.30.124/svn/智慧病房通用版",
        )
        # VisualSVN Web UI percent-encoded hash URL
        self.assertEqual(
            convert_visualsvn_url("https://192.168.30.124/!/#%E6%99%BA%E6%85%A7%E7%97%85%E6%88%BF%E9%80%9A%E7%94%A8%E7%89%88"),
            "https://192.168.30.124/svn/智慧病房通用版",
        )
        # VisualSVN Web UI internal view path
        self.assertEqual(
            convert_visualsvn_url("https://192.168.30.124/!/#智慧病房通用版/view/head/release"),
            "https://192.168.30.124/svn/智慧病房通用版/release",
        )
        # Normal SVN URL remains unchanged
        self.assertEqual(
            convert_visualsvn_url("https://192.168.30.124/svn/智慧病房通用版"),
            "https://192.168.30.124/svn/智慧病房通用版",
        )

    def test_normalize_svn_url(self):
        self.assertEqual(normalize_svn_url(""), "")
        self.assertEqual(
            normalize_svn_url("http://svn.example.com/svn/project//sub/"),
            "http://svn.example.com/svn/project/sub",
        )
        self.assertEqual(
            normalize_svn_url("http://svn.example.com/svn/测试//path/"),
            "http://svn.example.com/svn/测试/path",
        )

    def test_format_bytes(self):
        self.assertEqual(_format_bytes(None), "")
        self.assertEqual(_format_bytes(-1), "")
        self.assertEqual(_format_bytes(500), "500 B")
        self.assertEqual(_format_bytes(1024 * 512), "512.0 KB")
        self.assertEqual(_format_bytes(1024 * 1024 * 20), "20.0 MB")

    def test_build_target_url(self):
        base = "http://svn.example.com/svn/repo"
        self.assertEqual(_build_target_url(base, ""), "http://svn.example.com/svn/repo")
        self.assertEqual(
            _build_target_url(base, "folder/app.apk"),
            "http://svn.example.com/svn/repo/folder/app.apk",
        )


class TestAdbService(unittest.TestCase):
    def test_resolve_adb_path(self):
        path = resolve_adb_path("custom-adb")
        self.assertEqual(path, "custom-adb")
        default_path = resolve_adb_path(None)
        self.assertTrue(isinstance(default_path, str) and len(default_path) > 0)

    def test_extract_package_name_invalid_data(self):
        self.assertIsNone(extract_package_name_from_axml(b""))
        self.assertIsNone(extract_package_name_from_axml(b"invalid data"))

    def test_extract_package_name_plain_xml(self):
        xml_data = b'<?xml version="1.0" encoding="utf-8"?><manifest package="com.yarward.bedhead"></manifest>'
        pkg = extract_package_name_from_axml(xml_data)
        self.assertEqual(pkg, "com.yarward.bedhead")


if __name__ == "__main__":
    unittest.main()
