# -*- coding: utf-8 -*-
"""ADB device management, APK analysis and installation service."""

import asyncio
import logging
import os
import re
import shutil
import struct
import zipfile
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from tools.exec import run_process

logger = logging.getLogger(__name__)


def resolve_adb_path(adb_bin: Optional[str] = None) -> str:
    """Find the best available adb executable path."""
    if adb_bin and adb_bin.strip():
        return adb_bin.strip()

    found = shutil.which("adb")
    if found:
        return found

    candidates: List[str] = []
    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if android_home:
        candidates.append(os.path.join(android_home, "platform-tools", "adb.exe"))
        candidates.append(os.path.join(android_home, "platform-tools", "adb"))

    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        candidates.append(os.path.join(local_app_data, "Android", "Sdk", "platform-tools", "adb.exe"))

    # System drives scan for popular Android SDK / ADB platform-tools locations
    drives = ["D:", "C:", "E:", "F:"]
    subdirs = [
        r"androidSDK\platform-tools\adb.exe",
        r"AndroidSDK\platform-tools\adb.exe",
        r"adb\platform-tools\adb.exe",
        r"platform-tools\adb.exe",
        r"adb\adb.exe",
        r"Android\Sdk\platform-tools\adb.exe",
        r"android-sdk\platform-tools\adb.exe",
        r"application\platform-tools\adb.exe",
        r"Program Files (x86)\Android\android-sdk\platform-tools\adb.exe",
        r"Program Files\Android\android-sdk\platform-tools\adb.exe",
    ]
    for d in drives:
        for s in subdirs:
            candidates.append(os.path.join(d, "\\", s))

    # Also check popular scrcpy / utility tool paths
    candidates.extend([
        r"E:\zc\scrcpy-win64-v1.24\adb.exe",
        r"E:\软件\QtScrcpy-win-x64-v1.8.0\adb.exe",
        r"E:\软件\RKDevTool_Release_v2.84\RKDevTool_Release_v2.84\bin\adb.exe",
        r"E:\软件\ARDC\utils\adb.exe",
    ])

    for cand in candidates:
        if os.path.isfile(cand):
            return cand

    return "adb"


async def list_devices(adb_bin: Optional[str] = None) -> List[Dict[str, Any]]:
    """List connected ADB devices with detailed information."""
    bin_path = resolve_adb_path(adb_bin)

    def _sync_list() -> List[Dict[str, Any]]:
        try:
            proc = run_process([bin_path, "devices", "-l"], timeout=10)
        except Exception as exc:
            logger.warning("Failed to invoke adb devices: %s", exc)
            return []

        if proc.returncode != 0:
            return []

        devices: List[Dict[str, Any]] = []
        lines = proc.stdout.strip().splitlines()
        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("* daemon") or line_str.startswith("List of devices"):
                continue

            parts = line_str.split()
            if len(parts) < 2:
                continue

            serial = parts[0]
            status = parts[1]
            extra_props: Dict[str, str] = {}
            for token in parts[2:]:
                if ":" in token:
                    k, v = token.split(":", 1)
                    extra_props[k] = v

            devices.append({
                "serial": serial,
                "status": status,
                "model": extra_props.get("model", ""),
                "product": extra_props.get("product", ""),
                "device": extra_props.get("device", ""),
                "transport_id": extra_props.get("transport_id", ""),
                "isOnline": status == "device",
            })
        return devices

    return await asyncio.to_thread(_sync_list)


async def connect_device(target: str, adb_path: Optional[str] = None) -> Dict[str, Any]:
    """Connect to a remote wireless ADB device (IP or IP:PORT)."""
    bin_path = resolve_adb_path(adb_path)
    target_clean = target.strip()
    if ":" not in target_clean:
        target_clean = f"{target_clean}:5555"

    if bin_path == "adb" and not shutil.which("adb"):
        return {
            "success": False,
            "target": target_clean,
            "output": "系统未检测到 ADB 命令行工具 (adb.exe)，请在系统安装 Android platform-tools 或在设置中指定 adb 路径",
            "error": "系统未检测到 ADB 命令行工具 (adb.exe)",
        }

    def _sync_connect() -> Dict[str, Any]:
        try:
            proc = run_process([bin_path, "connect", target_clean], timeout=15)
            out = (proc.stdout + "\n" + proc.stderr).strip()
            lower = out.lower()
            success = "connected" in lower or "already connected" in lower
            return {
                "success": success,
                "target": target_clean,
                "output": out,
                "error": None if success else out,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "target": target_clean,
                "output": "系统未检测到 ADB 命令行工具 (adb.exe)，请检查环境变量或在设置中指定路径",
                "error": "未检测到 adb.exe",
            }
        except Exception as exc:
            return {
                "success": False,
                "target": target_clean,
                "output": str(exc),
                "error": str(exc),
            }

    return await asyncio.to_thread(_sync_connect)


