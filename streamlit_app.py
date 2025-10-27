import os
import subprocess
import time
import streamlit as st
import urllib.request
import tarfile

st.set_page_config(page_title="tmate 自动执行", page_icon="💻")
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

def download_tmate():
    url = "https://github.com/tmate-io/tmate/releases/latest/download/tmate-static-linux-amd64.tar.xz"
    tar_path = "/tmp/tmate.tar.xz"
    extract_path = "/tmp/tmate-static-linux-amd64"

    i
