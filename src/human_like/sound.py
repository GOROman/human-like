"""
Sound daemon for keyboard sound effects.
"""

import json
import os
import random
import signal
import socket
import sys
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    import numpy as np
    import sounddevice as sd
    import soundfile as sf

# ソケットパス（UIDを含めてマルチユーザー環境での競合を防ぐ）
_UID = os.getuid()
SOCKET_PATH = f"/tmp/human-like-sound-{_UID}.sock"
PID_FILE = f"/tmp/human-like-sound-{_UID}.pid"

# 音声ファイルのマッピング
SOUND_FILES = {
    "single_mid": "PC-Keyboard06-04(Single-Mid).mp3",
    "single_hard": "PC-Keyboard06-05(Single-Hard).mp3",
    "single_gentle": "PC-Keyboard06-06(Single-Gentle).mp3",
    "enter_mid": "PC-Keyboard06-08(Enter-Mid).mp3",
    "enter_hard": "PC-Keyboard06-09(Enter-Hard).mp3",
    "space_mid": "PC-Keyboard06-10(Space-Mid).mp3",
    "space_hard": "PC-Keyboard06-11(Space-Hard).mp3",
    "shift": "PC-Keyboard06-12(Shift).mp3",
}


# ボリュームのランダム範囲
VOLUME_RANGE = (0.7, 1.0)

# 小指で打つキー（音量が小さくなる）
PINKY_KEYS = set("qazQAZ1!`~pP;:'/\"?[{]}\\|0)-_=+")

# 小指キーのボリューム倍率
PINKY_VOLUME_MULTIPLIER = 0.6

# 単語先頭のボリュームブースト
WORD_START_VOLUME_BOOST = 1.2


class AudioMixer:
    """複数の音声を同時にMix再生するミキサー"""

    def __init__(self, samplerate: int = 44100, channels: int = 2):
        import numpy as np
        import sounddevice as sd
        import soundfile as sf

        self.np = np
        self.sd = sd
        self.sf = sf

        self.samplerate = samplerate
        self.channels = channels
        self.sounds: Dict[str, "np.ndarray"] = {}
        self.playing: List[Tuple["np.ndarray", int, float]] = []  # (data, pos, volume)
        self.lock = threading.Lock()
        self.stream: Optional["sd.OutputStream"] = None

    def load_sound(self, name: str, filepath: str) -> bool:
        """音声ファイルをメモリにロード"""
        try:
            data, sr = self.sf.read(filepath, dtype="float32")
            if sr != self.samplerate:
                print(
                    f"Warning: {filepath} has samplerate {sr}, expected {self.samplerate}"
                )
            if len(data.shape) == 1:
                data = self.np.column_stack([data, data])
            self.sounds[name] = data
            return True
        except Exception as e:
            print(f"Error loading {filepath}: {e}", file=sys.stderr)
            return False

    def callback(self, outdata, frames: int, time_info, status) -> None:
        """オーディオコールバック"""
        outdata.fill(0)
        with self.lock:
            active = []
            for data, pos, volume in self.playing:
                end = min(pos + frames, len(data))
                length = end - pos
                if length > 0:
                    outdata[:length] += data[pos:end] * volume
                if end < len(data):
                    active.append((data, end, volume))
            self.playing = active

        drive = 1.5
        outdata[:] = self.np.tanh(outdata * drive)

    def start(self) -> None:
        """オーディオストリームを開始"""
        if self.stream is None:
            self.stream = self.sd.OutputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                callback=self.callback,
            )
            self.stream.start()

    def stop(self) -> None:
        """オーディオストリームを停止"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def play(self, name: str, volume: float = 1.0) -> bool:
        """サウンドを再生"""
        if name not in self.sounds:
            return False
        with self.lock:
            self.playing.append((self.sounds[name], 0, volume))
        return True

    def stop_all(self) -> None:
        """全ての再生を停止"""
        with self.lock:
            self.playing.clear()


class SoundDaemon:
    """サウンドデーモン"""

    def __init__(self, sounds_dir: str):
        self.sounds_dir = Path(sounds_dir)
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.mixer = AudioMixer()

    def load_all_sounds(self) -> int:
        """全ての音声ファイルをロード"""
        loaded = 0
        for name, filename in SOUND_FILES.items():
            filepath = self.sounds_dir / filename
            if filepath.exists():
                if self.mixer.load_sound(name, str(filepath)):
                    loaded += 1
            else:
                print(f"Warning: {filepath} not found", file=sys.stderr)
        return loaded

    def get_volume_for_char(self, char: str, is_word_start: bool = False) -> float:
        """文字に応じたボリュームを計算"""
        base_volume = random.uniform(*VOLUME_RANGE)

        # 単語の先頭は少し強く打つ
        if is_word_start:
            base_volume *= WORD_START_VOLUME_BOOST

        # 小指キーは音量が小さい
        if char in PINKY_KEYS:
            base_volume *= PINKY_VOLUME_MULTIPLIER

        # 最大1.0に制限
        return min(base_volume, 1.0)

    def get_sound_for_char(self, char: str) -> Optional[str]:
        """文字に応じた音声キーを選択"""
        chance = random.randint(0, 99)

        if char in (" ", "　"):
            return "space_mid" if chance < 70 else "space_hard"
        elif char == "\n":
            return "enter_mid" if chance < 70 else "enter_hard"
        elif char == "\x7f":  # Backspace
            return "single_gentle"
        else:
            if chance < 50:
                return "single_mid"
            elif chance < 80:
                return "single_gentle"
            else:
                return "single_hard"

    def handle_client(self, conn: socket.socket) -> None:
        """クライアントからのリクエストを処理"""
        try:
            data = conn.recv(1024).decode("utf-8").strip()
            if not data:
                return

            try:
                request = json.loads(data)
                cmd = request.get("cmd", "")

                if cmd == "play":
                    char = request.get("char", "")
                    is_word_start = request.get("word_start", False)
                    sound_key = self.get_sound_for_char(char)
                    volume = self.get_volume_for_char(char, is_word_start)
                    if sound_key and self.mixer.play(sound_key, volume):
                        conn.send(b"ok")
                    else:
                        conn.send(b"no sound")

                elif cmd == "play_shift":
                    # Shiftキーの音（大文字入力前に呼ばれる）
                    volume = random.uniform(*VOLUME_RANGE) * PINKY_VOLUME_MULTIPLIER
                    if self.mixer.play("shift", volume):
                        conn.send(b"ok")
                    else:
                        conn.send(b"no sound")

                elif cmd == "stop":
                    self.mixer.stop_all()
                    conn.send(b"ok")

                elif cmd == "ping":
                    conn.send(b"pong")

                elif cmd == "shutdown":
                    conn.send(b"bye")
                    self.running = False

                else:
                    conn.send(b"unknown command")

            except json.JSONDecodeError:
                conn.send(b"invalid json")

        except Exception as e:
            print(f"Error handling client: {e}", file=sys.stderr)
        finally:
            conn.close()

    def cleanup(self) -> None:
        """クリーンアップ"""
        self.running = False
        self.mixer.stop()

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)

        if os.path.exists(PID_FILE):
            os.unlink(PID_FILE)

    def signal_handler(self, signum, frame):
        """シグナルハンドラ"""
        self.cleanup()
        sys.exit(0)

    def run(self) -> None:
        """デーモンを起動"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        loaded = self.load_all_sounds()
        if loaded == 0:
            print("Error: No sounds loaded!", file=sys.stderr)
            sys.exit(1)

        self.mixer.start()

        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(SOCKET_PATH)
        self.socket.listen(5)
        self.socket.settimeout(1.0)

        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        self.running = True

        try:
            while self.running:
                try:
                    conn, _ = self.socket.accept()
                    threading.Thread(
                        target=self.handle_client, args=(conn,), daemon=True
                    ).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Error accepting connection: {e}", file=sys.stderr)
        finally:
            self.cleanup()


