"""Quick test for Telegram bot token"""
import asyncio
import sys
from aiogram import Bot

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def test_token():
    token = "8553341623:AAFHawpWCMTJW9N84V16XR6CgpOpRGQ6MQs"

    try:
        bot = Bot(token=token)
        me = await bot.get_me()

        print("[OK] Token is working!")
        print(f"Bot ID: {me.id}")
        print(f"Bot Username: @{me.username}")
        print(f"Bot Name: {me.first_name}")

        await bot.session.close()
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_token())
