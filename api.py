#api.py
"""
API endpoint dla Facebook Messenger bota.
"""
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from dotenv import load_dotenv

from src import utils
from src.facebook_bot import FacebookBot
from src.messenger_monitor import MessengerMonitor
from config import settings

load_dotenv()

# Globalna instancja bota
bot_instance = None
monitor_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Zarządzanie cyklem życia aplikacji"""
    global bot_instance, monitor_task
    
    # Startup
    utils.setup_logging()
    email = os.getenv("FACEBOOK_EMAIL")
    password = os.getenv("FACEBOOK_PASSWORD")
    
    if not email or not password:
        raise ValueError("Brak EMAIL lub PASSWORD w .env")
    
    bot_instance = FacebookBot(email, password)
    bot_instance.login()
    
    if bot_instance.navigate_to_messenger():
        print("Bot uruchomiony i gotowy do pracy")
        monitor = MessengerMonitor(bot_instance.driver)
        # Uruchom monitoring w tle
        monitor_task = asyncio.create_task(
            asyncio.to_thread(monitor.run_monitoring_loop, settings.POLLING_INTERVAL)
        )
    
    yield
    
    # Shutdown
    if monitor_task:
        monitor_task.cancel()
    if bot_instance:
        bot_instance.close()
    print("Bot zatrzymany")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "Bot is running", "message": "Facebook Messenger Bot API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "bot_active": bot_instance is not None
    }

@app.post("/stop")
async def stop_bot():
    """Zatrzymaj bota"""
    global bot_instance
    if bot_instance:
        bot_instance.close()
        bot_instance = None
        return {"message": "Bot stopped"}
    return {"message": "Bot not running"}
