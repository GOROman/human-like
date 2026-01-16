"""Tests for typer module."""

import pytest
import sys
sys.path.insert(0, 'src')

from human_like.typer import (
    get_char_type,
    get_delay,
    get_fluency_multiplier,
    get_typo_char,
    should_typo,
    type_text,
)


class TestGetCharType:
    def test_after_newline(self):
        assert get_char_type("a", "\n") == "newline"

    def test_after_punctuation(self):
        assert get_char_type("a", ".") == "punctuation"
        assert get_char_type("a", "!") == "punctuation"

    def test_after_space(self):
        assert get_char_type("a", " ") == "space"
        assert get_char_type("a", "\t") == "space"

    def test_letter(self):
        assert get_char_type("b", "a") == "letter"
        assert get_char_type("a", None) == "letter"


class TestGetFluencyMultiplier:
    def test_same_key_repeat(self):
        mult = get_fluency_multiplier("l", "l")
        assert mult < 1.0  # Should be faster

    def test_home_row_keys(self):
        mult = get_fluency_multiplier("a", None)
        assert mult < 1.0  # Home row is faster

    def test_alternating_hands(self):
        mult = get_fluency_multiplier("j", "a")  # Left to right
        assert mult < 1.0

    def test_normal_key(self):
        mult = get_fluency_multiplier("q", "w")  # Same hand, not home row
        assert mult == 1.0


class TestGetDelay:
    def test_returns_positive_delay(self):
        delay = get_delay("a", None, speed=1.0)
        assert delay > 0

    def test_speed_affects_delay(self):
        delay1 = get_delay("a", None, speed=1.0)
        delay2 = get_delay("a", None, speed=2.0)
        # Higher speed = shorter delay (on average)
        # Note: Due to randomness, we test with multiple samples
        delays_slow = [get_delay("a", None, speed=1.0) for _ in range(100)]
        delays_fast = [get_delay("a", None, speed=2.0) for _ in range(100)]
        assert sum(delays_fast) < sum(delays_slow)

    def test_invalid_speed_raises_error(self):
        with pytest.raises(ValueError, match="speed must be > 0"):
            get_delay("a", None, speed=0)

        with pytest.raises(ValueError, match="speed must be > 0"):
            get_delay("a", None, speed=-1)


class TestGetTypoChar:
    def test_returns_different_char(self):
        # Most of the time should return a different char
        typos = [get_typo_char("a") for _ in range(100)]
        assert any(t != "a" for t in typos)

    def test_preserves_case(self):
        typos = [get_typo_char("A") for _ in range(100)]
        assert all(t.isupper() for t in typos)


class TestShouldTypo:
    def test_zero_rate_never_typos(self):
        results = [should_typo(0.0) for _ in range(100)]
        assert not any(results)

    def test_full_rate_always_typos(self):
        results = [should_typo(1.0) for _ in range(100)]
        assert all(results)

    def test_partial_rate(self):
        results = [should_typo(0.5) for _ in range(1000)]
        typo_count = sum(results)
        # Should be roughly 50% with some variance
        assert 400 < typo_count < 600


class TestTypeText:
    def test_yields_all_chars(self):
        text = "hello"
        result = list(type_text(text))
        # type_text returns (char, delay, needs_shift, is_word_start)
        chars = [c for c, _, _, _ in result]
        assert "".join(chars) == text

    def test_yields_delays(self):
        text = "hi"
        result = list(type_text(text))
        for char, delay, needs_shift, is_word_start in result:
            assert delay > 0

    def test_invalid_speed_raises_error(self):
        with pytest.raises(ValueError, match="speed must be > 0"):
            list(type_text("test", speed=0))

    def test_invalid_typo_rate_raises_error(self):
        with pytest.raises(ValueError, match="typo_rate must be 0.0-1.0"):
            list(type_text("test", typo_rate=1.5))

        with pytest.raises(ValueError, match="typo_rate must be 0.0-1.0"):
            list(type_text("test", typo_rate=-0.1))

    def test_typo_includes_backspace(self):
        # With 100% typo rate, should see backspaces
        result = list(type_text("ab", typo_rate=1.0))
        chars = [c for c, _, _, _ in result]
        assert "\x7f" in chars  # Backspace character

    def test_no_typo_on_whitespace(self):
        # Spaces and newlines should not trigger typos
        result = list(type_text(" \n", typo_rate=1.0))
        chars = [c for c, _, _, _ in result]
        assert "\x7f" not in chars
