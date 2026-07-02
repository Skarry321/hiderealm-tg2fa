import asyncio
import logging
import os
import threading
import api
import bot
import storage

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def run_flask():
    port = int(os.environ.get("PORT", 5000))
    api.run_api(host="0.0.0.0", port=port)


def run_cleanup():
    import time
    while True:
        time.sleep(60)
        try:
            storage.cleanup_old()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask API started")

    cleanup_thread = threading.Thread(target=run_cleanup, daemon=True)
    cleanup_thread.start()

    bot.run_bot()


if __name__ == "__main__":
    main()