def send_command(cmd: dict) -> Optional[str]:
    """デーモンにコマンドを送信"""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect(SOCKET_PATH)
        sock.send(json.dumps(cmd).encode("utf-8"))
        response = sock.recv(1024).decode("utf-8")
        sock.close()
        return response
    except Exception:
        return None


def is_daemon_running() -> bool:
    """デーモンが起動しているか確認"""
    if not os.path.exists(SOCKET_PATH):
        return False
    response = send_command({"cmd": "ping"})
    return response == "pong"


def play_sound(char: str, is_word_start: bool = False) -> bool:
    """文字に対応するサウンドを再生"""
    response = send_command({"cmd": "play", "char": char, "word_start": is_word_start})
    return response == "ok"


def play_shift_sound() -> bool:
    """Shiftキーのサウンドを再生"""
    response = send_command({"cmd": "play_shift"})
    return response == "ok"


def start_daemon(sounds_dir: str, foreground: bool = False) -> bool:
    """デーモンを起動"""
    if is_daemon_running():
        return True

    sounds_path = Path(sounds_dir)
    if not sounds_path.exists():
        print(f"Sounds directory not found: {sounds_dir}", file=sys.stderr)
        return False

    if foreground:
        daemon = SoundDaemon(str(sounds_path))
        daemon.run()
        return True

    # バックグラウンドで実行
    pid = os.fork()
    if pid > 0:
        import time

        time.sleep(0.5)
        return is_daemon_running()
    else:
        os.setsid()
        pid2 = os.fork()
        if pid2 > 0:
            sys.exit(0)

        sys.stdin = open(os.devnull, "r")
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

        daemon = SoundDaemon(str(sounds_path))
        daemon.run()
        return True


def stop_daemon() -> bool:
    """デーモンを停止"""
    if not is_daemon_running():
        return True

    response = send_command({"cmd": "shutdown"})
    return response == "bye"


def get_sounds_dir() -> Path:
    """デフォルトのsoundsディレクトリを取得"""
    return Path(__file__).parent.parent.parent / "sounds"
