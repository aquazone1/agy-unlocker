#!/usr/bin/env python3
"""Build a private sing-box config from a locally stored subscription."""
import argparse
import base64
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
import uuid


def build_config(uri):
    node = urlsplit(uri)
    query = parse_qs(node.query)
    # ponytail: only verified VLESS TCP Reality; add other transports after testing.
    if node.scheme != "vless" or query.get("type") != ["tcp"] or query.get("security") != ["reality"]:
        raise ValueError("Only VLESS TCP Reality nodes are supported")
    if not node.hostname or not node.port or not query.get("sni") or not query.get("pbk"):
        raise ValueError("Incomplete VLESS node")
    try:
        identity = str(uuid.UUID(unquote(node.username or "")))
    except ValueError:
        raise ValueError("Invalid VLESS UUID") from None
    return {
        "log": {"level": "error"},
        "inbounds": [{"type": "mixed", "tag": "local-proxy", "listen": "127.0.0.1", "listen_port": 18047}],
        "outbounds": [{
            "type": "vless", "tag": "google-egress", "server": node.hostname,
            "server_port": node.port, "uuid": identity, "flow": query.get("flow", [""])[0],
            "tls": {
                "enabled": True, "server_name": query["sni"][0],
                "utls": {"enabled": True, "fingerprint": query.get("fp", ["chrome"])[0]},
                "reality": {"enabled": True, "public_key": query["pbk"][0], "short_id": query.get("sid", [""])[0]},
            },
        }],
        "route": {"final": "google-egress"},
    }


def main():
    root = Path.home() / ".config/antigravity-proxy"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", type=int, required=True, help="1-based node number in your subscription")
    args = parser.parse_args()
    text = (root / "subscription").read_text().strip()
    if "://" not in text:
        compact = "".join(text.split())
        text = base64.b64decode(compact + "=" * (-len(compact) % 4), validate=True).decode()
    nodes = [line.strip() for line in text.splitlines() if "://" in line]
    if not 1 <= args.node <= len(nodes):
        raise ValueError("Node number out of range")
    config = build_config(nodes[args.node - 1])
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    # Refuse to overwrite an active config or follow an existing symlink.
    with os.fdopen(os.open(root / "config.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as file:
        json.dump(config, file, indent=2)
    print("Private proxy config created; run sing-box check before starting")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, UnicodeError):
        raise SystemExit("Configuration failed: check subscription, node type, and whether config.json already exists")
