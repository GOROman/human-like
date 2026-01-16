"""
Human-like typing delay logic.
"""

import math
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
    # 思考の揺らぎ：突然手が止まる
    "hesitation": (500, 2000),
    # 思考の揺らぎ：バースト入力（急に速くなる）
    "burst_thinking": (20, 50),
}

# リズム変動の範囲（遅延に掛ける係数）
RHYTHM_VARIATION = (0.7, 1.4)

# === 疲労シミュレーション設定 ===
# 疲労が始まる文字数
FATIGUE_START_CHARS = 100
# 最大疲労時の速度低下率（1.5 = 50%遅くなる）
FATIGUE_MAX_SLOWDOWN = 1.5
# 最大疲労時のミスタイプ増加率
FATIGUE_MAX_TYPO_INCREASE = 2.0
# 疲労が最大になる文字数
FATIGUE_MAX_CHARS = 500

# === 思考の揺らぎ設定 ===
# 手が止まる確率（文字ごと）
HESITATION_CHANCE = 0.02
# バースト入力が始まる確率（単語の途中で急に速くなる）
BURST_THINKING_CHANCE = 0.05
# バースト入力の継続文字数
BURST_THINKING_LENGTH = (3, 8)

# === 連続ミス設定 ===
# ミスした後に連続でミスする確率（焦り）
CONSECUTIVE_TYPO_CHANCE = 0.3
# 複数文字を消して打ち直す確率
MULTI_DELETE_CHANCE = 0.15
# 複数文字消す場合の文字数
MULTI_DELETE_COUNT = (2, 4)

# === 難しい文字設定 ===
# 難しい文字（hesitation確率が上がる）
DIFFICULT_CHARS = set("0123456789{}[]()<>@#$%^&*+=|\\~`")

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


def _get_fatigue_progress(total_chars: int) -> float:
    """
    疲労の進行度を計算（0.0〜1.0）

    Args:
        total_chars: これまでに入力した文字数

    Returns:
        進行度（0.0〜1.0）
    """
    if total_chars < FATIGUE_START_CHARS:
        return 0.0
    return min(
        (total_chars - FATIGUE_START_CHARS) / (FATIGUE_MAX_CHARS - FATIGUE_START_CHARS),
        1.0
    )


def get_fatigue_factor(total_chars: int) -> float:
    """
    疲労係数を計算（1.0 = 疲労なし、大きいほど疲労）
    対数曲線：最初は急激に疲労、後は緩やかに

    Args:
        total_chars: これまでに入力した文字数

    Returns:
        疲労係数（1.0〜FATIGUE_MAX_SLOWDOWN）
    """
    progress = _get_fatigue_progress(total_chars)
    if progress == 0.0:
        return 1.0

    # 対数曲線で最初急激、後は緩やか
    log_progress = math.log1p(progress * 2) / math.log1p(2)
    return 1.0 + log_progress * (FATIGUE_MAX_SLOWDOWN - 1.0)


def get_fatigue_typo_multiplier(total_chars: int) -> float:
    """
    疲労によるミスタイプ増加倍率を計算
    対数曲線：最初は急激に増加、後は緩やかに

    Args:
        total_chars: これまでに入力した文字数

    Returns:
        ミスタイプ倍率（1.0〜FATIGUE_MAX_TYPO_INCREASE）
    """
    progress = _get_fatigue_progress(total_chars)
    if progress == 0.0:
        return 1.0

    log_progress = math.log1p(progress * 2) / math.log1p(2)
    return 1.0 + log_progress * (FATIGUE_MAX_TYPO_INCREASE - 1.0)


