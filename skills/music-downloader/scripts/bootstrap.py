#!/usr/bin/env python3
"""为音乐下载技能创建隔离运行环境。"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
RUNTIME_DIR = SKILL_DIR / ".runtime"
REQUIREMENTS = SKILL_DIR / "requirements.txt"


class ChineseArgumentParser(argparse.ArgumentParser):
    """把 argparse 的固定帮助标题转换为中文。"""

    def __init__(self, *args: object, **kwargs: object) -> None:
        kwargs["add_help"] = False
        super().__init__(*args, **kwargs)
        self.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")

    def format_help(self) -> str:
        return super().format_help().replace("usage:", "用法：").replace("options:", "选项：")


def configure_stdio() -> None:
    """统一使用 UTF-8 输出，避免 Windows 控制台出现中文乱码。"""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def runtime_python() -> Path:
    """返回当前操作系统对应的虚拟环境 Python 路径。"""
    if os.name == "nt":
        return RUNTIME_DIR / "Scripts" / "python.exe"
    return RUNTIME_DIR / "bin" / "python"


def main() -> int:
    configure_stdio()
    parser = ChineseArgumentParser(description=__doc__)
    parser.add_argument("--upgrade", action="store_true", help="升级锁定版本的依赖")
    args = parser.parse_args()

    python_path = runtime_python()
    if not python_path.exists():
        print(f"正在创建隔离运行环境：{RUNTIME_DIR}")
        venv.EnvBuilder(with_pip=True).create(RUNTIME_DIR)

    # 始终从 requirements.txt 安装，确保首次安装和后续修复使用同一依赖入口。
    command = [str(python_path), "-m", "pip", "install", "--disable-pip-version-check"]
    if args.upgrade:
        command.append("--upgrade")
    command.extend(["-r", str(REQUIREMENTS)])
    subprocess.run(command, check=True)
    print(python_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
