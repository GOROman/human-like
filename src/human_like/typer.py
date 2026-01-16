"""
Human-like typing delay logic.
"""

import random
import string
from typing import Iterator, Tuple


# 遅延設定 (ミリ秒)
DELAY_RANGES = {
    # アルファベット連続: 流暢なタイピング（一般的なタイピスト相当）
    "letter": (80, 150),
    # バースト入力中（単語内）: より速いタイピング
    "burst": (40, 80),
    # 句読点後: 考え中の間
    "punctuation": (200, 600),
    # スペース後: 単語間の間
    "space": (150, 350),
    # 改行前: Enterを押す前の一呼吸
    "before_newline": (200, 500),
    # 改行後: 行間の間
    "newline": (300, 800),
    # 文頭の思考時間
    "thinking": (400, 1000),
    # Shiftキーを押す間（大文字の前）
    "shift": (50, 150),
    # ミスタイプ後の反応時間
    "typo_react": (100, 300),
    # 削除キーを押す間隔
    "backspace": (50, 120),
}

# リズム変動の範囲（遅延に掛ける係数）
RHYTHM_VARIATION = (0.7, 1.4)

# 句読点
PUNCTUATION = set(".,;:!?。、；：！？")

# キーボード隣接キーマップ (QWERTY配列)
ADJACENT_KEYS = {
    'q': 'wa', 'w': 'qeas', 'e': 'wrds', 'r': 'etfd', 't': 'rygf',
    'y': 'tuhg', 'u': 'yijh', 'i': 'uokj', 'o': 'iplk', 'p': 'ol',
    'a': 'qwsz', 's': 'awedxz', 'd': 'serfcx', 'f': 'drtgvc',
    'g': 'ftyhbv', 'h': 'gyujnb', 'j': 'huikmn', 'k': 'jiolm',
    'l': 'kop', 'z': 'asx', 'x': 'zsdc', 'c': 'xdfv', 'v': 'cfgb',
    'b': 'vghn', 'n': 'bhjm', 'm': 'njk',
}

# ホームポジションのキー（速く打てる）
HOME_KEYS = set('asdfghjkl')

# 左手のキー
LEFT_HAND_KEYS = set('qwertasdfgzxcvb')
# 右手のキー
RIGHT_HAND_KEYS = set('yuiophjklnm')


def get_char_type(char: str, prev_char: str | None) -> str:
    """文字種を判定"""
    if prev_char == "\n":
        return "newline"
    elif prev_char in PUNCTUATION:
        return "punctuation"
    elif prev_char in (" ", "\t", "　"):
        return "space"
    else:
        return "letter"


def get_fluency_multiplier(char: str, prev_char: str | None) -> float:
    """
    流暢性に基づく速度倍率を計算

    Returns:
        1.0未満: より速く打てる
        1.0より大きい: より遅くなる
    """
    multiplier = 1.0
    lower_char = char.lower()
    lower_prev = prev_char.lower() if prev_char else None

    # 同じキーの連打は速い（25%速くなる）
    if lower_prev and lower_char == lower_prev:
        multiplier *= 0.75

    # ホームポジションのキーは速い（10%速くなる）
    if lower_char in HOME_KEYS:
        multiplier *= 0.9

    # 左右の手が交互に使われると速い（5%速くなる）
    if lower_prev:
        prev_left = lower_prev in LEFT_HAND_KEYS
        prev_right = lower_prev in RIGHT_HAND_KEYS
        curr_left = lower_char in LEFT_HAND_KEYS
        curr_right = lower_char in RIGHT_HAND_KEYS

        if (prev_left and curr_right) or (prev_right and curr_left):
            multiplier *= 0.95

    return multiplier


def get_rhythm_variation() -> float:
    """リズム変動の係数を取得（人間らしいゆらぎ）"""
    return random.uniform(*RHYTHM_VARIATION)


def get_delay(
    char: str, prev_char: str | None, speed: float = 1.0, in_burst: bool = False
) -> float:
    """
    文字種に応じた遅延を計算する (秒単位で返す)

    Args:
        char: 現在の文字
        prev_char: 前の文字 (最初はNone)
        speed: 速度倍率 (大きいほど速い、0より大きい値)
        in_burst: バースト入力中（単語内）かどうか

    Returns:
        遅延時間 (秒)

    Raises:
        ValueError: speedが0以下の場合
    """
    if speed <= 0:
        raise ValueError(f"speed must be > 0, got {speed}")

    # バースト入力中は速いタイピング
    if in_burst:
        char_type = "burst"
    else:
        char_type = get_char_type(char, prev_char)
    min_ms, max_ms = DELAY_RANGES[char_type]

    # ランダムな遅延 (ミリ秒)
    delay_ms = random.uniform(min_ms, max_ms)

    # 流暢性倍率を適用
    fluency = get_fluency_multiplier(char, prev_char)
    delay_ms *= fluency

    # リズム変動を適用（人間らしいゆらぎ）
    delay_ms *= get_rhythm_variation()

    # 速度倍率を適用 (speedが大きいほど遅延は短い)
    delay_ms /= speed

    # ミリ秒から秒に変換
    return delay_ms / 1000.0


