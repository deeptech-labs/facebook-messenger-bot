"""
Główny plik uruchamiający bota z obsługą konfiguracji z bot_config.md.
"""
import os
import logging
from dotenv import load_dotenv
from src import utils
from src.facebook_bot import FacebookBot
from src.messenger_monitor import MessengerMonitor
from config import settings

# Załaduj zmienne środowiskowe z .env
load_dotenv()

# Pobierz logger
logger = logging.getLogger(__name__)


def print_config_info(config):
    """Wyświetla informacje o konfiguracji."""
    print("\n" + "="*60)
    print("📋 KONFIGURACJA BOTA")
    print("="*60)
    print(f"Tryb działania:        {config.get_mode()}")
    print(f"Zakres monitorowania:  {config.get_scope()}")
    print(f"Interwał monitorowania: {config.get_polling_interval()}s")
    print(f"Tryb headless:         {config.is_headless()}")
    print(f"Debugging włączony:    {config.is_debugging_enabled()}")
    print(f"Powiadomienia:         {config.are_notifications_enabled()}")

    # Jeśli zakres to specific, wyświetl konwersacje
    if config.get_scope() == 'specific':
        conversations = config.get_specific_conversations()
        if conversations:
            print(f"\nMonitorowane konwersacje ({len(conversations)}):")
            for conv in conversations:
                if conv.get('enabled', False):
                    print(f"  • {conv.get('name')} (priorytet: {conv.get('priority', 'medium')})")

    print("="*60 + "\n")


if __name__ == "__main__":
    # Ustaw logowanie
    utils.setup_logging()

    # Załaduj konfigurację
    config = settings.config

    # Wyświetl informacje o konfiguracji
    print_config_info(config)

    # Pobierz dane logowania z .env
    email = os.getenv("FACEBOOK_EMAIL")
    password = os.getenv("FACEBOOK_PASSWORD")

    if not email or not password:
        logger.error("❌ Błąd: Nie znaleziono EMAIL lub PASSWORD w pliku .env")
        print("❌ Błąd: Nie znaleziono EMAIL lub PASSWORD w pliku .env")
        exit(1)

    logger.info(f"🚀 Uruchamianie bota w trybie: {config.get_mode()}")
    print(f"🚀 Uruchamianie bota w trybie: {config.get_mode()}...")

    # Inicjalizacja bota z konfiguracją
    bot = FacebookBot(email, password, config=config)

    try:
        # Logowanie
        bot.login()
        logger.info("✅ Zalogowano pomyślnie")
        print("✅ Zalogowano pomyślnie.")

        # Przejście do Messengera
        if bot.navigate_to_messenger():
            logger.info("✅ Przejście do Messengera powiodło się")
            print("✅ Przejście do Messengera powiodło się.")

            # Inicjalizacja monitora z konfiguracją
            monitor = MessengerMonitor(bot.driver, config=config)

            # Wyświetl listę wszystkich dostępnych czatów
            print("\n📋 Pobieranie listy czatów...")
            conversations = monitor.list_all_conversations()

            # Zapisz wszystkie widoczne czaty do folderu data
            print("\n💾 Zapisywanie metadanych konwersacji do folderu data...")
            monitor.save_conversations_to_file(conversations)

            # AUTOMATYCZNA EKSTRAKCJA W TRYBIE EXTRACT
            mode = config.get_mode()

            # Sprawdź czy w trybie extract lub czy jakieś konwersacje mają akcję "extract_history" lub "save_messages"
            should_auto_extract = mode == 'extract'

            # Jeśli nie tryb extract, sprawdź actions w specific_conversations
            if not should_auto_extract and config.get_scope() == 'specific':
                specific_convs = config.get_specific_conversations()
                for conv_config in specific_convs:
                    if conv_config.get('enabled', True):
                        actions = conv_config.get('actions', [])
                        if 'extract_history' in actions or 'save_messages' in actions:
                            should_auto_extract = True
                            break

            if should_auto_extract:
                # AUTOMATYCZNA EKSTRAKCJA
                print(f"\n🚀 Tryb: {mode} - automatycznie ekstraktuję wiadomości...")
                logger.info(f"Automatyczna ekstrakcja wiadomości (tryb: {mode})")

                monitor.extract_and_save_all_conversations(
                    conversations=conversations,
                    output_dir='data',
                    max_conversations=None
                )

                print("\n✅ Ekstrakcja wiadomości zakończona!")
            else:
                # INTERAKTYWNE PYTANIE (tylko dla innych trybów)
                print("\n📥 Ekstraktuję wiadomości z konwersacji...")
                extract_choice = input("Czy chcesz wyekstraktować wiadomości z konwersacji? (t/n): ").lower()

                if extract_choice == 't':
                    max_conv = input("Ile konwersacji przetwarzać? (Enter = wszystkie, liczba = limit): ").strip()
                    max_conversations = int(max_conv) if max_conv.isdigit() else None

                    print(f"\n🚀 Rozpoczynam ekstrakcję wiadomości...")
                    monitor.extract_and_save_all_conversations(
                        conversations=conversations,
                        output_dir='data',
                        max_conversations=max_conversations
                    )

                    print("\n✅ Ekstrakcja wiadomości zakończona!")

            # Uruchomienie pętli monitorującej (interwał z konfiguracji)
            # Tylko jeśli monitoring jest włączony w konfiguracji
            if config.is_monitoring_enabled():
                monitor_choice = input("\nCzy chcesz uruchomić monitoring? (t/n): ").lower()

                if monitor_choice == 't':
                    print(f"\n🔄 Rozpoczynam monitorowanie (interwał: {config.get_polling_interval()}s)...")
                    print("   Naciśnij Ctrl+C aby zatrzymać.\n")
                    monitor.run_monitoring_loop()
                else:
                    print("\n✅ Zakończono bez uruchamiania monitoringu.")
            else:
                print("\n✅ Monitoring wyłączony w konfiguracji. Zakończono.")
        else:
            logger.error("❌ Nie udało się przejść do Messengera")
            print("❌ Nie udało się przejść do Messengera.")

    except KeyboardInterrupt:
        logger.info("⏹️ Przerwano przez użytkownika")
        print("\n⏹️ Przerwano przez użytkownika.")
    except Exception as e:
        logger.error(f"❌ Krytyczny błąd: {e}")
        print(f"\n❌ Krytyczny błąd: {e}")
    finally:
        # Zawsze zamknij przeglądarkę na końcu
        bot.close()
        logger.info("🔒 Zamknięto przeglądarkę")
        print("🔒 Zamknięto przeglądarkę.")
