#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
isolation_test.py
-----------------
模拟"新机器"环境，验证 electron_runner.py 的各命令在
不依赖本地 python/git/svn/node 的情况下能否正常运行。

用法（在项目根目录）：
    py isolation_test.py
    py -3 isolation_test.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
RUNNER  = SCRIPTS / "electron_runner.py"

# ── 找到可用的 Python 解释器 ──────────────────────────────────────────────────
BUNDLED_PY = ROOT / "runtime" / "python" / "python.exe"
if BUNDLED_PY.exists():
    PY_EXE  = str(BUNDLED_PY)
    PY_ARGS = []
    print(f"[OK]   Bundled Python : {PY_EXE}")
else:
    PY_EXE  = sys.executable   # 用当前解释器
    PY_ARGS = []
    print(f"[WARN] runtime/python/python.exe not found.")
    print(f"       Using current interpreter: {PY_EXE}")
    print(f"       Run `npm run setup:runtime` for a self-contained test.")

# ── 构造净化后的 PATH ─────────────────────────────────────────────────────────
STRIP_RE = re.compile(
    r'(python|\\git|git\\|/git|git/|tortoiseSVN|sliksvn|\\svn|/svn|nodejs|\\node|/node)',
    re.IGNORECASE,
)
runtime_node = ROOT / "runtime" / "node"
path_parts   = os.environ.get("PATH", "").split(os.pathsep)
clean_parts  = [p for p in path_parts if p and not STRIP_RE.search(p)]
if runtime_node.exists():
    clean_parts.insert(0, str(runtime_node))
    print(f"[OK]   Bundled Node   : {runtime_node}")
else:
    print(f"[WARN] runtime/node not found")

CLEAN_PATH = os.pathsep.join(clean_parts)
print(f"PATH   : system python/git/svn/node stripped")
print()

# ── 环境变量（模拟 Electron 打包后注入的变量）────────────────────────────────
ISO_ENV = dict(os.environ)
ISO_ENV["PATH"]                 = CLEAN_PATH
ISO_ENV["PYTHONUTF8"]          = "1"
ISO_ENV["ZBUILD_DATA_DIR"]     = str(Path(os.environ.get("APPDATA", "/tmp")) / "zbuild-isolation-test")
ISO_ENV["ZBUILD_RESOURCES_DIR"]= str(ROOT / "runtime")   # 模拟 process.resourcesPath
for k in ("VIRTUAL_ENV", "CONDA_DEFAULT_ENV", "PYTHONPATH", "CONDA_PREFIX"):
    ISO_ENV.pop(k, None)

# ── 统计 ─────────────────────────────────────────────────────────────────────
PASS = 0
FAIL = 0
ISSUES = []

def run_cmd(label, cmd, stdin_json="{}"):
    global PASS, FAIL
    print(f"  > {label}")
    args = [PY_EXE] + PY_ARGS + [str(RUNNER), cmd]
    try:
        proc = subprocess.run(
            args,
            input=stdin_json.encode(),
            capture_output=True,
            env=ISO_ENV,
            cwd=str(ROOT),
            timeout=30,
        )
        stdout = proc.stdout.decode("utf-8", errors="replace")
        stderr = proc.stderr.decode("utf-8", errors="replace")
        ok = proc.returncode == 0
        if ok:
            print(f"    PASS (exit 0)")
            PASS += 1
        else:
            print(f"    FAIL (exit {proc.returncode})")
            FAIL += 1
            ISSUES.append(f"{label}: exit {proc.returncode}")
        for line in stdout.strip().splitlines()[-4:]:
            print(f"    OUT: {line}")
        if stderr.strip():
            for line in stderr.strip().splitlines()[:6]:
                print(f"    ERR: {line}")
            if not ok:
                ISSUES.append(stderr.strip().splitlines()[0])
        return stdout
    except subprocess.TimeoutExpired:
        print("    FAIL (timeout)")
        FAIL += 1
        ISSUES.append(f"{label}: timeout")
        return ""
    except Exception as e:
        print(f"    FAIL ({e})")
        FAIL += 1
        ISSUES.append(f"{label}: {e}")
        return ""

# ────────────────────────────────────────────────────────────────────────────
print("=== Isolation Test ===")

# ── 1. Import 检查（语法 + 依赖 import） ─────────────────────────────────────
print("  > [1] syntax + import check")
import_code = f"""
import sys
sys.path.insert(0, r'{SCRIPTS}')
import runner.commands
import tools.detect
import tools.bundled
import core.config
import workflow.pipeline
print('imports OK')
"""
try:
    r = subprocess.run(
        [PY_EXE] + PY_ARGS + ["-c", import_code],
        capture_output=True, env=ISO_ENV, cwd=str(ROOT), timeout=20
    )
    out = r.stdout.decode("utf-8", errors="replace").strip()
    err = r.stderr.decode("utf-8", errors="replace").strip()
    if r.returncode == 0:
        print(f"    PASS  [{out}]")
        PASS += 1
    else:
        print(f"    FAIL")
        for line in err.splitlines()[:5]:
            print(f"    ERR: {line}")
        FAIL += 1
        ISSUES.append(f"import check: {err.splitlines()[0] if err else 'unknown'}")
except Exception as e:
    print(f"    FAIL ({e})")
    FAIL += 1

# ── 2. config 命令 ────────────────────────────────────────────────────────────
run_cmd("[2] config", "config")

# ── 3. detect-tools ───────────────────────────────────────────────────────────
detect_out = run_cmd("[3] detect-tools", "detect-tools")

# 解析工具检测结果
for line in detect_out.splitlines():
    if '"type"' in line and '"result"' in line:
        try:
            obj = json.loads(line)
            tools = obj.get("tools", {})
            if tools:
                print()
                print("    Tool detection results:")
                for name, info in tools.items():
                    p = info.get("path") if isinstance(info, dict) else info
                    if p:
                        print(f"    FOUND   {name:<8} {p}")
                    else:
                        print(f"    MISSING {name}")
        except Exception:
            pass

print()

# ── 4. history-list ───────────────────────────────────────────────────────────
run_cmd("[4] history-list", "history-list")

# ── 5. discover ───────────────────────────────────────────────────────────────
disc_payload = json.dumps({"root_path": str(ROOT)})
run_cmd("[5] discover", "discover", disc_payload)

# ── 결果 ─────────────────────────────────────────────────────────────────────
print()
print("================================")
if FAIL == 0:
    print(f"  ALL PASSED ({PASS} tests)")
else:
    print(f"  PASSED {PASS}  /  FAILED {FAIL}")
    for issue in ISSUES:
        print(f"  - {issue}")
print("================================")
sys.exit(0 if FAIL == 0 else 1)
