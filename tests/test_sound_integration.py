"""Integration tests for sound module.

These tests require audio hardware and sound files.
"""

import subprocess
import time
import pytest
from pathlib import Path

import sys
sys.path.insert(0, 'src')

from human_like.sound import (
    get_sounds_dir,
    is_daemon_running,
    start_daemon,
    stop_daemon,
    play_sound,
)
from human_like.tmux import send_text


@pytest.fixture
def sound_daemon():
    """Fixture to start and cleanup sound daemon."""
    sounds_dir = get_sounds_dir()
    if not sounds_dir.exists():
        pytest.skip("sounds directory not found")

    # Stop any existing daemon
    if is_daemon_running():
        stop_daemon()
        time.sleep(0.5)

    # Start daemon
    started = start_daemon(str(sounds_dir))
    if not started:
        pytest.skip("could not start sound daemon")

    time.sleep(0.5)
    yield

    # Cleanup
    stop_daemon()


class TestSoundDaemon:
    def test_daemon_starts_and_stops(self):
        sounds_dir = get_sounds_dir()
        if not sounds_dir.exists():
            pytest.skip("sounds directory not found")

        # Stop if running
        if is_daemon_running():
            stop_daemon()
            time.sleep(0.5)

        assert not is_daemon_running()

        # Start
        result = start_daemon(str(sounds_dir))
        assert result == True
        time.sleep(0.5)
        assert is_daemon_running()

        # Stop
        result = stop_daemon()
        assert result == True
        time.sleep(0.5)
        assert not is_daemon_running()

    def test_play_sound(self, sound_daemon):
        # Test playing different sounds
        assert play_sound("a") == True  # Regular key
        time.sleep(0.1)
        assert play_sound(" ") == True  # Space
        time.sleep(0.1)
        assert play_sound("\n") == True  # Enter


class TestSendTextWithSound:
    def test_typing_with_sound(self, sound_daemon):
        """Test that typing with sound works (sound callback is called)."""

        sounds_played = []

        def track_sound(char):
            play_sound(char)
            sounds_played.append(char)

        # Create test pane
        result = subprocess.run(
            ["tmux", "split-window", "-d", "-P", "-F", "#{pane_id}"],
            capture_output=True,
            text=True
        )
        pane_id = result.stdout.strip()
        time.sleep(0.2)

        try:
            # Type with sound
            send_text("hi", target=pane_id, speed=5.0, sound_callback=track_sound)

            # Verify sounds were played
            assert len(sounds_played) == 2
            assert sounds_played == ["h", "i"]

        finally:
            subprocess.run(["tmux", "kill-pane", "-t", pane_id], capture_output=True)

    def test_typing_code_with_sound(self, sound_daemon):
        """Test typing code with sound effects."""

        sounds_played = []

        def track_sound(char):
            play_sound(char)
            sounds_played.append(char)

        # Create test pane
        result = subprocess.run(
            ["tmux", "split-window", "-d", "-P", "-F", "#{pane_id}"],
            capture_output=True,
            text=True
        )
        pane_id = result.stdout.strip()
        time.sleep(0.2)

        try:
            code = "int x;"
            send_text(code, target=pane_id, speed=5.0, sound_callback=track_sound)

            # Verify all chars had sounds
            assert len(sounds_played) == len(code)

            # Verify pane content
            time.sleep(0.2)
            capture = subprocess.run(
                ["tmux", "capture-pane", "-t", pane_id, "-p"],
                capture_output=True,
                text=True
            )
            assert code in capture.stdout

        finally:
            subprocess.run(["tmux", "kill-pane", "-t", pane_id], capture_output=True)
