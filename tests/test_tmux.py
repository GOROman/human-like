"""Tests for tmux module."""

import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, 'src')

from human_like.tmux import send_key, send_text


class TestSendKey:
    @patch('human_like.tmux.subprocess.run')
    def test_send_regular_char(self, mock_run):
        send_key("a")
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd == ["tmux", "send-keys", "-l", "a"]

    @patch('human_like.tmux.subprocess.run')
    def test_send_enter(self, mock_run):
        send_key("\n")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["tmux", "send-keys", "Enter"]

    @patch('human_like.tmux.subprocess.run')
    def test_send_tab(self, mock_run):
        send_key("\t")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["tmux", "send-keys", "Tab"]

    @patch('human_like.tmux.subprocess.run')
    def test_send_space(self, mock_run):
        send_key(" ")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["tmux", "send-keys", "Space"]

    @patch('human_like.tmux.subprocess.run')
    def test_send_backspace(self, mock_run):
        send_key("\x7f")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["tmux", "send-keys", "BSpace"]

    @patch('human_like.tmux.subprocess.run')
    def test_send_semicolon(self, mock_run):
        send_key(";")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["tmux", "send-keys", "\\;"]

    @patch('human_like.tmux.subprocess.run')
    def test_send_with_target(self, mock_run):
        send_key("a", target="%1")
        cmd = mock_run.call_args[0][0]
        assert cmd == ["tmux", "send-keys", "-t", "%1", "-l", "a"]

    @patch('human_like.tmux.subprocess.run')
    def test_capture_output_false(self, mock_run):
        send_key("a")
        kwargs = mock_run.call_args[1]
        assert kwargs.get("capture_output") == False


class TestSendText:
    @patch('human_like.tmux.send_key')
    @patch('human_like.tmux.time.sleep')
    def test_sends_all_chars(self, mock_sleep, mock_send_key):
        send_text("hi")
        # Should call send_key for each character
        assert mock_send_key.call_count == 2
        calls = [call[0][0] for call in mock_send_key.call_args_list]
        assert calls == ["h", "i"]

    @patch('human_like.tmux.send_key')
    @patch('human_like.tmux.time.sleep')
    def test_applies_delays(self, mock_sleep, mock_send_key):
        send_text("ab")
        # Should sleep after each character
        assert mock_sleep.call_count == 2
        for call in mock_sleep.call_args_list:
            delay = call[0][0]
            assert delay > 0

    @patch('human_like.tmux.send_key')
    @patch('human_like.tmux.time.sleep')
    def test_with_target(self, mock_sleep, mock_send_key):
        send_text("a", target="%5")
        mock_send_key.assert_called_once_with("a", "%5")

    @patch('human_like.tmux.send_key')
    @patch('human_like.tmux.time.sleep')
    def test_sound_callback(self, mock_sleep, mock_send_key):
        callback = MagicMock()
        send_text("ab", sound_callback=callback)
        assert callback.call_count == 2
        calls = [call[0][0] for call in callback.call_args_list]
        assert calls == ["a", "b"]

    @patch('human_like.tmux.send_key')
    @patch('human_like.tmux.time.sleep')
    def test_typo_generates_backspace(self, mock_sleep, mock_send_key):
        send_text("ab", typo_rate=1.0)
        # With 100% typo, each char should have typo + backspace + correct
        calls = [call[0][0] for call in mock_send_key.call_args_list]
        assert "\x7f" in calls  # Backspace

    def test_invalid_speed_raises_error(self):
        with pytest.raises(ValueError, match="speed must be > 0"):
            send_text("test", speed=0)

    def test_invalid_typo_rate_raises_error(self):
        with pytest.raises(ValueError, match="typo_rate must be 0.0-1.0"):
            send_text("test", typo_rate=2.0)

    @patch('human_like.tmux.send_key')
    @patch('human_like.tmux.time.sleep')
    def test_empty_text(self, mock_sleep, mock_send_key):
        send_text("")
        mock_send_key.assert_not_called()
        mock_sleep.assert_not_called()
