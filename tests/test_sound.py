"""Tests for sound module."""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import sys
sys.path.insert(0, 'src')

from human_like.sound import (
    SOCKET_PATH,
    PID_FILE,
    SOUND_FILES,
    get_sounds_dir,
    is_daemon_running,
    send_command,
    play_sound,
)


class TestConstants:
    def test_socket_path_contains_uid(self):
        uid = os.getuid()
        assert str(uid) in SOCKET_PATH

    def test_pid_file_contains_uid(self):
        uid = os.getuid()
        assert str(uid) in PID_FILE

    def test_sound_files_defined(self):
        assert "single_mid" in SOUND_FILES
        assert "enter_mid" in SOUND_FILES
        assert "space_mid" in SOUND_FILES


class TestGetSoundsDir:
    def test_returns_path(self):
        result = get_sounds_dir()
        assert isinstance(result, Path)

    def test_points_to_sounds_directory(self):
        result = get_sounds_dir()
        assert result.name == "sounds"


class TestIsDaemonRunning:
    @patch('human_like.sound.os.path.exists')
    @patch('human_like.sound.send_command')
    def test_returns_false_if_socket_not_exists(self, mock_send, mock_exists):
        mock_exists.return_value = False
        assert is_daemon_running() == False
        mock_send.assert_not_called()

    @patch('human_like.sound.os.path.exists')
    @patch('human_like.sound.send_command')
    def test_returns_true_if_ping_pong(self, mock_send, mock_exists):
        mock_exists.return_value = True
        mock_send.return_value = "pong"
        assert is_daemon_running() == True

    @patch('human_like.sound.os.path.exists')
    @patch('human_like.sound.send_command')
    def test_returns_false_if_ping_fails(self, mock_send, mock_exists):
        mock_exists.return_value = True
        mock_send.return_value = None
        assert is_daemon_running() == False


class TestPlaySound:
    @patch('human_like.sound.send_command')
    def test_sends_play_command(self, mock_send):
        mock_send.return_value = "ok"
        result = play_sound("a")
        mock_send.assert_called_once_with({"cmd": "play", "char": "a"})
        assert result == True

    @patch('human_like.sound.send_command')
    def test_returns_false_on_failure(self, mock_send):
        mock_send.return_value = "error"
        result = play_sound("a")
        assert result == False
