from __future__ import annotations

import os
import re
import shutil
import sys
import time
from typing import Callable


class _Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        return f"\033[38;2;{r};{g};{b}m"


_GOLD = _Style.rgb(255, 215, 0)
_AMBER = _Style.rgb(255, 191, 0)
_BRONZE = _Style.rgb(205, 127, 50)
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"


def _w(text: str, *styles: str) -> str:
    return "".join(styles) + text + _Style.RESET if styles else text


_LOGO = r"""
{amber}   ███╗   ███╗ ██████╗ ██╗   ██╗██╗███████╗
{amber}   ████╗ ████║██╔═══██╗██║   ██║██║██╔════╝
{gold}   ██╔████╔██║██║   ██║██║   ██║██║█████╗
{gold}   ██║╚██╔╝██║██║   ██║╚██╗ ██╔╝██║██╔══╝
{bronze}   ██║ ╚═╝ ██║╚██████╔╝ ╚████╔╝ ██║███████╗
{bronze}   ╚═╝     ╚═╝ ╚═════╝   ╚═══╝  ╚═╝╚══════╝
""".lstrip("\n")


def _render_logo() -> str:
    return _LOGO.format(amber=_AMBER, gold=_GOLD, bronze=_BRONZE)


def _has_hebrew(text: str) -> bool:
    return any("\u0590" <= c <= "\u05FF" or "\uFB1D" <= c <= "\uFB4F" for c in text)


def _reverse_hebrew(text: str) -> str:
    result: list[str] = []
    buf: list[str] = []
    for c in text:
        if "\u0590" <= c <= "\u05FF" or "\uFB1D" <= c <= "\uFB4F":
            buf.append(c)
        else:
            if buf:
                result.extend(reversed(buf))
                buf = []
            result.append(c)
    if buf:
        result.extend(reversed(buf))
    return "".join(result)


def cprint(text: str = "", *styles: str) -> None:
    if os.name == "nt" and _has_hebrew(text):
        text = _reverse_hebrew(text)
    out = _w(text, *styles) + "\n"
    sys.stdout.buffer.write(out.encode(sys.stdout.encoding, errors="replace"))
    sys.stdout.flush()


def _sep(width: int) -> str:
    return "  " + _w("\u2500" * (width - 2), _Style.DIM)


def _strip_ansi(s: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", s)


def print_banner(config) -> None:
    tw = shutil.get_terminal_size().columns
    width = min(tw - 2, 58)

    for line in _render_logo().split("\n"):
        cprint(" " + line)
    cprint()

    title = f"Movie Bot  {_Style.DIM}v0.2.0{_Style.RESET}"
    cprint(f"  {title}")
    cprint()

    cprint(_sep(width))

    rows = [
        (f"{_Style.DIM}Download path{_Style.RESET}", f"{_Style.BOLD}{config.download_path}{_Style.RESET}"),
        (f"{_Style.DIM}Bridge bots{_Style.RESET}", f"{_Style.BOLD}{', '.join(config.bridge_bots)}{_Style.RESET}"),
        (f"{_Style.DIM}Groups{_Style.RESET}", f"{_Style.BOLD}{len(config.group_ids)}{_Style.RESET} {_Style.DIM}configured{_Style.RESET}"),
    ]

    label_w = max(len(_strip_ansi(l)) for l, _ in rows)
    for label, value in rows:
        label_clean = _strip_ansi(label)
        gap = " " * (label_w - len(label_clean))
        cprint(f"  {label}{gap}  {value}")

    cprint(_sep(width))
    cprint()


def prompt_movie_name() -> str:
    while True:
        name = input(_w("\n  Enter movie name ", _Style.BOLD, _CYAN) + _w("(or 'q' to quit): ", _Style.DIM))
        if name:
            return name


def show_options(buttons: list[str]) -> None:
    if not buttons:
        cprint(f"  {_w('No options available.', _RED)}")
        return
    cprint(f"  {_w('Options:', _Style.BOLD)}")
    for i, label in enumerate(buttons, 1):
        cprint(f"    {_w(f'{i}.', _CYAN)} {label}")


def prompt_selection(max_val: int) -> int:
    while True:
        raw = input(_w(f"  Select option (1-{max_val}): ", _Style.BOLD))
        try:
            val = int(raw)
            if 1 <= val <= max_val:
                return val
        except ValueError:
            pass
        cprint(f"  {_w('Invalid selection.', _RED)}")


def format_size(bytes_val: int) -> str:
    if bytes_val < 1024:
        return f"{bytes_val}B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.0f}KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.0f}MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f}GB"


_bar_width = 30


def print_progress(downloaded: int, total: int, speed: float) -> None:
    if total <= 0:
        return
    pct = downloaded / total
    filled = int(pct * _bar_width)
    bar = "█" * filled + "░" * (_bar_width - filled)
    pct_display = f"{pct * 100:.1f}%"
    dl = format_size(downloaded)
    total_s = format_size(total)
    speed_s = format_size(int(speed)) + "/s"
    line = f"  Downloading: [{bar}]  {dl} / {total_s}  ({pct_display})  {speed_s}"
    sys.stdout.write("\r" + line + " " * 10)
    sys.stdout.flush()


def clear_progress() -> None:
    sys.stdout.write("\r" + " " * (shutil.get_terminal_size().columns - 1) + "\r")
    sys.stdout.flush()


def make_progress_callback() -> tuple[Callable, Callable]:
    start_time = time.time()
    last_bytes = [0]
    last_time = [start_time]

    def callback(current: int, total: int):
        now = time.time()
        dt = now - last_time[0]
        if dt > 0.3:
            speed = (current - last_bytes[0]) / dt if dt > 0 else 0
            last_bytes[0] = current
            last_time[0] = now
        else:
            speed = 0
        print_progress(current, total, speed)

    def done():
        clear_progress()

    return callback, done


def print_status(msg: str) -> None:
    cprint(f"  {_w('>', _CYAN)} {msg}")


def print_success(msg: str) -> None:
    cprint(f"  {_w('OK', _GREEN)} {msg}")


def print_error(msg: str) -> None:
    cprint(f"  {_w('!!', _RED)} {msg}")


def sanitize_text(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "", name).strip()
