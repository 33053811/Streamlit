
import base64
import json

def load_nodes(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_subscribe_url(nodes):
    links = []
    for node in nodes:
        if node["type"] == "vless":
            link = f'vless://{node["uuid"]}@{node["address"]}:{node["port"]}?encryption={node["encryption"]}#VLESS节点'
        elif node["type"] == "hysteria2":
            link = f'hysteria2://{node["auth"]}@{node["server"]}?obfs={node["obfs"]}#H2节点'
        links.append(link)
    return "data:application/octet-stream;base64," + base64.b64encode("\n".join(links).encode()).decode()