def type_text(
    text: str, speed: float = 1.0, typo_rate: float = 0.0
) -> Iterator[Tuple[str, float, bool, bool]]:
    """
    テキストを遅延付きでイテレート

    Args:
        text: 入力テキスト
        speed: 速度倍率 (0より大きい値)
        typo_rate: ミスタイプ率 (0.0-1.0)

    Yields:
        (文字, 遅延秒, Shiftキーを押すか, 単語の先頭か) のタプル
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
    total_chars = 0  # 総入力文字数（疲労計算用）
    just_made_typo = False  # 直前にタイポしたか（連続ミス判定用）
    burst_thinking_remaining = 0  # バースト思考の残り文字数
    recent_typed: list[str] = []  # 最近入力した文字（複数削除用）

    for char in text:
        extra_delay = 0.0
        total_chars += 1

        # 疲労係数を計算
        fatigue = get_fatigue_factor(total_chars)
        fatigue_typo_mult = get_fatigue_typo_multiplier(total_chars)

        # 実効速度（疲労で遅くなる）
        effective_speed = speed / fatigue

        # 実効ミスタイプ率（疲労で増える + 直前のミスで焦る）
        effective_typo_rate = min(typo_rate * fatigue_typo_mult, 0.5)
        if just_made_typo and random.random() < CONSECUTIVE_TYPO_CHANCE:
            effective_typo_rate = min(effective_typo_rate * 1.5, 0.5)

        # === 思考の揺らぎ ===
        # 突然手が止まる（迷い・考え中）
        # 難しい文字（数字や記号）は確率が上がる
        hesitation_chance = HESITATION_CHANCE
        if char in DIFFICULT_CHARS:
            hesitation_chance *= 2
        if random.random() < hesitation_chance and char not in ("\n", " ", "\t"):
            hesit_min, hesit_max = DELAY_RANGES["hesitation"]
            extra_delay += random.uniform(hesit_min, hesit_max) / effective_speed / 1000.0

        # バースト思考の開始判定（急に速くなる）
        if burst_thinking_remaining == 0 and random.random() < BURST_THINKING_CHANCE:
            burst_thinking_remaining = random.randint(*BURST_THINKING_LENGTH)

        # 文頭の思考時間
        if is_sentence_start(prev_char) and char not in (" ", "\t", "\n", "　"):
            think_min, think_max = DELAY_RANGES["thinking"]
            extra_delay += random.uniform(think_min, think_max) / effective_speed / 1000.0

        # 大文字の前のShift遅延
        if char.isupper() and char.isalpha():
            shift_min, shift_max = DELAY_RANGES["shift"]
            extra_delay += random.uniform(shift_min, shift_max) / effective_speed / 1000.0

        # 改行前に一呼吸置く
        if char == "\n":
            before_min, before_max = DELAY_RANGES["before_newline"]
            before_delay = random.uniform(before_min, before_max) / effective_speed / 1000.0
            delay = get_delay(char, prev_char, effective_speed)
            yield char, extra_delay + before_delay + delay, False, False
            prev_char = char
            chars_in_word = 0
            recent_typed.clear()
            just_made_typo = False
            continue

        # Shiftキーが必要か（大文字のアルファベット）
        needs_shift = char.isupper() and char.isalpha()

        # 単語の先頭か
        is_word_start = is_word_char(char) and chars_in_word == 0

        # バースト入力判定（単語内で2文字目以降は速い、または思考バースト中）
        in_burst = (is_word_char(char) and chars_in_word >= 1) or burst_thinking_remaining > 0

        # バースト思考中はさらに速い
        if burst_thinking_remaining > 0:
            burst_thinking_remaining -= 1
            # 単語区切りでバースト終了
            if not is_word_char(char):
                burst_thinking_remaining = 0

        # 改行やスペースはタイポしない
        if effective_typo_rate > 0 and char not in ("\n", " ", "\t", "　") and should_typo(effective_typo_rate):
            just_made_typo = True

            # タイポ文字を入力
            typo_char = get_typo_char(char)
            typo_delay = get_delay(typo_char, prev_char, effective_speed, in_burst)

            # 反応時間（気づくまでの間）- タイポ後、気づくまでの遅延
            react_min, react_max = DELAY_RANGES["typo_react"]
            react_delay = random.uniform(react_min, react_max) / effective_speed / 1000.0

            # タイポ文字送信後、気づくまでの間を待つ
            typo_needs_shift = typo_char.isupper() and typo_char.isalpha()
            yield typo_char, extra_delay + typo_delay + react_delay, typo_needs_shift, is_word_start

            # === 複数文字削除パターン ===
            # 一定確率で複数文字消して打ち直す（気づかずに数文字打ってから消す）
            if recent_typed and random.random() < MULTI_DELETE_CHANCE:
                delete_count = min(
                    random.randint(*MULTI_DELETE_COUNT),
                    len(recent_typed)
                )
                # まず今のタイポを消す
                bs_min, bs_max = DELAY_RANGES["backspace"]
                bs_delay = random.uniform(bs_min, bs_max) / effective_speed / 1000.0
                yield "\x7f", bs_delay, False, False

                # さらに数文字消す
                deleted_chars = []
                for _ in range(delete_count):
                    if recent_typed:
                        deleted_chars.append(recent_typed.pop())
                        bs_delay = random.uniform(bs_min, bs_max) / effective_speed / 1000.0
                        yield "\x7f", bs_delay, False, False

                # 消した文字を打ち直す
                for retyped_char in reversed(deleted_chars):
                    retyped_delay = get_delay(retyped_char, prev_char, effective_speed, False)
                    retyped_shift = retyped_char.isupper() and retyped_char.isalpha()
                    yield retyped_char, retyped_delay, retyped_shift, False
                    recent_typed.append(retyped_char)

                # 正しい文字を入力
                char_delay = get_delay(char, prev_char, effective_speed, in_burst)
                yield char, char_delay, needs_shift, False
            else:
                # 通常の1文字削除
                bs_min, bs_max = DELAY_RANGES["backspace"]
                bs_delay = random.uniform(bs_min, bs_max) / effective_speed / 1000.0
                yield "\x7f", bs_delay, False, False

                # 正しい文字を入力
                char_delay = get_delay(char, prev_char, effective_speed, in_burst)
                yield char, char_delay, needs_shift, False
        else:
            just_made_typo = False
            delay = get_delay(char, prev_char, effective_speed, in_burst)
            yield char, extra_delay + delay, needs_shift, is_word_start

        # 単語内文字数の更新
        if is_word_char(char):
            chars_in_word += 1
        else:
            chars_in_word = 0

        # 最近入力した文字を記録（最大10文字）
        recent_typed.append(char)
        if len(recent_typed) > 10:
            recent_typed.pop(0)

        prev_char = char
