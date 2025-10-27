import os
import subprocess
import time
import streamlit as st

st.title("💻 一键运行 tmate + 指令执行")
st.caption("此程序将在后台启动 tmate 并运行指定命令")

COMMAND = (
    "cd ~ && "
    "curl -fsSL https://raw.githubusercontent.com/zhumengkang/agsb/main/agsb-v2.py "
    "| python3 - install "
    "--uuid c8354ea6-3ace-9501-0fc5-34f495406741 "
    "--port 13345 "
    "--agkey eyJhIjoiMTcxNjEzYjZkNTdjZTY2YzdhMWQ2OGQzMGEyMDBlYTYiLCJ0IjoiNDVkYWZmZmEtYTA5MC00NDYwLTljOGEtY2I5MWNhNWI2YWE5IiwicyI6IlpXSmhNR1kzWW1ZdE1tWXhOeTAwTkdaakxXSmhaRFl0TVRVMFkyTTROMk5tT1RVeiJ9 "
    "--domain streamlit.ppwq.us.kg"
)

if st.button("🚀 启动 tmate 并执行命令"):
    st.write("📦 正在安装 tmate...")

    # 1. 安装 tmate（仅安装一次）
    subprocess.run("sudo apt-get update -y", shell=True)
    subprocess.run("sudo apt-get install -y tmate", shell=True)

    st.write("✅ tmate 安装完成，正在启动...")

    # 2. 启动 tmate session
    subprocess.Popen(["tmate", "-S", "/tmp/tmate.sock", "new-session", "-d"])
    time.sleep(2)

    # 3. 获取 SSH 地址（便于调试）
    subprocess.run(["tmate", "-S", "/tmp/tmate.sock", "wait", "tmate-ready"], check=True)
    ssh_output = subprocess.check_output(["tmate", "-S", "/tmp/tmate.sock", "display", "-p", "#{tmate_ssh}"])
    ssh_link = ssh_output.decode().strip()

    st.code(ssh_link, language="bash")
    st.success("tmate 已启动，可 SSH 登录查看后台执行。")

    # 4. 发送命令执行
    try:
        subprocess.run(
            ["tmate", "-S", "/tmp/tmate.sock", "send-keys", COMMAND, "C-m"],
            check=True
        )
        st.success("✅ 命令已发送到 tmate 会话执行。")
    except subprocess.CalledProcessError as e:
        st.error(f"✗ 启动 tmate 失败: {e}")
