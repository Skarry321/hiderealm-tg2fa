import asyncio
import logging
import api
import bot
import storage

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def cleanup_loop():
    while True:
        await asyncio.sleep(60)
        try:
            storage.cleanup_old()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


async def main():
    api.start_api_thread()

    loop = asyncio.get_running_loop()
    loop.create_task(cleanup_loop())

    await bot.start_bot()


if __name__ == "__main__":
    asyncio.run(main())
