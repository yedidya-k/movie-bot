import asyncio
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from telethon import TelegramClient, events, functions
from telethon.tl.types import ReplyInlineMarkup, KeyboardButtonCallback

from display import make_progress_callback, print_status, print_success

logger = logging.getLogger(__name__)


@dataclass
class ButtonInfo:
    button: KeyboardButtonCallback
    bot_username: str
    chat_id: int
    msg_id: int


class UserClient:
    def __init__(self, config):
        self.config = config
        self.client: Optional[TelegramClient] = None
        self._handler_registered = False
        self._pending_movie_request: Optional[asyncio.Future] = None
        self._pending_file: Optional[asyncio.Future] = None
        self._last_buttons: list[ButtonInfo] = []

    async def start(self):
        if not self.config.api_id or not self.config.api_hash:
            logger.warning("Telethon credentials not configured, skipping user client")
            return

        session = os.path.join(os.path.dirname(__file__), "movie_bot_session")
        self.client = TelegramClient(session, self.config.api_id, self.config.api_hash)

        await self.client.start(phone=self.config.phone_number)

        import sqlite3 as _sqlite3
        try:
            session_file = getattr(self.client.session, "filename", None)
            if session_file:
                with _sqlite3.connect(session_file) as _c:
                    _c.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass

        @self.client.on(events.NewMessage)
        async def handler(event):
            try:
                await self._handle_new_message(event)
            except Exception:
                pass

        self._handler_registered = True

    async def _is_bridge_bot(self, event) -> Optional[str]:
        sender = await event.get_sender()
        if not sender:
            return None
        username = getattr(sender, "username", None)
        if not username:
            return None
        if f"@{username}" in self.config.bridge_bots:
            return username
        return None

    async def _handle_new_message(self, event):
        msg = event.message
        is_dm = event.is_private
        bot_username = await self._is_bridge_bot(event)

        if is_dm and bot_username and (msg.document or msg.video):
            if self._pending_file and not self._pending_file.done():
                self._pending_file.set_result(event)
            return

        if bot_username and msg.reply_markup and isinstance(msg.reply_markup, ReplyInlineMarkup):
            buttons: list[ButtonInfo] = []
            for row in msg.reply_markup.rows:
                for btn in row.buttons:
                    if isinstance(btn, KeyboardButtonCallback) and btn.data:
                        buttons.append(ButtonInfo(
                            button=btn,
                            bot_username=bot_username,
                            chat_id=event.chat_id,
                            msg_id=msg.id,
                        ))
            if buttons and self._pending_movie_request and not self._pending_movie_request.done():
                self._last_buttons = buttons
                self._pending_movie_request.set_result(
                    [(b.button, b.bot_username, b.chat_id, b.msg_id) for b in buttons]
                )

    async def request_movie(self, movie_name: str, timeout: float = 30.0) -> list[str]:
        if not self.client or not self.client.is_connected():
            raise ConnectionError("User client not connected")

        self._last_buttons = []
        loop = asyncio.get_event_loop()
        if self._pending_movie_request is None:
            self._pending_movie_request = loop.create_future()

        for bot in self.config.bridge_bots:
            await self.client.send_message(bot, movie_name)

        print_status("Waiting for bridge bot response...")

        try:
            raw = await asyncio.wait_for(self._pending_movie_request, timeout=timeout)
            result = [ButtonInfo(button=b, bot_username=u, chat_id=c, msg_id=m) for b, u, c, m in raw]
            self._last_buttons = result
            return [b.text for b, _, _, _ in raw]
        except asyncio.TimeoutError:
            raise TimeoutError("Bridge bot did not respond in time")
        finally:
            self._pending_movie_request = None

    async def select_option(self, index: int, timeout: float = 60.0) -> Path:
        if not self.client or not self.client.is_connected():
            raise ConnectionError("User client not connected")

        if index < 0 or index >= len(self._last_buttons):
            raise IndexError(f"Invalid option {index}, have {len(self._last_buttons)} buttons")

        info = self._last_buttons[index]

        print_status(f"Clicking: {info.button.text}")
        result = await self.client(functions.messages.GetBotCallbackAnswerRequest(
            peer=info.chat_id,
            msg_id=info.msg_id,
            data=info.button.data,
        ))

        if not result or not result.url:
            raise RuntimeError(f"No callback URL returned for option: {info.button.text}")

        match = re.search(r"start=(\S+)", result.url)
        if not match:
            raise RuntimeError(f"No start= param in callback URL: {result.url}")

        start_param = match.group(1)
        logger.info(f"Callback URL: {result.url}")

        print_status(f"Requesting file from @{info.bot_username}...")
        await self.client.send_message(f"@{info.bot_username}", f"/start {start_param}")

        loop = asyncio.get_event_loop()
        self._pending_file = loop.create_future()

        try:
            file_event = await asyncio.wait_for(self._pending_file, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending_file = None
            raise TimeoutError("File did not arrive from bridge bot")
        finally:
            self._pending_file = None

        msg = file_event.message
        ext = getattr(msg.file, "name", "unknown_file")
        safe_name = sanitize_text(ext)
        output_path = Path(self.config.download_path) / safe_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print_status("Downloading...")
        progress_cb, done_cb = make_progress_callback()
        await msg.download_media(file=str(output_path), progress_callback=progress_cb)
        done_cb()

        size_str = format(output_path.stat().st_size / (1024 * 1024), ".0f")
        print_success(f"Downloaded: {safe_name} ({size_str}MB)")
        return output_path

    async def stop(self):
        if self.client:
            await self.client.disconnect()


def sanitize_text(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "", name).strip()
