"""
CLI entry point for human-like typing.
"""

import sys
from typing import Optional

import click

from .sound import (
    DEFAULT_THEME,
    get_sounds_dir,
    get_theme_sound_files,
    get_theme_sounds_dir,
    is_daemon_running,
    list_themes,
    play_shift_sound,
    play_sound,
    start_daemon,
    stop_daemon,
)
from .tmux import send_text


@click.command()
@click.argument("text", required=False)
@click.option("-f", "--file", "input_file", type=click.Path(exists=True), help="Read text from file")
@click.option("-t", "--target", help="Target tmux pane (e.g., '{right}', '%1')")
@click.option("-s", "--speed", default=1.0, type=click.FloatRange(min=0.01), help="Speed multiplier (higher = faster, must be > 0)")
@click.option("--typo", default=0.0, type=click.FloatRange(min=0.0, max=1.0), help="Typo rate (0.0-1.0, e.g., 0.05 for 5%)")
@click.option("--sound/--no-sound", default=True, help="Enable/disable keyboard sounds")
@click.option("--enter/--no-enter", default=True, help="Add Enter key at end (default: enabled)")
@click.option("--theme", default=DEFAULT_THEME, help="Sound theme name ('list' to show available)")
@click.option("--daemon", type=click.Choice(["start", "stop", "status"]), help="Manage sound daemon")
def main(
    text: Optional[str],
    input_file: Optional[str],
    target: Optional[str],
    speed: float,
    typo: float,
    sound: bool,
    enter: bool,
    theme: str,
    daemon: Optional[str],
) -> None:
    """
    Human-like typing for tmux panes.

    Examples:

        human-like "Hello, World!"

        human-like -f script.txt

        echo "Hello" | human-like

        human-like --speed 2.0 --sound -t right "text"

        human-like --typo 0.1 "Typing with 10% typo rate"

        human-like --theme list
    """
    # テーマ一覧表示
    if theme == "list":
        handle_theme_list()
        return

    # デーモン管理コマンド
    if daemon:
        handle_daemon_command(daemon, theme)
        return

    # テキスト入力の取得
    input_text = get_input_text(text, input_file)
    if not input_text:
        click.echo("Error: No input text provided", err=True)
        click.echo("Usage: human-like [OPTIONS] [TEXT]", err=True)
        sys.exit(1)

    # 最後に改行を追加
    if enter and not input_text.endswith("\n"):
        input_text += "\n"

    # サウンドの設定
    sound_callback = None
    shift_sound_callback = None
    if sound:
        # テーマのサウンドディレクトリとファイルを取得
        sounds_dir = get_theme_sounds_dir(theme)
        sound_files = get_theme_sound_files(theme)

        if sound_files is None:
            click.echo(f"Error: Theme '{theme}' not found or invalid", err=True)
            sys.exit(1)

        if sounds_dir.exists():
            if not is_daemon_running():
                start_daemon(str(sounds_dir), sound_files=sound_files)
            if is_daemon_running():
                sound_callback = play_sound
                shift_sound_callback = play_shift_sound
            else:
                click.echo("Warning: Could not start sound daemon", err=True)
        else:
            click.echo(f"Warning: Sounds directory not found: {sounds_dir}", err=True)

    # テキスト送信
    try:
        send_text(input_text, target=target, speed=speed, typo_rate=typo, sound_callback=sound_callback, shift_sound_callback=shift_sound_callback)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def get_input_text(text: Optional[str], input_file: Optional[str]) -> str:
    """入力テキストを取得"""
    if text:
        return text
    elif input_file:
        with open(input_file, "r") as f:
            return f.read()
    elif not sys.stdin.isatty():
        return sys.stdin.read()
    else:
        return ""


def handle_theme_list() -> None:
    """利用可能なテーマを表示"""
    themes = list_themes()
    if not themes:
        click.echo("No themes found")
        return

    click.echo("Available themes:")
    for theme_name in themes:
        prefix = "* " if theme_name == DEFAULT_THEME else "  "
        click.echo(f"{prefix}{theme_name}")


def handle_daemon_command(cmd: str, theme: str = DEFAULT_THEME) -> None:
    """デーモン管理コマンドを処理"""
    sounds_dir = get_theme_sounds_dir(theme)
    sound_files = get_theme_sound_files(theme)

    if sound_files is None:
        click.echo(f"Error: Theme '{theme}' not found or invalid", err=True)
        sys.exit(1)

    if cmd == "start":
        if is_daemon_running():
            click.echo("Sound daemon is already running")
        elif not sounds_dir.exists():
            click.echo(f"Error: Sounds directory not found: {sounds_dir}", err=True)
            sys.exit(1)
        elif start_daemon(str(sounds_dir), sound_files=sound_files):
            click.echo(f"Sound daemon started (theme: {theme})")
        else:
            click.echo("Error: Failed to start sound daemon", err=True)
            sys.exit(1)

    elif cmd == "stop":
        if not is_daemon_running():
            click.echo("Sound daemon is not running")
        elif stop_daemon():
            click.echo("Sound daemon stopped")
        else:
            click.echo("Error: Failed to stop sound daemon", err=True)
            sys.exit(1)

    elif cmd == "status":
        if is_daemon_running():
            click.echo("Sound daemon is running")
        else:
            click.echo("Sound daemon is not running")


if __name__ == "__main__":
    main()
