#src/facebook_bot.py
"""
Klasa do logowania i interakcji z Facebookiem.
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import settings
from src import utils
from src.debug_logger import DebugLogger  # NOWE


class FacebookBot:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None
        self.debug_logger = DebugLogger()  # NOWE
        self.setup_driver()

    def setup_driver(self):
        """Inicjalizuje WebDriver."""
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        
        # Dodatkowe opcje dla lepszej stabilności
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        
        # NOWE: Wyłącz powiadomienia przeglądarki
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,  # 1=allow, 2=block
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.geolocation": 2,
        })
        
        # User agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Włącz logi przeglądarki dla debugowania
        chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        
        # Używamy ChromeDriverManager zamiast stałej ścieżki
        service = Service(ChromeDriverManager().install())
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(settings.WAIT_TIMEOUT)

    def login(self):
        """Loguje się do Facebooka."""
        try:
            self.driver.get(settings.LOGIN_URL)
            
            # NOWE: Zapisz stan przed logowaniem
            self.debug_logger.save_debug_snapshot(
                self.driver,
                "before_login",
                f"Próba logowania dla: {self.email}"
            )
            
            print("🍪 Obsługuję popup cookies...")
            cookie_handled = utils.handle_cookie_popup(self.driver, timeout=2)  # Zwiększ z 5 do 10
            
            if not cookie_handled:
                print("⚠ Popup cookies nie został obsłużony, kontynuuję mimo to...")
                
            time.sleep(2)

            # Znajdź pola email i password i wpisz dane
            utils.wait_for_element_and_send_keys(self.driver, (By.ID, "email"), self.email)
            utils.wait_for_element_and_send_keys(self.driver, (By.ID, "pass"), self.password)
            
            # Znajdź przycisk logowania i kliknij go
            utils.wait_for_element_and_click(self.driver, (By.NAME, "login"))
            
            # Opcjonalnie: czekaj, aż strona się załaduje po zalogowaniu
            time.sleep(5)
            
            # NOWE: Zapisz stan po logowaniu
            self.debug_logger.save_debug_snapshot(
                self.driver,
                "after_login",
                f"Logowanie zakończone dla: {self.email}"
            )
            
        except Exception as e:
            print(f"Błąd podczas logowania: {e}")
            self.debug_logger.save_error_snapshot(self.driver, e)  # NOWE
            raise

    def navigate_to_messenger(self):
        """Przechodzi do Messenger."""
        try:
            # Znajdź link do Messengera w pasku nawigacyjnym
            messenger_link = utils.wait_for_element_presence(
                self.driver, 
                (By.CSS_SELECTOR, "a[aria-label='Messenger']")
            )
            
            if messenger_link:
                # NOWE: Zapisz przed przejściem
                self.debug_logger.save_debug_snapshot(
                    self.driver,
                    "before_messenger",
                    "Przed przejściem do Messengera"
                )
                
                messenger_link.click()
                time.sleep(3)  # Czekaj na załadowanie
                
                # NOWE: Zapisz po przejściu
                self.debug_logger.save_debug_snapshot(
                    self.driver,
                    "after_messenger",
                    "Po przejściu do Messengera"
                )
                
                return True
            else:
                print("Nie udało się znaleźć linku do Messengera.")
                # NOWE: Zapisz gdy nie znaleziono
                self.debug_logger.save_debug_snapshot(
                    self.driver,
                    "messenger_not_found",
                    "Nie znaleziono linku do Messengera"
                )
                return False
                
        except Exception as e:
            print(f"Błąd podczas przechodzenia do Messengera: {e}")
            self.debug_logger.save_error_snapshot(self.driver, e)  # NOWE
            return False

    def close(self):
        """Zamyka przeglądarkę."""
        if self.driver:
            try:
                # NOWE: Zapisz final state przed zamknięciem
                self.debug_logger.save_debug_snapshot(
                    self.driver,
                    "before_close",
                    "Przed zamknięciem przeglądarki"
                )
            except Exception as e:
                print(f"Nie udało się zapisać final snapshot: {e}")
            
            self.driver.quit()