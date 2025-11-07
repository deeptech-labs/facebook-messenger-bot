#config/settings.py
"""
Ustawienia projektu.
"""
import os
from dotenv import load_dotenv
from config.config_parser import ConfigParser

load_dotenv()

# Ścieżki
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
DEBUG_DIR = os.path.join(BASE_DIR, "debug_res")

# Utwórz katalogi jeśli nie istnieją
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

# Załaduj konfigurację - użyj zmiennej środowiskowej BOT_CONFIG_FILE jeśli jest ustawiona
# Domyślnie: bot_config.yaml, fallback do bot_config.md
CONFIG_FILE_NAME = os.getenv("BOT_CONFIG_FILE", "bot_config.yaml")
CONFIG_FILE = os.path.join(BASE_DIR, CONFIG_FILE_NAME)

# Jeśli wybrany plik nie istnieje, spróbuj bot_config.md
if not os.path.exists(CONFIG_FILE):
    CONFIG_FILE = os.path.join(BASE_DIR, "bot_config.md")

config_parser = ConfigParser(CONFIG_FILE)

# Ścieżka do WebDriver (nie jest już potrzebna z webdriver-manager, ale zostawiamy dla kompatybilności)
DRIVER_PATH = os.getenv("DRIVER_PATH", "chromedriver")

# PIN do Messengera (dla przywrócenia historii czatu)
PIN_MESSENGER = os.getenv("PIN_MESSENGER")

# URL do logowania
LOGIN_URL = "https://www.facebook.com/"
MESSENGER_URL = "https://www.messenger.com/"

# Opóźnienie dla oczekiwania (w sekundach) - teraz z konfiguracji
POLLING_INTERVAL = config_parser.get_polling_interval()
WAIT_TIMEOUT = config_parser.get_wait_timeout()

# Tryb headless - z konfiguracji
HEADLESS_MODE = config_parser.is_headless()

# Ustawienia debugowania - z konfiguracji
DEBUG_ENABLED = config_parser.is_debugging_enabled()
SAVE_SCREENSHOTS = config_parser.should_save_screenshots()
SCREENSHOT_ON_ERROR = config_parser.should_screenshot_on_error()

# Export obiektu config_parser dla innych modułów
config = config_parser