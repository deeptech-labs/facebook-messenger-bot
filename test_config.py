#!/usr/bin/env python
"""
Test skrypt dla parsera konfiguracji.
"""
import sys
import os

# Dodaj katalog projektu do ścieżki
sys.path.insert(0, os.path.dirname(__file__))

from config.config_parser import ConfigParser


def test_parser():
    """Test parsera konfiguracji."""
    print("=" * 60)
    print("📋 TEST PARSERA KONFIGURACJI")
    print("=" * 60)

    try:
        # Utwórz parser
        parser = ConfigParser('bot_config.md')
        print("✅ Parser zainicjalizowany pomyślnie\n")

        # Test głównych metod
        print("📌 GŁÓWNE USTAWIENIA:")
        print(f"  Tryb działania:         {parser.get_mode()}")
        print(f"  Zakres monitorowania:   {parser.get_scope()}")
        print(f"  Interwał monitorowania: {parser.get_polling_interval()}s")
        print(f"  Timeout oczekiwania:    {parser.get_wait_timeout()}s")
        print(f"  Tryb headless:          {parser.is_headless()}")

        print("\n📌 MONITORING:")
        print(f"  Monitoring włączony:    {parser.is_monitoring_enabled()}")
        print(f"  Wykrywanie wiadomości:  {parser.should_detect_new_messages()}")
        print(f"  Wykrywanie pisania:     {parser.should_detect_typing()}")
        print(f"  Śledzenie licznika:     {parser.should_track_message_count()}")

        print("\n📌 POWIADOMIENIA:")
        print(f"  Powiadomienia włączone: {parser.are_notifications_enabled()}")
        print(f"  Metody powiadamiania:   {', '.join(parser.get_notification_methods())}")

        print("\n📌 DEBUG:")
        print(f"  Debugging włączony:     {parser.is_debugging_enabled()}")
        print(f"  Zapisywanie screenshots: {parser.should_save_screenshots()}")
        print(f"  Screenshot przy błędzie: {parser.should_screenshot_on_error()}")
        print(f"  Poziom logowania:       {parser.get_log_level()}")

        print("\n📌 BEZPIECZEŃSTWO:")
        print(f"  Losowe opóźnienia:      {parser.should_use_random_delays()}")
        print(f"  Minimalne opóźnienie:   {parser.get_min_delay()}s")
        print(f"  Maksymalne opóźnienie:  {parser.get_max_delay()}s")
        print(f"  Szanuj rate limits:     {parser.should_respect_rate_limits()}")

        # Test konwersacji
        print("\n📌 KONWERSACJE:")
        conversations = parser.get_specific_conversations()
        print(f"  Liczba konwersacji:     {len(conversations)}")

        if conversations:
            print("\n  Włączone konwersacje:")
            for conv in conversations:
                if conv.get('enabled', False):
                    name = conv.get('name', 'Nieznana')
                    priority = conv.get('priority', 'medium')
                    actions = ', '.join(conv.get('actions', []))
                    print(f"    • {name}")
                    print(f"      Priorytet: {priority}")
                    print(f"      Akcje: {actions}")

        # Test dostępu przez notację kropkową
        print("\n📌 TEST DOSTĘPU PRZEZ NOTACJĘ KROPKOWĄ:")
        test_keys = [
            'mode',
            'debugging.enabled',
            'debugging.log_level',
            'security.min_delay',
            'notifications.methods'
        ]

        for key in test_keys:
            value = parser.get(key)
            print(f"  {key}: {value}")

        print("\n" + "=" * 60)
        print("✅ WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ BŁĄD: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_parser()
    sys.exit(0 if success else 1)
