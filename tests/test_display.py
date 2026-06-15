import re

import pytest
from display import (
    show_options, prompt_selection, print_progress,
    print_status, print_error, sanitize_text,
)


def _strip_ansi(s: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", s)


def test_show_options_renders_numbered_list(capsys):
    show_options(["1080p", "720p", "4K"])
    captured = capsys.readouterr()
    clean = _strip_ansi(captured.out)
    assert "1. 1080p" in clean
    assert "2. 720p" in clean
    assert "3. 4K" in clean


def test_show_options_empty(capsys):
    show_options([])
    captured = capsys.readouterr()
    assert "No options" in captured.out


def test_prompt_selection_valid(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "2")
    result = prompt_selection(5)
    assert result == 2


def test_prompt_selection_invalid_then_valid(monkeypatch):
    inputs = iter(["0", "6", "abc", "3"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    result = prompt_selection(5)
    assert result == 3


def test_print_progress_renders_bar(capsys):
    print_progress(downloaded=500, total=1000, speed=2.5)
    captured = capsys.readouterr()
    assert "50.0%" in captured.out


def test_print_status(capsys):
    print_status("Hello")
    captured = capsys.readouterr()
    assert "Hello" in captured.out


def test_print_error(capsys):
    print_error("Something failed")
    captured = capsys.readouterr()
    assert "Something failed" in captured.out
    assert captured.out  # non-empty


def test_sanitize_text():
    assert sanitize_text("Inception.mkv") == "Inception.mkv"
    assert sanitize_text("a/b\\c") == "abc"
    assert sanitize_text("a<b>c:d\"e") == "abcde"
