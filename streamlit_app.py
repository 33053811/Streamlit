import os
import sys
import subprocess
import time
import signal
from pathlib import Path
import requests
from datetime import datetime
import streamlit as st
import tarfile
import io

# ====== 基本配置 ======
TMATE_VERSION = "2.4.0"
TMATE_DOWNLOAD_URL = f"https://github.com/tmate-io/tmate/releases/download/{TMATE_VERSION}/tmate-{TMATE_VERSION}-static-linux-amd64.tar.xz"
USER_HOME = Path.home()
SSH_INFO_FILE = "/tmp/ssh.txt"

class TmateManager:
    def __init__(self):
        self.tmate_dir = USER_HOME / "tmate"
        self.tmate_path = self.tmate_dir / "tmate"
        self.ssh_info_path = Path(SSH_INFO_FILE)
        self.session_info = {}

    def download_tmate(self):
        """下载并安装 tmate"""
        st.info("正在下载并安装 tmate...")
        self.tmate_dir.mkdir(exist_ok=True)
        try:
            response = requests.get(TMATE_DOWNLOAD_URL, stream=True)
            response.raise_for_status()

            with io.BytesIO(response.content) as tar_stream:
                with tarfile.open(fileobj=tar_stream, mode="r:xz") as tar:
                    tar.extract("tmate-2.4.0-static-linux-amd64/tmate", path=str(self.tmate_dir))

            extracted_path = self.tmate_dir / "tmate-2.4.0-static-linux-amd64" / "tmate"
            if extracted_path.exists():
                extracted_path.rename(self.tmate_path)
                os.chmod(self.tmate_path, 0o755)
                subprocess.run(["rm", "-rf", str(self.tmate_dir / "tmate-2.4.0-static-linux-amd64")])
                st.success(f"✓ tmate 已安装到: {self.tmate_path}")
                return True
            else:
                st.error("✗ 未找到 tmate 可执行文件")
                return False
        except Exception as e:
            st.error(f"✗ 下载或安装失败: {e}")
            return False

    def start_tmate(self, command: str):
        """启动 tmate 会话并在其中执行指定命令"""
        st.info("正在启动 tmate 会话...")

        if not self.tmate_path.exists():
            st.error("tmate 文件不存在，请先安装")
            return False

        try:
            # 启动一个 tmate 后台 session 并执行命令
            start_cmd = [
                str(self.tmate_path), "-S", "/tmp/tmate.sock", "new-session", "-d", "bash"
            ]
            subprocess.run(start_cmd, check=True)

            # 等待会话建立
            time.sleep(3)

            # 进入 tmate shell 并执行命令
            exec_cmd = [str(self.tmate_path), "-S", "/tmp/tmate.sock", "send-keys", f"{command}", "C-m"]
            subprocess.run(exec_cmd, check=True)

            # 获取 SSH / Web 地址
            self.get_session_info()

            return True
        except Exception as e:
            st.error(f"✗ 启动 tmate 失败: {e}")
            return False

    def get_session_info(self):
        """获取 tmate 的 SSH 和 Web 地址"""
        try:
            ssh_cmd = [str(self.tmate_path), "-S", "/tmp/tmate.sock", "display", "-p", "#{tmate_ssh}"]
            web_cmd = [str(self.tmate_path), "-S", "/tmp/tmate.sock", "display", "-p", "#{tmate_web}"]

            ssh_result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=5)
            web_result = subprocess.run(web_cmd, capture_output=True, text=True, timeout=5)

            self.session_info["ssh"] = ssh_result.stdout.strip()
            self.session_info["web"] = web_result.stdout.strip()

            if self.session_info["ssh"]:
                st.success(f"✅ SSH 连接命令: {self.session_info['ssh']}")
            if self.session_info["web"]:
                st.info(f"🌐 Web 访问地址: {self.session_info['web']}")
        except Exception as e:
            st.error(f"✗ 获取会话信息失败: {e}")

    def save_ssh_info(self):
        """保存 SSH 会话信息到文件"""
        try:
            if not self.session_info.get('ssh'):
                st.error("没有可保存的 SSH 信息")
                return False

            content = f"""Tmate SSH 会话信息
版本: {TMATE_VERSION}
创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SSH连接命令:
{self.session_info['ssh']}

Web访问地址:
{self.session_info.get('web', '无')}

说明:
- 会话在 Streamlit 关闭后自动终止
- 临时会话最长可持续2小时
"""
            with open(self.ssh_info_path, "w", encoding="utf-8") as f:
                f.write(content)

            st.success(f"✓ SSH信息已保存到: {self.ssh_info_path}")
            st.code(content, language="text")

            with open(self.ssh_info_path, "r") as f:
                st.download_button(
                    label="下载 SSH 信息文件",
                    data=f,
                    file_name="ssh_info.txt",
                    mime="text/plain"
                )
            return True
        except Exception as e:
            st.error(f"✗ 保存 SSH 信息失败: {e}")
            return False


def main():
    st.title("🚀 一键创建 SSH + 自动执行命令")
    st.markdown(f"""
    此工具会:
    1. 自动下载并安装 tmate；
    2. 创建临时 SSH 连接；
    3. 在连接中自动执行你指定的命令。
    """)

    command = st.text_input("请输入要自动执行的命令，例如：", "ls -al")
    manager = TmateManager()

    if st.button("创建并运行"):
        with st.spinner("正在创建 tmate 会话..."):
            if not manager.download_tmate():
                return
            if manager.start_tmate(command):
                st.success("🎉 会话创建成功！命令已自动执行。")
                manager.save_ssh_info()
                st.balloons()
            else:
                st.error("创建会话失败，请重试。")

if __name__ == "__main__":
    main()
