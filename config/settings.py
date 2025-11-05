#config/settings.py
"""
Ustawienia projektu.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Ścieżki
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
DEBUG_DIR = os.path.join(BASE_DIR, "debug_res")  # NOWE

# Utwórz katalogi jeśli nie istnieją
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)  # NOWE

# Ścieżka do WebDriver (nie jest już potrzebna z webdriver-manager, ale zostawiamy dla kompatybilności)
DRIVER_PATH = os.getenv("DRIVER_PATH", "chromedriver")

# URL do logowania
LOGIN_URL = "https://www.facebook.com/"
MESSENGER_URL = "https://www.messenger.com/"

# Opóźnienie dla oczekiwania (w sekundach)
POLLING_INTERVAL = 10
WAIT_TIMEOUT = 10