def get_typo_char(char: str) -> str:
    """
    タイポ文字を取得（隣接キーまたはランダム）
    """
    lower = char.lower()
    if lower in ADJACENT_KEYS:
        typo = random.choice(ADJACENT_KEYS[lower])
        return typo.upper() if char.isupper() else typo
    elif char in string.ascii_letters:
        typo = random.choice(string.ascii_lowercase)
        return typo.upper() if char.isupper() else typo
    else:
        return char


def should_typo(typo_rate: float) -> bool:
    """タイポするかどうかを判定"""
    return random.random() < typo_rate


def is_word_char(char: str) -> bool:
    """単語を構成する文字かどうか"""
    return char.isalnum() or char in "_-'"


def is_sentence_start(prev_char: str | None) -> bool:
    """文頭かどうか（思考の間を入れるべき位置）"""
    if prev_char is None:
        return True
    # 改行後、または文末記号後
    return prev_char in "\n.!?。！？"


def type_text(
    text: str, speed: float = 1.0, typo_rate: float = 0.0
) -> Iterator[Tuple[str, float]]:
    """
    テキストを遅延付きでイテレート

    Args:
        text: 入力テキスト
        speed: 速度倍率 (0より大きい値)
        typo_rate: ミスタイプ率 (0.0-1.0)

    Yields:
        (文字, 遅延秒) のタプル
        特殊文字として "\x7f" (DEL) はBackspaceを表す

    Raises:
        ValueError: speedが0以下、またはtypo_rateが0.0-1.0の範囲外の場合
    """
    if speed <= 0:
        raise ValueError(f"speed must be > 0, got {speed}")
    if not (0.0 <= typo_rate <= 1.0):
        raise ValueError(f"typo_rate must be 0.0-1.0, got {typo_rate}")

    prev_char: str | None = None
    chars_in_word = 0  # 現在の単語内の文字数（バースト入力判定用）

    for char in text:
        extra_delay = 0.0

        # 文頭の思考時間
        if is_sentence_start(prev_char) and char not in (" ", "\t", "\n", "　"):
            think_min, think_max = DELAY_RANGES["thinking"]
            extra_delay += random.uniform(think_min, think_max) / speed / 1000.0

        # 大文字の前のShift遅延
        if char.isupper() and char.isalpha():
            shift_min, shift_max = DELAY_RANGES["shift"]
            extra_delay += random.uniform(shift_min, shift_max) / speed / 1000.0

        # 改行前に一呼吸置く
        if char == "\n":
            before_min, before_max = DELAY_RANGES["before_newline"]
            before_delay = random.uniform(before_min, before_max) / speed / 1000.0
            delay = get_delay(char, prev_char, speed)
            yield char, extra_delay + before_delay + delay
            prev_char = char
            chars_in_word = 0
            continue

        # バースト入力判定（単語内で2文字目以降は速い）
        in_burst = is_word_char(char) and chars_in_word >= 1

        # 改行やスペースはタイポしない
        if typo_rate > 0 and char not in ("\n", " ", "\t", "　") and should_typo(typo_rate):
            # タイポ文字を入力
            typo_char = get_typo_char(char)
            typo_delay = get_delay(typo_char, prev_char, speed, in_burst)

            # 反応時間（気づくまでの間）- タイポ後、気づくまでの遅延
            react_min, react_max = DELAY_RANGES["typo_react"]
            react_delay = random.uniform(react_min, react_max) / speed / 1000.0

            # タイポ文字送信後、気づくまでの間を待つ
            yield typo_char, extra_delay + typo_delay + react_delay

            # Backspaceで削除
            bs_min, bs_max = DELAY_RANGES["backspace"]
            bs_delay = random.uniform(bs_min, bs_max) / speed / 1000.0
            yield "\x7f", bs_delay  # DEL = Backspace

            # 正しい文字を入力
            char_delay = get_delay(char, prev_char, speed, in_burst)
            yield char, char_delay
        else:
            delay = get_delay(char, prev_char, speed, in_burst)
            yield char, extra_delay + delay

        # 単語内文字数の更新
        if is_word_char(char):
            chars_in_word += 1
        else:
            chars_in_word = 0

        prev_char = char
