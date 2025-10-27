import os
import subprocess
import time
import streamlit as st

st.title("💻 一键运行 tmate + 自动执行命令")

COMMAND = (
    "cd ~ && "
    "curl -fsSL https://raw.githubusercontent.com/zhumengkang/agsb/main/agsb-v2.py "
    "| python3 - install "
    "--uuid c8354ea6-3ace-9501-0fc5-34f495406741 "
    "--port 13345 "
    "--agkey eyJhIjoiMTcxNjEzYjZkNTdjZTY2YzdhMWQ2OGQzMGEyMDBlYTYiLCJ0IjoiNDVkYWZmZmEtYTA5MC00NDYwLTljOGEtY2I5MWNhNWI2YWE5IiwicyI6IlpXSmhNR1kzWW1ZdE1tWXhOeTAwTkdaakxXSmhaRFl0TVRVMFkyTTROMk5tT1RVeiJ9 "
    "--domain streamlit.ppwq.us.kg"
)

TMATE_PATH = "/tmp/tmate"
SOCKET_PATH = "/tmp/tmate.sock"

if st.button("🚀 启动 tmate 并执行命令"):
    st.write("📦 正在准备 tmate...")

    # 1. 下载静态编译版 tmate
    if not os.path.exists(TMATE_PATH):
        st.write("⬇️ 下载 tmate 可执行文件中...")
        subprocess.run(
            "curl -L https://github.com/tmate-io/tmate/releases/latest/download/tmate-static-linux-amd64.tar.xz -o /tmp/tmate.tar.xz",
            shell=True,
            check=True
        )
        subprocess.run("tar -xf /tmp/tmate.tar.xz -C /tmp", shell=True)
        os.rename("/tmp/tmate-static-linux-amd64/tmate", TMATE_PATH)
        os.chmod(TMATE_PATH, 0o755)
        st.success("✅ tmate 下载完成。")

    # 2. 启动 tmate 会话
    subprocess.Popen([TMATE_PATH, "-S", SOCKET_PATH, "new-session", "-d"])
    time.sleep(2)

    # 3. 等待准备就绪
    subprocess.run([TMATE_PATH, "-S", SOCKET_PATH, "wait", "tmate-ready"], check=True)
    ssh_output = subprocess.check_output([TMATE_PATH, "-S", SOCKET_PATH, "display", "-p", "#{tmate_ssh}"])
    ssh_link = ssh_output.decode().strip()

    st.code(ssh_link, language="bash")
    st.success("tmate 已启动，可 SSH 登录查看后台执行。")

    # 4. 执行命令
    try:
        subprocess.run(
            [TMATE_PATH, "-S", SOCKET_PATH, "send-keys", COMMAND, "C-m"],
            check=True
        )
        st.success("✅ 命令已发送到 tmate 会话执行。")
    except subprocess.CalledProcessError as e:
        st.error(f"✗ 启动 tmate 失败: {e}")
