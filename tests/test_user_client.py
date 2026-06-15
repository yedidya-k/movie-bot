import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from user_client.client import UserClient, sanitize_text


def test_sanitize():
    assert sanitize_text("Inception.mkv") == "Inception.mkv"
    assert sanitize_text("a/b\\c") == "abc"


@pytest.mark.asyncio
async def test_start_skipped_without_credentials():
    cfg = MagicMock()
    cfg.api_id = None
    cfg.api_hash = ""
    cfg.phone_number = ""
    cfg.bridge_bots = []

    uc = UserClient(cfg)
    await uc.start()

    assert uc.client is None


@pytest.mark.asyncio
async def test_request_movie_returns_buttons():
    cfg = MagicMock()
    cfg.api_id = 12345
    cfg.api_hash = "abc"
    cfg.phone_number = "+123"
    cfg.bridge_bots = ["@SerchtAsBot"]

    uc = UserClient(cfg)

    mock_client = AsyncMock()
    mock_client.is_connected = MagicMock(return_value=True)
    uc.client = mock_client
    uc._handler_registered = True

    loop = asyncio.get_event_loop()
    future = loop.create_future()
    uc._pending_movie_request = future

    mock_sender = AsyncMock()
    mock_sender.username = "SerchtAsBot"

    mock_btn1 = MagicMock()
    mock_btn1.text = "1080p"
    mock_btn2 = MagicMock()
    mock_btn2.text = "720p"

    mock_row = MagicMock()
    mock_row.buttons = [mock_btn1, mock_btn2]

    mock_markup = MagicMock()
    mock_markup.rows = [mock_row]

    mock_msg = MagicMock()
    mock_msg.reply_markup = mock_markup
    mock_msg.id = 42

    future.set_result([
        (mock_btn1, "SerchtAsBot", -100333, 42),
        (mock_btn2, "SerchtAsBot", -100333, 42),
    ])

    uc._last_buttons = [
        MagicMock(button=mock_btn1, bot_username="SerchtAsBot", chat_id=-100333, msg_id=42),
        MagicMock(button=mock_btn2, bot_username="SerchtAsBot", chat_id=-100333, msg_id=42),
    ]

    buttons = await uc.request_movie("Inception")
    assert buttons == ["1080p", "720p"]


@pytest.mark.asyncio
async def test_request_movie_timeout():
    cfg = MagicMock()
    cfg.api_id = 12345
    cfg.api_hash = "abc"
    cfg.phone_number = "+123"
    cfg.bridge_bots = ["@SerchtAsBot"]

    uc = UserClient(cfg)

    mock_client = AsyncMock()
    mock_client.is_connected = MagicMock(return_value=True)
    uc.client = mock_client
    uc._handler_registered = True

    with pytest.raises(TimeoutError):
        await uc.request_movie("Inception", timeout=0.1)


@pytest.mark.asyncio
async def test_select_option_invalid_index():
    cfg = MagicMock()
    cfg.api_id = 12345
    cfg.api_hash = "abc"
    cfg.phone_number = "+123"
    cfg.bridge_bots = ["@SerchtAsBot"]

    uc = UserClient(cfg)
    mock_client = AsyncMock()
    mock_client.is_connected = MagicMock(return_value=True)
    uc.client = mock_client
    uc._handler_registered = True
    uc._last_buttons = []

    with pytest.raises(IndexError):
        await uc.select_option(0)


@pytest.mark.asyncio
async def test_select_option_no_callback_url():
    cfg = MagicMock()
    cfg.api_id = 12345
    cfg.api_hash = "abc"
    cfg.phone_number = "+123"
    cfg.download_path = "./downloads/"
    cfg.bridge_bots = ["@SerchtAsBot"]

    uc = UserClient(cfg)
    mock_client = AsyncMock()
    mock_client.is_connected = MagicMock(return_value=True)
    uc.client = mock_client
    uc._handler_registered = True

    mock_btn = MagicMock()
    mock_btn.text = "1080p"
    mock_btn.data = b"some_data"

    uc._last_buttons = [
        MagicMock(button=mock_btn, bot_username="SerchtAsBot", chat_id=-100333, msg_id=42)
    ]

    mock_result = MagicMock()
    mock_result.url = None
    mock_client.return_value = mock_result

    with pytest.raises(RuntimeError, match="No callback URL"):
        await uc.select_option(0)


@pytest.mark.asyncio
async def test_select_option_disconnected():
    cfg = MagicMock()
    cfg.api_id = 12345
    cfg.api_hash = "abc"
    cfg.phone_number = "+123"
    cfg.bridge_bots = ["@SerchtAsBot"]

    uc = UserClient(cfg)
    uc.client = AsyncMock()
    uc.client.is_connected = MagicMock(return_value=False)

    with pytest.raises(ConnectionError):
        await uc.select_option(0)


@pytest.mark.asyncio
async def test_request_movie_disconnected():
    cfg = MagicMock()
    cfg.api_id = 12345
    cfg.api_hash = "abc"
    cfg.phone_number = "+123"
    cfg.bridge_bots = ["@SerchtAsBot"]

    uc = UserClient(cfg)
    uc.client = AsyncMock()
    uc.client.is_connected = MagicMock(return_value=False)

    with pytest.raises(ConnectionError):
        await uc.request_movie("Inception")
