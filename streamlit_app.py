import os
import sys
import subprocess
import time
from pathlib import Path
import requests
from datetime import datetime
import streamlit as st
import tarfile
import io

# ======================
# 基础配置
# ======================

TMATE_VERSION = "2.4.0"
TMATE_DOWNLOAD_URL = (
    f"https://github.com/tmate-io/tmate/releases/download/"
    f"{TMATE_VERSION}/tmate-{TMATE_VERSION}-static-linux-amd64.tar.xz"
)

USER_HOME = Path.home()
SSH_INFO_FILE = "/tmp/ssh.txt"
TMATE_SOCKET = "/tmp/tmate.sock"

# ======================
# Token 登录（方案 B：第二道锁）
# ======================

def require_token():
    if st.session_state.get("auth_ok"):
        return

    st.set_page_config(page_title="Secure SSH Manager", layout="centered")
    st.title("🔐 二次验证（Token）")

    token = st.text_input("请输入访问 Token", type="password")

    if st.button("验证"):
        if not os.getenv("APP_TOKEN"):
            st.error("服务端未设置 APP_TOKEN 环境变量")
            st.stop()

        if token == os.getenv("APP_TOKEN"):
            st.session_state["auth_ok"] = True
            st.success("验证成功")
            st.rerun()
        else:
            st.error("Token 错误")

    st.stop()

# ======================
# Tmate 管理器
# ======================

class TmateManager:
    def __init__(self):
        self.tmate_dir = USER_HOME / "tmate"
        self.tmate_path = self.tmate_dir / "tmate"
        self.ssh_info_path = Path(SSH_INFO_FILE)
        self.session_info = {}

    def download_tmate(self):
        st.info("正在下载并安装 tmate ...")
        self.tmate_dir.mkdir(exist_ok=True)

        try:
            r = requests.get(TMATE_DOWNLOAD_URL, timeout=30)
            r.raise_for_status()

            with io.BytesIO(r.content) as buf:
                with tarfile.open(fileobj=buf, mode="r:xz") as tar:
                    tar.extract(
                        f"tmate-{TMATE_VERSION}-static-linux-amd64/tmate",
                        path=self.tmate_dir
                    )

            extracted = (
                self.tmate_dir /
                f"tmate-{TMATE_VERSION}-static-linux-amd64" /
                "tmate"
            )

            extracted.rename(self.tmate_path)
            os.chmod(self.tmate_path, 0o755)

            subprocess.run(
                ["rm", "-rf", str(self.tmate_dir / f"tmate-{TMATE_VERSION}-static-linux-amd64")]
            )

            st.success(f"✓ tmate 已安装：{self.tmate_path}")
            return True

        except Exception as e:
            st.error(f"✗ 安装 tmate 失败：{e}")
            return False

    def start_tmate(self):
        st.info("正在启动 tmate 会话 ...")

        if not self.tmate_path.exists():
            st.error("tmate 未安装")
            return False

        subprocess.Popen(
            [
                str(self.tmate_path),
                "-S", TMATE_SOCKET,
                "new-session",
                "-d"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        time.sleep(3)
        return self.get_session_info()

    def get_session_info(self):
        try:
            r = subprocess.run(
                [
                    str(self.tmate_path),
                    "-S", TMATE_SOCKET,
                    "display", "-p", "#{tmate_ssh}"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )

            if r.returncode == 0 and r.stdout.strip():
                self.session_info["ssh"] = r.stdout.strip()
                st.success("✓ SSH 会话创建成功")
                st.code(self.session_info["ssh"], language="bash")
                return True

            st.error("未能获取 SSH 信息")
            return False

        except Exception as e:
            st.error(f"获取会话失败：{e}")
            return False

    def save_ssh_info(self):
        if "ssh" not in self.session_info:
            return

        content = f"""
Tmate SSH 会话信息
-----------------
版本: {TMATE_VERSION}
创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SSH 命令:
{self.session_info["ssh"]}

注意：
- 会话在服务停止后立即失效
- 请勿泄露该命令
""".strip()

        self.ssh_info_path.write_text(content, encoding="utf-8")

        st.success("✓ SSH 信息已保存")
        st.code(content, language="text")

        with open(self.ssh_info_path, "r") as f:
            st.download_button(
                "下载 SSH 信息文件",
                f,
                file_name="ssh_info.txt",
                mime="text/plain"
            )

    def run_command(self, command, timeout, max_chars):
        try:
            r = subprocess.run(
                ["/bin/bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            out = r.stdout[:max_chars]
            err = r.stderr[:max_chars]

            return r.returncode, out, err

        except subprocess.TimeoutExpired:
            return None, "", "命令执行超时"

# ======================
# 主界面
# ======================

def main():
    require_token()

    st.title("🛡 Secure SSH 管理器（方案 B）")

    st.info(
        "🔒 本服务已启用 Cloudflare Tunnel + Cloudflare Access\n\n"
        "✔ 无公网端口\n"
        "✔ IP 完全隐藏\n"
        "✔ 双重身份验证"
    )

    manager = TmateManager()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 创建 SSH 会话"):
            if manager.download_tmate():
                if manager.start_tmate():
                    manager.save_ssh_info()

    with col2:
        st.subheader("⚙ 在容器内执行命令（本地）")

        cmd = st.text_area(
            "Shell 命令",
            height=140,
            placeholder="echo hello"
        )

        timeout = st.number_input("超时（秒）", 60, 3600, 600, 60)
        max_chars = st.number_input("输出截断", 1000, 500000, 100000, 1000)

        if st.button("▶ 执行命令"):
            code, out, err = manager.run_command(cmd, timeout, max_chars)

            st.subheader("stdout")
            st.code(out or "[无输出]", language="bash")

            st.subheader("stderr")
            st.code(err or "[无错误]", language="bash")

if __name__ == "__main__":
    main()
