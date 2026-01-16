"""
tmux integration for sending keys.
"""

import subprocess
import time
from typing import Callable

from .typer import type_text


def send_key(char: str, target: str | None = None) -> None:
    """
    tmuxペインに1文字送信

    Args:
        char: 送信する文字
        target: ターゲットペイン（例: "{right}", "%1"）。Noneで現在のペイン
    """
    cmd = ["tmux", "send-keys"]
    if target:
        cmd.extend(["-t", target])

    # 特殊文字の処理
    if char == "\n":
        cmd.append("Enter")
    elif char == "\t":
        cmd.append("Tab")
    elif char == " ":
        cmd.append("Space")
    elif char == "\x7f":  # DEL = Backspace
        cmd.append("BSpace")
    elif char == ";":
        # セミコロンはtmuxで特殊文字なのでエスケープ
        cmd.append("\\;")
    else:
        # -l: リテラルモード（特殊文字をエスケープ）
        cmd.extend(["-l", char])

    subprocess.run(cmd, check=True, capture_output=False)


def send_text(
    text: str,
    target: str | None = None,
    speed: float = 1.0,
    typo_rate: float = 0.0,
    sound_callback: Callable[[str], None] | None = None,
) -> None:
    """
    テキスト全体を人間らしいタイピングで送信

    Args:
        text: 送信するテキスト
        target: ターゲットペイン
        speed: 速度倍率 (0より大きい値)
        typo_rate: ミスタイプ率 (0.0-1.0)
        sound_callback: 各文字送信時に呼ばれるコールバック（サウンド再生用）

    Raises:
        ValueError: speedが0以下、またはtypo_rateが0.0-1.0の範囲外の場合
    """
    for char, delay in type_text(text, speed, typo_rate):
        # サウンド再生
        if sound_callback:
            sound_callback(char)

        # 文字送信
        send_key(char, target)

        # 遅延
        time.sleep(delay)