async def disconnect_device(serial: str, adb_path: Optional[str] = None) -> Dict[str, Any]:
    """Disconnect an ADB device."""
    bin_path = resolve_adb_path(adb_path)
    serial_clean = serial.strip()

    if bin_path == "adb" and not shutil.which("adb"):
        return {
            "success": False,
            "serial": serial_clean,
            "output": "系统未检测到 ADB 工具 (adb.exe)",
            "error": "未检测到 adb.exe",
        }

    def _sync_disconnect() -> Dict[str, Any]:
        try:
            proc = run_process([bin_path, "disconnect", serial_clean], timeout=15)
            out = (proc.stdout + "\n" + proc.stderr).strip()
            return {
                "success": proc.returncode == 0,
                "serial": serial_clean,
                "output": out,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "serial": serial_clean,
                "output": "系统未检测到 ADB 工具 (adb.exe)",
                "error": "未检测到 adb.exe",
            }
        except Exception as exc:
            return {
                "success": False,
                "serial": serial_clean,
                "output": str(exc),
                "error": str(exc),
            }

    return await asyncio.to_thread(_sync_disconnect)


def extract_package_name_from_axml(data: bytes) -> Optional[str]:
    """Extract Android package name from binary AndroidManifest.xml (AXML)."""
    if len(data) < 8:
        return None

    magic = struct.unpack_from("<I", data, 0)[0]
    if magic != 0x00080003:
        # Plaintext XML fallback
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(data.decode("utf-8", errors="ignore"))
            return root.get("package")
        except Exception:
            return None

    offset = 8
    strings: List[str] = []
    while offset < len(data):
        if offset + 8 > len(data):
            break
        chunk_type, chunk_size = struct.unpack_from("<II", data, offset)
        if chunk_size <= 0:
            break
        if chunk_type == 0x00010001:  # RES_STRING_POOL_TYPE
            if offset + 28 > len(data):
                break
            string_count, style_count, flags, strings_start, _ = struct.unpack_from(
                "<IIIII", data, offset + 8
            )
            is_utf8 = bool(flags & (1 << 8))
            offsets_start = offset + 28
            pool_data_start = offset + strings_start

            for i in range(string_count):
                if offsets_start + (i + 1) * 4 > len(data):
                    break
                str_offset = struct.unpack_from("<I", data, offsets_start + i * 4)[0]
                pos = pool_data_start + str_offset
                if pos >= len(data):
                    strings.append("")
                    continue
                try:
                    if is_utf8:
                        if data[pos] & 0x80:
                            pos += 2
                        else:
                            pos += 1
                        if pos < len(data) and (data[pos] & 0x80):
                            u8len = ((data[pos] & 0x7F) << 8) | data[pos + 1]
                            pos += 2
                        elif pos < len(data):
                            u8len = data[pos]
                            pos += 1
                        else:
                            u8len = 0
                        s_bytes = data[pos : pos + u8len]
                        strings.append(s_bytes.decode("utf-8", errors="ignore"))
                    else:
                        u16len = struct.unpack_from("<H", data, pos)[0]
                        pos += 2
                        if u16len & 0x8000:
                            u16len = ((u16len & 0x7FFF) << 16) | struct.unpack_from("<H", data, pos)[0]
                            pos += 2
                        s_bytes = data[pos : pos + u16len * 2]
                        strings.append(s_bytes.decode("utf-16le", errors="ignore"))
                except Exception:
                    strings.append("")
            break
        offset += chunk_size

    if not strings:
        return None

    # Search for manifest start tag and package attribute
    offset = 8
    while offset < len(data):
        if offset + 8 > len(data):
            break
        chunk_type, chunk_size = struct.unpack_from("<II", data, offset)
        if chunk_size <= 0:
            break
        if chunk_type == 0x00100102:  # START_TAG
            if offset + 36 <= len(data):
                name_idx = struct.unpack_from("<I", data, offset + 20)[0]
                tag_name = strings[name_idx] if name_idx < len(strings) else ""
                if tag_name == "manifest":
                    attr_count = struct.unpack_from("<H", data, offset + 28)[0]
                    attr_offset = offset + 36
                    for _ in range(attr_count):
                        if attr_offset + 20 > len(data):
                            break
                        _, attr_name_idx, val_str_idx, _, _ = struct.unpack_from(
                            "<IIIII", data, attr_offset
                        )
                        attr_name = strings[attr_name_idx] if attr_name_idx < len(strings) else ""
                        if attr_name == "package" and val_str_idx < len(strings):
                            return strings[val_str_idx]
                        attr_offset += 20
        offset += chunk_size

    # Fallback: regex search on strings for standard Android package name
    for s in strings:
        if re.match(r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$", s):
            if not s.startswith("android.") and not s.startswith("schemas.") and not s.startswith("http"):
                return s

    return None


async def get_package_name_from_apk(local_apk: str) -> Optional[str]:
    """Inspect local APK file to extract the application package name."""
    apk_path = Path(local_apk)
    if not apk_path.is_file():
        return None

    def _sync_extract() -> Optional[str]:
        # 1. Try aapt if available
        aapt_path = shutil.which("aapt") or shutil.which("aapt2")
        if aapt_path:
            try:
                proc = run_process([aapt_path, "dump", "badging", str(apk_path)], timeout=15)
                if proc.returncode == 0:
                    m = re.search(r"package:\s*name='([^']+)'", proc.stdout)
                    if m:
                        return m.group(1)
            except Exception:
                pass

        # 2. Parse AndroidManifest.xml from zip archive
        try:
            with zipfile.ZipFile(str(apk_path), "r") as zf:
                if "AndroidManifest.xml" in zf.namelist():
                    data = zf.read("AndroidManifest.xml")
                    pkg = extract_package_name_from_axml(data)
                    if pkg:
                        return pkg
        except Exception as exc:
            logger.warning("Failed to parse APK zipfile %s: %s", local_apk, exc)

        return None

    return await asyncio.to_thread(_sync_extract)


async def install_apk(
    serial: str,
    apk_path: str,
    reinstall: bool = True,
    auto_reinstall_on_incompatible: bool = True,
    adb_path: Optional[str] = None,
) -> AsyncIterator[Dict[str, Any]]:
    """Install APK on specified device, with auto-retry on signature mismatch."""
    bin_path = resolve_adb_path(adb_path)
    if bin_path == "adb" and not shutil.which("adb"):
        yield {
            "message": "【错误】系统未检测到 ADB 命令行工具 (adb.exe)，请在系统安装 Android platform-tools 或指定路径！",
            "done": True,
            "success": False,
        }
        return

    apk_name = Path(apk_path).name

    yield {
        "message": f"准备推送到设备 [{serial}] 安装应用: {apk_name}...",
        "done": False,
    }

    install_cmd = [bin_path, "-s", serial, "install"]
    if reinstall:
        install_cmd.extend(["-r", "-d", "-t"])
    install_cmd.append(str(apk_path))

    proc = await asyncio.to_thread(run_process, install_cmd, timeout=300)
    out = (proc.stdout + "\n" + proc.stderr).strip()

    if "Success" in out:
        yield {
            "message": "APK 安装成功！",
            "done": True,
            "success": True,
        }
        return

    incompatible_markers = [
        "INSTALL_FAILED_UPDATE_INCOMPATIBLE",
        "INSTALL_FAILED_ALREADY_EXISTS",
        "INSTALL_FAILED_SHARED_USER_INCOMPATIBLE",
        "signatures do not match",
        "INSTALL_FAILED_VERSION_DOWNGRADE",
    ]

    if auto_reinstall_on_incompatible and any(marker in out for marker in incompatible_markers):
        yield {
            "message": f"安装检测到版本或签名冲突 ({out})，准备尝试卸载旧版本并重装...",
            "done": False,
        }
        pkg_name = await get_package_name_from_apk(apk_path)
        if pkg_name:
            yield {
                "message": f"已识别包名 [{pkg_name}]，正在执行卸载...",
                "done": False,
            }
            un_cmd = [bin_path, "-s", serial, "uninstall", pkg_name]
            un_proc = await asyncio.to_thread(run_process, un_cmd, timeout=60)
            yield {
                "message": f"卸载反馈: {un_proc.stdout.strip() or un_proc.stderr.strip()}，正在重新安装...",
                "done": False,
            }
            retry_proc = await asyncio.to_thread(run_process, install_cmd, timeout=300)
            retry_out = (retry_proc.stdout + "\n" + retry_proc.stderr).strip()
            if "Success" in retry_out:
                yield {
                    "message": "卸载后重新安装成功！",
                    "done": True,
                    "success": True,
                }
                return
            else:
                yield {
                    "message": f"重新安装失败: {retry_out}",
                    "done": True,
                    "success": False,
                    "error": retry_out,
                }
                return
        else:
            yield {
                "message": "未能自动解析 APK 包名，请在设备上手动卸载旧版本应用后重试。",
                "done": False,
            }

    yield {
        "message": f"APK 安装失败: {out}",
        "done": True,
        "success": False,
        "error": out,
    }


async def launch_app(
    serial: str,
    pkg_name: str,
    adb_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Launch the main launcher activity of an application on the device."""
    bin_path = resolve_adb_path(adb_path)

    def _sync_launch() -> Dict[str, Any]:
        # Launch using monkey to trigger default LAUNCHER intent
        cmd = [bin_path, "-s", serial, "shell", "monkey", "-p", pkg_name, "-c", "android.intent.category.LAUNCHER", "1"]
        try:
            proc = run_process(cmd, timeout=15)
            out = (proc.stdout + "\n" + proc.stderr).strip()
            if proc.returncode == 0 and ("Events injected: 1" in out or "events injected" in out.lower()):
                return {"success": True, "output": out}
            # Fallback to am start
            proc2 = run_process([bin_path, "-s", serial, "shell", "am", "start", "-n", pkg_name], timeout=15)
            out2 = (proc2.stdout + "\n" + proc2.stderr).strip()
            success = proc.returncode == 0 or proc2.returncode == 0
            return {"success": success, "output": out or out2}
        except Exception as exc:
            return {"success": False, "output": str(exc), "error": str(exc)}

    return await asyncio.to_thread(_sync_launch)
