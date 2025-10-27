# -*- coding: utf-8 -*-
"""
自动 tmate 管理器 + 定时执行
功能:
1. 自动下载并安装 tmate
2. 自动启动 tmate 会话
3. 输出 SSH / Web 访问链接
4. 可选: 在启动后执行自定义命令
5. 定时循环执行任务（可自定义间隔）
"""

import os
import subprocess
import time
import tarfile
import io
import requests
from pathlib import Path
from datetime import datetime

# ========== 可自定义配置 ==========
TMATE_VERSION = "2.4.0"
TMATE_URL = f"https://github.com/tmate-io/tmate/releases/download/{TMATE_VERSION}/tmate-{TMATE_VERSION}-static-linux-amd64.tar.xz"
INSTALL_DIR = Path.home() / "tmate"
TMATE_BIN = INSTALL_DIR / "tmate"
SOCKET_PATH = "/tmp/tmate.sock"
SSH_FILE = "/tmp/ssh.txt"
EXEC_COMMAND = "ls -la"         # 启动后自动执行的命令（可为空字符串）
INTERVAL_MINUTES = 60           # 定时间隔（分钟）
# ==================================


class TmateAuto:
    def __init__(self):
        self.tmate_bin = TMATE_BIN
        self.session_info = {}

    def install_tmate(self):
        """下载并安装 tmate"""
        print("[*] 检查 tmate 是否已安装...")
        if self.tmate_bin.exists():
            print(f"✓ 已存在: {self.tmate_bin}")
            return True

        print("[*] 正在下载 tmate...")
        INSTALL_DIR.mkdir(exist_ok=True)
        try:
            resp = requests.get(TMATE_URL, stream=True)
            resp.raise_for_status()

            with io.BytesIO(resp.content) as tar_stream:
                with tarfile.open(fileobj=tar_stream, mode="r:xz") as tar:
                    tar.extractall(path=INSTALL_DIR)

            # 定位提取出的文件
            extracted = INSTALL_DIR / f"tmate-{TMATE_VERSION}-static-linux-amd64" / "tmate"
            if extracted.exists():
                extracted.rename(self.tmate_bin)
                os.chmod(self.tmate_bin, 0o755)
            subprocess.run(["rm", "-rf", str(INSTALL_DIR / f"tmate-{TMATE_VERSION}-static-linux-amd64")])

            if self.tmate_bin.exists():
                print(f"✓ tmate 安装完成: {self.tmate_bin}")
                return True
            else:
                print("✗ 安装失败: 文件不存在")
                return False
        except Exception as e:
            print(f"✗ 安装失败: {e}")
            return False

    def start_session(self):
        """启动 tmate 会话"""
