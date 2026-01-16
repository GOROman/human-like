# Human Like Typing

A Python application that types text into tmux panes with human-like delays and keyboard sound effects.

## Installation

```bash
pip install -e .
```

## Usage

### Basic Usage

```bash
# Type text directly
human-like "Hello, World!"

# Read from file
human-like -f script.txt

# Pipe input
echo "Hello" | human-like
```

### Options

```bash
# Speed multiplier (2.0 = twice as fast)
human-like --speed 2.0 "text"

# Typo rate (0.1 = 10% chance of typos, auto-corrected with backspace)
human-like --typo 0.1 "text"

# Disable sound effects
human-like --no-sound "text"

# Send to specific tmux pane
human-like -t right "text"
human-like -t %1 "text"

# Combine options
human-like --speed 2.0 --typo 0.05 -t %8 "Hello, World!"
```

### Sound Daemon Management

```bash
# Check daemon status
human-like --daemon status

# Manually start daemon
human-like --daemon start

# Stop daemon
human-like --daemon stop
```

## Features

### Human-like Typing Delays

Random delays based on character type:

| Context | Delay Range |
|---------|-------------|
| Consecutive letters | 20-50ms (fluent typing) |
| After punctuation | 200-600ms (thinking pause) |
| After space | 100-300ms |
| After newline | 300-800ms |

### Fluency Modifiers

Typing speed is adjusted based on keyboard ergonomics:

- **Same key repeat**: 25% faster (e.g., "ll", "ss")
- **Home row keys** (asdfghjkl): 10% faster
- **Alternating hands**: 5% faster (e.g., "aj", "sl")

### Typo Simulation

When `--typo` is enabled:

1. Mistypes occur based on the specified rate
2. Wrong character is typed (adjacent key on QWERTY layout)
3. Brief pause (realizing the mistake)
4. Backspace to delete
5. Correct character is typed

### Keyboard Sound Effects

- Realistic keyboard sounds via Unix socket daemon
- Different sounds for regular keys, Enter, Space
- Sounds mix naturally when typing fast
- Auto-starts when needed, runs in background

## Sound Files

The `sounds/` directory contains keyboard sound effects:

| File | Description |
|------|-------------|
| `PC-Keyboard06-04(Single-Mid).mp3` | Regular key press (medium) |
| `PC-Keyboard06-05(Single-Hard).mp3` | Regular key press (hard) |
| `PC-Keyboard06-06(Single-Gentle).mp3` | Regular key press (gentle) |
| `PC-Keyboard06-08(Enter-Mid).mp3` | Enter key (medium) |
| `PC-Keyboard06-09(Enter-Hard).mp3` | Enter key (hard) |
| `PC-Keyboard06-10(Space-Mid).mp3` | Space key (medium) |
| `PC-Keyboard06-11(Space-Hard).mp3` | Space key (hard) |
| `PC-Keyboard06-12(Shift).mp3` | Shift key |

**Source:** [OtoLogic](https://otologic.jp/free/se/pc-keyboard01.html)
**License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Dependencies

- Python 3.10+
- click: CLI framework
- numpy: Audio mixing
- sounddevice: Real-time audio playback
- soundfile: Audio file loading

## License

MIT

---

Built with [Claude Code](https://claude.ai/code)
