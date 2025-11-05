"""
Główny plik uruchamiający bota.
"""
import os
from dotenv import load_dotenv
from src import utils
from src.facebook_bot import FacebookBot
from src.messenger_monitor import MessengerMonitor
from config import settings

# Załaduj zmienne środowiskowe z .env
load_dotenv()

if __name__ == "__main__":
    # Ustaw logowanie
    utils.setup_logging()

    email = os.getenv("FACEBOOK_EMAIL")
    password = os.getenv("FACEBOOK_PASSWORD")

    if not email or not password:
        print("Błąd: Nie znaleziono EMAIL lub PASSWORD w pliku .env")
        exit(1)

    # Inicjalizacja bota
    bot = FacebookBot(email, password)

    try:
        # Logowanie
        bot.login()
        print("Zalogowano pomyślnie.")

        # Przejście do Messengera
        if bot.navigate_to_messenger():
            print("Przejście do Messengera powiodło się.")
            # Inicjalizacja monitora
            monitor = MessengerMonitor(bot.driver)
            # Uruchomienie pętli monitorującej
            monitor.run_monitoring_loop(settings.POLLING_INTERVAL)
        else:
            print("Nie udało się przejść do Messengera.")

    except KeyboardInterrupt:
        print("\nPrzerwano przez użytkownika.")
    finally:
        # Zawsze zamknij przeglądarkę na końcu
        bot.close()
        print("Zamknięto przeglądarkę.")
