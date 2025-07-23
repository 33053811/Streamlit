
import base64
import json
import socket

def load_nodes(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_connectivity(address, port, timeout=1.5):
    try:
        with socket.create_connection((address, int(port)), timeout=timeout):
            return True
    except Exception:
        return False

def generate_subscribe_url(nodes):
    links = []
    for node in nodes:
        link = ""
        if node["type"] == "vless":
            link = f'vless://{node["uuid"]}@{node["address"]}:{node["port"]}?encryption={node["encryption"]}&security={node.get("tls", "none")}#VLESS节点'
        elif node["type"] == "hysteria2":
            link = f'hysteria2://{node["auth"]}@{node["server"]}?obfs={node["obfs"]}#H2节点'
        elif node["type"] == "tuic":
            link = f'tuic://{node["username"]}:{node["password"]}@{node["address"]}:{node["port"]}?sni={node["sni"]}#Tuic节点'
        elif node["type"] == "anytls":
            link = f'anytls://{node["uuid"]}@{node["address"]}:{node["port"]}?fp={node["fingerprint"]}#AnyTLS节点'
        if link:
            links.append(link)
    return "data:application/octet-stream;base64," + base64.b64encode("\n".join(links).encode()).decode()
