
import streamlit as st
from utils.subgen import generate_subscribe_url, load_nodes

st.title("🛰️ Karing 多协议订阅生成器")
st.caption("支持 VLESS / Hysteria2 / Tuic / Reality 等协议")

nodes = load_nodes("configs/nodes.json")
selected = st.multiselect("选择要加入订阅的节点", nodes.keys())

if st.button("生成订阅"):
    result = generate_subscribe_url([nodes[name] for name in selected])
    st.code(result, language="text")
    st.markdown(f"[复制订阅链接](#{result})")
