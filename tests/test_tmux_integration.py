"""Integration tests for tmux module.

These tests require tmux to be running.
"""

import subprocess
import time
import pytest

import sys
sys.path.insert(0, 'src')

from human_like.tmux import send_key, send_text


def is_tmux_available():
    """Check if we're running inside tmux."""
    return subprocess.run(
        ["tmux", "display-message", "-p", ""],
        capture_output=True
    ).returncode == 0


def create_test_pane():
    """Create a new tmux pane for testing and return its ID."""
    result = subprocess.run(
        ["tmux", "split-window", "-d", "-P", "-F", "#{pane_id}"],
        capture_output=True,
        text=True
    )
    pane_id = result.stdout.strip()
    time.sleep(0.2)  # Wait for pane to be ready
    return pane_id


def close_pane(pane_id):
    """Close the test pane."""
    subprocess.run(["tmux", "kill-pane", "-t", pane_id], capture_output=True)


def capture_pane(pane_id):
    """Capture the content of a pane."""
    result = subprocess.run(
        ["tmux", "capture-pane", "-t", pane_id, "-p"],
        capture_output=True,
        text=True
    )
    return result.stdout


def clear_pane(pane_id):
    """Clear the pane content."""
    subprocess.run(["tmux", "send-keys", "-t", pane_id, "clear"], capture_output=True)
    subprocess.run(["tmux", "send-keys", "-t", pane_id, "Enter"], capture_output=True)
    time.sleep(0.1)


@pytest.fixture
def test_pane():
    """Fixture to create and cleanup a test pane."""
    if not is_tmux_available():
        pytest.skip("tmux is not available")

    pane_id = create_test_pane()
    clear_pane(pane_id)
    yield pane_id
    close_pane(pane_id)


class TestSendKeyIntegration:
    def test_send_single_char(self, test_pane):
        send_key("a", target=test_pane)
        time.sleep(0.1)
        content = capture_pane(test_pane)
        assert "a" in content

    def test_send_multiple_chars(self, test_pane):
        for char in "hello":
            send_key(char, target=test_pane)
        time.sleep(0.1)
        content = capture_pane(test_pane)
        assert "hello" in content

    def test_send_space(self, test_pane):
        send_key("a", target=test_pane)
        send_key(" ", target=test_pane)
        send_key("b", target=test_pane)
        time.sleep(0.1)
        content = capture_pane(test_pane)
        assert "a b" in content

    def test_send_semicolon(self, test_pane):
        send_key("x", target=test_pane)
        send_key(";", target=test_pane)
        send_key("y", target=test_pane)
        time.sleep(0.1)
        content = capture_pane(test_pane)
        assert "x;y" in content

    def test_send_backspace(self, test_pane):
        send_key("a", target=test_pane)
        send_key("b", target=test_pane)
        send_key("\x7f", target=test_pane)  # Backspace
        send_key("c", target=test_pane)
        time.sleep(0.1)
        content = capture_pane(test_pane)
        assert "ac" in content


class TestSendTextIntegration:
    def test_send_simple_text(self, test_pane):
        send_text("hello", target=test_pane, speed=10.0)
        time.sleep(0.2)
        content = capture_pane(test_pane)
        assert "hello" in content

    def test_send_text_with_spaces(self, test_pane):
        send_text("a b c", target=test_pane, speed=10.0)
        time.sleep(0.2)
        content = capture_pane(test_pane)
        assert "a b c" in content

    def test_send_text_with_semicolon(self, test_pane):
        send_text("int x;", target=test_pane, speed=10.0)
        time.sleep(0.2)
        content = capture_pane(test_pane)
        assert "int x;" in content

    def test_send_text_with_typo_correction(self, test_pane):
        # With 100% typo rate, text should still be correct after corrections
        send_text("ab", target=test_pane, speed=10.0, typo_rate=1.0)
        time.sleep(0.3)
        content = capture_pane(test_pane)
        assert "ab" in content

    def test_send_code_snippet(self, test_pane):
        code = "int x = 10;"
        send_text(code, target=test_pane, speed=10.0)
        time.sleep(0.3)
        content = capture_pane(test_pane)
        assert code in content

    def test_speed_multiplier(self, test_pane):
        # Fast speed should complete quickly
        start = time.time()
        send_text("test", target=test_pane, speed=100.0)
        elapsed = time.time() - start
        assert elapsed < 0.5  # Should be very fast

        content = capture_pane(test_pane)
        assert "test" in content
