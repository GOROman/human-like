# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Install in development mode
pip install -e .

# Run the CLI
human-like "text"
human-like --speed 2.0 --typo 0.05 -t %8 "text"

# Sound daemon management
human-like --daemon status
human-like --daemon start
human-like --daemon stop
```

## Architecture

This is a CLI tool that sends keystrokes to tmux panes with human-like timing and optional keyboard sounds.

### Module Structure

- **cli.py** - Click-based CLI entry point. Handles argument parsing and orchestrates typing.
- **typer.py** - Typing delay logic. Calculates delays based on character type (letter, punctuation, space, newline) and fluency modifiers (home row, same key repeat, alternating hands). Also handles typo generation using QWERTY adjacent keys.
- **tmux.py** - tmux integration. Sends individual keys via `tmux send-keys`. Special handling for semicolon (`;`) which must be escaped as `\;` for tmux.
- **sound.py** - Unix socket-based sound daemon. Loads MP3 files into memory, mixes audio in real-time using numpy/sounddevice. Auto-forks to background.

### Data Flow

1. CLI receives text input (argument, file, or stdin)
2. `typer.type_text()` yields `(char, delay)` tuples with optional typo injection
3. `tmux.send_text()` iterates, calling sound callback and `send_key()` with delays
4. Sound daemon receives play commands via Unix socket, mixes and outputs audio

### Key Constants

- Socket path: `/tmp/human-like-sound.sock`
- PID file: `/tmp/human-like-sound.pid`
- Sound files in `sounds/` directory (MP3 format)
