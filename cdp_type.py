#!/usr/bin/env python3
"""
human-like CDP Typer
Chrome DevTools Protocol経由でアクティブタブに直接human-likeな入力を送る。
Chrome拡張不要。Chrome --remote-debugging-port=9222 で起動済みであること。

Usage:
    python cdp_type.py "タイプするテキスト"
    python cdp_type.py --delay-min 80 --delay-max 200 "テキスト"
    python cdp_type.py --list-tabs          # タブ一覧表示
    python cdp_type.py --tab-index 2 "テキスト"  # 指定タブに入力
"""

import argparse
import asyncio
import json
import math
import random
import sys
import time
import urllib.request

try:
    import websockets
except ImportError:
    print("websockets not installed. Run: uv pip install websockets")
    sys.exit(1)

# human-likeのサウンドデーモンに音を送る
def _play_sound(char: str, is_word_start: bool = False):
    try:
        import socket as _socket
        import os
        uid = os.getuid()
        sock_path = f"/tmp/human-like-sound-{uid}.sock"
        if not os.path.exists(sock_path):
            return
        s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        s.settimeout(0.1)
        s.connect(sock_path)
        s.send(json.dumps({"cmd": "play", "char": char, "word_start": is_word_start}).encode())
        s.recv(64)
        s.close()
    except Exception:
        pass

CDP_HOST = "localhost"
CDP_PORT = 9222


def get_tabs():
    url = f"http://{CDP_HOST}:{CDP_PORT}/json"
    with urllib.request.urlopen(url) as resp:
        tabs = json.loads(resp.read())
    return [t for t in tabs if t.get("type") == "page"]


def _human_delay(delay_min: int, delay_max: int, prev_char: str = "", char: str = "") -> float:
    """より人間らしいランダム遅延を生成"""
    base = random.uniform(delay_min / 1000, delay_max / 1000)
    # 単語区切り（スペース・句読点）後は少し長め
    if prev_char in (" ", "　", "。", "、", ".", ","):
        base *= random.uniform(1.2, 1.8)
    # たまに大きなポーズ（考えてる感）
    if random.random() < 0.05:
        base += random.uniform(0.15, 0.4)
    # リズムの揺らぎ（正規分布的）
    jitter = random.gauss(0, (delay_max - delay_min) / 6000)
    return max(delay_min / 2000, base + jitter)


async def cdp_type(ws_url: str, text: str, delay_min: int, delay_max: int, sound: bool = True):
    async with websockets.connect(ws_url) as ws:
        msg_id = 1

        async def send(method, params=None):
            nonlocal msg_id
            payload = {"id": msg_id, "method": method, "params": params or {}}
            await ws.send(json.dumps(payload))
            msg_id += 1
            while True:
                raw = await ws.recv()
                data = json.loads(raw)
                if data.get("id") == msg_id - 1:
                    return data

        await send("Runtime.enable")

        prev_char = ""
        for i, char in enumerate(text):
            is_word_start = (i == 0 or prev_char in (" ", "　"))

            # サウンド再生
            if sound:
                _play_sound(char, is_word_start)

            # charイベントのみで入力（keyDown+charの二重入力を防ぐ）
            await send("Input.dispatchKeyEvent", {
                "type": "char",
                "text": char,
                "key": char,
                "modifiers": 0,
            })

            delay = _human_delay(delay_min, delay_max, prev_char, char)
            await asyncio.sleep(delay)
            prev_char = char

        print(f"Typed {len(text)} chars to Chrome tab.")


def main():
    parser = argparse.ArgumentParser(description="human-like CDP Typer")
    parser.add_argument("text", nargs="?", help="タイプするテキスト")
    parser.add_argument("--delay-min", type=int, default=60, help="最小遅延ms (default: 60)")
    parser.add_argument("--delay-max", type=int, default=180, help="最大遅延ms (default: 180)")
    parser.add_argument("--tab-index", type=int, default=0, help="対象タブのインデックス (default: 0=最前面)")
    parser.add_argument("--list-tabs", action="store_true", help="タブ一覧を表示")
    args = parser.parse_args()

    tabs = get_tabs()

    if args.list_tabs:
        for i, t in enumerate(tabs):
            print(f"[{i}] {t['title'][:60]} — {t['url'][:80]}")
        return

    if not args.text:
        parser.print_help()
        return

    if args.tab_index >= len(tabs):
        print(f"Error: tab index {args.tab_index} out of range (0-{len(tabs)-1})")
        sys.exit(1)

    tab = tabs[args.tab_index]
    ws_url = tab["webSocketDebuggerUrl"]
    print(f"Target tab [{args.tab_index}]: {tab['title'][:60]}")
    print(f"Typing: {args.text!r} (delay {args.delay_min}-{args.delay_max}ms)")

    asyncio.run(cdp_type(ws_url, args.text, args.delay_min, args.delay_max))


if __name__ == "__main__":
    main()
