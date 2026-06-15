import asyncio
import logging
import os
import sys

from config import Config
from display import (
    is_page_indicator, is_page_arrow, format_button_text,
    print_banner, prompt_movie_name, show_options,
    prompt_selection, print_status, print_error, print_success,
)
from user_client.client import UserClient

logging.basicConfig(
    format="%(asctime)s - %(message)s",
    level=logging.WARNING,
)
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("user_client").setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def main():
    try:
        config = Config()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    uc = UserClient(config)
    await uc.start()

    if not uc.client or not uc.client.is_connected():
        print_error("Telethon client not connected — check API_ID, API_HASH, PHONE_NUMBER in .env")
        return

    os.system("cls" if os.name == "nt" else "clear")
    print_banner(config)

    while True:
        try:
            name = prompt_movie_name()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if name.lower() in ("q", "quit", "exit"):
            print_status("Goodbye!")
            break

        try:
            buttons = await uc.request_movie(name)
        except TimeoutError:
            print_error("No response from bridge bot — try again")
            continue
        except ConnectionError as e:
            print_error(str(e))
            break
        except Exception as e:
            logger.error(f"Request failed: {e}")
            print_error("Request failed — check logs")
            continue

        if not buttons:
            print_error("No options returned by bridge bot")
            continue

        while True:
            display_items = []
            arrow_indices = set()
            orig_by_display = {}
            for i, text in enumerate(buttons):
                if is_page_indicator(text):
                    continue
                display_idx = len(display_items)
                if is_page_arrow(text):
                    display_items.append(format_button_text(text))
                    arrow_indices.add(display_idx)
                else:
                    display_items.append(text)
                orig_by_display[display_idx] = i

            show_options(display_items)
            choice = prompt_selection(len(display_items))
            display_idx = choice - 1
            orig_idx = orig_by_display[display_idx]

            if display_idx in arrow_indices:
                try:
                    buttons = await uc.click_pagination(orig_idx)
                    continue
                except TimeoutError:
                    print_error("Page did not load — try again")
                    break
                except Exception as e:
                    logger.error(f"Pagination failed: {e}")
                    print_error("Page navigation failed")
                    break

            try:
                path = await uc.select_option(orig_idx)
                print_success(f"Saved to: {path}")
                return
            except TimeoutError:
                print_error("File did not arrive — try again")
            except (IndexError, RuntimeError) as e:
                print_error(str(e))
            except BaseException as e:
                logger.error(f"Download failed: {e}")
                print_error("Download failed — check logs")
            break

    await uc.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print_status("Goodbye!")
