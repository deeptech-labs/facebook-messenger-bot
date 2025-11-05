#src/facebook_bot.py
"""
Klasa do logowania i interakcji z Facebookiem.
"""
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import settings
from src import utils
from src.debug_logger import DebugLogger
import logging

logger = logging.getLogger(__name__)


class FacebookBot:
    def __init__(self, email, password, config=None):
        self.email = email
        self.password = password
        self.driver = None
        self.config = config if config else settings.config
        self.debug_logger = DebugLogger()
        self.setup_driver()

    def setup_driver(self):
        """Inicjalizuje WebDriver z ustawieniami z konfiguracji."""
        chrome_options = Options()

        # Tryb headless z konfiguracji
        if self.config.is_headless():
            chrome_options.add_argument("--headless")
            logger.info("Przeglądarka uruchomiona w trybie headless")

        # Dodatkowe opcje dla lepszej stabilności
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")

        # Wyłącz powiadomienia przeglądarki
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,  # 1=allow, 2=block
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.geolocation": 2,
        })

        # User agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Włącz logi przeglądarki dla debugowania (jeśli debugging włączony)
        if self.config.is_debugging_enabled():
            chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

        # Używamy ChromeDriverManager zamiast stałej ścieżki
        service = Service(ChromeDriverManager().install())

        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(self.config.get_wait_timeout())

        logger.info(f"WebDriver zainicjalizowany (headless: {self.config.is_headless()}, timeout: {self.config.get_wait_timeout()}s)")

    def login(self):
        """Loguje się do Facebooka z obsługą opóźnień z konfiguracji."""
        try:
            self.driver.get(settings.LOGIN_URL)

            # Zapisz stan przed logowaniem (jeśli debugging włączony)
            if self.config.should_save_screenshots():
                self.debug_logger.save_debug_snapshot(
                    self.driver,
                    "before_login",
                    f"Próba logowania dla: {self.email}"
                )

            logger.info("🍪 Obsługuję popup cookies...")
            cookie_handled = utils.handle_cookie_popup(self.driver, timeout=2)

            if not cookie_handled:
                logger.warning("⚠ Popup cookies nie został obsłużony, kontynuuję mimo to...")

            # Losowe opóźnienie dla większej naturalności (jeśli włączone w konfiguracji)
            self._apply_random_delay()

            # Znajdź pola email i password i wpisz dane
            utils.wait_for_element_and_send_keys(self.driver, (By.ID, "email"), self.email)
            self._apply_random_delay()

            utils.wait_for_element_and_send_keys(self.driver, (By.ID, "pass"), self.password)
            self._apply_random_delay()

            # Znajdź przycisk logowania i kliknij go
            utils.wait_for_element_and_click(self.driver, (By.NAME, "login"))

            # Czekaj na załadowanie
            time.sleep(5)

            # Zapisz stan po logowaniu (jeśli debugging włączony)
            if self.config.should_save_screenshots():
                self.debug_logger.save_debug_snapshot(
                    self.driver,
                    "after_login",
                    f"Logowanie zakończone dla: {self.email}"
                )

            logger.info("✅ Zalogowano pomyślnie")

        except Exception as e:
            logger.error(f"Błąd podczas logowania: {e}")
            if self.config.should_screenshot_on_error():
                self.debug_logger.save_error_snapshot(self.driver, e)
            raise

    def _apply_random_delay(self):
        """Stosuje losowe opóźnienie zgodnie z konfiguracją bezpieczeństwa."""
        if self.config.should_use_random_delays():
            min_delay = self.config.get_min_delay()
            max_delay = self.config.get_max_delay()
            delay = random.uniform(min_delay, max_delay)
            time.sleep(delay)

    def navigate_to_messenger(self):
        """Przechodzi do Messenger poprzez bezpośrednią nawigację do URL."""
        try:
            # Zapisz przed przejściem (jeśli debugging włączony)
            if self.config.should_save_screenshots():
                self.debug_logger.save_debug_snapshot(
                    self.driver,
                    "before_messenger",
                    "Przed przejściem do Messengera"
                )

            # Bezpośrednia nawigacja do Messenger URL
            logger.info("🔄 Przechodzę do Messenger przez bezpośredni link...")
            self.driver.get("https://www.facebook.com/messages/")
            time.sleep(5)  # Czekaj na załadowanie

            # Sprawdź czy udało się przejść do Messengera
            current_url = self.driver.current_url
            if "messages" in current_url or "messenger.com" in current_url:
                # Zapisz po przejściu (jeśli debugging włączony)
                if self.config.should_save_screenshots():
                    self.debug_logger.save_debug_snapshot(
                        self.driver,
                        "after_messenger",
                        f"Po przejściu do Messengera\nURL: {current_url}"
                    )

                logger.info(f"✅ Przejście do Messengera powiodło się: {current_url}")
                return True
            else:
                logger.error(f"❌ Nie udało się przejść do Messengera. Aktualny URL: {current_url}")
                # Zapisz gdy nie udało się przejść (jeśli debugging włączony)
                if self.config.should_save_screenshots():
                    self.debug_logger.save_debug_snapshot(
                        self.driver,
                        "messenger_navigation_failed",
                        f"Nie udało się przejść do Messengera\nAktualny URL: {current_url}"
                    )
                return False

        except Exception as e:
            logger.error(f"Błąd podczas przechodzenia do Messengera: {e}")
            if self.config.should_screenshot_on_error():
                self.debug_logger.save_error_snapshot(self.driver, e)
            return False

    def close(self):
        """Zamyka przeglądarkę."""
        if self.driver:
            try:
                # Zapisz final state przed zamknięciem (jeśli debugging włączony)
                if self.config.should_save_screenshots():
                    self.debug_logger.save_debug_snapshot(
                        self.driver,
                        "before_close",
                        "Przed zamknięciem przeglądarki"
                    )
            except Exception as e:
                logger.warning(f"Nie udało się zapisać final snapshot: {e}")

            self.driver.quit()
            logger.info("🔒 Zamknięto przeglądarkę")